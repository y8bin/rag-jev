import asyncio
import json
import shutil
from pathlib import Path

import httpx
import numpy as np
import pytest
from qdrant_client import QdrantClient, models

from legal_rag_jev.config import Config
from legal_rag_jev.index import VectorIndex, build_index, eligible, point_id
from legal_rag_jev.providers import Providers, Result


@pytest.mark.parametrize('policy', ['include', 'exclude'])
@pytest.mark.parametrize('filters', [True, False])
def test_filter_matches_existing_temporal_rules(corpus, policy, filters):
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={'unknown_temporal_policy': policy, 'apply_metadata_filters': filters})
    chunks += [dict(chunks[0], chunk_id='unknown', effective_from=None),
               dict(chunks[0], chunk_id='future', effective_from='2026-01-01'),
               dict(chunks[0], chunk_id='unknown-ended', effective_from=None, effective_to='2025-01-01')]

    async def check():
        p = Providers(cfg)
        try:
            await build_index(cfg, chunks, p)
            with VectorIndex(cfg, p) as idx:
                for when in ['2019-01-01', '2024-12-31', '2025-01-01', '2027-01-01', None]:
                    for jurisdiction in ['KR', 'US', 'absent', '']:
                        query = dict(q.json_record(), as_of_date=when, jurisdiction=jurisdiction)
                        result = await idx.search(query)
                        expected = [c for c in chunks if eligible(c, query, cfg)]
                        assert result['eligible_count'] == len(expected)
                        assert len(result['candidates']) == min(len(expected), cfg.top_k)
                        assert all(eligible(c, query, cfg) for c in result['candidates'])
                empty = await idx.search(dict(q.json_record(), jurisdiction='absent'))
                if filters:
                    assert empty['candidates'] == []
        finally:
            await p.close()
    asyncio.run(check())


def test_exact_cosine_order_and_boundary_ties(corpus):
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={'apply_metadata_filters': False, 'top_k': 2})
    chunks = [dict(chunks[0], chunk_id=c) for c in ['z', 'a', 'b', 'lower']]
    matrix = np.array([[3, 4], [3, 4], [3, 4], [-3, -4]], dtype=np.float32)

    async def check():
        p = Providers(cfg)
        async def embed(texts, query=False):
            return Result(matrix[:1] if query else matrix, {})
        p.embed = embed
        try:
            m = await build_index(cfg, chunks, p)
            with VectorIndex(cfg, p) as idx:
                result = await idx.search(q.json_record())
                assert [c['chunk_id'] for c in result['candidates']] == ['a', 'b']
                assert [c['vector_rank'] for c in result['candidates']] == [1, 2]
                assert np.allclose([c['vector_score'] for c in result['candidates']], 1)
                assert result['eligible_count'] == 4
                assert m['dimension'] == 2
        finally:
            await p.close()
    asyncio.run(check())


@pytest.mark.parametrize('change', ['payload', 'vector', 'delete'])
def test_live_collection_mutation_detected_and_lock_released(corpus, change):
    cfg, _, chunks, _ = corpus
    async def check():
        p = Providers(cfg)
        try:
            m = await build_index(cfg, chunks, p)
            client = QdrantClient(path=str(Path(cfg.index_dir) / 'qdrant'))
            try:
                pid = point_id(chunks[0]['chunk_id'])
                if change == 'payload':
                    client.set_payload(m['collection'], {'tampered': True}, points=[pid], wait=True)
                elif change == 'vector':
                    client.update_vectors(m['collection'], [models.PointVectors(id=pid, vector=[1.0] + [0.0] * (m['dimension'] - 1))], wait=True)
                else:
                    client.delete(m['collection'], models.PointIdsList(points=[pid]), wait=True)
            finally:
                client.close()
            for _ in range(2):
                with pytest.raises(ValueError, match='integrity|count'):
                    VectorIndex(cfg, p)
        finally:
            await p.close()
    asyncio.run(check())


def test_storage_identity_and_immutable_corpus(corpus):
    cfg, _, chunks, _ = corpus
    async def check():
        p = Providers(cfg)
        try:
            await build_index(cfg, chunks, p)
            with pytest.raises(ValueError, match='immutable'):
                await build_index(cfg, [dict(chunks[0], text='changed'), *chunks[1:]], p)
            with pytest.raises(ValueError, match='Duplicate'):
                await build_index(cfg, [chunks[0], chunks[0]], p)
            changed = cfg.model_copy(update={'qdrant_collection': 'different'})
            with pytest.raises(ValueError, match='mismatch'):
                VectorIndex(changed, p)
            shutil.rmtree(Path(cfg.index_dir) / 'qdrant')
            with pytest.raises(ValueError, match='missing'):
                VectorIndex(cfg, p)
            assert not (Path(cfg.index_dir) / 'qdrant').exists()
        finally:
            await p.close()
    asyncio.run(check())


@pytest.mark.parametrize('fail_first_upload', [False, True])
def test_server_rest_build_load_search_and_auth(corpus, monkeypatch, fail_first_upload):
    import legal_rag_jev.index as module
    cfg, _, chunks, q = corpus
    cfg = cfg.model_copy(update={'qdrant_mode': 'remote'})
    monkeypatch.setenv('QDRANT_BASE_URL', 'https://qdrant.test.invalid')
    monkeypatch.setenv('QDRANT_API_KEY', 'test-only-key')
    server = QdrantClient(':memory:')
    requests = []
    failures = [fail_first_upload]
    def handle(request):
        requests.append(request)
        assert request.headers['api-key'] == 'test-only-key'
        parts = request.url.path.strip('/').split('/')
        body = json.loads(request.content) if request.content else {}
        collection = parts[1] if len(parts) > 1 else None
        action = '/'.join(parts[2:])
        if parts == ['']:
            result = {'title': 'qdrant', 'version': '1.19.0'}
            return httpx.Response(200, json=result)
        if action == 'exists':
            result = {'exists': server.collection_exists(collection)}
        elif action == '' and request.method == 'PUT':
            result = server.create_collection(collection, vectors_config=models.VectorParams(**body['vectors']))
        elif action == '' and request.method == 'GET':
            result = server.get_collection(collection).model_dump(mode='json')
        elif action == '' and request.method == 'DELETE':
            result = server.delete_collection(collection)
        elif action == 'index':
            result = {'operation_id': 0, 'status': 'completed'}
        elif action == 'points' and request.method == 'PUT':
            if failures[0]:
                failures[0] = False
                return httpx.Response(503, json={'status': {'error': 'upload failed'}})
            result = server.upsert(collection, [models.PointStruct(**p) for p in body['points']], wait=True).model_dump(mode='json')
        elif action == 'points/count':
            result = server.count(collection, count_filter=models.Filter(**body['filter']) if body.get('filter') else None, exact=body['exact']).model_dump(mode='json')
        elif action == 'points/scroll':
            points, offset = server.scroll(collection, offset=body.get('offset'), limit=body['limit'], with_payload=True, with_vectors=True)
            result = {'points': [p.model_dump(mode='json') for p in points], 'next_page_offset': offset}
        elif action == 'points/query':
            assert body['params']['exact'] is True
            query = body['query']
            if isinstance(query, dict):
                query = query['nearest']
            result = server.query_points(collection, query=query,
                query_filter=models.Filter(**body['filter']) if body.get('filter') else None,
                limit=body['limit'], with_payload=True).model_dump(mode='json')
        else:
            raise AssertionError((request.method, request.url, body))
        return httpx.Response(200, json={'result': result, 'status': 'ok', 'time': 0.0})
    transport = httpx.MockTransport(handle)
    def client_factory(**kwargs):
        return QdrantClient(**kwargs, transport=transport, check_compatibility=False)
    monkeypatch.setattr(module, 'QdrantClient', client_factory)
    async def check():
        p = Providers(cfg)
        try:
            if fail_first_upload:
                from qdrant_client.http.exceptions import UnexpectedResponse
                with pytest.raises(UnexpectedResponse):
                    await build_index(cfg, chunks, p)
                assert server.get_collections().collections == []
                assert not Path(cfg.index_dir).exists()
                assert not list(Path(cfg.index_dir).parent.glob('.index-*'))
            m = await build_index(cfg, chunks, p)
            assert not (Path(cfg.index_dir) / 'qdrant').exists()
            assert 'test-only-key' not in json.dumps(m)
            with VectorIndex(cfg, p) as idx:
                found = await idx.search(q.json_record())
                assert [c['doc_id'] for c in found['candidates']] == ['law']
                assert found['eligible_count'] == 1
            assert (await build_index(cfg, chunks, p))['index_version'] == m['index_version']
            other = cfg.model_copy(update={'index_dir': cfg.index_dir + '-other'})
            with pytest.raises(ValueError, match='already exists'):
                await build_index(other, chunks, p)
            assert server.count(m['collection'], exact=True).count == len(chunks)
            assert not Path(other.index_dir).exists()
            index_requests = [r for r in requests if r.url.path.endswith('/index')]
            assert len(index_requests) == (6 if fail_first_upload else 3)
            assert all(r.url.params.get('wait') == 'true' for r in index_requests)
            query_request = next(r for r in requests if r.url.path.endswith('/query'))
            assert 'filter' in json.loads(query_request.content)
        finally:
            await p.close()
            server.close()
    asyncio.run(check())


def test_invalid_collection_prefix_rejected():
    with pytest.raises(ValueError):
        Config(qdrant_collection='../invalid')
