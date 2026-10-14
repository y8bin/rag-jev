# 현재 진행 상황과 실험 시작 안내

확인일: 2026-10-14. 기존 Markdown과 감사 문서를 현재 코드·파일에 대조하고, 기존 70개 테스트 통과를 확인한 뒤 논문 검증 보완 및 회귀 테스트를 진행했다. 현재 **88 passed**이며 오프라인 `readiness`에서 연구 입력·인덱스·비용 누락을 확인했다. 실제 모델 API 호출, 원격 Qdrant 접속, 법률 데이터 실험과 최신 서비스 요금 확인은 이번 작업에서 수행하지 않았다. 단계별 실행과 자료 양식은 [논문 검증 실행서](PAPER_VALIDATION_RUNBOOK.md)를 따른다.

## 1. 현재 어디까지 진행됐는가

**연구 설계와 실험 실행 도구가 준비되어 있고, 가상 데이터로 전체 흐름을 확인한 상태다. 실제 법률 데이터 파일럿과 성능 검증은 아직 시작되지 않았다.** 최종 전략의 실행 단계로 보면 단계 0(범위·API·평가 인력 확인)을 마무리해야 한다.

| 항목 | 확인한 상태 | 의미 |
|---|---|---|
| 연구 설계 | 자체 코퍼스, 5개 비교군, 검색·답변·비용 평가 절차 작성 | 실행 기준 있음 |
| Python CLI | ingest부터 통계·그림까지 구현 | 새 실행기를 처음부터 만들 필요 없음 |
| 환경 | `.venv`와 Qdrant, sentence-transformers, torch, pypdf, matplotlib 등 설치 확인 | 모델 가중치·실제 추론 성공까지 확인한 것은 아님 |
| 자동 검증 | `.venv/bin/python -m pytest -q`: **88 passed** | 지표 v2·주장 완전성·인용 일치도·FR 통계/불가능 분기·pilot 보호·계획 잠금 검증; HTTP는 mock 기반 |
| 예제 입력 | 가상 문서 6행, 질문 6행(dev 3/test 3), 청크 6개 | 연구용 원문·평가 세트 아님 |
| 이전 산출물 | 프로젝트 밖 별도 보관 후 현재 데모 재생성 | `/private/tmp/rag-jev-before-qdrant-20261012/demo-artifacts.tar.gz` |
| 이번 합성 CLI 재검증 | 격리 Qdrant 로컬 영속 모드, dev 3문항 × 5방법 = 15행·실패 0 | `results/preparation/engineering_20261014/runs/20261014T022851_4764d168`, 연구 유효성 false |
| 이전 Qdrant smoke | `status: ok`, 6 points, 256차원, 필터 후 5개 중 5개 반환 | 2026-10-12 기록; 현재 로컬 무결성·검색은 자동 테스트와 합성 CLI로 재검증 |
| 실제 코퍼스 | `data/raw`, `data/processed` 없음 | 데이터 구축 필요 |
| 실제 모델·API 설정 | `.env` 있음; 임베딩·CE·Jev 식별 설정 로컬 확인 | 새 코드에서 실제 인증·계약·usage/단가 검증 필요 |
| 실제 인덱스 | `indexes/main` 없음 | 실제 임베딩으로 새로 구축 필요 |
| 평가·최종 시험 | 사람 판정, `configs/final.yaml`, 시험 lock 없음 | 개발·튜닝·잠금 시험 미수행 |
| 코드 이력 | Git 저장소 있음. 환경 manifest에 commit·dirty·패키지 전체 기록 | 실행 commit과 implementation digest 함께 보존 |
| 준비 자료 | pilot/pilot-answers/split/dev YAML, 범위·평가·통계 초안, 입력 manifest 양식, 71개 환경 pin | 실제 데이터·사람 승인·재설치 검증은 미완료 |

데모는 임베딩·CE·Jev·생성 모두 mock이며 `research_valid: false`다. 사람 답변 평가도 없다. 데모의 높은 검색 점수나 0원 비용은 Jev의 실제 성능·가격을 의미하지 않는다. 실제 Qdrant를 사용했다는 사실만으로 연구 결과가 되지 않는다.

## 2. 문서를 읽는 순서와 최종 연구 방향

1. [final_research_strategy.md](final_research_strategy.md): 최신 연구 결정과 평가 원칙.
2. [README.md](README.md): 실제 CLI, 환경변수, 파일 형식, 사람 평가 절차.
3. [legal_rag_jev_experiment_design (1).md](legal_rag_jev_experiment_design%20%281%29.md): 보조 실험 설계. 충돌하면 최종 전략 우선.
4. [legal_rag_jev_paper_design.md](legal_rag_jev_paper_design.md): 최초 논문 구상과 목차 참고. 공개 벤치마크 사용·4개 비교군·최소 1개 근거 선택 등의 옛 조건은 폐기됨.

현재 실행 기준은 Qdrant를 사용하는 README와 `src/legal_rag_jev`다. 초기 설계의 예시 필드보다 현재 `schemas/`와 `schema.py`를 우선한다.

최종 연구는 자체 법률 원문·질문·정답 근거를 사용한다. LegalBench-RAG/KBL은 현재 계획의 필수 다운로드 대상이 아니다. Jev는 후보가 질문의 직접 법적 근거인지 판단하며, 최종 답변은 별도 생성 모델이 만든다.

| 비교군 | 공통 후보 K개 이후의 동작 |
|---|---|
| Vector | 벡터 순서 상위 N개 |
| CE-R | Cross-Encoder 재채점 후 상위 N개 |
| CE-FR | CE 문턱값을 통과한 후보 중 최대 N개, 0개 가능 |
| Jev-R | Jev 재채점 후 상위 N개 |
| Jev-FR | Jev 문턱값을 통과한 후보 중 최대 N개, 0개 가능 |

초기 설정은 K=20, N=5. 최종 값은 개발 세트에서 고정한다. 연구 질문은 ① 충분한 정답 근거를 더 잘 선택하는가 ② 근거 있는 정답이 늘어나는가 ③ 허용한 품질 하락 이내에서 총비용을 줄이는가다. Jev 우월성은 아직 확인되지 않았다.

## 3. 바로 실행할 수 있는 것: API 없는 데모

현재 `.venv`는 Python 3.12.13과 Qdrant 클라이언트로 구성했다. 네트워크 제한으로 로컬 패키지 캐시를 사용했으며, 이전 Python 3.14 환경은 `/private/tmp/rag-jev-before-qdrant-20261012/python314-environment`에 보관했다. 다른 환경에서는 README의 설치 명령으로 필수 의존성을 설치한다.

```bash
cd /Users/indeep/Desktop/RAG-jev
source .venv/bin/activate
python -m pytest -q
python -m legal_rag_jev --config configs/demo.yaml demo
```

출력되는 `run` 경로에서 다음을 확인한다.

- `completion.json`: 계획한 행 수, 실제 행 수, 실패 수.
- `raw.jsonl`: 질문별 후보, 점수·순위, 선택 근거, 답변, 호출 기록.
- `summary.csv`, `summary.json`: 방법별 집계와 평가 분모.
- `statistics.json`, `confidence_intervals.json`: 통계 출력 형식. 이 소규모 가상 예제에서 과학적 결론을 내리지 않는다.

데모와 실제 실행 모두 Qdrant를 사용한다. 로컬 모드는 서버 없이 실행하며, 서버 연결은 `qdrant_mode: remote`와 `QDRANT_BASE_URL/API_KEY`로 설정한다. 서버 HTTP 계약과 실패 시 컬렉션 정리는 mock transport로 확인했고 실제 서버 접속은 수행하지 않았다.

### Qdrant 전환으로 달라진 실행 조건

현재 `configs/main.yaml`과 `configs/demo.yaml`은 모두 아래 저장 방식을 사용한다. `.venv`에서 확인한 `qdrant-client` 버전은 1.19.0이다.

```yaml
index_backend: qdrant
qdrant_mode: local
qdrant_collection: legal_rag
```

| 항목 | 현재 구현 |
|---|---|
| 벡터 저장 | 로컬은 `index_dir/qdrant/`, remote는 지정한 서버/Cloud 컬렉션 |
| 메타데이터 | UUID point ID와 payload의 `chunk`에 원문·판본·관할·효력·오프셋 저장 |
| 검색 | 정규화 벡터의 Dot 점수; remote는 `exact=True`, local은 정확 검색 |
| 필터 | Qdrant 질의에 관할·효력 기간 필터 적용 |
| 동점 | 점수 내림차순 이후 chunk_id 순서 |
| 재현 기록 | 로컬 manifest·chunks 스냅샷과 실제 point 벡터·payload 해시 검증 |
| 컬렉션 이름 | `qdrant_collection`은 접두어이며 실제 이름에는 index_version이 붙음 |

로컬 모드에는 Docker, 서버 주소, Qdrant API 키가 필요 없다. 같은 저장소는 한 프로세스만 열 수 있으므로 같은 index_dir로 두 CLI를 동시에 실행하지 않는다. Qdrant 서버를 localhost에서 실행하더라도 HTTP로 접속하면 이 프로젝트 설정에서는 `remote`다.

원격 연결이 필요하면 별도 설정에서 다음과 같이 지정한다. 아래 주소는 실행 중인 로컬 서버가 있을 때의 예시다.

```yaml
index_backend: qdrant
qdrant_mode: remote
qdrant_collection: legal_rag
index_dir: indexes/pilot_remote_v1
```

```dotenv
QDRANT_BASE_URL=http://localhost:6333
QDRANT_API_KEY=
```

Cloud라면 실제 클러스터 주소와 키를 사용한다. remote도 로컬 index_dir의 manifest와 chunks 스냅샷이 필요하다. 기존 임의 컬렉션 이름을 넣어 바로 연결하는 구조가 아니므로, 이미 보유한 컬렉션을 쓰려면 현재 point/payload 스키마와 manifest를 맞추는 별도 이관이 필요하다.

이전 FAISS 인덱스·캐시·시험 lock은 재사용하지 않는다. 원문·청크를 바탕으로 Qdrant 인덱스를 새로 만들고, 평가 실행 및 lock도 새로 생성한다. 코퍼스·모델·로컬/원격 모드·서버 주소·접두어가 달라지면 새 index_dir를 사용한다.

**대규모 실행 전 확인할 구현 한계:** 현재 검색은 필터를 통과한 전체 point의 점수와 payload를 받아 정렬한 뒤 K개를 고른다. 인덱스를 열 때도 모든 벡터와 payload를 읽어 해시를 검사한다. 따라서 Qdrant로 바뀌었다고 대규모 검색·네트워크 전송이 자동으로 최적화된 것은 아니다. 실제 코퍼스 규모에서 시작 시간·메모리·질의 지연을 측정하고, 필요하면 무결성 검증 시점과 Top-K 동점 처리 방식을 보완해야 한다. 근사 검색을 도입하면 후보 재현율을 별도로 검증한다.

**원격 비용의 한계:** 원격 검색은 별도 `QDRANT_USD_PER_HOUR`로 요청 경과 시간을 환산하며 미입력은 null이다. 로컬 모델 시간 단가로 대체하지 않는다. Cloud 청구액·저장·네트워크·서버 유지비를 자동 수집하지 않으므로 실제 청구와 시간 배분식을 비용 manifest에 기록·검증해야 한다.

## 4. 실제 실험 전에 필요한 준비물

### A. 범위와 원문

법률 분야, 언어, 관할, 포함할 문서 유형, 수집 기준일, 원문 출처·사용 범위를 정한다. `data/raw/corpus.jsonl` 또는 메타데이터를 갖춘 원문 폴더가 필요하다. 수집·크롤링·OCR 자체는 현재 도구가 대신하지 않는다.

문서 필수 필드는 `doc_id`, `version_id`, `group_id`, `text`다. 실험에서는 제목·유형·관할·인용명·출처·수집일·효력 기간도 채운다. 같은 문서의 개정판과 파생 사건은 문서 계열을 일관되게 묶는다.

- `effective_to`는 해당 날짜를 포함하지 않는 종료일이다.
- 기본 시점 정책은 `unknown_temporal_policy: exclude`다. 기준일이 있는 질의에 효력 정보가 불명확한 자료를 넣으면 후보에서 제외될 수 있다.
- 이미지 PDF는 사전에 OCR해야 한다. 폴더 입력은 각 파일 옆에 `파일명.ext.meta.json`이 필요하다.
- 청킹은 조문·문단과 길이 제한에 기반한 구현이다. 실제 판례·표·항호 구조 보존 여부는 샘플 확인이 필요하다.

### B. 질문과 정답 근거

최초 연결 확인에는 실제 질문 10~20개를 준비한다. 이는 100문항 파일럿 전에 하는 소규모 확인 단계다. 같은 파일에서 해당 질문들의 `split`을 `pilot`으로 지정하면 `run --split pilot`으로 실행할 수 있다.

질문은 최소한 다음 정보를 갖춰야 한다.

| 필드 | 작성 내용 |
|---|---|
| `query_id`, `group_id`, `split` | 고유 ID, 누출 방지 그룹, pilot/dev/test |
| `question`, `as_of_date`, `jurisdiction`, `task_type` | 질문, 적용 기준일·관할, 유형 |
| `answerable`, `reference_answer` | 코퍼스로 답할 수 있는지와 기준 답변 |
| `evidence_units` | 정답 근거의 문서·판본·문자 구간 또는 확인된 chunk ID |
| `sufficient_sets` | 답 전체를 뒷받침하는 근거 단위 조합 |
| `relevance` | 검색 후보별 0/1/2 등급. 후보 수집 후 보완 가능 |

`answerable: true`에는 `sufficient_sets`가 반드시 있어야 한다. 따라서 질문만 적은 파일로 현재 실험 CLI를 바로 돌릴 수는 없다. 답할 수 없는 질문에는 `evidence_units: []`, `sufficient_sets: []`를 사용한다.

오프셋은 ingest 후 정규화된 문서의 Python 문자 위치 `[start, end)`다. 원본 PDF 바이트 위치나 정규화 전 위치를 쓰지 않는다. 충분한 근거가 U1과 U2의 조합이면 `[["U1", "U2"]]`, 어느 하나만 있어도 충분하면 `[["U1"], ["U2"]]`다. 후보 관련성 등급을 채워도 이 조합은 자동 생성되지 않는다.

초기 `relevance: {}`로 실행할 수는 있지만 nDCG/MRR 등 후보 등급 기반 평가는 불완전하다. 본 실험 전 공통 후보와 대체 근거를 판정해야 한다.

### C. 모델·API와 비용

```bash
cp .env.example .env
```

현재 `.env`가 이미 있으므로 위 복사 명령을 실행하지 않는다. 새 환경에서 파일이 없을 때만 한 번 복사한다. 키는 `.env`에 입력하고 YAML에는 넣지 않는다.

기본 CLI는 `.env`를 읽는다. 다른 파일을 의도적으로 사용하려면 전역 옵션 `--env-file '파일 경로'`를 지정한다. 파일 내용이나 키는 이 문서에 기록하지 않는다.

| 역할 | 기본 설정에서 필요한 항목 |
|---|---|
| 로컬 임베딩 | `EMBEDDING_LOCAL_MODEL`, `EMBEDDING_LOCAL_REVISION` |
| 로컬 CE | `CE_LOCAL_MODEL`, `CE_LOCAL_REVISION` |
| Jev | `JEV_BASE_URL`, `JEV_API_KEY`, `JEV_MODEL` |
| 생성 | `GENERATION_BASE_URL`, 서비스에 필요한 키, `GENERATION_MODEL` |
| 비용 평가 | Jev·생성 입력/출력 단가, `LOCAL_USD_PER_HOUR`, remote이면 `QDRANT_USD_PER_HOUR` |
| 실행 장치 | `MODEL_DEVICE` 및 모델 다운로드·메모리 여건 |

`BAAI/bge-m3`는 `.env.example`의 임베딩 후보이며 실제 모델 선정이 끝났다는 의미는 아니다. 모델 revision은 정확한 값을 고정한다. Hugging Face 접근 제한이 있는 모델이면 접근 권한과 `HF_TOKEN`도 필요하다.

HTTP 임베딩·CE를 사용할 경우 YAML의 해당 backend를 `http`로 바꾸고 각각 `EMBEDDING_BASE_URL/API_KEY/MODEL`, `CE_BASE_URL/API_KEY/API_MODEL`을 설정한다. 현재 adapter는 `/embeddings`, `/rerank`, `/chat/completions` 응답 형식을 기대한다. BASE_URL에 최종 endpoint를 중복해서 붙이지 않는다.

단가가 없거나 응답 usage가 없으면 비용은 `null`이다. 로컬 Qdrant 검색 비용도 포함하므로 HTTP 모델만 사용하더라도 총비용 평가에는 로컬 비용 기준이 필요하다. 무료인 경우에만 명시적으로 0을 사용한다. 재시도 청구가 불명확한 경우도 비용이 누락될 수 있다. **`tune`은 완전한 비용과 사람 답변 판정이 없으면 진행하지 않는다.**

자동 judge 설정은 첫 실험의 필수 조건이 아니다. `judge`를 실행할 때 필요하며 사람 gold를 자동으로 대체하지 않는다.

### D. 평가 인력과 운영 자료

법률 검토가 가능한 평가자, 판정 지침, 불일치 조정 담당, 평가 시간·예산을 확보한다. 후보 관련성, answerability, 충분한 근거 조합, 최종 답변·주장·인용을 구분해 검토한다. 현재 도구는 JSONL 판정 양식을 내보내고 가져오며, 전용 웹 라벨링 화면은 제공하지 않는다.

본 시험 전 추가 산출물은 수집 명세, 라벨링 루브릭과 예시, 그룹 분할 기록, 실행 예산, 실제 모델·revision·하드웨어 기록, 의존성 lockfile 및 코드 버전 기록이다.

## 5. 실제 10~20문항 연결 확인 순서

아래 명령은 입력 파일과 모델 설정을 준비한 뒤 실행한다. 실제 API 사용량이 발생한다. `legal-rag`와 `python -m legal_rag_jev`는 같은 CLI다.

### 5-1. 별도 파일럿 설정

```bash
cp configs/main.yaml configs/pilot.yaml
```

복사한 파일에서 다음 항목을 변경한다. 나머지는 main의 초기값을 유지한다.

```yaml
documents: data/processed/documents.jsonl
chunks: data/processed/chunks.jsonl
queries: data/processed/queries_pilot.jsonl
index_dir: indexes/pilot_v1
index_backend: qdrant
qdrant_mode: local
qdrant_collection: legal_rag_pilot
output_dir: results/pilot
cache_dir: .cache/pilot
methods: [vector, ce_r, jev_r]
generate: false
```

FR은 개발 문턱값이 아직 없으므로 첫 확인에서는 고정 N의 세 방법을 사용한다. 기본 main은 5방법인데 FR 문턱값이 둘 다 `null`이라 그대로 `run`하면 오류가 난다. 초기 3방법 연결 확인이 끝나면 5방법 파일럿·개발로 확장한다.

### 5-2. 정규화·청킹과 gold 작성

```bash
legal-rag --config configs/pilot.yaml ingest --input data/raw/corpus.jsonl
legal-rag --config configs/pilot.yaml chunk
```

이제 정규화 원문·청크를 기준으로 질문 10~20개와 근거를 `data/processed/queries_pilot.jsonl`에 작성하고 각 split을 `pilot`으로 지정한다.

```bash
legal-rag --config configs/pilot.yaml validate
legal-rag --config configs/pilot.yaml smoke
legal-rag --config configs/pilot.yaml build-index
legal-rag --config configs/pilot.yaml smoke
```

`smoke`는 인덱스 없이 가능하지만 질문 파일의 첫 질문과 청크 파일의 첫 청크를 사용한다. 현재 구현은 methods 목록과 관계없이 임베딩·CE·Jev를 모두 호출한다. `generate: false`이면 생성은 호출하지 않는다. 10~20문항 전체를 점검하는 명령이 아니라 연결 확인 1회이므로 다음 `run`이 필요하다.

첫 smoke에서 로컬 Qdrant가 `index_not_built`인 것은 아직 구축하지 않았다는 뜻이다. build-index 뒤 두 번째 smoke에서는 실제 컬렉션 조회·검색과 `qdrant.status: ok`를 확인한다. 두 번 모두 모델 호출이 포함되어 실제 API 사용량이 발생한다. remote의 구축 전 `reachable`도 연결 확인일 뿐 인덱스 구축 완료를 의미하지 않는다.

### 5-3. 검색 비교

```bash
legal-rag --config configs/pilot.yaml run --split pilot --run-id retrieval_001
legal-rag --config configs/pilot.yaml evaluate --run results/pilot/retrieval_001
```

이 단계에서 확인할 것은 다음과 같다.

1. `completion.json`의 계획 행 수가 질문 수 × 3이고 누락·실패 원인을 설명할 수 있는가?
2. 공통 Top-K에 충분한 정답 근거가 있는가? 없다면 임베딩·청킹·K·시점 필터를 먼저 점검한다.
3. Jev 점수, 반환 모델, usage, 비용, 재시도 로그가 실제로 수집되는가?
4. CE 입력 잘림과 근거 문맥 길이에 문제가 없는가?
5. 각 방법에 동일한 후보가 전달되는가?

### 5-4. 같은 표본으로 생성 확인

`configs/pilot.yaml`의 `generate`를 `true`로 바꾸고 생성 설정을 채운다. 이전 실행을 덮어쓰지 않도록 새 run ID를 사용한다.

```bash
legal-rag --config configs/pilot.yaml smoke
legal-rag --config configs/pilot.yaml run --split pilot --run-id answers_001
legal-rag --config configs/pilot.yaml export-annotations --run results/pilot/answers_001 --kind answers --output results/pilot/answer_review_001
```

평가자는 `tasks.jsonl`의 correctness, core_supported, 주장별 support, 인용별 supported, reviewer를 채운다. 두 평가자용 파일은 동일하게 내보낸 양식을 복사해서 만든다. `private_mapping.json`은 평가자에게 전달하지 않는다. 질문·답변·근거 본문은 수정하지 않는다.

```bash
legal-rag --config configs/pilot.yaml import-answers --run results/pilot/answers_001 --tasks results/pilot/answer_review_001/adjudicated.jsonl --mapping results/pilot/answer_review_001/private_mapping.json
legal-rag --config configs/pilot.yaml evaluate --run results/pilot/answers_001
```

`adjudicated.jsonl`은 사람이 판정하고 불일치를 조정해 만들어야 하는 파일이다. 명령이 자동 생성하는 정답이 아니다.

## 6. 파일럿 이후 개발·최종 시험

초기 계획은 파일럿 100문항, 개발 200문항, 독립 잠금 시험 600문항이다. 검정력이 보장된 고정 수치가 아니며 파일럿의 불일치율·독립 그룹 수·라벨링 시간·예산으로 확정한다. 시험 구성의 초기 목표는 답할 수 있음 80%, 근거 부족 20%다.

### 6-1. 그룹 분할과 후보 라벨

실제 질문 전체의 경로를 설정에 반영한 뒤 `split`을 사용한다. 기존 pilot의 연결 성분은 기본 pilot에 유지되고 test로 재배정되지 않는다. 개발 재사용을 사전 지정하면 `--reuse-pilot-in-dev`로 dev에 포함한다. 나머지 미노출 연결 성분을 기본 dev 25%/test 75%로 분할하며 최소 2개가 필요하다. 입력·청크·출력 해시와 실제 구성은 `.split_manifest.json`에 기록된다. 그룹 단위이므로 목표 문항 비율과 다를 수 있다.

```bash
legal-rag --config configs/main.yaml split --output data/processed/queries_split.jsonl
# main.yaml의 queries를 위 출력 경로로 변경
legal-rag --config configs/main.yaml validate
legal-rag --config configs/main.yaml retrieve --split dev
legal-rag --config configs/main.yaml lexical-pool --split dev --top-k 20
```

이 단계 전에 main의 원문·청크·인덱스 경로를 실제 구축물에 맞춘다. 파일럿과 코퍼스·임베딩·청킹이 같다면 검증된 인덱스를 참조할 수 있고, 다르면 새로운 index_dir에 구축한다.

각 명령이 출력한 실행 경로에 대해 `export-annotations --kind relevance`를 실행한다. 후보 등급은 2=직접 근거, 1=관련 배경, 0=부적합이다. `agreement`로 두 평가자 일치도를 확인하고 조정한 판정을 `import-relevance`로 반영한다. test 후보도 방법별 성능을 확인하기 전에 같은 절차로 완성한다. 여러 풀의 판정을 순차 반영할 때는 이미 반영한 질문 파일을 다음 import의 입력으로 사용한다.

최종 reviewed 질문 파일을 main의 queries에 반영한다. answerability와 충분한 근거 조합은 후보 등급과 별개로 검토한다. 시험 질문·라벨은 모델·프롬프트·K·문턱값 선택에 사용하지 않는다.

### 6-2. 개발 세트 문턱값 결정

main은 5방법, `generate: true`로 설정하고 K, 모델, 평가 지침, 비용, `quality_delta`를 정한다. 기본 delta 0.02는 2%p의 초기값이지 정당화가 끝난 기준이 아니다.

```bash
legal-rag --config configs/main.yaml sweep --grid-size 5
```

출력된 실행 경로를 아래 `SWEEP_PATH` 대신 넣는다.

```bash
legal-rag --config configs/main.yaml export-annotations --run SWEEP_PATH --kind answers --output results/dev_answer_review
# 사람 판정·불일치 조정 후 adjudicated_answers.jsonl 준비
legal-rag --config configs/main.yaml import-answers --run SWEEP_PATH --tasks adjudicated_answers.jsonl --mapping results/dev_answer_review/private_mapping.json
legal-rag --config configs/main.yaml evaluate --run SWEEP_PATH
legal-rag --config configs/main.yaml tune --run SWEEP_PATH --output-config configs/final.yaml
```

`sweep`은 CE-R·Jev-R 기준선 2조건과 각 FR 5조건, 총 12조건이다. 개발 200문항이면 최대 2,400개의 답변 판정 단위가 생긴다. 동일 문맥 답변은 캐시될 수 있어 실제 생성 API 호출 수와 같지는 않다. 전체 사람 평가가 어렵다면 실행 전에 `human_evaluation_limit`를 정한다. 같은 표본 질문의 모든 조건을 평가해야 한다.

`tune`은 CE-R 대비 ESR과 v2 근거 있는 정답 비율 하락이 margin 이내인 문턱값 중 최소 총 온라인 비용을 고른다. 지표별 `esr_quality_delta`·`answer_quality_delta`를 지정할 수 있다. 만족값이 없으면 기본은 보고서만 남기며, 시험 전 분기를 정했다면 `--allow-infeasible`로 불가능 FR만 제외하고 고정 N·가능한 FR 설정을 만든다. 시험 결과를 본 뒤 기준을 완화하지 않는다. 새 답변 양식은 핵심 여부·주장 완전성 판정이 필요하며 기존 v1을 새 주 지표로 자동 전환하지 않는다.

### 6-3. 잠금 시험

```bash
legal-rag --config configs/final.yaml freeze --output results/protocol_lock.json
legal-rag --config configs/final.yaml run --split test --lock results/protocol_lock.json --run-id final_test
legal-rag --config configs/final.yaml export-annotations --run results/final_test --kind answers --output results/test_answer_review
# 사람 판정 및 불일치 조정 후 test_adjudicated.jsonl 준비
legal-rag --config configs/final.yaml import-answers --run results/final_test --tasks test_adjudicated.jsonl --mapping results/test_answer_review/private_mapping.json
legal-rag --config configs/final.yaml evaluate --run results/final_test
legal-rag --config configs/final.yaml statistics --run results/final_test
legal-rag --config configs/final.yaml plot --run results/final_test
legal-rag --config configs/final.yaml errors --run results/final_test --output results/error_sample.jsonl
```

위 경로는 final 설정의 output_dir가 `results`인 경우다. freeze 이후 질문 파일·모델·가격·프롬프트·코드 등 잠근 항목이 바뀌면 그대로 이어 실행하지 못한다. `--resume`은 같은 실행에서 누락된 조건을 이어 수행하며 이미 저장된 실패를 성공으로 덮어쓰는 기능은 아니다.

### 6-4. 추가 검증

```bash
legal-rag --config configs/final.yaml benchmark --split test --lock results/protocol_lock.json --limit 20 --warmup 1 --repeats 5
legal-rag --config configs/final.yaml summarize-benchmark --run BENCHMARK_PATH
```

`BENCHMARK_PATH`는 benchmark 출력 경로로 바꾼다. 캐시를 쓰는 품질 실험 시간을 실제 온라인 지연으로 보고하지 않는다.

필수 문구 ablation은 `jev_instruction: relevance`와 `methods: [jev_r]`를 별도 설정에 둔다. 공통 토큰 예산, 입력 길이 통제, K/N 민감도, 시점 필터를 끈 판본 혼합 진단도 주 실험과 구분한다. 시험 진단은 결과를 보기 전에 별도 설정·lock을 정한다. 자동 judge와 확률 calibration은 보조 분석이다. 생성형 LLM reranker 비교는 현재 기본 5조건에 없으므로 그 방법보다 우수하다는 주장에는 추가 구현·실험이 필요하다.

## 7. 작업량과 예상 병목

다음은 계획량 산술이며 실제 API 요금·시간 견적이 아니다.

| 작업 | K=20 기준 초기 규모 |
|---|---|
| 연결 확인 20문항 | Jev 후보 판정 최대 400건, 고정 N 3조건 답변 최대 60개 |
| 파일럿 100문항 | 후보 쌍 최대 2,000개; 5조건이면 답변 최대 500개 |
| 개발 200문항 | 공통 후보 쌍 최대 4,000개; grid=5 sweep 답변 판정 최대 2,400개 |
| 시험 600문항 | 후보 쌍 최대 12,000개; 5조건 답변 최대 3,000개 |
| 시험 후보 이중 판정 | 최대 24,000회 + 대체 근거 탐색·조정 |
| 시험 답변 이중 판정 | 최대 6,000회 + 주장·인용별 확인·조정 |

현재 Jev 구현은 질문-후보별 요청이다. 한 품질 실행에서 R/FR 재채점은 공유될 수 있으므로 600문항의 Jev 평가를 방법 수만큼 단순 배수로 계산하지 않는다. 반면 benchmark는 캐시·방법 간 공유를 끄고 반복하므로 별도 호출 예산이 필요하다. 재시도, 워밍업, ablation, 후보 부족, 동일 문맥 캐시에 따라 실제 건수는 달라진다.

금액을 계산하려면 먼저 소규모 실제 호출에서 후보당 입력량, 생성 입출력량, usage 누락·실패율, 로컬 처리시간과 실제 단가를 확보해야 한다. 현재 자료로 신뢰할 수 있는 총비용이나 완료 날짜를 확정할 수 없다.

## 8. 실행 중 막히기 쉬운 부분

| 증상 | 점검할 원인·조치 |
|---|---|
| `requires a development-selected threshold` | 첫 실행은 3방법으로 제한하거나 dev sweep/tune으로 FR 문턱값 선정 |
| `smoke`에서 파일 없음 | 질문·청크가 먼저 필요; 최초 입력 없이 API만 테스트하는 명령이 아님 |
| 모델 이름·revision 오류 | `.env`의 로컬 모델과 revision, Jev·생성 모델 설정 확인 |
| 검색 후보가 너무 적음 | 관할, 기준일, 효력 기간, unknown_temporal_policy, 코퍼스 규모 확인 |
| gold 구간 오류 | 정규화본 기준 오프셋인지, 청킹 변경으로 ID가 바뀌었는지 확인 |
| 그룹 누출 오류 | 같은 조문·사건·판본·연결 근거를 같은 분할에 배치 |
| nDCG·답변 지표 누락 | 후보 relevance 또는 사람 답변 판정이 없거나 불완전한지 확인 |
| 비용 null / tune 거절 | 단가·usage·로컬 검색 비용·재시도 청구 완결성 확인 |
| 인덱스 변경 오류 | 코퍼스·모델·관련 구현이 바뀌면 새 index_dir 사용 |
| 프로토콜 잠금 불일치 | 잠근 설정·질문·가격·코드 등을 변경했는지 확인 |
| 오래된 문서 예시 JSON 거절 | 현재 스키마는 알 수 없는 필드를 거절함; README·schemas 기준으로 작성 |

코드상 `research_valid: true`는 mock 사용 등 일부 조건을 통과했다는 표식이다. 라벨 품질, 통계 검정력, 데이터 대표성까지 자동으로 보증하지 않는다.

## 9. 당장 결정하고 준비할 순서

1. 실험할 법률 분야·관할·기준일과 실제 원문 묶음 확정.
2. 실제 질문 10~20개, 기준 답변, 충분한 근거 조합 작성.
3. 임베딩·CE·Jev·생성 모델, 접근 권한·revision 설정.
4. 3방법 검색·생성 연결 확인과 usage·단가 기록.
5. 평가자와 지침 확보 후 100문항 파일럿, 후보 라벨링 및 5조건 개발 탐색.
6. 개발에서 문항 수·K·모델·문턱값·표본·허용 품질 하락을 확정한 뒤 독립 시험 잠금.

현재 가장 큰 미완료 작업은 실제 데이터와 정답 근거 라벨, 실제 서비스 연결 검증, 평가 운영 준비다. 기본 실험 코드는 이미 실행 가능한 상태이며, 실제 표본에서 확인된 문제에 맞춰 보완하면 된다.
