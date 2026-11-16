"""Guard upstream compatibility and the audited cross-pool indexing fix."""
import ast
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('reproduction',Path('scripts/experiment/run_koblex_reproduction.py'))
reproduction=importlib.util.module_from_spec(spec)
spec.loader.exec_module(reproduction)
reproduction.UP=Path("data/koblex/upstream")
reproduction.QA=reproduction.UP/"experiments/source/koblex.jsonl"


def test_raw_selection_matches_upstream_and_fix_stays_in_displayed_pool():
    tree=ast.parse((reproduction.UP/'experiments/parser/openai/selection_retrieval.py').read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='process_completions')
    scope={'List':list,'Any':object}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'upstream-selection','exec'),scope)
    pools=[list(range(10)),list(range(100,110)),list(range(200,210))]
    responses=[('Answer: 2',0),('Answer: 4',0),('invalid',0)]
    choices=[reproduction.choice_from(t) for t,_ in responses]
    upstream=scope['process_completions'](responses,[3],[pools])[0]
    assert reproduction.selected_from(pools,choices,raw=True)==upstream==[2,4,0]
    assert reproduction.selected_from(pools,choices)==[2,104,200]


def test_parametric_parser_preserves_upstream_escape_and_empty_behavior():
    assert reproduction.parse_subs('Answer: ["법령 하나", "법령 둘"]')==['법령 하나','법령 둘']
    assert reproduction.parse_subs('No list returned')==[]
    assert reproduction.choice_from('Answer: 10')==0
    assert reproduction.choice_from('Answer: 9')==9


def test_online_question_whitelist_excludes_all_gold_fields():
    questions=reproduction.input_questions()
    assert len(questions)==226
    assert all(set(q)=={'id','background','question'} for q in questions)


def test_generation_prompt_is_verbatim_upstream_template():
    import runpy
    module=runpy.run_path(str(reproduction.UP/'experiments/parser/prompts/question_answering.py'))
    expected=module['SYSTEM_PROMPT']+'\n\n'+module['INSTRUCTION_PROMPT'].substitute(question='Q',context_str='LAW')
    assert reproduction.prompt('question_answering',question='Q',context_str='LAW')==expected


def test_concurrent_answer_runner_preserves_raw_fixed_mapping_and_export_order(tmp_path,monkeypatch):
    import asyncio
    import contextlib
    import json
    import sys
    sys.path.insert(0,str(Path('scripts/experiment').resolve()))
    import run_koblex_reproduction_answers as runner
    study=runner.study
    from legal_rag_jev.config import Config
    from legal_rag_jev.io import write_jsonl,read_jsonl
    root=tmp_path/'study';root.mkdir()
    (root/'protocol-lock.json').write_text('{}')
    corpus=tmp_path/'corpus.jsonl'
    write_jsonl(corpus,[{'hierarchy':'LAW','content':str(i)} for i in range(20)])
    questions=[{'id':f'Q{i}','background':'BG','question':f'QUESTION{i}'} for i in range(6)]
    for kind in ('ce','jev'):
        write_jsonl(root/f'ranking-{kind}.jsonl',[{'query_id':q['id'],'pools':[
            {'top10_row_ids':list(range(10))},{'top10_row_ids':list(range(10,20))}]} for q in questions])
    monkeypatch.setattr(study,'ROOT',root);monkeypatch.setattr(study,'CORPUS',corpus)
    monkeypatch.setattr(study,'freeze',lambda cfg:None)
    monkeypatch.setattr(study,'input_questions',lambda:questions)
    monkeypatch.setattr(runner,'environment_file_scope',lambda *args:contextlib.nullcontext())
    monkeypatch.setattr(runner.Config,'load',lambda *args:Config())
    active=0;maximum=0
    async def chat(cfg,transport,text):
        nonlocal active,maximum
        active+=1;maximum=max(maximum,active)
        await asyncio.sleep(.001)
        active-=1
        return ('Answer: 2' if text.startswith('selection_retrieval') else 'Answer: RESULT'),{}
    monkeypatch.setattr(study,'chat',chat)
    monkeypatch.setattr(study,'prompt',lambda name,**kwargs:name+json.dumps(kwargs))
    class NoNetwork:
        def __init__(self,cfg):pass
        async def close(self):pass
    monkeypatch.setattr(runner,'Transport',NoNetwork)
    asyncio.run(runner.main())
    assert 1<maximum<=4
    for arm in study.ARMS:
        rows=read_jsonl(root/'predictions'/f'{arm}.jsonl')
        assert [r['query_id'] for r in rows]==[q['id'] for q in questions]
        assert all(r['selected_row_ids']==([2,2] if arm=='parser_ce_raw' else [2,12]) for r in rows)
        assert all(r['answer']=='RESULT' for r in rows)


def test_token_window_waits_for_expiry_and_rejects_oversized_request():
    import asyncio
    import sys
    import time
    sys.path.insert(0,str(Path('scripts/experiment').resolve()))
    from run_koblex_reproduction_answers_paced import TokenWindow
    async def exercise():
        window=TokenWindow(limit=100,period=.02)
        await window.acquire(60)
        started=time.monotonic()
        await window.acquire(60)
        assert time.monotonic()-started>=.02
        assert sum(w for _,w in window.events)<=100
        with pytest.raises(ValueError):await window.acquire(101)
    asyncio.run(exercise())
