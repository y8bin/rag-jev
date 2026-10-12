# 처음 시작하는 사람을 위한 실험 안내

이 문서는 개발 경험이 없어도 이 저장소로 실험을 따라 할 수 있도록 순서대로 정리한 안내서입니다. 명령어는 그대로 복사해서 터미널에 붙여 넣으면 됩니다. 더 자세한 규칙은 마지막의 [문서 지도](#문서-지도)에 있는 원문서를 따릅니다. 내용이 충돌하면 `final_research_strategy.md`가 우선입니다.

---

## 1. 이 실험은 무엇을 확인하나

법률 질문이 들어오면 시스템은 ① 법률 원문에서 관련 있어 보이는 조각(청크) 20개를 찾고, ② 그중 답변 근거로 쓸 5개를 골라, ③ 그 근거만 보고 답을 씁니다.

이 실험은 **②번, 근거를 고르는 방법**을 비교합니다. 다섯 가지 방법이 모두 같은 후보 20개를 받습니다.

| 이름 | 고르는 방식 |
|---|---|
| Vector | 처음 검색된 순서 그대로 위에서 5개 |
| CE-R | Cross-Encoder(일반적인 재정렬 모델)로 다시 점수를 매겨 위에서 5개 |
| CE-FR | CE 점수가 기준선(문턱값)을 넘는 것만, 최대 5개. 0개일 수도 있음 |
| Jev-R | Jev(법적 근거로 적합한지 판단하는 모델)로 다시 점수를 매겨 위에서 5개 |
| Jev-FR | Jev 점수가 문턱값을 넘는 것만, 최대 5개. 0개일 수도 있음 |

알고 싶은 것은 세 가지입니다.

1. Jev가 정답에 필요한 근거를 더 잘 고르는가?
2. 그 결과 근거가 있는 정답이 늘어나는가?
3. 품질을 크게 잃지 않으면서 비용을 줄일 수 있는가?

아직 어떤 방법이 낫다는 결론은 없습니다. 이 저장소는 그것을 공정하게 확인하기 위한 도구입니다.

## 2. 누가 무엇을 하나

| 역할 | 하는 일 | 필요한 것 |
|---|---|---|
| 실행 담당 | 설치, 명령 실행, 결과 확인 | 이 문서, 터미널 |
| 데이터 담당 | 법률 원문 수집·정리, 질문과 정답 근거 작성 | 법률 지식, 텍스트 편집기 |
| 평가자 (2명 이상) | 검색 후보와 답변이 맞는지 판정 | 법률 지식. 코드는 몰라도 됨 |
| 조정 담당 | 두 평가자의 판정이 다를 때 최종 결정 | 법률 지식 |

평가자는 어떤 방법이 낸 결과인지 모르는 상태로 판정합니다. 이를 위해 `private_mapping.json` 파일은 **평가자에게 절대 보내지 않습니다.**

## 3. 처음 한 번만: 설치

필요한 것: Python 3.11 이상, Git, 인터넷 연결, 여유 디스크 수 GB(로컬 모델 파일이 첫 실행 때 내려받아집니다).

터미널(맥: 응용 프로그램 → 유틸리티 → 터미널)을 열고 한 줄씩 실행합니다.

```bash
git clone <이 저장소 주소>
cd RAG-jev
python3 -m venv .venv
source .venv/bin/activate          # Windows는 .venv\Scripts\activate
python -m pip install -e '.[test,local,documents]'
cp .env.example .env
```

- `source .venv/bin/activate`는 **터미널을 새로 열 때마다** 다시 실행해야 합니다. 프롬프트 앞에 `(.venv)`가 보이면 준비된 상태입니다.
- `cp .env.example .env`는 처음 한 번만 실행합니다. 다시 실행하면 입력해 둔 키가 지워집니다.
- 설치가 됐는지 확인: `legal-rag --help`가 명령 목록을 보여주면 성공입니다.
- 제대로 동작하는지 확인: `python -m pytest -q` 결과가 모두 `passed`면 정상입니다.

## 4. 비용 없이 먼저 해보기: 데모와 뷰어

API 키 없이, 돈이 들지 않는 가상 데이터로 전체 흐름을 봅니다.

```bash
legal-rag --config configs/demo.yaml demo
legal-rag viewer
```

브라우저에서 http://127.0.0.1:8765 를 엽니다. 뷰어를 끄려면 터미널에서 `Ctrl + C`를 누릅니다.

- **새 질문**: 설정에서 `demo`를 고르고 질문하면 다섯 방법의 답과 근거가 한 표에 나란히 나옵니다. CE-R 열이 기준이고, 기준과 같은 칸은 "(기준과 같음)", 달라진 곳은 밑줄로 표시됩니다.
- **실행 기록**: 방금 만든 `demo` 실행을 열면 질문별 비교, 요약 지표, 오류를 볼 수 있습니다.
- **설정 비교**: 실험 설정 파일들의 차이를 봅니다.

데모 결과는 가짜 모델이 만든 것이라 "mock"으로 표시되며, **어떤 결론의 근거로도 쓰지 않습니다.**

## 5. 실제 실험 순서

전체 흐름은 아래와 같습니다. 각 단계는 앞 단계가 끝나야 시작합니다.

```
범위 정하기 → 원문 준비 → 질문·정답 작성 → API 설정 → 소규모 연결 확인(10~20문항)
→ 파일럿(약 100문항) → 개발 세트로 설정 확정(약 200문항) → 잠금 시험(약 600문항) → 추가 검증
```

문항 수는 시작 계획일 뿐이며 파일럿 결과와 예산을 보고 정합니다.

### 5-1. 범위 정하기 (팀 회의)

다음을 정하고 기록합니다: 법률 분야, 언어, 관할(예: KR), 포함할 문서 종류(법령·판례 등), 수집 기준일, 원문 출처와 사용 범위, 평가자와 판정 기준.

### 5-2. 원문 준비 (데이터 담당)

원문은 `data/raw/corpus.jsonl` 파일 하나에 **한 줄에 문서 하나**씩 적습니다.

```json
{"doc_id":"LAW_A","version_id":"2026-01","group_id":"LAW_A_FAMILY","text":"제1조 ...","title":"○○법","doc_type":"statute","jurisdiction":"KR","citation_key":"○○법 제1조","source_uri":"https://...","effective_from":"2026-01-01","effective_to":null,"collected_at":"2026-10-09"}
```

| 필드 | 뜻 |
|---|---|
| `doc_id` | 문서 고유 이름 (영문·숫자 권장) |
| `version_id` | 판본 이름. 같은 법의 개정판은 같은 `doc_id`, 다른 `version_id` |
| `group_id` | 같은 법·사건 계열끼리 같은 값. 개발/시험 세트가 섞이지 않게 묶는 용도 |
| `text` | 원문 전체 |
| `effective_from` / `effective_to` | 효력 시작일 / 종료일. 종료일 **당일은 포함하지 않음**. 없으면 `null` |

- 앞의 네 개(`doc_id`, `version_id`, `group_id`, `text`)는 필수입니다. 나머지도 실험에서는 채웁니다.
- 효력 날짜가 비어 있으면 기준일이 있는 질문의 검색에서 빠질 수 있습니다.
- 스캔한 이미지 PDF는 미리 글자로 바꿔(OCR) 넣어야 합니다.
- `data/` 폴더는 GitHub에 올라가지 않습니다(원문 보호). 원문은 팀 공유 드라이브 등 별도 경로로 주고받습니다.

### 5-3. 원문을 조각내기 (실행 담당)

먼저 파일럿용 설정을 만듭니다. 아래 내용을 `configs/pilot.yaml`로 저장합니다.

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

```bash
legal-rag --config configs/pilot.yaml ingest --input data/raw/corpus.jsonl
legal-rag --config configs/pilot.yaml chunk
```

결과로 `data/processed/chunks.jsonl`이 생깁니다. 각 줄이 조각 하나이고, `chunk_id`(예: `C_208c5131…`)와 `text`가 들어 있습니다. 데이터 담당에게 이 파일을 넘깁니다.

> 처음에는 세 방법(`vector, ce_r, jev_r`)만 씁니다. FR 두 방법은 문턱값이 정해진 뒤(5-8) 추가합니다. 문턱값 없이 FR을 넣으면 오류가 납니다.

### 5-4. 질문과 정답 근거 작성 (데이터 담당)

`data/processed/queries_pilot.jsonl`에 **한 줄에 질문 하나**씩 적습니다. 처음에는 실제 질문 10~20개면 충분합니다.

가장 쉬운 방법은 정답 근거를 **조각 ID(`chunk_id`)로 지정**하는 것입니다. `chunks.jsonl`에서 답의 근거가 되는 조각을 찾아 그 ID를 적습니다.

답할 수 있는 질문:

```json
{"query_id":"P001","group_id":"LAW_A_FAMILY","split":"pilot","question":"○○ 신청 기한은 언제까지인가?","answerable":true,"reference_answer":"처분 통지일부터 30일 이내","as_of_date":"2026-10-09","jurisdiction":"KR","task_type":"direct","evidence_units":[{"unit_id":"U1","chunk_ids":["C_208c5131ec736a2d05df6652"]}],"sufficient_sets":[["U1"]],"relevance":{}}
```

원문에 근거가 없는 질문:

```json
{"query_id":"P002","group_id":"NONE_1","split":"pilot","question":"○○ 위반 과태료는 얼마인가?","answerable":false,"reference_answer":"근거 부족","as_of_date":"2026-10-09","jurisdiction":"KR","task_type":"unanswerable","evidence_units":[],"sufficient_sets":[],"relevance":{}}
```

| 필드 | 뜻 |
|---|---|
| `evidence_units` | 정답 근거 목록. 각 근거에 `unit_id`(U1, U2…)를 붙이고 해당 조각 ID를 적음. 여러 ID를 적으면 "그중 하나만 있어도 이 근거로 인정" |
| `sufficient_sets` | 답 전체를 뒷받침하는 근거 조합. U1과 U2가 **둘 다** 필요하면 `[["U1","U2"]]`, **둘 중 하나**면 `[["U1"],["U2"]]` |
| `relevance` | 처음에는 `{}`로 둡니다. 나중에 평가자 판정으로 채워집니다 |
| `split` | 연결 확인 단계에서는 `pilot` |

- 조각 ID는 원문이나 조각 방식이 바뀌면 달라집니다. 원문을 고치면 5-3부터 다시 하고 ID도 다시 확인합니다.
- 다 쓰면 형식 검사를 합니다: `legal-rag --config configs/pilot.yaml validate`. 오류 메시지가 나오면 해당 질문 ID를 고칩니다.

### 5-5. API 설정 (실행 담당)

`.env` 파일을 텍스트 편집기로 열어 채웁니다. 키는 이 파일에만 적고 **절대 GitHub에 올리지 않습니다**(`.gitignore`에 이미 제외되어 있습니다).

| 항목 | 필수 여부 |
|---|---|
| `JEV_API_KEY` | 필수. `JEV_MODEL`은 가능하면 `jev-latest` 대신 고정된 모델 이름 |
| `GENERATION_BASE_URL`, `GENERATION_MODEL`, `GENERATION_API_KEY` | 답변 생성 단계(5-7)부터 필수 |
| `*_INPUT_USD_PER_MILLION` 등 단가, `LOCAL_USD_PER_HOUR` | 비용 비교에 필수. 모르면 비워 두고(=미확인), 무료일 때만 `0` |
| `MODEL_DEVICE` | 기본 `cpu`. GPU가 있으면 `cuda` 또는 `mps` |

임베딩·CE 모델은 이미 기본값이 들어 있어 그대로 쓰면 됩니다.

### 5-6. 소규모 연결 확인 (실행 담당)

여기서부터 **실제 API 비용이 발생합니다.**

```bash
legal-rag --config configs/pilot.yaml smoke          # 모델 연결 확인
legal-rag --config configs/pilot.yaml build-index    # 검색 색인 만들기
legal-rag --config configs/pilot.yaml smoke          # 색인까지 포함해 다시 확인
legal-rag --config configs/pilot.yaml run --split pilot --run-id retrieval_001
legal-rag --config configs/pilot.yaml evaluate --run results/pilot/retrieval_001
```

뷰어를 `legal-rag viewer --results results/pilot`으로 열고 다음을 확인합니다.

1. 실행 기록의 행 수가 질문 수 × 3이고 실패가 없는가? 실패가 있으면 오류 탭에서 이유를 본다.
2. 질문·답변 탭의 "공통 후보" 표에 정답 근거(파란 "근거 U1" 표시)가 들어 있는가? 거의 없다면 원문·조각·검색 설정부터 점검한다.
3. 다섯 방법 모두 같은 후보를 받았는가?
4. 수치 칸에 비용·재채점 건수가 기록되는가?

### 5-7. 답변 생성과 사람 평가

`configs/pilot.yaml`에서 `generate: false`를 `generate: true`로 바꾸고, `.env`의 생성 설정을 채운 뒤 실행합니다. 이전 결과를 덮어쓰지 않도록 새 이름(`answers_001`)을 씁니다.

```bash
legal-rag --config configs/pilot.yaml smoke
legal-rag --config configs/pilot.yaml run --split pilot --run-id answers_001
legal-rag --config configs/pilot.yaml export-annotations --run results/pilot/answers_001 --kind answers --output results/pilot/answer_review_001
```

`results/pilot/answer_review_001/tasks.jsonl`을 평가자 수만큼 복사해 나눠 줍니다(`private_mapping.json`은 주지 않음). 평가자는 각 답변에 대해 정답 여부(`correctness`), 핵심 주장이 근거로 뒷받침되는지(`core_supported`), 주장별 지지 여부(`supported`/`unsupported`/`contradicted`), 인용별 지지 여부, 평가자 이름(`reviewer`)을 채웁니다. 질문·답변·근거 본문은 고치지 않습니다.

두 평가자의 판정을 비교해 다른 부분을 조정 담당이 정리한 최종 파일 `adjudicated.jsonl`을 만든 뒤 가져옵니다.

```bash
legal-rag --config configs/pilot.yaml import-answers --run results/pilot/answers_001 --tasks results/pilot/answer_review_001/adjudicated.jsonl --mapping results/pilot/answer_review_001/private_mapping.json
legal-rag --config configs/pilot.yaml evaluate --run results/pilot/answers_001
```

이제 뷰어의 요약 탭에 "근거 있는 정답" 같은 답변 지표가 채워집니다.

### 5-8. 개발 세트로 설정 확정

파일럿에서 문제가 없으면 질문을 늘려 개발/시험 세트를 만듭니다. 이 단계는 실행 담당과 연구 책임자가 함께 진행하며, 자세한 명령은 `EXPERIMENT_READINESS.md` 6장을 따릅니다. 큰 흐름만 적으면 다음과 같습니다.

1. `split`으로 질문을 개발(dev)·시험(test) 세트로 나눕니다. 같은 법·사건 계열은 같은 쪽에 들어갑니다.
2. `retrieve`로 후보를 모으고 `export-annotations --kind relevance`로 평가자에게 후보별 등급(2=직접 근거, 1=관련 배경, 0=부적합)을 받습니다. `agreement`로 두 평가자 일치도를 보고, 조정 후 `import-relevance`로 반영합니다.
3. `configs/main.yaml`을 다섯 방법으로 두고 `sweep`으로 FR 문턱값 후보를 시험합니다. 답변을 사람이 판정한 뒤 `tune`이 품질 조건을 만족하는 가장 저렴한 문턱값을 골라 `configs/final.yaml`을 만듭니다.

### 5-9. 잠금 시험 (본 실험)

```bash
legal-rag --config configs/final.yaml freeze --output results/protocol_lock.json
legal-rag --config configs/final.yaml run --split test --lock results/protocol_lock.json --run-id final_test
```

`freeze`는 설정·모델·가격·질문 파일·프롬프트를 잠급니다. 잠근 뒤 하나라도 바뀌면 시험 실행이 멈춥니다. 이후 5-7과 같은 방식으로 사람 평가를 하고 `evaluate`, `statistics`, `plot`, `errors`로 결과·통계·그림·오류 표본을 만듭니다. 명령은 `README.md`의 "잠금 시험과 결과 생성"에 있습니다.

### 5-10. 추가 검증

실제 응답 시간 측정(`benchmark`), Jev 질문 문구 비교, 토큰 예산 통제 같은 보조 실험입니다. 주 실험과 섞지 않고 별도 설정·잠금으로 진행합니다(`README.md` "지연·ablation·자동 보조 평가").

## 6. 꼭 지킬 규칙

- **시험 세트 결과를 보고 설정을 바꾸지 않습니다.** 모델·문턱값·질문 문구는 개발 세트에서만 정합니다.
- **mock 결과와 뷰어 "새 질문"(탐색 기록)은 연구 근거로 인용하지 않습니다.** 탐색 기록은 `results/_explore/`에 따로 쌓이고 지표·통계에 들어가지 않습니다.
- **평가자에게 `private_mapping.json`을 주지 않습니다.**
- **`.env`(키)와 `data/`(원문), `results/`(질문·원문 포함)는 GitHub에 올리지 않습니다.** 이미 `.gitignore`로 제외되어 있습니다.
- **실패한 기록을 덮어쓰지 않습니다.** 중간에 끊긴 실행은 같은 명령에 `--resume`을 붙여 빠진 부분만 이어서 합니다. 처음부터 다시 하려면 새 `--run-id`를 씁니다.
- **같은 색인 폴더로 두 명령을 동시에 실행하지 않습니다.** 실험이 돌고 있을 때 뷰어에서 같은 설정으로 질문하지 않습니다.

## 7. 막혔을 때

| 증상 | 해결 |
|---|---|
| `legal-rag: command not found` | `source .venv/bin/activate`를 먼저 실행 |
| `requires a development-selected threshold` | 설정의 `methods`에서 `ce_fr`, `jev_fr`를 빼고 실행 (문턱값은 5-8에서 정함) |
| `Set JEV_API_KEY in .env…` 같은 메시지 | `.env`의 해당 항목을 채움 |
| `smoke`에서 파일이 없다는 오류 | 5-3(조각내기)과 5-4(질문 파일)를 먼저 끝냄 |
| `index_not_built` | 아직 `build-index` 전이라는 뜻. 5-6 순서대로 진행 |
| 검색 후보가 너무 적음 | 질문의 관할·기준일과 원문의 효력 날짜가 맞는지 확인 |
| `unknown evidence chunks` | 질문에 적은 조각 ID가 현재 `chunks.jsonl`에 없음. 원문을 고쳤다면 ID를 다시 확인 |
| 비용이 `—`로 나옴 / `tune`이 거절 | `.env`의 단가가 비어 있음. 확인한 값을 입력 |
| 뷰어가 안 열림 | 뷰어를 실행한 터미널이 켜져 있는지 확인. 다른 포트: `legal-rag viewer --port 8800` |

그래도 안 되면 오류 메시지 전체와 실행한 명령을 그대로 복사해 실행 담당에게 전달합니다.

## 8. 용어

| 용어 | 뜻 |
|---|---|
| 청크(chunk) | 긴 원문을 검색하기 좋게 자른 조각 |
| 후보 K개 | 처음 검색에서 가져오는 조각 수 (기본 20) |
| N개 | 그중 답변에 실제로 넣는 최대 개수 (기본 5) |
| 재정렬(rerank) | 후보에 점수를 다시 매겨 순서를 바꾸는 것 |
| 문턱값(threshold) | FR 방법에서 이 점수를 넘어야 근거로 채택 |
| ESR | 정답에 필요한 근거 조합을 모두 골라낸 비율. 근거 선택의 주 지표 |
| 근거 있는 정답 | 답이 맞고, 핵심 주장이 고른 근거로 뒷받침되는 비율. 답변의 주 지표 |
| 분모(n) | 그 지표를 계산한 질문 수. 뷰어에서 숫자 아래 작게 표시 |
| mock | 실험 흐름 확인용 가짜 모델. 결과에 의미 없음 |
| Qdrant | 조각을 저장하고 검색하는 데이터베이스. 기본은 내 컴퓨터 안에서 동작 |
| 잠금(freeze) | 본 시험 전에 설정을 고정해 나중에 몰래 바뀌지 않게 하는 것 |

## 문서 지도

| 문서 | 언제 읽나 |
|---|---|
| `GETTING_STARTED.md` (이 문서) | 처음 시작할 때 |
| `final_research_strategy.md` | 연구 목적·비교 방법·평가 원칙. 다른 문서와 충돌하면 이 문서가 우선 |
| `README.md` | 모든 명령, 환경변수, 파일 형식의 정확한 기준 |
| `EXPERIMENT_READINESS.md` | 현재 진행 상황, 단계별 상세 명령, 예상 작업량 |
| `legal_rag_jev_experiment_design (1).md` | 보조 실험 설계 (참고용) |
| `legal_rag_jev_paper_design.md` | 최초 논문 구상 (일부 조건은 폐기됨, 참고용) |
| `PRODUCT.md`, `DESIGN.md` | 뷰어 화면의 목적과 디자인 규칙 (뷰어를 고칠 때만) |
