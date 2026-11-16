# ARS 파이프라인 상태 — 제4장 (mid-entry)

- 범위: 제4장(실험 결과 및 분석)만. 다른 장은 팀원 담당이며 작성하지 않는다.
- 진입: Stage 2.5 (기존 원고 보유). 교차 모델 검증·외부 감사 게이트: 사용하지 않음(사용자 지시).
- 원 실험 결과·실행 잠금(`results/*/protocol-lock.json`, `scripts/experiment/`)은 수정하지 않는다.

## experiment_intake_declaration (사용자 확인 2026-11-13)

| 실험 | 근거 경로 | 상태 |
|---|---|---|
| 주 실험(KoBLEX ParSeR, CE 참조/수정 CE/Jev, 226문항) | `results/koblex-reproduction-v1/` (analysis.json, chapter4-prep-v1/) | 완료 |
| 재정렬 단계 지연(60문항×2방법×3회) | `results/koblex-latency-v1/` | 완료 |
| 문턱값 필터링 + 답변 재생성(E2E) | `results/koblex-filtering-v1/` (summary.json, e2e-summary.json) | 완료 |

### experiment_provenance[]

| 실험 | repro_lock | planned_vs_executed | negative_results | known_limitations |
|---|---|---|---|---|
| main | `results/koblex-reproduction-v1/protocol-lock.json` (sha256 99d5c5cc…; bootstrap seed 20261108, 151그룹×10,000회; BM25 k=100, top_n=10; gpt-4o-2024-08-06; jev-1.14.0; dragonkue/bge-reranker-v2-m3-ko@2aca5884…) | 3조건×226문항 답변·공식 지표·LF-Eval: executed | EM 차이 CI [−1.77, +5.19], 완전 회수 CI [−2.90, +4.53] (0 포함); 1-hop F1 78.07→76.90 | 시험 결과 관찰 후 탐색 분석, 다중 비교 무보정; 정확 문자열 지표; 고유 gold 27개 corpus 미매핑(29문항) |
| latency | `results/koblex-latency-v1/protocol.json` (order seed 20261109, sample seed 20261108, warmup 3, reps 3, cache off; CE MPS/float32/batch 50; Jev concurrency 4) | 60문항×2방법×3회=360 측정: executed, 실패 0 | Jev 지연 2.25배 [2.11, 2.39]; Jev top-10 재현 2/180 | 로컬 CE vs 원격 API 배포 조건 비교; scorer-only(E2E 아님); 60문항 표본·단일 세션 네트워크 |
| filtering+E2E | `results/koblex-filtering-v1/summary.json` rule (5-fold, cv seed 20261109, 허용 F1 하락 1점, 20 분위수 격자) + `e2e-summary.json` (bootstrap seed 20261108, 10,000회) | CV 시뮬레이션, 답변 재생성(CE 10/Jev 45), LF 재평가: executed | Jev LF −1.02 [−2.23, +0.15]; CE Token F1 −0.54 [−1.19, −0.07]; Jev 완전 회수 −1.77 [−3.51, −0.43] | 비열등성 마진 사전 미지정; 같은 226문항 안의 CV(미노출 시험 아님); 비용·지연 변화 미측정 |

- **사용자 지시: 사람 평가와 관련된 내용은 본문·보충자료를 포함한 논문 어디에도 넣지 않는다.** (사람 평가 양식은 존재하나 판단 0건이며 논문 범위에서 제외.)

## 단계 기록

| 단계 | 결과 | 산출물 | 사용자 결정 |
|---|---|---|---|
| 2.5 INTEGRITY (round 1) | FAIL — SERIOUS 2, MEDIUM 1, MINOR 8; 수치 151/151 MATCH; Mode 6 SUSPECTED | `stage2_5_integrity_report.md` | E2E 결과를 4.4에 반영 / 사람 평가 언급 전면 삭제 / MINOR 전부 수정 |
| 2.5 correction round 1 | 수정 완료, PDF 3쪽 | `stage2_5_correction_round1.md` | — |
| 2.5 INTEGRITY (round 2, 독립 전체 재검증) | FAIL — SERIOUS 0, MEDIUM 2(provenance 필드 누락, 보충자료가 링크한 구 수치 원장), MINOR 0; 수치 126/126, 주장 58/58; 7모드 모두 CLEAR | `stage2_5_integrity_report_round2.md` | — |
| 2.5 correction round 2 | 보충자료의 구 원장 링크를 원자료 경로로 교체; provenance 4개 필드 기록; N4(층화 무작위 표본 명시)·N7("따라서" 연결) 반영. 변경 항목 결정적 재확인: 원장 링크 0, 사람 평가 언급 0, PDF 3쪽, Overfull/미정의 참조 0 | 이 파일 | MANDATORY checkpoint 대기 |
| 3 REVIEW Phase 0 | 심사자 카드 5자리 작성 | `stage3_reviewer_cards.md` | 사용자: 카드 전체 승인 (2026-11-13) |
| 3 REVIEW Phase 1–2 | 5자리 모두 Minor; 편집 판정 Minor Revision; 로드맵 RM-01~30(P0 2, P1 16), 거절·보류 D-01~17, 팀 메모 T1~T12 | `stage3_review_*.md`, `stage3_editorial_decision.md`, `stage3_revision_roadmap.md` | MANDATORY checkpoint 대기 |
| 3 checkpoint | — | — | 사용자: P0+P1 반영, P2는 보충자료·길이중립 문구만 / 코칭 건너뜀 |
| 4 REVISE | RM-01~18 전부, P2는 보충/길이중립; PDF 3쪽; 신규 CI는 잠금 bootstrap 재사용(저장 구간 26/26 재현); 원자료 해시 불변; RM-16 로드맵 오류(API 표기) 정정 | `stage4_response_to_reviewers.md`, `stage4_delta_report.md`, `results/koblex-reproduction-v1/chapter4-revision-v1/` | 사용자 확인 대기 |
| 4 checkpoint | — | — | 사용자: 3′ 재심사 진행 (2026-11-14) |
| 3′ RE-REVIEW | **Accept** (B6): must_fix 2/2 FULLY, should_fix 16/16(15 FULLY, RM-05 PARTIAL·잔여 consider), consider 10 FULLY·2 CANNOT_VERIFY; 신규 이슈 0, 과장 0; 계약 규칙 수작업 적용(manifest/checker 없음) | `stage3prime/phase1_criteria.md`, `phase2a_evidence_verdicts.md`, `stage3prime_verification_report.md` | MANDATORY checkpoint 대기 |
| 3′ checkpoint | — | — | 사용자: 잔여 항목 수정 진행, 4.5는 일단 제외; 분량 축소에 무게 (2026-11-14) |
| 잔여 수정·분량 축소 | 본문 7,575→6,261자(−17%); 잔여 1–7 처리; 수치 대조표 신설; PDF 3쪽; 4.5 미실행(사용자 지시) | `chapter4-revision-v1/manuscript-number-map.md`, 백업 `pre_stage4prime/` | 사용자 확인 대기 |
