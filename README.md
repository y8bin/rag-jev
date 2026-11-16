# KoBLEX ParSeR · CE와 Jev 리랭커 비교

**새 세션에서 이어갈 때:** [세션 인계 문서](SESSION_HANDOFF.md)를 먼저 읽고 [제4장 집필 계획](research/CHAPTER4_WRITING_PLAN_20261109.md)에 따라 기존 결과의 추가 집계부터 진행한다. 제4장 본문과 A1~A6 추가 집계는 아직 미작성·미실행이다.

공식 KoBLEX 한국어226문항에서 원 ParSeR 절차를 재현하고, CE 점수화 단계만 Jev로 교체한 실험이다. 자동 실험·678개 답변 평가·전수 검증을 완료했으며 실제 사람 평가는 대기 중이다.

| 조건 | 근거 F1 | LF-Eval |
|---|---:|---:|
| 공개 코드 CE · 선택 인덱스 오류 보존 | 48.72 | 58.30 |
| 수정 CE · 주 기준선 | 58.57 | 67.57 |
| Jev 교체 · 주 비교 | 61.75 | 70.15 |

[결과와 해석](research/KOBLEX_REPRODUCTION_RESULTS_20261109.md) · [실행 안내](research/KOBLEX_REPRODUCTION_RUNBOOK.md) · [사람 평가 안내](research/KOBLEX_REPRODUCTION_HUMAN_REVIEW.md) · [입력 진단 및 정리 기록](research/KOBLEX_REPRODUCTION_AUDIT_20261109.md)

## 현재 구조

- `configs/koblex-reproduction.yaml`: 현재 실험 설정. BM25 후보100개, reranker shortlist10개, LLM 선택.
- `data/koblex/upstream/`: 고정한 공식 QA·코드·프롬프트 원본.
- `data/koblex/downloads/`, `data/koblex/prepared-v1/`: 공식 법령 corpus와 평가 입력.
- `results/koblex-reproduction-v1/`: 현재 세 조건의 원시 결과·캐시·평가·통계·사람 평가 양식.
- `scripts/experiment/`: 실제 실행한 과학적 처리 코드의 바이트 불변 원본.
- `results/koblex-reproduction-v1/budget/ledger.sqlite`: 현재 요청 상세와 이전 사용액의 집계 이월 잔액. 총100달러·OpenAI37달러 상한 유지.
- `scripts/koblex.py`: 현재 실험의 단일 실행 진입점.
- `tests/`: 현재 실험 검증 테스트22개.

현재 연구에 필요한 데이터·실행 환경·검증 코드를 남겼다. 이전 실험 결과·설정·캐시·인덱스·UI와 자동 실행 작업은 삭제했다. 기존 Git 이력은 다시 쓰지 않았다.

## 확인

```bash
.venv/bin/python scripts/koblex.py verify
.venv/bin/python scripts/koblex.py audit
.venv/bin/python scripts/koblex.py budget
.venv/bin/python -m pytest -q
```

`legal-rag verify`와 `python -m legal_rag_jev verify`도 같은 현재 진입점을 사용한다. API 인증은 Git에서 제외된 `.env.koblex`에 두고, 필요한 항목은 `.env.example`을 참고한다. 검증·예산 조회·기존 결과 감사는 유료 호출을 하지 않는다. 실제 재개는 실행 안내의 해당 단계를 사용한다.
