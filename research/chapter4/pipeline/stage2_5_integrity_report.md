# Academic Integrity Verification Report — 제4장 (실험 결과 및 분석)

## Verification Mode
Initial Verification (Mode 1, Stage 2.5 pre-review). 단일 장(Chapter 4) 대상. 검증일 2026-11-13.

- 주 원고: `research/chapter4/chapter4.md` (sha256 앞 16자 `3cdf21dc12c07a41`)
- 동기화 대상: `research/chapter4/section4_1.tex` ~ `section4_5.tex`, 그림/표 캡션
- 보충: `research/chapter4/chapter4-supplement.md` (`a066f3a54ba7f6b9`)
- 근거(ground truth)로 인정한 파일만 사용: `results/koblex-reproduction-v1/{analysis.json, protocol-lock.json, runtime-settings.json, human-review/}`, `configs/koblex-reproduction.yaml`, `results/koblex-reproduction-v1/chapter4-prep-v1/` (A1–A6), `results/koblex-latency-v1/`, `results/koblex-filtering-v1/` (e2e 포함). `manuscript-facts.json`, `draft-validation.json`은 근거로 쓰지 않았다.
- 실행한 것: 로컬 JSON/CSV/JSONL 읽기와 재계산(python3)만. 모델·API 호출, 실험, 외부 전송, 교차 모델 검증 없음.

## Verdict
**FAIL**

사유: SERIOUS 2건(완료된 E2E 답변 재생성 실험을 "수행하지 않았다"고 서술), MEDIUM 1건(C4-D7 구조적 FAIL), MAJOR_DISTORTION 1건(Phase E), AI Failure Mode 6 SUSPECTED(차단). 그 외 수치 자체는 추적 가능한 모든 값이 원자료와 일치했다.

## Verification Summary

| Category | Total | Passed | Issues |
|----------|-------|--------|--------|
| Reference Existence (Phase A) | 0 (chapter4.md에 참고문헌 목록·인용 없음 → N/A, registered population = 0) | – | – |
| Bibliographic Accuracy (A2) | 0 → N/A | – | – |
| Ghost Citations (A3) | – | – | 0 orphan / 0 dangling (본문에 인용 표지 없음) |
| Citation Context Accuracy (Phase B) | 0 → N/A | – | – |
| Statistical Data Accuracy (C1) | 151 수치(본문 130 + 표·캡션 21) | 151 MATCH | 0 MISMATCH, 0 NOT_TRACEABLE |
| Internal Consistency (C2) | – | Fail(경미) | 4 (단위 혼용 1, 라벨 오기 1, 논리 어구 1, 조건 표기 모호 1) — 모두 MINOR |
| md↔tex 동기화 | 19 문단 + 5 캡션 + 2 표 | 전부 일치 | 0 (단, tex의 하드코딩 그림/표 번호는 MINOR) |
| Figure/Table Caption Fidelity (C3) | 3 그림 + 2 표 | 5 PASS WITH NOTES | 1 MINOR (provenance 누락·stale 문구) |
| Experiment Provenance (C4) | D7 선행 검사 | – | 1 구조적 FAIL (experiment_intake_declaration 부재) |
| Originality (D1/D2) | NOT RUN — 외부 검색 금지 지시(원고 외부 전송 불가) | – | – |
| Claim Verification (E) | 52 of 52 registered (Mode 1 #549: HIGH-IMPACT 52, RANDOM 0, TOP-UP 0, NOT-SELECTED 0 — 결과 밀집 장이므로 전수) | 47 VERIFIED | 1 MAJOR_DISTORTION, 4 MINOR_DISTORTION, 0 UNVERIFIABLE |

Phase A/B 메모: `chapter4.md`와 `section4_*.tex`에는 참고문헌 목록도, 인용 표지도 없다(검색 확인). 따라서 Phase A/B는 N/A이며 등록 모집단은 0이다. 보충 자료 S5에 문헌 1건(Lee et al., 2025, arXiv:2509.01324)이 있으나 이 감사의 범위 밖이고, WebSearch 금지 조건이라 검증하지 않았다(NOT_SEARCHED, note).

## Phase D: Originality Verification Results
NOT RUN. 원고 내용을 외부로 보내지 말라는 지시 때문에 WebSearch 기반 D1/D2를 수행하지 않았다. 이 항목은 0으로 보고하지 않는다.

| Grade | Paragraph Count | Proportion |
|-------|----------------|-----------|
| (not run) | – | – |

## Phase E: Claim Verification Results

**Claim Registry coverage sidecar (#737)**

- Status: `not_run` — 이 감사는 읽기 전용 수동 감사로, `claim-registry/1.0` 산출물과 `scripts/claim_registry_coverage.py`를 실행하지 않았다. 아래 Claim 표는 수동 레지스트리의 렌더링이다.
- **E1-COVERAGE-UNRESOLVED**: candidate-unregistered count는 0으로 보고할 수 없다. Semantic extraction coverage: `not_machine_detectable`.

| Verdict | Claim Count | Proportion |
|---------|------------|-----------|
| VERIFIED | 47 | 90.4% |
| MINOR_DISTORTION | 4 | 7.7% |
| MAJOR_DISTORTION | 1 | 1.9% |
| UNVERIFIABLE | 0 | 0% |
| UNVERIFIABLE_ACCESS | 0 | 0% |

Persisted evidence rows (#656): `scripts/evidence_rows.py`를 실행하지 않았으므로 `phases.E_claims.evidence_rows[]`는 생성되지 않았다. 아래 "Verification Audit Trail"의 Claim 표(C-01~C-52)가 근거 경로·키를 담은 수동 대체물이다.

Scope-conformance (#547): `[E4-SKIPPED: no scope context]` (RQ Brief 미제공).
Novelty-claim (#548): 장 내에 "최초/새로운" 류 신규성 주장 없음 — 해당 없음.
Cache staleness (#541): 인용 없음 — 해당 없음.
Claim-strength drift (#569): `[E6-SKIPPED: no revision evidence]` (첫 감사).

### C4 Experiment Provenance & Claim Alignment
**Boundary (verbatim):** "This check verifies disclosure and claim-to-provenance fidelity. It does not judge whether the experiment was correctly designed, run, statistically adequate, or reproducible by ARS."

- D7: Material Passport, `repro_lock.ars_version`, `experiment_intake_declaration`, `experiment_provenance[]` 어느 것도 제공되지 않았다. 버전 증명이 없으므로 post-#260으로 취급하며, D7 조건 1(declaration 부재)에 해당하는 **구조적 FAIL**이다(IL-MEDIUM-1).
- 대체 수행: 결과 폴더(`koblex-reproduction-v1`, `chapter4-prep-v1`, `koblex-latency-v1`, `koblex-filtering-v1`, `koblex-filtering-v1/e2e`)를 실험 단위로 보고, 각 장 주장이 해당 결과와 맞는지 수동 대조했다. 결과: 3개 실험(주 품질, 지연, 오프라인 필터링)은 정렬됨(ALIGNED). **4번째 완료 실험(필터링 근거로 답변 재생성 E2E, `results/koblex-filtering-v1/e2e-summary.json`, 226×2 조건 완료)은 본문과 보충 자료에서 "수행하지 않았다"고 서술되어 NOT_SUPPORTED_BY_PROVENANCE에 해당**(IL-SERIOUS-1/2).

### C3 Figure/Table Caption Fidelity
`figure_table_trace[]`를 담은 Figure Package는 없다. `figures/section-figures-v1/provenance.json`과 `build_manuscript_figures.py`, `*.data.json`으로 수동 추적했다.

| 산출물 | source_data | transformation | caption claim 판정 | 비고 |
|---|---|---|---|---|
| 그림 1 (`fig_4_2_evidence_effects_column`) | `fig_4_2_evidence_effects.data.json` ← `analysis.json` comparisons[0..3] (sha 7609288f… 일치) | `build_manuscript_figures.py` L15 | PASS: 4지표 Jev−CE 점추정·95% CI, EM·완전회수율은 %p·나머지는 점 — 데이터와 일치. 렌더링에서도 EM·coverage CI가 0을 가로지름 | provenance.json에 `_column` 출력 해시 없음 |
| 그림 2 (`fig_4_3_shortlist_quality_column`) | `fig_4_3_shortlist_quality.data.json` ← `A4/stage-summary.csv` (sha 5581f4ac… 일치) | L19 | PASS: 69.47/74.63, 49.56/57.52, 오차막대 없음 | provenance 캡션에 stale 문구 "지연은 최종 집계 미완료로 포함하지 않았다" |
| 그림 3 (`fig_4_5_gold_loss_stages_column`) | `fig_4_5_gold_loss_stages.data.json` ← `A4/stage-summary.csv` | L23 | PASS: 443건 배타 분류, 33/75/42·13/60·72/233·250 | – |
| 표 1 (지연) | `koblex-latency-v1/summary.json` per_question_ms | 직접 전기, raw.jsonl에서 재계산 일치 | PASS | 표 trace 없음 → trace-unavailable note |
| 표 2 (필터링) | `koblex-filtering-v1/summary.json` cv_overall | 직접 전기 | PASS(수치). 단 본문 4.4 마지막 문단의 "답변 재생성 안 함" 서술은 IL-SERIOUS-1 | 표 trace 없음 → trace-unavailable note |

Limitation visibility: 그림 1(탐색적, 다중비교 무보정 — 4.1에 명시), 그림 2(문항별 평균, 오차막대 없음 — 캡션에 명시), 그림 3(선택 수 제약 — 캡션에 명시). 누락된 한계 없음.

## Issue List (Sorted by Severity)

### SERIOUS (Must Fix)
| ID | # | Category | Location | Issue Description | Correct Information | Source |
|----|---|----------|----------|------------------|--------------------|----|
| IL-SERIOUS-1 | 1 | 방법 서술 허위 / 완료 실험 누락 (Phase E MAJOR_DISTORTION, C4 NOT_SUPPORTED_BY_PROVENANCE, Mode 6) | `chapter4.md:67`, `section4_4.tex:30` | 원고: "필터링 후 답변은 재생성하지 않았으므로 답변 품질 유지나 실제 비용 절감으로 해석하지 않았다." 필터링된 근거로 답변을 재생성하고 Token F1·LF-Eval을 다시 평가한 E2E 실험이 완료되어 있다(원고 수정 시각 23:02:51보다 앞선 22:59:02 생성). 따라서 이 문장은 사실과 다르고, 완료된 실험 결과가 4.4에서 빠져 있다. | E2E: 교차검증 τ를 고정한 뒤 근거가 바뀐 문항만 재생성(CE 10, Jev 45문항). 나머지는 원 답변을 재사용했고, 재사용 문항의 LF 점수가 원 실험과 같음을 확인했다(`reused_lf_identical: true`). 결과 Token F1/LF-Eval: CE-FR 45.65/67.13, Jev-FR 47.03/69.13. Jev-FR−Jev-R: Token F1 −0.28 [−1.10, +0.44], LF −1.02 [−2.23, +0.15]. CE-FR−CE-R: Token F1 −0.54 [−1.19, −0.07], LF −0.44 [−1.22, +0.14]. Jev-FR−CE-R: Token F1 +0.83 [−0.39, +2.00], LF +1.56 [−0.83, +3.86]. 추가 비용 약 $0.46(README 기재, 원장 미대조). **수정안**: (a) E2E 결과를 4.4에 추가한다. 예: "필터링 근거로 변경 문항의 답변을 재생성한 결과 Jev의 Token F1은 47.31→47.03(차이 −0.28, CI [−1.10, +0.44]), LF-Eval은 70.15→69.13(−1.02, CI [−2.23, +0.15])이었다. 사전 비열등성 마진이 없으므로 품질 유지로 해석하지 않는다." (b) 싣지 않기로 했다면 허위 문장을 지우고 "답변 재생성 E2E 결과는 본문에서 제외하였다(사유)"로 바꾼다. 어느 쪽이든 "재생성하지 않았다"는 표현은 삭제한다. | `results/koblex-filtering-v1/e2e-summary.json` (`checks.*.regenerated`, `means.*`, `paired_bootstrap_points.*`); `results/koblex-filtering-v1/README.md` "추가: 필터링된 근거로 답변 재생성(E2E)"; `e2e/predictions/*.jsonl`, `e2e/lf-eval/*/metrics.jsonl` (각 226행) |
| IL-SERIOUS-2 | 2 | 보충 자료의 동일 허위 서술 및 범위 과대진술 | `chapter4-supplement.md:101`, `:105` | :101 "필터링된 근거로 답변을 재생성하거나 사람 판단을 수행하지 않았다." 재생성 부분이 거짓이다. :105 "본문은 완료된 … 필터링 … 분석을 수록한다"는 완료된 E2E가 빠진 상태에서 완결성을 암시한다. S7 전체가 E2E 이전 상태(`summary.json` status `…NO_ANSWER_REGENERATION`)를 기준으로 쓰였다. | :101 → "필터링 근거로 변경 문항의 답변을 재생성한 E2E 결과는 `e2e-summary.json`에 있으며 [본문 4.4에 수록/제외]하였다. 사람 판단은 수행하지 않았다." :105의 수록 범위 문장에 E2E의 포함·제외를 명시한다. | 위와 동일 |

### MEDIUM (Must Fix)
| ID | # | Category | Location | Issue Description | Correct Information | Source |
|----|---|----------|----------|------------------|--------------------|----|
| IL-MEDIUM-1 | 1 | C4-D7 구조적 FAIL (원고 내용 오류가 아닌 파이프라인 산출물 부재) | 파이프라인 passport | `experiment_intake_declaration`과 `experiment_provenance[]`가 없다. 장이 자체 실험 결과를 보고하므로(`status: experiments_declared` 필요), declaration이 없으면 D7 조건 1로 FAIL이다. | 실험 4건(품질 재현, 지연, 오프라인 필터링, 필터링 E2E)을 `experiment_provenance[]`로 선언한다. 각 항목에 repro_lock(`protocol-lock.json`, `latency-v1/protocol.json`, `filtering summary.json` rule/seed), planned_vs_executed, negative_results(예: EM·완전회수율 CI가 0 포함, Jev top-10 재현율 1.11%, E2E LF CI 하한 −2.23), known_limitations를 넣는다. | ARS `integrity_verification_agent.md` §C4 D7 |

### MINOR (Recommended Fix at Stage 2.5; Must Fix at Stage 4.5)
| ID | # | Category | Location | Issue Description | Suggestion |
|----|---|----------|----------|------------------|----|
| IL-MINOR-1 | 1 | 지표 라벨 오기 (MINOR_DISTORTION) | `chapter4.md:65`, `section4_4.tex:28`; `chapter4-supplement.md:101` | "pool별 gold 유지 비율이 CE 66.14→51.47%, Jev 72.69→69.30%". 값은 맞다. 다만 이 값은 pool 단위가 아니라 **문항별 gold 출현 443건 기준 micro 비율**이다(66.14% = 293/443, 72.69% = 322/443로 `A4/stage-summary.csv` shortlist micro와 정확히 같음). | "gold 출현(443건) 기준 shortlist 유지 비율"로 바꾸고, 그림 2(문항별 평균)와 다르며 그림 3과 분모가 같다고 적는다. |
| IL-MINOR-2 | 2 | 논리 어구 오류 (MINOR_DISTORTION) | `chapter4.md:52`, `section4_4.tex:7` | "선택 목록은 양쪽 모두 478개로 동일하므로, 이는 선택 수 감소가 아닌 선택 내용 변화에 따른 결과이다." 문맥 토큰은 **증가**했으므로 대비 대상은 "선택 수 증가"여야 한다. | "선택 수 증가가 아닌" 또는 "선택 수의 차이가 아닌"으로 고친다. |
| IL-MINOR-3 | 3 | 조건 표기 모호 (MINOR_DISTORTION) | `chapter4.md:50`, `section4_4.tex:5` | "Jev의 Token F1은 46.20점에서 47.31점으로". 46.20은 CE 값이므로 Jev 자체가 변한 것처럼 읽힌다(4.2의 "63.46점에서 66.85점으로"와 같은 패턴이지만 여기서는 주어가 Jev로 명시됨). | "Token F1은 CE 46.20점에서 Jev 47.31점으로, LF-Eval은 67.57점에서 70.15점으로"로 고친다. |
| IL-MINOR-4 | 4 | 단위 혼용 (C2) | `chapter4.md:11` vs `:25`; tex 동일 | 문항별 평균 Recall이 4.2에서는 "점"(57.74점), 4.3에서는 "%"·"%p"(69.47%, 5.16%p)로 표기된다. 그림 1 캡션은 비율형 지표(EM·완전회수율)만 %p로 정의한다. | 문항별 평균형 지표(P/R/F1, shortlist Recall)는 "점", 문항 비율형(EM, 완전회수율, 모든 gold 포함률)은 "%·%p"로 통일한다. 아니면 4.3 첫 문단에 단위 정의를 추가한다. |
| IL-MINOR-5 | 5 | 보충 자료 참조 과대 (MINOR_DISTORTION) | `chapter4.md:79`, `section4_5.tex:16` | "사례 식별자·원문·선정 규칙은 보충자료에 제시하였다." 보충 S4에는 식별자와 선정 규칙이, S6에는 일부 조문명이 있다. 그러나 사례의 질문·답변·조문 **원문**은 없다(S5 "관련 원문"은 KoBLEX 논문 서지). | 보충 자료에 세 사례의 질문·gold·선택 조문·답변 원문을 추가한다(출처: `A6/casebook.jsonl`). 아니면 본문을 "사례 식별자와 선정 규칙"으로 줄인다. |
| IL-MINOR-6 | 6 | LaTeX 상호참조 하드코딩 | `section4_2.tex:14`, `section4_3.tex:5`, `section4_4.tex:28`, `section4_5.tex:5` | "(그림 1)", "(그림 2)", "(표 2)", "(그림 3)"을 문자열로 적었다. `\label{fig:ch4_2}` 등은 정의되어 있지만 쓰이지 않는다. 통합 논문에 앞 장 그림이 있으면 번호가 어긋난다. | `그림~\ref{fig:ch4_2}` 등 `\ref`를 쓰고, 표에도 `\label`을 추가한다. |
| IL-MINOR-7 | 7 | 그림 provenance 불완전·stale (C3 note) | `figures/section-figures-v1/provenance.json`, `README.md` | 본문이 쓰는 `_column` 3종의 출력 해시가 provenance에 없다. fig_4_3 provenance 캡션에 "지연은 최종 집계 미완료로 포함하지 않았다", README 끝에 "4.3 지연 비교는 … 별도 갱신해야 한다"가 남아 있다(지연은 완료됨). 본문 캡션 자체는 정확하다. | `build_manuscript_figures.py` 출력 해시와 입력 data.json 해시를 provenance에 추가하고, stale 문구를 갱신한다. |
| IL-MINOR-8 | 8 | 재현 정보 축약 | `chapter4.md:5`, `section4_1.tex:5` | CE 모델을 `bge-reranker-v2-m3-ko`로 축약했다. 실제는 `dragonkue/bge-reranker-v2-m3-ko`, revision `2aca5884…`이다. | 전체 HF ID를 쓰거나 3장 방법 절의 해당 위치를 참조한다. |

### Notes (비차단, 이슈 수에 미포함)
- N1. CE 입력 형식 진단(`ce-diagnostic-summary.json`: 기존 시험 30문항에서 4개 입력 형식 비교, plain question 형식이 최고)은 주 실험 CE 입력("original question only")의 선택과 관련 있다. 4장은 "모든 비교는 기존 시험 결과를 확인한 뒤 수행한 탐색적 분석"으로 포괄 서술했지만, 이 진단을 3장 또는 4.1에서 공개하는 것이 투명하다.
- N2. `koblex-latency-v1/summary.json`의 limits는 "60-question pre-registered sample"이라고 쓰는 반면, 보충 S9는 "사전등록을 뜻하지 않는다"고 쓴다. 본문의 "미리 고정한"은 두 쪽과 모순되지 않는다. 출처 쪽 표현을 정리하길 권한다.
- N3. 본문은 KoBLEX·ParSeR·LF-Eval·BM25·bge-reranker를 인용 없이 언급한다(보충 S5에 KoBLEX 1건만 있음). 통합 논문의 2·3장에서 인용된다면 문제없다. 4장이 단독으로 쓰인다면 인용 추가가 필요하다.
- N4. Jev 품질 수치는 단일 실행 결과다. 지연 벤치마크에서 같은 입력의 top-10 완전 일치율이 1.11%(2/180)였으므로, 3.19점 F1 차이의 run-to-run 변동은 측정되지 않았다. 본문 4.3 마지막 문단에서 이를 공개했다. 공개는 적절하며 결과 해석(3장/5장)에 반영할 필요가 있다.
- N5. 보충 S5의 문헌(Lee et al., 2025, arXiv:2509.01324)은 WebSearch 금지로 NOT_SEARCHED.

## AI Research Failure Mode Checklist

| Mode | Outcome | Evidence | Blocks? |
|------|---------|----------|---------|
| 1. Implementation bug passing self-review | CLEAR | 모든 수치가 저장된 산출물(analysis.json, A1–A6, latency raw/summary, filtering summary/csv)로 추적되고, 핵심 값을 원시 파일에서 독립 재계산해 일치시켰다(예: raw.jsonl 360행 → 평균 5.009/10.650초, 2/180, 0.91509, $0.6100542, 실패·재시도 0; question-stages → 478 pool, 77/79, 126/116). CI는 지표마다 다르고, 의심스러운 정수·동일 구간이 없다. CE 점수 척도(문턱값 ~3.8e-6)는 README가 진단·공개한 sigmoid 출력 특성이다. | no |
| 2. Hallucinated citation | CLEAR (N/A 성격) | 본문에 인용·참고문헌 목록이 없어 등록 모집단이 0이다. 보충 S5 1건은 NOT_SEARCHED(note N5). | no |
| 3. Hallucinated experimental result | CLEAR | 본문·캡션·표의 수치 151개 전부 MATCH, NOT_TRACEABLE 0. 사례 A/B/C의 조문·점수도 `A6/casebook.jsonl`과 일치한다. | no |
| 4. Shortcut reliance | INSUFFICIENT EVIDENCE (flag only) | 교란 요인 ablation은 없다. Jev instruction은 사전 고정이라 결과 기반 튜닝이 없었다(`protocol-lock.json` sampling). 그러나 Jev 출력이 비결정적이고(top-10 재현 1.11%) 품질 실험은 1회라서, 개선의 실행 간 안정성을 판단할 근거가 없다(N4). CE 입력 형식은 시험 문항 진단 후 정해졌다(N1, CE에 유리한 방향). | no (2.5에서 flag-only) |
| 5. Bug reframed as novel insight | CLEAR | "놀랍게도/예상과 달리" 류 서술이 없다. 비정상 관측(공개 코드 인덱스 문제, Jev 비결정성)은 발견이 아니라 한계·수정으로 서술했고, 원인은 `protocol-lock.json`(`contexts_list[0][choice]`)과 latency raw로 뒷받침된다. | no |
| 6. Methodology fabrication | **SUSPECTED** | 본문 4.4(`chapter4.md:67`)와 보충 S7(`:101`)이 "필터링 후 답변은 재생성하지 않았다"고 서술한다. 실제로는 E2E 답변 재생성·LF 평가가 완료되어 있다(`e2e-summary.json`, 226×2). 실제 실행과 다른 방법 서술이다(IL-SERIOUS-1/2). 나머지 방법 수치(K=100, top-10, 151그룹, 10,000회, seed, MPS/float32/batch 50, concurrency 4, warmup 3, 3회 반복, 800자 clip, 5-fold, 20 분위수 격자, 1점 허용)는 config/protocol과 모두 일치한다. | **yes** |
| 7. Frame-lock at early stage | INSUFFICIENT EVIDENCE (warning) | 원고가 E2E 이전 프레임("필터링=근거 지표만, 답변 품질 미측정", `summary.json` status)에 고정된 채, 이후 완료된 E2E가 4.4·보충·WRITING_NOTES 어디에도 반영되지 않았다. 집필 프레임이 최신 실험 상태를 따라가지 못한 징후다. RQ 자체를 잘못 세웠다는 증거는 없다. | no (경고, 4.5에서 재검) |

차단 사유: Mode 6 SUSPECTED.

## Tool Limitation Disclaimer

> 이 보고서의 Phase D(원문성)는 원고를 외부로 보내지 말라는 지시에 따라 수행하지 않았다. 따라서 표절·중복 여부는 확인되지 않았으며, 정식 투고 전 전문 표절 검사 도구 사용을 권한다. Phase E의 레지스트리·커버리지 스크립트와 evidence-row 스크립트도 실행하지 않았다(E1-COVERAGE-UNRESOLVED). 아래 표는 수동 감사 기록이다.

## Verification Audit Trail

경로 약어: **AJ** = `results/koblex-reproduction-v1/analysis.json`; **PL** = `.../protocol-lock.json`; **CFG** = `configs/koblex-reproduction.yaml`; **SS** = `.../chapter4-prep-v1/A4/stage-summary.csv`; **DEN** = `.../A4/denominators.json`; **PF** = `.../A4/pool-feasibility-summary.json`; **QS** = `.../A4/question-stages.jsonl`; **WTL** = `.../A3/win-tie-loss.json`; **DS** = `.../A5/descriptive-statistics.csv`; **CSU** = `.../A5/cache-separated-usage.csv`; **CB** = `.../A6/casebook.jsonl`; **RC** = `.../A6/proposed-three-candidates.json`; **HB** = `.../A6/human-review-boundary.json`; **LP** = `results/koblex-latency-v1/protocol.json`; **LS** = `.../summary.json`; **LR** = `.../raw.jsonl`; **FS** = `results/koblex-filtering-v1/summary.json`; **PMK** = `.../post_matched_keep_rate.csv`; **PRE** = `.../pre_matched_keep_rate.csv`; **E2E** = `.../e2e-summary.json`. 비교 인덱스 `cmp[i]`는 AJ `comparisons[i]`(0 F1, 1 Recall, 2 EM, 3 coverage, 4 Token F1, 5 LF, 6 raw→fixed F1). 원값 0~1은 ×100으로 비교했다.

### A. 수치 추적 (C1/C2)

| ID | 위치(md) | 원고 수치 | 출처 경로·키 | 원값 → 재계산 | 판정 |
|---|---|---|---|---|---|
| N-001 | :5 | 226문항 | AJ summaries.*.questions | 226 | MATCH |
| N-002 | :5 | bge-reranker-v2-m3-ko | PL signature.ce.model | dragonkue/bge-reranker-v2-m3-ko | MATCH (축약, IL-MINOR-8) |
| N-003 | :5 | jev-1.14.0 | PL signature.jev.model | jev-1.14.0 | MATCH |
| N-004 | :5 | gpt-4o-2024-08-06 (선택·생성·평가) | PL generation.model; lf-eval/*/manifest.json model | 둘 다 gpt-4o-2024-08-06 | MATCH |
| N-005 | :5 | 후보 100개 | CFG top_k; PL retriever k=100 | 100 | MATCH |
| N-006 | :5 | 상위 10개 | CFG top_n; PL top_n_before_llm_selection | 10 | MATCH |
| N-007 | :5 | 목록당 하나 선택 | PF rule "pool capacity 1" | 1 | MATCH |
| N-008 | :5 | 478개 후보 목록 | QS Σn_pools; DS selected_list_count sum; candidate-audit parametric_provisions | 478 | MATCH |
| N-009 | :7 | 세 조건 각 226개 답변·평가 | AJ lf_eval_status COMPLETE ×3; final-status answers 678 | 226×3 | MATCH |
| N-010 | :7 | 95% CI | AJ cmp[*].ci95 | 95% | MATCH |
| N-011 | :7 | 151개 그룹 | AJ cmp[*].clusters | 151 | MATCH |
| N-012 | :7 | bootstrap 10,000회 | AJ cmp[*].repetitions | 10000 | MATCH |
| N-013 | :7 | 60문항 | LP sample.questions | 60 | MATCH |
| N-014 | :7 | 15/34/11 | LP sample.hop_counts; CFG human_evaluation_ids 개수 확인 | 15/34/11 | MATCH |
| N-015 | :7 | 52개 의존 그룹 | LS jev_minus_ce_ms.clusters | 52 | MATCH |
| N-016 | :11 | Jev F1 61.75 | AJ parser_jev_fixed.retrieval.f1 | 0.617531 → 61.75 | MATCH |
| N-017 | :11 | CE F1 58.57 | AJ parser_ce_fixed.retrieval.f1 | 0.585651 → 58.57 | MATCH |
| N-018 | :11 | 3.19점 높음 | AJ cmp[0].mean_difference | 0.031879 → 3.19 | MATCH |
| N-019 | :11 | Precision 63.46 | AJ ce_fixed.precision | 0.634587 → 63.46 | MATCH |
| N-020 | :11 | Precision 66.85 | AJ jev_fixed.precision | 0.668510 → 66.85 | MATCH |
| N-021 | :11 | Recall 57.74 | AJ ce_fixed.recall | 0.577434 → 57.74 | MATCH |
| N-022 | :11 | Recall 60.69 | AJ jev_fixed.recall | 0.606932 → 60.69 | MATCH |
| N-023 | :17 | F1 CI [+0.75, +5.68] | AJ cmp[0].ci95 | [0.7469, 5.6762] | MATCH |
| N-024 | :17 | Recall CI [+0.39, +5.51] | AJ cmp[1].ci95 | [0.3912, 5.5067] | MATCH |
| N-025 | :17 | EM 27.88% | AJ ce_fixed.em | 0.278761 → 27.88 | MATCH |
| N-026 | :17 | EM 29.65% | AJ jev_fixed.em | 0.296460 → 29.65 | MATCH |
| N-027 | :17 | 완전 회수율 34.07% | AJ ce_fixed.gold_set_coverage | 0.340708 → 34.07 | MATCH |
| N-028 | :17 | 완전 회수율 34.96% | AJ jev_fixed.gold_set_coverage | 0.349558 → 34.96 | MATCH |
| N-029 | :17 | 두 CI가 0 포함 (EM) | AJ cmp[2].ci95 | [−1.77, +5.19] | MATCH |
| N-030 | :17 | 두 CI가 0 포함 (coverage) | AJ cmp[3].ci95 | [−2.90, +4.53] | MATCH |
| N-031 | :17 | 77개 | SS ce final all_gold_questions; QS Σall_gold_selected | 77 (=34.07%×226) | MATCH |
| N-032 | :17 | 79개 | SS jev final | 79 | MATCH |
| N-033 | :19 | Jev 우세 32 | WTL counts.f1.Jev_higher | 32 | MATCH |
| N-034 | :19 | 동일 177 | WTL counts.f1.tie | 177 | MATCH |
| N-035 | :19 | CE 우세 17 | WTL counts.f1.CE_higher | 17 (32+177+17=226) | MATCH |
| N-036 | :19 | 1-hop 78.07 | AJ ce_fixed.diagnostics.by_hop.1.f1 | 0.780702 | MATCH |
| N-037 | :19 | 1-hop 76.90 | AJ jev_fixed.by_hop.1.f1 | 0.769006 | MATCH |
| N-038 | :19 | 2-hop 53.33 | AJ ce_fixed.by_hop.2.f1 | 0.533333 | MATCH |
| N-039 | :19 | 2-hop 57.24 | AJ jev_fixed.by_hop.2.f1 | 0.572441 | MATCH |
| N-040 | :19 | 3-hop 47.91 | AJ ce_fixed.by_hop.3.f1 | 0.479138 | MATCH |
| N-041 | :19 | 3-hop 54.83 | AJ jev_fixed.by_hop.3.f1 | 0.548299 | MATCH |
| N-042 | :19 | 3-hop 완전회수 1/42 (양 조건) | AJ by_hop.3.gold_set_coverage ×2, questions 42 | 0.02381×42 = 1 | MATCH |
| N-043 | :19 | 고유 gold 386 | DEN unique_gold_global | 386 | MATCH |
| N-044 | :19 | 미매핑 27 | DEN unmapped_unique_gold_global | 27 | MATCH |
| N-045 | :19 | 영향 29문항 | AJ diagnostics.unavailable_gold_affected.questions | 29 | MATCH |
| N-046 | :19 | 완전 매핑 197문항 | AJ diagnostics.fully_mapped.questions | 197 (197+29=226) | MATCH |
| N-047 | :19 | 197문항 F1 64.12 | AJ ce_fixed.fully_mapped.f1 | 0.641238 | MATCH |
| N-048 | :19 | 197문항 F1 67.21 | AJ jev_fixed.fully_mapped.f1 | 0.672057 | MATCH |
| N-049 | :19 | 29문항 F1 20.80 | AJ ce_fixed.unavailable_gold_affected.f1 | 0.208046 | MATCH |
| N-050 | :19 | 29문항 F1 24.71 | AJ jev_fixed.unavailable_gold_affected.f1 | 0.247126 | MATCH |
| N-051 | :21 | 공개 코드 CE F1 48.72 | AJ parser_ce_raw.retrieval.f1 | 0.487168 | MATCH |
| N-052 | :21 | 9.85점 차이 | AJ cmp[6].mean_difference | 0.098483 → 9.85 | MATCH |
| N-053 | :25 | 상위 10개 | CFG top_n | 10 | MATCH |
| N-054 | :25 | BM25 합집합 Recall 77.21% | SS bm25 macro_question_gold_recall; candidate-audit candidate_recall | 0.772124 | MATCH |
| N-055 | :25 | shortlist CE 69.47% | SS ce shortlist macro | 0.694690 | MATCH |
| N-056 | :25 | shortlist Jev 74.63% | SS jev shortlist macro | 0.746313 | MATCH |
| N-057 | :25 | 5.16%p | 재계산 74.6313−69.4690 | 5.162 | MATCH |
| N-058 | :25 | 112개 | SS ce shortlist all_gold_questions; PF all_gold_in_union | 112 | MATCH |
| N-059 | :25 | 49.56% | 112/226 | 49.558 | MATCH |
| N-060 | :25 | 130개 | SS jev shortlist all_gold_questions | 130 | MATCH |
| N-061 | :25 | 57.52% | 130/226 | 57.522 | MATCH |
| N-062 | :31 | 동시 선택 가능 CE 104 | PF ce shortlist all_gold_jointly_selectable | 104 | MATCH |
| N-063 | :31 | 동시 선택 가능 Jev 120 | PF jev shortlist | 120 | MATCH |
| N-064 | :31 | 실제 77/79 | SS final | 77/79 | MATCH |
| N-065 | :34 | 상위 10개 구성까지 | LP timed_region | "per-pool sort + top-10" | MATCH |
| N-066 | :34 | 워밍업 3문항 | LP warmup_questions_per_method; LR warmup 행 3/방법 | 3 | MATCH |
| N-067 | :34 | 3회 반복 | LP repetitions; LR 문항별 3행 | 3 | MATCH |
| N-068 | :34 | float32 | LP ce.dtype | float32 | MATCH |
| N-069 | :34 | 배치 50 | LP ce.batch_size | 50 | MATCH |
| N-070 | :34 | 동시 요청 4개 | LP jev.concurrency | 4 | MATCH |
| N-071 | :34 | 360개 본 측정 | LR warmup=false 행 | 180+180 | MATCH |
| N-072 | :34 | 실패 0 | LS failed_attempts; LR status 전부 ok | 0/0 | MATCH |
| N-073 | :34 | Jev 재시도 0 | LS jev_retries; LR Σretries | 0 | MATCH |
| N-074 | 표1 캡션 | 60문항, 3회 평균 분포 | LS per_question_ms.n; analyze_koblex_latency.py 문항별 평균 | 60 | MATCH |
| N-075 | 표1 | CE 평균 5.01 | LS per_question_ms.ce.mean; LR 재계산 | 5008.97ms | MATCH |
| N-076 | 표1 | Jev 평균 10.65 | LS jev.mean; LR 재계산 | 10649.73ms | MATCH |
| N-077 | 표1 | CE 중앙값 4.82 | LS ce.median; LR 재계산 | 4816.85ms | MATCH |
| N-078 | 표1 | Jev 중앙값 10.79 | LS jev.median | 10794.56ms | MATCH |
| N-079 | 표1 | CE p95 8.87 | LS ce.p95 | 8870.05ms | MATCH |
| N-080 | 표1 | Jev p95 16.53 | LS jev.p95 | 16527.20ms | MATCH |
| N-081 | :44 | 평균 5.01초 / 10.65초 | 위와 동일 | – | MATCH |
| N-082 | :44 | 5.64초 길었다 | LS jev_minus_ce_ms.mean_difference | 5640.76ms | MATCH |
| N-083 | :44 | CI [+5.15, +6.17] | LS jev_minus_ce_ms.ci95 | [5148.5, 6165.9] | MATCH |
| N-084 | :44 | 기하평균 비율 2.25배 | LS jev_over_ce_geometric_mean_ratio.estimate | 2.2523 | MATCH |
| N-085 | :44 | CI [2.11, 2.39] | 동 ci95 | [2.1056, 2.3948] | MATCH |
| N-086 | :44 | 품질 226 / 지연 60 | AJ / LS | 226 / 60 | MATCH |
| N-087 | :46 | CE 100% | LS repeatability.ce.top10_identical… | 1.0 | MATCH |
| N-088 | :46 | 180/180 | LR CE 비워밍업 Σtop10_same | 180 | MATCH |
| N-089 | :46 | Jev 1.11% | LS jev.top10_identical… | 0.011111 | MATCH |
| N-090 | :46 | 2/180 | LR Jev Σtop10_same | 2 | MATCH |
| N-091 | :46 | 91.51% (정의 포함) | LS jev.top10_set_overlap_mean; benchmark_koblex_latency.py L154 Σ|∩|/(10·pools) | 0.915093 | MATCH |
| N-092 | :50 | Token F1 46.20 | AJ ce_fixed.token_f1 | 0.461954 | MATCH |
| N-093 | :50 | Token F1 47.31 | AJ jev_fixed.token_f1 | 0.473130 | MATCH |
| N-094 | :50 | LF 67.57 | AJ ce_fixed.lf_eval | 0.675712 | MATCH |
| N-095 | :50 | LF 70.15 | AJ jev_fixed.lf_eval | 0.701526 | MATCH |
| N-096 | :50 | Token F1 CI [+0.02, +2.27] | AJ cmp[4].ci95 | [0.0179, 2.2737] | MATCH |
| N-097 | :50 | LF CI [+0.37, +4.79] | AJ cmp[5].ci95 | [0.3746, 4.7916] | MATCH |
| N-098 | :50 | 앞 800자 | AJ compatibility_answer_clip_chars; lf manifest answer_clip_chars; koblex.py L148 | 800 | MATCH |
| N-099 | :50 | p ≈ 0.0525 | AJ cmp[4].p_centered_bootstrap_two_sided | 0.052495 | MATCH |
| N-100 | :52 | 문맥 203.67 | DS ce_fixed context_tokens mean | 203.668 | MATCH |
| N-101 | :52 | 문맥 215.60 | DS jev_fixed context_tokens mean | 215.597 | MATCH |
| N-102 | :52 | API 입력 2302.67 | DS ce_fixed api_input_tokens mean | 2302.668 | MATCH |
| N-103 | :52 | API 입력 2314.58 | DS jev_fixed api_input_tokens mean | 2314.584 | MATCH |
| N-104 | :52 | 출력 72.16 | DS ce_fixed api_output_tokens mean | 72.159 | MATCH |
| N-105 | :52 | 출력 73.98 | DS jev_fixed api_output_tokens mean | 73.978 | MATCH |
| N-106 | :52 | 중앙값 164 | DS ce_fixed context_tokens median | 164 | MATCH |
| N-107 | :52 | 중앙값 170.5 | DS jev_fixed context_tokens median | 170.5 | MATCH |
| N-108 | :52 | 문항별 차이 중앙값 0 | DS "Jev minus CE (paired)" context_tokens median | 0 | MATCH |
| N-109 | :52 | 선택 목록 478/478 | DS selected_list_count sum; paired diff 0 | 478, 478 | MATCH |
| N-110 | :54 | 151개 의존 그룹 5-fold | FS rule.folds; README | 5, 151 | MATCH |
| N-111 | :54 | F1 하락 1점 이내 | FS rule.tolerance_f1_points | 1.0 | MATCH |
| N-112 | :54 | 동일 크기 분위수 격자 | FS rule.cv_grid (scorer별 20 분위수) | 20/scorer | MATCH |
| N-113 | 표2 캡션 | 검증 fold 통합, 226문항 | FS cv_overall.*.questions | 226 | MATCH |
| N-114 | 표2 | CE 478/58.57/63.46/57.74 | FS cv_overall.ce.unfiltered | 478/58.565/63.459/57.743 | MATCH |
| N-115 | 표2 | CE+필터링 467 | FS ce.filtered_cv.kept_items_total | 467 | MATCH |
| N-116 | 표2 | CE+필터링 F1 58.54 | FS ce.filtered_cv.f1 | 58.536 | MATCH |
| N-117 | 표2 | CE+필터링 P 64.56 | FS ce.filtered_cv.precision | 64.565 | MATCH |
| N-118 | 표2 | CE+필터링 R 57.15 | FS ce.filtered_cv.recall | 57.153 | MATCH |
| N-119 | 표2 | Jev 478/61.75/66.85/60.69 | FS jev.unfiltered | 478/61.753/66.851/60.693 | MATCH |
| N-120 | 표2 | Jev+필터링 426 | FS jev.filtered_cv.kept_items_total | 426 | MATCH |
| N-121 | 표2 | Jev+필터링 F1 61.43 | FS jev.filtered_cv.f1 | 61.429 | MATCH |
| N-122 | 표2 | Jev+필터링 P 69.80 | FS jev.filtered_cv.precision | 69.801 | MATCH |
| N-123 | 표2 | Jev+필터링 R 58.26 | FS jev.filtered_cv.recall | 58.260 | MATCH |
| N-124 | :65 | 89.12% 유지 | FS jev.filtered_cv.kept_fraction; 426/478 | 0.891213 | MATCH |
| N-125 | :65 | F1 −0.32 | FS paired_bootstrap jev; E2E jev_fr-jev_r.f1 | −0.3245 | MATCH |
| N-126 | :65 | Precision +2.95 | E2E jev_fr-jev_r.precision | +2.9499 | MATCH |
| N-127 | :65 | Recall −2.43 | E2E jev_fr-jev_r.recall | −2.4336 | MATCH |
| N-128 | :65 | F1 CI [−1.76, +1.07] | E2E jev_fr-jev_r.f1.ci95 (FS 동일) | [−1.756, +1.066] | MATCH |
| N-129 | :65 | 근거 0개 CE 1, Jev 4 | FS *.filtered_cv.zero_evidence_questions | 1 / 4 | MATCH |
| N-130 | :65 | 90% 유지 F1 CE 57.21 / Jev 61.66 | PMK target 0.9 | 57.208 / 61.665 | MATCH |
| N-131 | :65 | 선택 전 CE 66.14→51.47% | PRE ce keep 1.0 / 0.5 shortlist_gold_recall | 66.140 / 51.467 | MATCH (라벨은 IL-MINOR-1) |
| N-132 | :65 | 선택 전 Jev 72.69→69.30% | PRE jev 1.0 / 0.5 | 72.686 / 69.300 | MATCH (라벨은 IL-MINOR-1) |
| N-133 | :65 | 약 절반 | PRE shortlist_size_mean_per_pool @0.5 | CE 5.00, Jev 5.03 | MATCH |
| N-134 | :67 | Jev 측정 비용 약 0.61달러 | LS jev_cost_usd_measured_reps; LR 비워밍업 Σcost | 0.6100542 (워밍업 포함 시 0.6177) | MATCH |
| N-135 | :71 | 443건 | DEN gold_occurrences_per_arm; SS denominator | 443 | MATCH |
| N-136 | :71 | corpus 미매핑 33 (공통) | DEN first_loss_counts.*.corpus_absent | 33/33 | MATCH |
| N-137 | :71 | BM25 미회수 75 (공통) | DEN *.bm25_absent | 75/75 | MATCH |
| N-138 | :71 | shortlist 탈락 42→13 | DEN *.shortlist_absent | 42 / 13 | MATCH |
| N-139 | :71 | 미선택 60 / 72 | DEN *.shortlist_present_unselected | 60 / 72 | MATCH |
| N-140 | :71 | 최종 선택 233→250 | DEN *.selected | 233 / 250 (합 443 확인) | MATCH |
| N-141 | :71 | 386개 | DEN unique_gold_global | 386 | MATCH |
| N-142 | 그림3 캡션 | 443건 | fig_4_5 data.json denominator | 443 | MATCH |
| N-143 | :77 | 사례 A F1 50→100 | CB qa_124_2hop_480_rand paired_metrics.ce/jev.f1 | 0.5 / 1.0 | MATCH |
| N-144 | :77 | 사례 A LF 65.29→99.18 | CB 동 lf_eval | 0.65293 / 0.99185 | MATCH |
| N-145 | :77 | 사례 B F1 80→40 | CB qa_324_2hop_515 f1 | 0.8 / 0.4 | MATCH |
| N-146 | :77 | 사례 B LF 71.79→52.67 | CB 동 lf_eval | 0.71786 / 0.52667 | MATCH |
| N-147 | :79 | 사례 C gold 3, 후보 목록 2 | CB qa_443_3hop_703 stages n_gold / n_pools | 3 / 2 | MATCH |
| N-148 | :79 | 사례 C F1 40→0 | CB 동 f1 | 0.4 / 0.0 | MATCH |
| N-149 | :79 | 사례 C Token F1 18.60→25.88 | CB 동 token_f1 | 0.186 / 0.2588 | MATCH |
| N-150 | 그림1 캡션 | EM·완전회수 %p, 나머지 점 | fig_4_2 data.json 4지표 ×100 | 일치 | MATCH |
| N-151 | 그림2 캡션 | 226문항, 오차막대 없음 | fig_4_3 data.json n=226, CI 필드 없음 | 일치 | MATCH |

합계: 151 수치/수치 진술 — MATCH 151, MISMATCH 0, NOT_TRACEABLE 0. (보충 자료에서 추가 대조: IQR 133.75/142.50, 차이 +11.93/IQR 2.50, 407/409, 71/69, 캐시 72/122, 138/226=61.06%, 정답 외 선택 126/116, hop 차이 −1.17/+3.91/+6.92, 467/478=97.70%, τ 범위, 176.98쌍, CV 16.93%/3.43%, 0.9150925926, $0.6100542, seed 20261108/20261109 — 모두 MATCH.)

### B. 주장 추적 (Phase E / C4)

| ID | 위치 | 주장(요지) | 근거 | 판정 |
|---|---|---|---|---|
| C-01 | :5 | 재정렬 모델만 CE→Jev 교체 | PL purpose "replacement of CE scoring only"; 같은 입력 형식 | VERIFIED |
| C-02 | :5 | 두 조건이 예상 법령·BM25 후보 공유 | candidates.jsonl 1개(226행)를 양 조건이 사용; QS bm25 값 양 조건 동일 | VERIFIED |
| C-03 | :5 | 선택 개수는 gold 수로 정하지 않음 | QS n_pools≠n_gold; PL "no gold used" | VERIFIED |
| C-04 | :7 | 주 기준선은 참조 문제를 수정한 CE | PL primary_comparison, correction `contexts_list[subquery_index][choice]` | VERIFIED |
| C-05 | :7 | 공개 코드는 현재 목록에서 고른 번호를 첫 목록에 적용 | PL raw_reference `contexts_list[0][choice]` | VERIFIED |
| C-06 | :7 | 기존 시험 결과를 확인한 뒤의 탐색적 분석 | PL observed_prior_test_results true, claim "not untouched confirmatory test"; AJ confirmatory False | VERIFIED |
| C-07 | :7 | CI = 출처·gold 공유 151그룹 대응 bootstrap | AJ cmp clusters 151; koblex_analysis.paired_bootstrap | VERIFIED |
| C-08 | :7 | 다중 비교 무보정 | AJ에 보정 필드 없음, 원 percentile CI 그대로 | VERIFIED |
| C-09 | :7 | 지연은 미리 고정한 60문항에서 별도 측정 | LP sample source = human_review_sample(CFG에 실험 전 고정) | VERIFIED |
| C-10 | :11 | 근거 평가 = 정확 문자열 집합, 문항 동일 가중 | AJ estimand "unweighted question mean"; prep README canonical hierarchy+content | VERIFIED |
| C-11 | :11 | 정답 외 근거의 법률적 타당성은 판정하지 않음 | HB human_judgments_created 0; human-review 360 판단 전부 null | VERIFIED |
| C-12 | :17 | EM·완전 회수 증가가 작고 CI가 0 포함 | AJ cmp[2],[3] | VERIFIED |
| C-13 | :19 | hop별 값은 관측 평균이며 검정 아님 | prep README "새로운 CI·검정 없음" | VERIFIED |
| C-14 | :19 | 미매핑 문항을 전체 분석에서 제외하지 않음 | AJ notes "missing gold remains in denominator"; questions 226 | VERIFIED |
| C-15 | :21 | 9.85점은 참조 수정 효과이며 Jev 효과와 구별 | PL arms(raw vs fixed는 참조 방식만 다름) | VERIFIED |
| C-16 | :21 | 원 논문 실제 실행의 문제 여부는 미확인 | 원 실행 로그 부재; 보충 S2 동일 서술 | VERIFIED |
| C-17 | :25 | shortlist 지표는 최종 선택 성능과 구별되는 후보 유지 수준 | SS stage 정의 | VERIFIED |
| C-18 | :31 | 후보 유지 개선이 최종 완전 회수로 다 이어지지 않음 | 112→130(+18) vs 77→79(+2); PF 104/120 | VERIFIED |
| C-19 | :31 | 하나만 선택하는 제약 반영 시 104/120으로 줄어듦 | PF union_complete_but_capacity_insufficient 8/10 | VERIFIED |
| C-20 | :34 | 문항 내 중복 제거 후 점수화 | LP duplicate_policy | VERIFIED |
| C-21 | :34 | 캐시 비활성 | LP cache false | VERIFIED |
| C-22 | :34 | 문항·방법 순서 무작위화 | LP order_seed; benchmark 스크립트 L144–147 shuffle | VERIFIED |
| C-23 | :34 | CE 로컬 MPS, Jev 원격 API | LP ce.device mps; jev.backend http | VERIFIED |
| C-24 | :34 | 분석 단위 = 문항별 3회 평균 | analyze_koblex_latency.py per_q mean | VERIFIED |
| C-25 | :44 | 품질과 지연은 별도 실행이며 동시 검증 아님 | AJ(226, 11-09 03:33) vs LS(60, 13:53) 별도 | VERIFIED |
| C-26 | :44 | 배포 조건 의존, 모델 고유 속도로 일반화 불가 | LS limits[1] | VERIFIED |
| C-27 | :44 | 예상 법령·BM25·LLM 선택·생성·모델 로드 제외 | LP excluded 5항목 | VERIFIED |
| C-28 | :46 | 기존 Jev 품질 수치는 저장된 실행의 값이며 재호출 시 같은 결과를 보장하지 않음 | LS Jev top10 1.11%, overlap 91.51% | VERIFIED |
| C-29 | :50 | Token F1 = 공백 단위 표현 중복 | koblex.py L116–118 (정규화 후 split) | VERIFIED |
| C-30 | :50 | LF-Eval = 정답·gold 기준 결론·누락·모순 평가 | research/prompts/koblex_lf_eval.json evaluation_steps | VERIFIED |
| C-31 | :50 | 모든 자동 지표가 유의하게 개선되었다고 해석하지 않음 | Token F1 p 0.0525 대 CI 하한 +0.02 불일치 | VERIFIED |
| C-32 | :52 | 늘어난 문맥은 선택 수 [감소]가 아닌 선택 내용 변화 때문 | DS 목록 수 차이 0, 문맥 +11.93 | MINOR_DISTORTION (IL-MINOR-2: "감소"→"증가") |
| C-33 | :52 | 입력량 절감은 관찰되지 않음 | DS context/api_input 모두 Jev가 더 큼 | VERIFIED |
| C-34 | :52 | 사용량 토큰은 재사용 응답을 포함하며 신규 청구액이 아님 | CSU 캐시 72/122행 포함 | VERIFIED |
| C-35 | :54 | 저장된 선택 근거에 문턱값을 적용한 오프라인 필터링 | FS filter_position post-selection, paid_calls 0 | VERIFIED |
| C-36 | :54 | 학습 fold 규칙으로 문턱값을 고르고 검증 fold에 적용 | FS rule.objective, chosen_tau_per_fold | VERIFIED |
| C-37 | :65 | F1 차이 CI만으로 동등성·비열등성을 입증하지 못함 | FS/E2E note "not a non-inferiority test" | VERIFIED |
| C-38 | :65 | 선택 전 필터링 값은 "pool별" 집계 | PRE 66.14 = 293/443, 72.69 = 322/443 (출현 단위 micro) | MINOR_DISTORTION (IL-MINOR-1) |
| C-39 | :65 | 그 분모는 그림 2의 문항별 평균 Recall과 다름 | 443 출현 대 226 문항 평균 | VERIFIED |
| C-40 | :67 | **필터링 후 답변은 재생성하지 않았다** | E2E: 재생성 CE 10/Jev 45, 226×2 예측·LF 완료 | **MAJOR_DISTORTION** (IL-SERIOUS-1) |
| C-41 | :67 | LF-Eval은 실제 제공 근거의 주장 지지를 직접 평가하지 않음 | LF rubric context = gold provisions | VERIFIED |
| C-42 | :67 | 0.61달러에 CE 장비·전력·후속 생성 비용 미포함 | LS limits[2]; cost = Jev 측정 반복만 | VERIFIED |
| C-43 | :71 | 출현을 최초 탈락 단계 또는 최종 선택 하나에만 배타 배정 | QS first_loss_counts 합 = n_gold | VERIFIED |
| C-44 | :71 | shortlist 탈락은 줄고 미선택은 늘어남 | DEN 42→13, 60→72 | VERIFIED |
| C-45 | :77 | 대표 사례 = 각 집단 F1 차이 절댓값 중앙값에 가장 가까운 문항 | RC selection_key abs_delta_F1, distance_to_median 0 ×3 | VERIFIED |
| C-46 | :77 | 사례 A: Jev가 식품위생법 42조2항 유지 + 45조1항 추가 확보 | CB Jev_only_canonical = 45조1항; 양쪽 42조2항 | VERIFIED |
| C-47 | :77 | 사례 B: gold 민사소송법 79조1항이 Jev shortlist에서 탈락, 83조1항 선택 | CB jev first_loss shortlist_absent 1; CE_only = 79조; Jev_only = 83조1항 | VERIFIED |
| C-48 | :79 | 사례 C: gold 하나는 corpus 미매핑, 하나는 BM25 미회수, Jev는 CE가 고른 나머지 gold(형법 40조)도 놓침 | CB labels corpus_absent/bm25_absent; jev shortlist_present_unselected; CE_only 형법 40조 | VERIFIED |
| C-49 | :79 | 표현 중복 증가가 더 나은 근거 선택을 보장하지 않음(반례 제시) | 사례 C Token F1↑·근거 F1↓ (단일 반례로 비보장 주장은 성립) | VERIFIED |
| C-50 | :79 | 사례는 자동 관측이며 법률적 판정이 아님 | RC legal_review_status NOT_REVIEWED | VERIFIED |
| C-51 | :79 | 사례 식별자·**원문**·선정 규칙이 보충 자료에 있음 | 보충 S4(ID·규칙)는 있으나 사례 원문 없음 | MINOR_DISTORTION (IL-MINOR-5) |
| C-52 | :50 | "Jev의 Token F1은 46.20점에서 47.31점으로" | 46.20은 CE 값(AJ) | MINOR_DISTORTION (IL-MINOR-3) |

보충 자료 의존 주장 대조:
- S4 사례 선정과 60문항 표본 밖 여부: HB existing_sample_ids에 세 사례 ID가 없다(qa_124_1hop_223은 다른 문항) → VERIFIED.
- S4 "실제 판단은 아직 없다": human-review/reviewer-A·B 각 180행, 판단 필드 전부 null, manifest status AWAITING_REAL_HUMANS → VERIFIED.
- S7 :101 "답변을 재생성하… 않았다" → 거짓(IL-SERIOUS-2).

### C. md ↔ tex 동기화 (C2)
`section4_1..5.tex`의 산문 19문단을 정규화(`\%`→%, `$\to$`→→, `$-$`→−, `\texttt{}`→백틱)한 뒤 `chapter4.md`와 문단 단위로 비교했다. 결과는 **완전 일치**(차이 0)다. 그림 캡션 3개와 표 캡션 2개도 글자 단위로 일치하고, 표 1·2의 12개·20개 셀 값도 일치한다. 수치 multiset 차이는 절 번호(4.1–4.5)와 `\label`·파일명 숫자뿐이다. 하드코딩된 그림/표 번호는 IL-MINOR-6이다.

### D. 완료 실험 반영 여부
| 결과 폴더 | 상태 | 본문 반영 |
|---|---|---|
| koblex-reproduction-v1 (3조건×226, LF 완료) | 완료 | 반영(4.1–4.2, 4.4) |
| chapter4-prep-v1 A1–A6 | 완료 | 반영(4.2–4.5) |
| koblex-latency-v1 (60×3×2) | 완료 | 반영(4.3, 표 1) |
| koblex-filtering-v1 오프라인 CV | 완료 | 반영(4.4, 표 2) |
| **koblex-filtering-v1/e2e (답변 재생성 + LF, 226×2)** | **완료** | **미반영, 그리고 "수행하지 않음"으로 잘못 서술** |
| human-review (180답변×2 검토자) | 미실시(판단 0) | "미수록"으로 정확히 서술(보충 S4/S8) |
| ce-diagnostic (30문항 입력 형식 진단) | 완료(탐색) | 미언급 — note N1 |
