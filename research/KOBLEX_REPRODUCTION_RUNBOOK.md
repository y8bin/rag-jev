# 현재 KoBLEX 실험 실행 안내

유일한 활성 설정은 `configs/koblex-reproduction.yaml`, 진입점은 `scripts/koblex.py`다. 별도 실험을 시작하지 않고 완료된 현재 실행을 검증하거나 누락된 부분을 재개한다.

## 검증 · 유료 호출 없음

```bash
.venv/bin/python scripts/koblex.py verify
.venv/bin/python scripts/koblex.py audit
.venv/bin/python scripts/koblex.py budget
.venv/bin/python -m pytest -q
```

공식 데이터·실행 당시 코드·현재 어댑터·기존 과학적 결과의 해시를 확인한다. `integrity-audit-current.json`이 정리 후의 전수 검증이며, 실행 당시 잠금은 `protocol-lock.json`에 그대로 있다. 정리 후 새 잠금을 만들어 실행 전 잠금으로 가장하지 않았다. 경로 이동과 활성 설정 분리는 `cleanup-manifest.json`에 기록했다.

## 실제 실행 · 필요한 단계만

```bash
.venv/bin/python scripts/koblex.py parametric
.venv/bin/python scripts/koblex.py retrieve
.venv/bin/python scripts/koblex.py ce
.venv/bin/python scripts/koblex.py jev
.venv/bin/python scripts/koblex.py answers
.venv/bin/python scripts/koblex.py metrics
.venv-lf-eval/bin/python scripts/koblex.py lf-eval
.venv/bin/python scripts/koblex.py analyze
.venv/bin/python scripts/koblex.py review
```

예상 법령 생성 → 예상 법령별 BM25 100개 → CE/Jev 상위10개 → 같은 LLM의 하나 선택 → 같은 답변 생성·평가 순서다. `top_n: 10`은 최종 근거 개수가 아니라 LLM에 제시하는 shortlist다. 정답 hop 수로 선택 개수를 정하지 않는다. 세 조건 이름은 `parser_ce_raw`, `parser_ce_fixed`, `parser_jev_fixed`다.

MPS에서 CE를 실행하며 CPU로 자동 대체하지 않는다. Jev·OpenAI API 호출에는 비용이 발생한다. 답변 생성은 분당 토큰 예약을 적용하고, LF-Eval은 고정 evaluator로 조건별 순서를 유지한 최대3개 동시 스트림을 사용한다. 동일 평가 프롬프트는 잠금과 캐시를 공유한다. 원시 응답·실패 기록·미정산 예약액을 보존한다.

동일 단계를 중복 프로세스로 실행하지 않는다. 기존 성공 문항과 동일 입력의 캐시는 재사용한다. 모델·문항·출력 한도·평가 범위를 바꿔 중단을 우회하지 않는다. 코드·입력·패키지가 달라지면 검증에서 중단한다.

## 예산

현재 원장은 `results/koblex-reproduction-v1/budget/ledger.sqlite`다. 이전 호출의 상세는 삭제하고 generation/judge/Jev별 집계 이월 잔액만 유지했다. 현재 실험 요청41,322건과 미정산12건은 삭제하지 않았다. 이월액은 별도 표시하며, 집계 행을 새 API 요청으로 해석하지 않는다. 총100달러·OpenAI37달러의 누적 상한과 남은 금액은 바뀌지 않았다.

## 실제 사람 평가

[별도 안내](KOBLEX_REPRODUCTION_HUMAN_REVIEW.md)를 따른다. 두 평가자의 독립 판단과 전문가 조정은 아직 진행되지 않았다. 작성본은 템플릿을 덮어쓰지 않고 별도 파일로 제출한다.

현재 자동 결과는 [최종 보고서](KOBLEX_REPRODUCTION_RESULTS_20261109.md)와 `analysis.json`에 있다. 품질 실행 시간을 온라인 지연으로 사용하지 않는다. 실제 제공 근거의 주장 지지 여부는 사람 평가로 확인한다.
