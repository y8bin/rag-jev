**기존 벡터 DB와 KBL을 전환해서 사용하기**

대시보드의 질문 입력 아래 `설정`에서 검색 소스를 바꾼다. 소스를 바꾸면 입력 양식도 함께 바뀐다. 설정별 입력 초안을 따로 보관하며, 과거 질문을 보고 있을 때 소스를 바꾸면 새 질문 화면으로 이동한다.

| 선택 항목 | 검색 원본 | 입력 방식 |
|---|---|---|
| `env-qdrant` | 기존 `.env`의 Qdrant 컬렉션 | 자유 질문 |
| `KBL · 제공 후보` | KBL STATq 52문항의 사전 검색 후보 | 문항 선택, 질문·보기 고정 |
| `KBL 법령 · BM25` | 공개 법령 전체의 로컬 어휘 인덱스 | 자유 질문 |

기존 설정·Qdrant 컬렉션은 유지한다. KBL 두 경로는 임베딩 모델이나 Qdrant 연결을 사용하지 않는다. CE·Jev·생성기는 해당 설정과 기존 `.env`를 사용한다. 기본 설정은 `retrieval`, `ce_r`, `jev_r`을 실행한다. API를 사용하는 재채점·생성에는 기존과 같이 비용이 발생할 수 있다.

KBL은 시행일을 검증하지 않은 역사 스냅샷이다. KBL 화면에는 오늘 기준일을 자동 입력하지 않으며, 제공 후보의 질문·관할·기준일을 변경한 요청은 거절한다. 현행 법률 정확도를 검증한 서비스라는 의미는 아니다.

이 작업에서 실제로 준비한 데이터는 다음과 같다.

- 제공 후보: 52문항, 문항별 후보 10개, 중복을 제외한 원문 361개.
- 법령 코퍼스: 원문 220,160개, 1,800자 이하로 구조 분할한 청크 281,402개.
- BM25: SQLite FTS5 역색인. 공백 제거·NFC 정규화·소문자화 후 글자쌍을 ASCII 토큰으로 변환한다. 원 논문의 Pyserini 설정과 별도 구현이다.

준비 명령은 같은 입력으로 다시 실행해도 결과를 덮어쓰지 않고 해시를 검증한다. 다른 원본·분할 정책으로 준비하려면 새 출력 경로·인덱스 경로를 사용한다.

```bash
# 1. 공개 문제·후보를 고정 커밋에서 받아 정답과 분리한다.
legal-rag kbl-prepare

# 2. 법령 원문을 받아 Document / Chunk로 변환한다.
legal-rag --config configs/kbl-bm25.yaml kbl-corpus

# 3. 전체 법령의 BM25 인덱스를 만든다.
legal-rag --config configs/kbl-bm25.yaml build-index

# 4. 대시보드에서 세 가지 소스를 전환한다.
legal-rag viewer
```

외부 네트워크가 없는 환경에서는 이미 내려받은 파일을 `kbl-prepare --input <RAG JSON>` 또는 `kbl-corpus --input <원문 JSONL>`로 변환한다. 원본 SHA-256과 출처 커밋은 변환 manifest에 기록된다. 온라인 다운로드에는 별도 source receipt를 생성한다.

저장 위치는 다음과 같다. 데이터·인덱스·실행 결과는 기존 `.gitignore` 정책으로 Git에서 제외된다.

```text
data/kbl/downloads/                  고정 원본과 다운로드 receipt
data/kbl/statq-rag-s/questions.jsonl 질문·선택지, 정답 없음
data/kbl/statq-rag-s/candidates.jsonl 원문 후보·원 순위·점수, 정답 없음
data/kbl/statq-rag-s/gold.jsonl      평가 전용 정답 문자
data/kbl/statq-rag-s/manifest.json   출처·해시·후보 수
data/kbl/statutes/documents.jsonl   정규화한 원문
data/kbl/statutes/chunks.jsonl      위치·해시가 있는 청크
indexes/kbl-statutes-bm25/           검색 DB와 manifest
```

질문과 후보의 허용 필드만 모델 입력으로 구성한다. `label`·`label_long`은 모델 입력에 복사하지 않는다. 생성기·CE·Jev에는 질문과 모든 선택지를 동일하게 제공한다. 제공 후보 모드에서 원문을 다른 질문에 붙이거나, 부족한 후보를 복제해서 K를 채우지 않는다. 기본 K=10이고 K를 늘려도 실제 제공된 후보까지만 반환한다.

객관식 실험은 CLI의 기존 `run` / `evaluate`로 실행한다. `kbl-bm25.yaml`도 같은 52문항을 새로 검색해서 비교할 수 있다. 이 설정에서 대시보드의 자유 질문은 일반 답변 생성으로 처리하고, CLI의 준비된 문제는 객관식 생성으로 처리한다.

```bash
legal-rag --config configs/kbl-replay.yaml validate
legal-rag --config configs/kbl-replay.yaml run --split pilot --run-id statq-pilot
legal-rag --config configs/kbl-replay.yaml evaluate --run results/kbl/replay/statq-pilot

legal-rag --config configs/kbl-bm25.yaml run --split pilot --run-id bm25-pilot
legal-rag --config configs/kbl-bm25.yaml evaluate --run results/kbl/bm25/bm25-pilot
```

`run` 명령은 실제 모델 호출을 수행한다. 기본 생성기는 `OPENAI_MODEL`, CE/Jev는 기존 환경의 모델·단가 설정을 따른다. `smoke`는 선택한 검색 소스와 사용 중인 제공자만 점검하며 KBL에서 임베딩을 호출하지 않는다. `readiness`는 네트워크 호출 없이 파일·설정·정답 연결을 점검한다.

객관식 정답률은 `mcq_accuracy`로 저장한다. 출력은 허용된 정답 문자 하나여야 한다. 여러 답·설명 문장이 섞인 출력은 형식 오류로 기록하고 오답 처리한다. 기술 실패도 전체 계획 문항의 분모에 포함한다. 정답률은 근거 충분성·인용 정확도를 뜻하지 않으므로 ESR와 기존 사람 판정 기반 accuracy는 null로 유지한다. 객관식 결과에 기존의 근거 충분성 통계를 실행하면 명시적으로 거절한다.

제공 후보의 원래 검색 비용·지연은 알 수 없어 전체 온라인 비용과 지연을 확정하지 않는다. 재채점·생성 비용은 `rerank_generation_usd`로 따로 기록한다. BM25의 로컬 검색 비용은 `LOCAL_USD_PER_HOUR`를 이용한 시간 배분 추정이며, 단가가 없으면 null이다. 캐시 품질 실험과 실제 서비스 측정은 기존과 같이 구분한다.

FR을 사용하려면 개발 데이터로 문턱값을 먼저 정한 뒤 `methods`에 `ce_fr`·`jev_fr`과 해당 threshold를 추가한다. 임의의 기본 문턱값을 채워 실행하지 않는다. 현재 52문항 import는 모두 pilot이며 독립 시험 표본으로 간주하지 않는다. 시험 분할을 별도로 준비한 경우 `freeze --output <lock>` 이후 `run --split test --lock <lock>`으로 고정 프로토콜을 사용한다.

추가 유형과 판례를 준비하는 명령도 제공한다. 현재 설치한 것은 STATq와 법령 코퍼스이며, 아래 명령은 추가 다운로드를 수행한다.

```bash
legal-rag kbl-prepare --task legal_concept_qa --variant rag_s --output data/kbl/concept-rag-s
legal-rag kbl-prepare --variant rag_p --output data/kbl/statq-rag-p
legal-rag --config configs/kbl-bm25.yaml kbl-corpus --kind precedents --output data/kbl/precedents
```

다른 replay 데이터는 `kbl-replay.yaml`을 복사해 `index_dir`, `queries`, `benchmark_gold`, 결과·캐시 경로를 함께 바꾼다. 판례 BM25는 `kbl-bm25.yaml`을 복사해 documents/chunks/index_dir를 판례용으로 바꾸고 `build-index`를 실행한다. 긴 원문은 원문 위치를 보존하며 분할한다. 선택지별 검색만 있는 RAG 레코드는 묵시적으로 합치지 않고 명시적인 오류를 반환한다. 이 유형은 합치기·중복 제거·K 정책을 먼저 정해야 한다.

공개 데이터 라이선스는 CC BY-NC 4.0이다. 배포·공개 결과에는 출처·라이선스·변환 사항을 함께 기록하고 상업적 이용 범위를 확인한다. 데이터와 기준 버전은 [KBL 도입 전략](KBL_RAG_ADOPTION_STRATEGY.md) 및 [원본 검사 기록](kbl_source_audit.json)을 참조한다.
