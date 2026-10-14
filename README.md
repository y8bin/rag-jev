# Legal RAG / Jev 실험 구현

Decision Model for Legal RAG: An Empirical Evaluation of Retrieval Accuracy, Groundedness, and End-to-End Latency

> 처음이라면 [처음 시작하는 사람을 위한 실험 안내](GETTING_STARTED.md)부터 읽는다.

[최종 연구 전략](final_research_strategy.md)을 실행하는 Python CLI다. 자체 코퍼스만 사용한다. Qdrant 색인, Vector/CE-R/CE-FR/Jev-R/Jev-FR, 개발 세트 문턱값 탐색, 근거·답변 평가, 사람 판정 양식, paired cluster bootstrap, 지연 반복 측정과 논문 그림을 제공한다.

## 설치와 API 설정

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test,local,documents]'
cp .env.example .env
```

HTTP 임베딩·HTTP reranker만 쓰면 `local` 추가 의존성은 생략할 수 있다. `documents`는 텍스트 PDF를 읽을 때 필요하다. 설치 후 `legal-rag --help`로 명령을 확인한다. 개발 중에는 `PYTHONPATH=src python3 -m legal_rag_jev`도 사용할 수 있다. YAML 경로는 명령을 실행하는 작업 디렉터리를 기준으로 한다.

모든 API 주소·키·모델·가격은 [.env.example](.env.example)에 정의된 환경변수로 설정한다. 기존 프로세스 환경변수가 `.env`보다 우선하며 `--env-file`로 다른 파일을 지정할 수 있다. YAML에는 실험 설정과 로컬 파일 경로만 들어간다. `.env`, 실제 데이터, 캐시와 결과는 `.gitignore` 대상이다. 캐시와 raw 결과에는 질문·원문이 있으므로 공개 전에 검토한다.

| 구성 | 설정 | 환경변수 / 서비스 계약 |
|---|---|---|
| 임베딩 | `embedding_backend: local` | `EMBEDDING_LOCAL_MODEL`, 정확한 `EMBEDDING_LOCAL_REVISION`, `HF_TOKEN`, `MODEL_DEVICE` |
| HTTP 임베딩 | `embedding_backend: http` | `EMBEDDING_BASE_URL/API_KEY/MODEL`, `POST /embeddings`, 응답 `data: [{index, embedding}]` |
| 로컬 CE | `ce_backend: local` | `CE_LOCAL_MODEL`, 정확한 `CE_LOCAL_REVISION`, `MODEL_DEVICE` |
| HTTP CE | `ce_backend: http` | `CE_BASE_URL/API_KEY/API_MODEL`, `POST /rerank`, 응답 `results: [{index, relevance_score}]` |
| Jev | `jev_backend: http` | `JEV_BASE_URL/API_KEY/MODEL`, 공식 `/v1/systemone`의 named `noul` 질문·응답 |
| 생성 | `generation_backend: http` | `GENERATION_BASE_URL/API_KEY/MODEL`, `POST /chat/completions` |
| OpenAI 생성 | `generation_backend: openai` | `OPENAI_API_KEY`, `OPENAI_MODEL`, 공식 `POST /v1/responses`, strict JSON Schema |
| 자동 judge | `judge_backend: http` | `JUDGE_BASE_URL/API_KEY/MODEL`, 생성과 같은 HTTP 계약 |
| OpenAI judge | `judge_backend: openai` | `OPENAI_API_KEY`, `OPENAI_JUDGE_MODEL`, 생성과 같은 Responses 계약 |

BASE_URL에는 최종 endpoint를 붙이지 않는다. 예를 들어 chat/embedding 서비스가 `/v1` 아래에 있으면 BASE_URL에 `/v1`을 포함한다. Jev BASE_URL은 기본적으로 `https://api.typesafe.ai`다. 응답 구조가 다른 서비스는 `providers.py`의 해당 adapter를 수정해야 한다. API 키가 필요 없는 로컬 서버는 키를 비워둘 수 있다. Jev 키는 필수다. 로컬 모델은 revision을 입력해야 로드되므로 시험 중 모델 변경을 막을 수 있다.

`temperature: null`이 기본값이며 생성·judge 요청에서 이 파라미터를 생략하고 모델/서비스의 기본 동작을 따른다. 추론이 활성화된 GPT-6.1 Sol처럼 샘플링 옵션을 제한하는 모델에 사용한다. 숫자를 지정하면 해당 값을 그대로 전송하므로 모델이 지원하는지 먼저 확인한다. `null`과 `0`은 다른 설정이며 캐시와 시험 프로토콜에도 구분해 기록한다.

가격은 `*_INPUT_USD_PER_MILLION`, `*_OUTPUT_USD_PER_MILLION`, 로컬 비용은 `LOCAL_USD_PER_HOUR`, 원격 Qdrant 시간 배분 비용은 `QDRANT_USD_PER_HOUR`로 설정한다. 원격 검색에 로컬 모델 단가를 대신 쓰지 않는다. Qdrant 시간 환산은 청구액 자동 수집이 아니므로 Cloud·저장·네트워크·유지비의 포함 범위와 배분식을 별도 기록한다. 가격 또는 billable usage가 없으면 비용은 `null`이다. 무료 단가는 명시적으로 `0`을 입력한다. 실패한 요청의 청구 여부를 확인할 수 없는 재시도에는 총비용을 `null`로 남긴다. 실제 청구 기록 확인 없이 가격을 추측하지 않는다. 비용 완결성이 없는 데이터는 문턱값 최적화에 사용할 수 없고, 일부 확인된 비용만으로 평균·paired 비용 추론을 제공하지 않는다.

실제 연구의 실행 순서·완료 근거·필요 자료는 [논문 검증 실행서](PAPER_VALIDATION_RUNBOOK.md)에 정리했다. `legal-rag --config configs/pilot.yaml readiness --output results/preparation/readiness.json`은 네트워크·모델 호출 없이 입력 파일·형식·설정 누락을 확인한다. 구조 확인 통과가 법률 검토나 연구 타당성을 보증하지 않는다.

OpenAI Platform 연결 절차는 [OpenAI 설정 안내](OPENAI_SETUP.md)를 따른다. `.env`에 `OPENAI_API_KEY`, `OPENAI_MODEL`을 추가하고 `legal-rag --config configs/openai.yaml smoke-generation`으로 가상 근거 기반 답변 1회를 점검한다. 원문·색인·다른 API 없이 생성 연결만 확인하며 실제 비용이 발생할 수 있다. 기존 YAML에서는 `generation_backend: openai`를 선택해야 한다. 캐시 입력/쓰기 usage가 있으면 해당 `*_CACHED_INPUT_USD_PER_MILLION`, `*_CACHE_WRITE_USD_PER_MILLION` 단가도 필요하다.

## API 없는 예제 실행

```bash
legal-rag --config configs/demo.yaml demo
```

예제의 법률 규정은 모두 가상이다. demo 임베딩·CE·Jev·생성기는 결정적인 시험용 구현이며 모든 산출물을 `research_valid: false`로 표시한다. demo도 Qdrant 로컬 영속 모드로 색인·검색하며 서버나 API 키 없이 실행할 수 있다. `qdrant-client`는 필수 의존성이다. demo의 입력량은 오프라인 문자 계산이고, 실제 실험은 설정한 tiktoken 공통 인코딩과 제공자의 billable usage를 함께 기록한다. tiktoken의 인코딩 파일은 첫 사용 시 내려받을 수 있으므로 오프라인 환경에서는 미리 캐시해야 한다.

## 데이터 형식

원문 입력은 JSONL 또는 `.txt/.md/.pdf` 폴더다. 폴더 입력은 각 파일에 `filename.ext.meta.json` 메타데이터가 필요하다. PDF는 텍스트를 추출하며 이미지 PDF의 OCR은 수집 전처리에서 완료해야 한다.

원문 JSONL의 한 행:

```json
{"doc_id":"LAW_A","version_id":"2026-01","group_id":"LAW_A_FAMILY","text":"제1조 ...","title":"...","doc_type":"statute","jurisdiction":"KR","citation_key":"...","source_uri":"...","effective_from":"2026-01-01","effective_to":null,"collected_at":"2026-10-09"}
```

`effective_to`는 해당 날짜를 포함하지 않는 종료일이다. 원문과 정규화본은 별도 보관한다. ingest는 개행/NFC를 정규화하고 원본 해시를 남긴다. **근거 오프셋은 정규화본의 Python 문자 위치**다. 청크 오프셋은 `[start, end)`이고 ID는 문서·판본·위치·본문에 따라 안정적으로 생성된다. 원본 PDF byte offset과 같지 않다.

```bash
legal-rag ingest --input data/raw/corpus.jsonl
legal-rag chunk
legal-rag build-index
```

Qdrant 컬렉션에 L2 정규화한 float32 벡터를 `Distance.DOT`으로 저장한다. 문서와 질의 모두 정규화하므로 점수는 코사인 유사도에 대응한다. 안정적인 UUID point ID는 `chunk_id`에서 생성하고, 원문·판본·효력 기간·관할·인용·오프셋은 point payload의 `chunk`에 저장한다. 관할과 효력 기간 필터를 Qdrant 질의에 적용하고 `SearchParams(exact=True)`로 검색한다. 효력 시작일은 포함하고 종료일은 제외하며, 날짜가 없는 자료는 설정한 정책을 따른다. 동점은 `chunk_id` 순서로 정렬한다.

기본 `qdrant_mode: local`은 `index_dir/qdrant/`에 저장하며 한 프로세스만 해당 저장소를 열 수 있다. 서버/Cloud 연결은 YAML에 `qdrant_mode: remote`를 설정하고 `.env`에 `QDRANT_BASE_URL`, 필요하면 `QDRANT_API_KEY`를 입력한다. 서버는 query API를 지원해야 한다(1.10 이상, 클라이언트와 호환되는 버전 권장). 서버 모드에서는 관할·효력 날짜 payload index도 생성한다. 예를 들어 로컬 서버는 `http://localhost:6333`에 연결한다.

`legal-rag smoke`는 모델 호출과 Qdrant 상태를 함께 확인한다. 구축된 인덱스가 있으면 무결성 검증과 실제 질의 검색을 수행한다. 구축 전 서버 모드에서는 연결을 확인하고, 구축 전 로컬 모드에서는 `index_not_built` 상태를 보고한다.

컬렉션 이름은 `qdrant_collection` 접두어와 `index_version`을 조합한다. 코퍼스·모델·저장 모드·서버 주소·접두어가 바뀌면 새 `index_dir`를 사용한다. 기존 컬렉션을 덮어쓰지 않는다. 로컬 manifest와 `chunks.jsonl` 스냅샷을 보존하며, 매 로드 시 스냅샷 해시·차원·거리·개수와 실제 Qdrant의 모든 벡터·payload 해시를 확인한다. 검색 캐시와 시험 lock도 새 인덱스 버전에 연결된다. 이전 저장 형식의 인덱스·캐시·lock은 재사용하지 않고 청크에서 새로 구축한다.

정확 검색과 Top-K 경계 동점의 재현성을 위해 필터를 통과한 전체 결과를 반환받아 정렬한다. 큰 코퍼스에서는 전체 반환과 로드 무결성 검증 비용이 증가한다. 근사 검색으로 변경한다면 별도 후보 재현율 검증이 필요하다. 원격 검색 비용은 별도 `QDRANT_USD_PER_HOUR`에 기반한 시간 배분 추정치이며 실제 서버/Cloud 비용·저장·네트워크 포함 범위를 별도 검증한다.

질문 JSONL의 한 행:

```json
{"query_id":"Q001","group_id":"ISSUE_A","split":"dev","question":"...","answerable":true,"reference_answer":"...","as_of_date":"2026-10-09","jurisdiction":"KR","task_type":"application","evidence_units":[{"unit_id":"U1","doc_id":"LAW_A","version_id":"2026-01","start":0,"end":40}],"sufficient_sets":[["U1"]],"relevance":{},"annotation_version":"v1"}
```

근거 단위는 원문 구간 또는 사람이 확인한 대체 `chunk_ids`로 표현한다. 단위의 여러 chunk_ids는 그중 어느 하나가 해당 근거를 제공한다는 뜻이다. `sufficient_sets`는 충분한 근거의 대체 조합이며 한 조합의 모든 단위를 회수해야 성공이다. `answerable: false`는 evidence_units와 sufficient_sets가 비어 있어야 한다. `relevance`는 `chunk_id: 0|1|2`이고 미판정은 키를 넣지 않는다. 미판정을 0점으로 계산하지 않는다.

```bash
legal-rag split --output data/processed/queries_split.jsonl
# 새 질문 경로를 config의 queries에 반영
legal-rag validate
```

split은 질문 group_id와 참조 문서의 group_id를 연결해 그룹 단위로 분리한다. 여러 근거가 연결하는 그룹은 같은 분할에 둔다. 자동 분할 전에 중복/파생 사건·조문을 같은 문서 계열로 지정해야 한다. validate는 문서 계열의 분할 누출, ID, 정답 근거, 정규화본 오프셋을 확인한다.

기존 pilot 문항의 연결 성분은 기본 pilot에 유지하며 test로 보내지 않는다. 개발 재사용을 사전 지정했다면 `split --reuse-pilot-in-dev`로 해당 성분 전체를 dev로 옮긴다. 미노출 dev/test 연결 성분은 최소 2개가 필요하다. 질문 파일 옆 `.split_manifest.json`에 입력·청크·출력 해시, seed, 그룹 매핑과 실제 구성 수를 기록한다.

## 공통 후보 판정

개발 및 시험 후보를 먼저 만들어 라벨을 완성한다. 이 단계는 방법별 성능을 계산하지 않으므로 시험 질문의 정답 라벨 보완에 사용할 수 있다.

```bash
legal-rag retrieve --split dev
legal-rag export-annotations --run results/candidates_ID --kind relevance --output results/relevance_review
legal-rag lexical-pool --split dev --top-k 20
# 보완 어휘 검색 결과도 별도 export-annotations로 검토
```

`tasks.jsonl`을 두 평가자에게 복사하고 grade/reason/reviewer를 채운다. `private_mapping.json`은 방법·원래 ID 연결을 관리하는 파일이므로 평가자에게 제공하지 않는다.

```bash
legal-rag agreement --first reviewer_a.jsonl --second reviewer_b.jsonl --output results/agreement.json
# 불일치에 대한 사람 조정 후 최종 tasks 파일 사용
legal-rag import-relevance --tasks adjudicated.jsonl --mapping results/relevance_review/private_mapping.json --output data/processed/queries_reviewed.jsonl
```

시험 후보에도 같은 작업을 수행하고 질문 경로를 최종 reviewed 파일로 바꾼다. 충분한 근거 집합과 answerability는 별도로 전문 검토해야 한다. 등급 라벨을 import한다고 충분한 근거 집합이 자동 생성되지는 않는다. 보완 어휘 검색과 원문 탐색은 라벨링 작업에 포함한다.

lexical-pool은 문자 bigram BM25로 대체 근거를 탐색하는 보조 도구다. 이 결과를 공통 Qdrant 후보로 바꾸지 않는다. `legal-rag schemas --output schemas`로 데이터 입력/출력 JSON Schema를 생성할 수 있다.

## 개발 세트 탐색과 답변 판정

`configs/main.yaml`의 FR 문턱값은 처음에 `null`이다. 고정 N 비교만 먼저 실행하려면 methods를 `[vector, ce_r, jev_r]`로 설정한다. 후보 수와 모델을 결정한 뒤 최종 5개 methods로 바꾸고 개발 sweep을 실행한다.

```bash
legal-rag smoke
legal-rag sweep --grid-size 5
legal-rag export-annotations --run results/SWEEP_ID --kind answers --output results/answer_review
```

sweep은 CE/Jev의 개발 점수 분위수로 각각 같은 수의 문턱값을 만들고, 빈 선택 조건을 포함한다. 각 선택 문맥으로 실제 답변을 생성하며 다른 문맥의 답변을 재사용하지 않는다. 동일 문맥/모델/프롬프트의 답변 캐시는 재사용한다. 생성 결과에는 주장별 evidence_ids와 답변 보류 여부가 포함된다.

사람 평가자는 v2 양식의 correctness, core_supported, claims_complete, omitted_claims, 주장별 is_core·support·citation support, reviewer를 채운다. `answer`와 `rationale`의 검증 가능한 주장이 claims에서 빠졌는지 전체 텍스트를 확인한다. 누락 문장은 omitted_claims에 기록하고 claims_complete=false로 판정한다. support는 `supported/unsupported/contradicted` 중 하나다. 두 평가자의 불일치를 조정한 파일을 import한다. 질문·답변·근거를 임의로 편집하지 않는다. 상세 예시와 primary/strict 구분은 [평가 지침](research/annotation_guidelines.md)을 따른다. `agreement`는 인용 지지·핵심 분류·완전성 일치도와 후보 등급의 비가중/가중 kappa도 출력한다.

전체 답변을 사람이 검토하기 어렵다면 `human_evaluation_limit`를 설정한다. 질문 유형/answerability별로 실행 전에 표본을 고정하고 같은 질문의 모든 조건을 평가한다. 표본 ID도 manifest에 저장되며 설정 잠금에 포함된다. 정해진 표본의 필수 판정이 끝나기 전에는 답변 주 지표의 집계와 추론을 제공하지 않는다. 검색은 전체 질문, 답변 사람 평가는 해당 표본에 대한 결과이며 각 분모를 함께 보고한다.

```bash
legal-rag import-answers --run results/SWEEP_ID --tasks adjudicated_answers.jsonl --mapping results/answer_review/private_mapping.json
legal-rag evaluate --run results/SWEEP_ID
legal-rag tune --run results/SWEEP_ID --output-config configs/final.yaml
```

tune은 CE-R 대비 ESR과 근거가 있는 정답 비율의 감소가 quality_delta 이내인 문턱값 중 비용이 가장 낮은 것을 선택한다. `esr_quality_delta`·`answer_quality_delta`로 각각 다른 허용치를 지정할 수 있다(null이면 quality_delta 사용). 모든 사전 지정 답변 판정과 비용이 있어야 진행한다. 두 FR 중 하나라도 제약을 만족하지 못하면 기본은 보고서를 저장하고 설정을 만들지 않는다. 시험 전에 불가능 분기를 정했다면 `tune --allow-infeasible`로 해당 FR만 제외하고 고정 N·가능한 FR의 final 설정을 만든다. 불가능 방법은 threshold_selection.json에 기록하며 시험 결과로 제약을 완화하지 않는다. 후보 회수율/K, 지침, margin과 최종 문항 수는 개발 단계에서 정한다.

## 잠금 시험과 결과 생성

```bash
legal-rag --config configs/final.yaml freeze --output results/protocol_lock.json
legal-rag --config configs/final.yaml run --split test --lock results/protocol_lock.json --run-id final_test
legal-rag --config configs/final.yaml export-annotations --run results/final_test --kind answers --output results/test_answer_review
# 사람 판정 및 조정
legal-rag --config configs/final.yaml import-answers --run results/final_test --tasks test_adjudicated.jsonl --mapping results/test_answer_review/private_mapping.json
legal-rag --config configs/final.yaml evaluate --run results/final_test
legal-rag --config configs/final.yaml statistics --run results/final_test
legal-rag --config configs/final.yaml plot --run results/final_test
legal-rag --config configs/final.yaml errors --run results/final_test --output results/error_sample.jsonl
```

freeze는 설정·모델/주소·가격·질문 파일 해시·인덱스 버전·프롬프트와 `protocol_documents`의 첨부 파일 해시를 잠근다. 키는 저장하지 않는다. 범위·판정 지침·분석 계획·split·모델/가격 명세를 첨부하면 시험 후 변경도 감지한다. 실제 test 실행은 lock이 필수이며 불일치하면 중단한다. lock은 로컬 불변 설정 파일로서 변경 탐지 수단이며 제3자 사전등록을 대체하지 않는다. raw 결과는 질문별로 저장하고 같은 명령에 `--resume`을 주면 누락된 조건만 수행한다. 완료된 실패 기록은 덮어쓰지 않으며 새 실험으로 재실행한다.

출력 파일:

- `manifest.json`, `completion.json`: 실행 설정, 환경, 계획 질문과 실패 수.
- `raw.jsonl`: 공통 후보, 순위, 선택 문맥, 답변, 호출별 사용량·실패·재시도·비용.
- `annotations.jsonl`: 해시로 연결한 사람 답변 판정.
- `metrics.jsonl`, `summary.json/csv`: 질문별 및 방법별 지표, 각 지표의 평가 질문 수.
- `statistics.json`: 그룹 단위 신뢰구간, cluster sign-flip 비교, Holm 보정, FR 품질 비열등성 분석.
- `figures/`: 표준 matplotlib PNG/PDF 그림.

근거 선택 주 지표는 충분한 근거 집합 회수율이다. nDCG는 공통 후보 풀 기준이고 FR도 같은 N의 IDCG를 쓴다. 답변 주 지표 `grounded_correct`는 핵심 정답·필수 요건, 주장 완전성, 모든 핵심 주장의 지지와 각각의 제공 근거 지지 인용을 요구한다. 전체 생성 주장·전체 인용까지 요구하는 기존 기준은 `strict_grounded_correct`로 보존한다. 기존 v1 판정으로 새 주 지표를 추정하지 않으며 새 v2 양식으로 재검토해야 한다. 검증 가능한 주장이 없는 답변의 지지율은 N/A다. 사람 판정이 없는 답변 지표는 누락으로 표시하며 단순 문자열 일치로 법률 서술형 정답을 확정하지 않는다. 기술 실패는 전체 태스크 성공에 실패로 포함하고 공통 성공 질문의 비교도 별도로 제공한다. 낮은 질문 수나 독립 그룹 수에서는 통계 추론이 제한된다.

statistics는 주 3비교와 각 FR 대 자체 R·FR 간 보조 품질/비용 차이·CI를 구분한다. Holm은 주/보조 및 공통 성공/전체 가족별로 적용한다. FR 비열등성은 공통 성공 질문에서 각 품질 제약과 공동 충족 여부를 출력하며 `noninferiority_alpha`로 단측 신뢰수준을 지정한다. 두 FR 공동 주장의 다중 비교 범위와 power는 [분석 계획](research/statistical_analysis_plan.md)에서 시험 전에 확정한다. 환경 manifest는 설치된 패키지 전체와 Git commit·dirty를 기록한다. 의존성 pin 파일의 새 환경 재설치 성공은 별도 확인해야 한다.

## 지연·ablation·자동 보조 평가

```bash
legal-rag --config configs/final.yaml benchmark --split test --lock results/protocol_lock.json --limit 20 --warmup 1 --repeats 5
legal-rag summarize-benchmark --run results/benchmark_ID
```

benchmark는 캐시와 방법 간 점수 공유를 끄고 순서를 섞어 실제 검색~생성 wall-clock을 측정한다. 워밍업은 결과에서 제외한다. 품질 실행의 캐시 소요 시간을 온라인 지연으로 쓰지 않는다. 원래 점수를 R/FR이 공유해도 서비스 비용은 각 방법에 후보 전체의 재채점 비용을 귀속한다.

로컬 모델의 최초 로딩 시간은 `initialization_ms`로 별도 기록하고 질의별 추론 비용에서 제외한다. 실제 반복 wall-clock에 초기화가 들어가지 않도록 워밍업을 사용한다. 설치와 모델 파일 내려받기는 사전 환경 준비이며 실험 요청 비용과 구분한다.

진단 실험은 최종 YAML을 복사하고 하나의 변수만 바꿔 별도 설정/lock/run_id로 실행한다. 개발 세트에서 먼저 검증하고 시험 진단 조건도 결과를 보기 전에 고정한다.

- 관련성 ablation: `jev_instruction: relevance`, methods는 `[jev_r]`.
- 토큰 예산: `token_budget` 설정. system/question/근거를 공통 tokenizer로 세고 완전한 청크만 순서대로 추가한다.
- 시점 진단: `apply_metadata_filters: false`, 동일한 판본 혼합 후보 풀 사용. 주 실험과 섞지 않는다.
- 입력 길이 통제: `common_input_chars` 설정. 선택된 실제 원문 구간을 기록한다. 이 분석의 gold는 원문 구간으로 정의해 잘린 부분을 회수했다고 계산하지 않도록 한다.
- K/N: 설정별 인덱스는 유지하되 후보 캐시 키에 K와 필터를 포함한다.

```bash
legal-rag judge --run results/final_test
legal-rag calibration --run results/final_test --bins 10
```

judge는 독립 환경변수의 모델을 사용하고 `auto_annotations.jsonl`에 보조 판정을 저장한다. evaluate의 사람 gold로 자동 import되지 않는다. calibration은 진짜 Jev noul 확률과 사람 후보 라벨이 있을 때 Brier/ECE를 계산한다. 개발용 mock 점수에는 수행할 수 없다. 일반 LLM reranker 대비 우월성은 해당 추가 비교 없이 주장하지 않는다.

## 결과 뷰어

질문 화면은 `configs/env-qdrant.yaml`을 기본으로 선택한다. 이 설정은 `.env`의
`QDRANT_BASE_URL`과 `QDRANT_API_KEY`로 서버에 연결하고 기존 컬렉션을 읽기 전용으로 검색한다.
`QDRANT_COLLECTION`에 실제 컬렉션 이름을 지정한다. 비워두면 `legal_rag_demo`와
`legal_rag_connection_check`로 시작하는 시험용 컬렉션을 제외하고 하나만 남을 때 자동 선택한다.
여러 컬렉션이 있으면 선택 가능한 이름을 오류에 표시한다. named dense vector가 여러 개이면
`QDRANT_VECTOR_NAME`도 지정한다. 질의 임베딩 모델은 해당 컬렉션을 구축한 모델과 같아야 한다.
차원이 다르면 검색을 중단한다. 본문 payload는 `chunk.text`, `text`, `page_content`, `content`,
`document`, `chunk_text`를 지원하며 `metadata` 안의 출처 정보도 사용한다.
`legal_article`과 `legal_as_is` payload의 `document_id`, `law_name`, `article`, `article_title`,
`header`도 읽는다. `header`는 근거 제목·인용명, `document_id`는 문서 ID로 사용한다.
항·분할 정보와 `version_conflict`는 재채점·생성 입력에 전달한다. 원래 `chunk_id`와
`member_chunk_ids`는 기록에 보존하며, 답변 인용 ID는 컬렉션·point별 고유 ID를 사용한다.

기존 컬렉션에는 로컬 manifest나 재색인이 필요하지 않다. 변경된 데이터를 바로 검색하도록
이 모드의 캐시는 사용하지 않는다. 기존 payload의 효력 기간·관할 필드는 검증되지 않았으므로
메타데이터 필터를 적용하지 않고 화면과 기록에 표시한다. 이 모드는 뷰어 탐색용이다.
연구 실행은 기존처럼 관리된 인덱스와 스냅샷을 사용한다.

```bash
legal-rag viewer            # http://127.0.0.1:8765
legal-rag viewer --results results/pilot --port 8800
```

메인 화면은 질문 → 조건별 답변 대비다. 설정을 고르고 질문하면 실험과 같은 파이프라인(공통 후보 검색 → CE/Jev 재채점 → 선택 → 생성)이 돌고, 다섯 조건의 답변·근거를 신구조문대비표처럼 나란히 보여준다. CE-R 열이 기준이며 기준과 같은 칸은 “(기준과 같음)”으로 접고, 기준에 없던 단어·근거는 밑줄, 빠진 근거는 취소선으로 표시한다.

- 직접 질문은 설정에 따라 **실제 API를 호출하고 비용이 발생**한다. 화면의 안내 문구로 mock 여부와 호출 대상을 먼저 보여준다. 인덱스가 없는 설정은 질문할 수 없고, FR 문턱값이 없는 설정은 해당 FR 조건을 건너뛴다.
- 직접 질문은 `results/_explore/asks.jsonl`에 탐색 기록으로만 저장한다. 실행(run)이 아니며 evaluate·statistics·tune에 들어가지 않는다. 연구 결과로 인용하지 않는다.
- 실행 기록: `results/` 아래 실행을 같은 대비 형식(질문·답변)으로 열고, 요약(지표와 분모, 사전 지정 비교, FR 비열등성)·오류·실행 정보를 본다. `null`은 —로 표시하며 0으로 바꾸지 않는다.
- 설정 비교: YAML 사이에 다른 항목, 코드 기본값을 쓰는 항목, 스키마 검증 실패.

기본으로 127.0.0.1에만 열린다. 결과와 탐색 기록에는 질문·원문이 들어 있으므로 `--host 0.0.0.0`으로 공유하기 전에 공개 범위를 검토한다. 로컬 Qdrant 저장소는 한 프로세스만 열 수 있으므로, 같은 index_dir로 CLI 실행이 진행 중일 때는 뷰어에서 질문하지 않는다.

## 검증

```bash
python -m pytest -q
```

테스트는 원문 구간 보존, 그룹 누출, 시간 필터, 인덱스 무결성, 실제 Qdrant 로컬 영속 저장과 서버 HTTP 계약, 공식 Jev 응답/재시도, 캐시·동점·빈 문맥, 미판정 처리, 블라인드 양식, 잠금 설정, 전체 파이프라인을 검증한다. HTTP 계약은 mock transport로 테스트하므로 실제 계정의 인증·모델 접근성·서비스 단가는 `.env` 설정 후 smoke로 확인해야 한다. 예제 결과는 논문 증거가 아니다.

## 공식 구현 자료

- [TypeSafe OpenAPI](https://api.typesafe.ai/openapi.json): Jev named 질문과 noul 응답 계약.
- [Qdrant 인덱스 문서](https://qdrant.tech/documentation/concepts/points/): UUID point ID와 payload 저장.
- [Sentence Transformers CrossEncoder](https://www.sbert.net/docs/package_reference/cross_encoder/model.html): 로컬 CE 모델과 입력 길이 설정.
