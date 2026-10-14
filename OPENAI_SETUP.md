# OpenAI Platform으로 답변 생성하기

`generation_backend: openai`는 공식 `https://api.openai.com/v1/responses`로 검색 근거를 보내 답변을 생성한다. 기존 `http` 백엔드는 Chat Completions 호환 게이트웨이·로컬 서버용으로 유지한다. 답변 생성, 실행 기록, 캐시, 뷰어의 새 질문이 같은 생성기를 사용한다.

## 1. API 키와 모델 설정

OpenAI Platform에서 프로젝트 API 키를 발급하고 기존 `.env`에 아래 항목을 추가한다. 기존 파일을 `.env.example`로 덮어쓰지 않는다.

```dotenv
OPENAI_API_KEY=발급받은_API_키
OPENAI_MODEL=계정에서_사용_가능한_모델_ID
```

모델은 Responses API와 Structured Outputs를 지원해야 한다. ChatGPT/Codex에서 표시되는 모델 이름이나 게이트웨이의 `codex/...` ID를 그대로 복사하지 말고 Platform의 모델 ID와 프로젝트 권한을 확인한다. 모델은 자동 선택하지 않는다. 연구에서는 가능하면 고정된 snapshot을 사용한다. 특정 조직·프로젝트가 필요하면 `OPENAI_ORG_ID`, `OPENAI_PROJECT_ID`를 추가한다. 키는 서버 환경에서만 읽으며 설정·캐시·실행 기록·브라우저 응답에 저장하지 않는다.

## 2. 생성 연결만 확인

가상 규정 하나로 요청한다. 원문 파일, Qdrant, 임베딩·CE·Jev 설정은 필요하지 않다. 실제 API 비용이 발생할 수 있다. 재시도 가능한 오류는 설정한 한도 안에서 다시 요청한다.

```bash
source .venv/bin/activate
legal-rag --config configs/openai.yaml smoke-generation
```

출력에는 `answer`, `rationale`, `claims`, `citations`, `abstained`와 모델·토큰 사용량·요청 ID가 포함된다. `invalid_citations`가 비어 있는지도 확인한다. 결과는 가상 예시의 연결 점검이며 `research_valid: false`다. 구현 테스트는 HTTP 응답을 모사하며 실제 API 키나 유료 호출을 사용하지 않는다.

키 누락은 `Set OPENAI_API_KEY`, 모델 누락은 `Set OPENAI_MODEL`로 안내한다. 401은 키, 403/404는 프로젝트 권한과 모델 ID를 확인한다. 429는 서버 오류 설명의 quota/rate-limit 원인을 확인한다. `incomplete (max_output_tokens)`는 설정의 `max_output_tokens`를 늘리고 재점검한다. 이 한도에는 추론 토큰도 포함된다. 거절·불완전 응답은 유효한 답변이나 근거 부족 보류로 처리하지 않는다.

## 3. 실제 검색과 뷰어에 적용

기존 인덱스를 사용하는 YAML(예: `configs/env-qdrant.yaml`)에서 다음 값을 선택하면 된다. OpenAI 경로에서는 `GENERATION_BASE_URL`, `GENERATION_API_KEY`, `GENERATION_MODEL`을 사용하지 않는다. 검색 설정과 인덱스는 실제 데이터에 맞게 준비해야 한다.

```yaml
generation_backend: openai
generate: true
max_output_tokens: 4096
temperature: null
```

`temperature: null`이면 파라미터를 생략한다. 숫자는 선택한 모델이 지원할 때만 지정한다. 근거는 질문·기준일·관할과 함께 전송하며 정답 참조는 생성기에 보내지 않는다. JSON Schema로 답변 구조를 제한해도 정확성·인용 지지·근거 완전성은 별도 사람 판정이 필요하다.

`configs/openai.yaml`은 실제 파일럿용 로컬 managed 인덱스 설정이다. `configs/pilot.yaml`과 동일한 검색 설정·모델로 구축한 `indexes/research_v1`을 사용한다. 데이터 준비 절차는 [논문 검증 실행서](PAPER_VALIDATION_RUNBOOK.md)를 따른다.

```bash
legal-rag --config configs/openai.yaml readiness
legal-rag --config configs/openai.yaml smoke
legal-rag --config configs/openai.yaml run --split pilot --run-id openai_answers_001
legal-rag viewer --results results
```

뷰어의 새 질문에서는 OpenAI를 선택한 YAML을 고른다. 설정 변경은 캐시·프로토콜에 반영되므로 시험용 모델·가격·설정을 확정한 뒤 새 lock을 만든다. `store: false`로 독립 요청을 보내며 이전 응답이나 대화 상태를 공유하지 않는다. 이 옵션을 데이터 무보관 보증으로 해석하지 않는다.

## 4. 비용과 자동 보조 평가

실제 선택 모델·서비스 등급의 확인된 입력/출력 단가를 `GENERATION_INPUT_USD_PER_MILLION`, `GENERATION_OUTPUT_USD_PER_MILLION`에 입력한다. usage의 `cached_tokens`·`cache_write_tokens`가 0보다 크면 각각 `GENERATION_CACHED_INPUT_USD_PER_MILLION`, `GENERATION_CACHE_WRITE_USD_PER_MILLION`도 필요하다. 모델에 캐시 쓰기 추가 요금이 없으면 해당 단가는 일반 입력 단가와 같다. 단가를 추측하거나 빈 값을 무료로 해석하지 않는다. 추론 토큰은 출력 토큰에 이미 포함되므로 별도로 더하지 않는다. 재시도에서 앞선 요청의 청구 여부가 불명확하면 총비용은 `null`이다. 비용은 설정한 단가와 usage를 이용한 추정이며 청구 내역 확인이 필요하다.

자동 judge는 선택 사항이다. `judge_backend: openai`와 `OPENAI_JUDGE_MODEL`을 지정하면 `judge` 명령도 Responses API를 사용한다. 평가 모델을 별도로 선택하고 `JUDGE_*_USD_PER_MILLION` 단가를 설정한다. 자동 판정은 사람 gold를 대체하지 않는다.

공식 계약 확인: [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses), [인증](https://developers.openai.com/api/reference/overview), [캐시 usage와 비용](https://developers.openai.com/api/docs/guides/prompt-caching).
