# Academic Integrity Verification Report — 제4장 (실험 결과 및 분석), 재검증 라운드 2

## Verification Mode
Initial Verification (Mode 1, Stage 2.5 pre-review). 수정 라운드 1 이후의 재검증이다. 원고 전체를 처음부터 다시 검사했다(차분만 보지 않음).
- 일자: 2026-11-13. 검사자: `integrity_verification_agent` (ARS 3.24.2).
- 대상: `research/chapter4/chapter4.md`(주), `chapter4-supplement.md`, `section4_1..5.tex`, `figures/section-figures-v1/*.data.json`·`provenance.json`·`README.md`, `output/pdf/chapter4-final.pdf`, `tmp/pdfs/chapter4/authoring-build.log`·`chapter4-draft.aux`.
- 제약: 읽기 전용. 모델/API 호출, 실험, 외부 전송, 교차 모델 검증은 하지 않았다. JSON/CSV/JSONL은 일반 python으로 읽고 다시 계산했다.
- 근거로 인정한 자료: `results/koblex-reproduction-v1/`(analysis.json, protocol-lock.json, runtime-settings.json, ce-diagnostic-summary.json, chapter4-prep-v1/A1–A6), `results/koblex-latency-v1/`(protocol.json, summary.json, raw.jsonl, completed.json), `results/koblex-filtering-v1/`(summary.json, e2e-summary.json, e2e/, CSV, README.md), `configs/koblex-reproduction.yaml`. 이전 보고서, manuscript-facts.json, draft-validation.json은 맥락 참고용으로만 읽었고 근거로 쓰지 않았다.
- 보조 대조(근거 경로 확인용): `src/legal_rag_jev/koblex.py`, `koblex_lf_eval.py`, `research/prompts/koblex_lf_eval.json`(sha256이 e2e 서명의 rubric_sha256과 같음), `scripts/benchmark_koblex_latency.py`, `scripts/analyze_koblex_latency.py`, `chapter4-prep-v1/code/prepare_chapter4.py`, `research/koblex_source_audit_20261108.json`, 로컬 원문 `research/chapter4/style-study-v1/papers/2509.01324.txt`.

## Verdict
**FAIL**. SERIOUS 0, MEDIUM 2, MINOR 0, 비차단 Note 9.

- 원고 본문, 표, 캡션, 보충 자료의 수치 추적 행 126개(본문 95, 보충 31; 행마다 수치 1개 이상, 개별 수치 전체 포함)가 **모두 MATCH**다. MISMATCH 0, NOT_TRACEABLE 0.
- 등록한 주장 58건은 모두 VERIFIED다. MAJOR_DISTORTION 0, MINOR_DISTORTION 0, UNVERIFIABLE 0.
- 본문·보충·tex·PDF 텍스트에는 사람 평가 언급이 0건이다.
- FAIL의 원인은 원고 문장이 아니다. (1) 파이프라인 passport의 `experiment_provenance[]` 항목이 필수 키를 갖추지 않아 C4 check (0) MALFORMED에 해당한다. (2) 보충 자료가 링크하는 수치 원장 `manuscript-facts.json`이 갱신되지 않은 채 human review 문자열을 담고 있다.
- 두 항목만 고치면 원고 기준으로는 PASS WITH NOTES에 해당한다.

## Verification Summary

| Category | Total | Passed | Issues |
|----------|-------|--------|--------|
| Reference Existence | 1 | 1 (로컬 원문 PDF/텍스트로 확인) | 0 |
| Bibliographic Accuracy | 1 | 1 | 0 |
| Ghost Citations | -- | -- | 0 orphan / 0 dangling |
| Citation Context Accuracy | 1 (100%) | 1 | 0 |
| Statistical Data Accuracy | 126 행 | 126 | 0 |
| Internal Consistency | -- | Pass | 0 (Note 3: 반올림 표시 2건, 그림 2 축 라벨) |
| Originality Check (D1) | 0 (외부 전송 금지로 미실시) | -- | -- (NOT_SEARCHED, note) |
| Self-Plagiarism (D2) | 해당 없음(저자명 미제공) | -- | -- |
| Claim Verification (E) | 58 of 58 (Mode 1, 등록 주장 전수 검사 — #549 표본 추출 대신 100%; NOT-SELECTED 0; semantic extraction coverage: not_machine_detectable; candidate gaps: 0 수동 확인) | 58 | 0 |
| C3 Figure/Table Caption Fidelity | 그림 3 + 표 2 | 5 | 0 (ARS Figure Package 없음 → legacy note) |
| C4 Experiment Provenance | D7 1 + 실험 3 | D7 PASS | check (0) MALFORMED 3항목 → IL-MEDIUM-1 |
| 사용자 부정 제약(사람 평가 언급 금지) | 본문/보충/tex/PDF/그림 README/provenance | 0건 | 링크된 원장 3곳 → IL-MEDIUM-2 |
| LaTeX/PDF | 3쪽, `\ref` 5개 | 모두 해결 | Overfull 0, 미정의 0, Underfull 6 (note) |

## Phase D: Originality Verification Results

외부 WebSearch는 사용자 제약(외부 전송 금지)으로 실행하지 않았다. 모든 단락이 NOT_SEARCHED이며 이는 note다. 원고 수치와 문장이 이 저장소의 실험 산출물에서 직접 나왔다는 점은 C1/E로 확인했다.

| Grade | Paragraph Count | Proportion |
|-------|----------------|-----------|
| ORIGINAL | – | – |
| COMMON_KNOWLEDGE | – | – |
| PARAPHRASE | – | – |
| CLOSE_MATCH | – | – |
| VERBATIM | – | – |
| NOT_SEARCHED | 본문·보충 전 문단 | 100% |

## Phase E: Claim Verification Results

**Claim Registry coverage sidecar (#737)**
- Status: `not_run`. `scripts/claim_registry_coverage.py`를 실행할 schema-valid claim-registry/1.0 산출물이 없다. 이 라운드는 수동 등록표(아래 감사 기록 B)로 대체했다.
- Draft binding: `chapter4.md` 현재본(2026-11-13 16:45:29). 수정 라운드 1 렌더와 같은 시각이다.
- Candidate-unregistered count: 기계적으로 산출하지 않았다. 수동 대조에서는 수치·인용을 담은 문장이 모두 등록표 A/B에 포함됐다.
- Semantic extraction coverage: `not_machine_detectable`.
- `E1-COVERAGE-UNRESOLVED` (note): 기계적 커버리지 리포트가 없다. 원고 문장 전체(본문 산문 20문단과 보충 전 문단)를 수동으로 전수 대조했으므로 실질적인 누락 위험은 낮다고 본다.

| Verdict | Claim Count | Proportion |
|---------|------------|-----------|
| VERIFIED | 58 | 100% |
| MINOR_DISTORTION | 0 | 0% |
| MAJOR_DISTORTION | 0 | 0% |
| UNVERIFIABLE | 0 | 0% |
| UNVERIFIABLE_ACCESS | 0 | 0% |

**Persisted Phase E evidence rows (#656)**: `scripts/evidence_rows.py` 파이프라인을 쓰지 않았다(인용 기반 주장이 1건뿐이고, 나머지는 자체 실험 산출물과 대조함). 근거 경로와 키는 감사 기록 A·B에 행 단위로 적었다.

**Scope-conformance (#547) / Novelty (#548) / Cache staleness (#541)**: 해당 행 없음. 원고는 신규성 주장을 하지 않는다.

**Claim-strength drift (#569, revision round)**: 라운드 1 대비 강도를 비교했다.

| ID | Round | Claim location | Prior → current | Direction |
|----|-------|----------------|-----------------|-----------|
| E6-1 | 1→2 | `chapter4.md:67`, 보충 `:101,:103` | "필터링 후 답변은 재생성하지 않았다"(거짓) → E2E 재생성 결과를 CI와 함께 보고하고, 비열등성 마진이 없으므로 유지·동등성으로 해석하지 않는다고 명시 | 약화·정정(정확도 상승). 과장 방향 drift 없음 |
| E6-2 | 1→2 | `chapter4.md:69` | "재생성하지 않았으므로 … 비용 절감으로 해석하지 않았다" → "비용·지연 변화는 측정하지 않았다" | 동일 강도. 비용 절감 주장 없음 |

두 행 모두 저자 처분이 필요 없는 정정 방향이다.

### C3 Figure/Table Caption Fidelity
ARS visualization_agent의 Figure Package(`figure_table_trace[]`)는 없다. 대신 프로젝트 고유의 `provenance.json`(source sha256, builder sha256, 출력 sha256)이 있으므로 legacy 경로로 판정했다(PASS WITH NOTES 사유).

| 산출물 | source_data / 변환 | 캡션 주장 판정 | 원고 연결(정·역방향) | 판정 |
|---|---|---|---|---|
| 그림 1 `fig_4_2_evidence_effects_column` | `fig_4_2_evidence_effects.data.json`(sha256 7f8e41e1…, provenance와 일치) ← analysis.json comparisons[0..3] ×100. builder `build_manuscript_figures.py` sha256 8b89fb47… 일치 | "EM·완전 회수율 차이는 %p, 나머지는 점": data.json 4지표가 F1/recall(점)과 em/coverage(문항 비율)로 맞다. PNG 확인 결과 EM·Complete coverage 막대가 0을 가로지르고, F1·Recall은 0 위에 있다 | `:17` "(그림 1)" F1/Recall CI 수치 일치. "두 차이의 CI는 0을 포함" 일치 | PASS |
| 그림 2 `fig_4_3_shortlist_quality_column` | `fig_4_3_shortlist_quality.data.json`(128e0ee0… 일치) ← A4/stage-summary.csv shortlist 행(5581f4ac… 일치) | 226문항, Recall은 문항별 평균, 모든 gold 포함률은 문항 비율, 오차막대 없음: data.json n=226, CI 필드 없음. PNG 값 69.47/74.63/49.56/57.52 | `:25` 수치 일치 | PASS. Note: y축 라벨 "Shortlist quality (%)"는 4.1 규약상 Recall(점)과 다르지만 캡션이 이를 밝힌다 |
| 그림 3 `fig_4_5_gold_loss_stages_column` | `fig_4_5_gold_loss_stages.data.json`(d7341564… 일치) ← stage-summary 단계 생존 수의 차분(443−410=33, 410−335=75, 335−293/322=42/13, 293/322−233/250=60/72) = A4/denominators.json first_loss_counts | "443건의 배타적 단계 분류, 미선택은 목록별 선택 수 제약의 영향도 받음": 합계 443, pool capacity 1 규칙(A4/pool-feasibility-summary.json) | `:65`, `:73` 일치 | PASS |
| 표 1 (지연) | latency summary.json per_question_ms. raw.jsonl로 재계산 일치 | 60문항, 초, 3회 평균 분포 | `:44` 일치 | PASS (trace-unavailable note) |
| 표 2 (필터링) | summary.json cv_overall + e2e-summary.json means | 검증 fold 통합, 226문항, P·R 정의 | `:65`, `:67` 일치 | PASS (trace-unavailable note) |

`_column` 출력 9개 파일(pdf/png/svg ×3)과 입력 data.json 3개, builder의 sha256을 모두 `shasum -a 256`으로 계산했다. 결과가 `provenance.json.manuscript_column_figures`와 **12/12 일치**한다. provenance의 원천 해시(analysis.json 7609288f…, protocol-lock.json 99d5c5cc…, stage-summary.csv 5581f4ac…, descriptive-statistics.csv 45fb58d6…)도 현재 파일과 일치한다.

### C4 Experiment Provenance & Claim Alignment
"This check verifies disclosure and claim-to-provenance fidelity. It does not judge whether the experiment was correctly designed, run, statistically adequate, or reproducible by ARS."

- **D7 (declaration-anchored anti-skip): PASS.** `pipeline_state.md` §experiment_intake_declaration에 사용자 확인 선언이 있다(2026-11-13, declared_by = 사용자, 실질 status = experiments_declared). 실험 3건(주 실험, 지연, 필터링+E2E)과 근거 경로가 적혀 있다. repro_lock.ars_version 증명이 없으므로 post-#260으로 취급하지만, 선언이 있으므로 조건 1은 해당하지 않는다. 조건 2·3·5도 해당하지 않는다(provenance 목록이 비어 있지 않음). 조건 4: 원고가 보고한 자체 실험은 모두 선언된 3건 안에 있다. CE 입력 형식 진단(30문항)은 `results/koblex-reproduction-v1/` 안의 주 실험 부속 절차로 본다.
- **check (0) entry well-formedness: MALFORMED (3/3 항목).** 선언 표의 항목에는 experiment_id/title/근거 경로/상태만 있고, 필수 키 `repro_lock`(또는 null + repro_lock_reason), `planned_vs_executed`, `negative_results`, `known_limitations`가 없다. 역할 정의상 MALFORMED 항목은 check (1)–(4)를 건너뛰고 FAIL이다 → **IL-MEDIUM-1**(라운드 1 IL-MEDIUM-1이 부분 해소된 상태).
- **참고용 수동 정렬**(형식 판정을 대체하지 않음): 결과 폴더를 직접 대조했다. 아래 EA 행의 실질 정렬은 모두 ALIGNED이고, 표본 비율은 실험 근거 주장 38건 중 14건(37%, 30% 이상)이다.

| finding_id | claim (요지) | experiment_id | result_pointer | manuscript_locator | 실질 판정 |
|---|---|---|---|---|---|
| EA-001 | Jev F1 61.75 vs CE 58.57, +3.19 [+0.75,+5.68] | main | analysis.json comparisons[0] | §4.2 :11,:17 | ALIGNED |
| EA-002 | EM·완전회수 CI가 0을 포함 | main | comparisons[2],[3].ci95 | §4.2 :17 | ALIGNED (negative result 공개됨) |
| EA-003 | 공개 코드 CE 48.72, 수정 효과 9.85 | main | summaries.parser_ce_raw; comparisons[6] | §4.2 :21 | ALIGNED |
| EA-004 | shortlist Recall 69.47→74.63, 112→130 | main | A4/stage-summary.csv | §4.3 :25 | ALIGNED |
| EA-005 | 지연 5.01 vs 10.65초, +5.64 [+5.15,+6.17] | latency | summary.json per_question_ms, jev_minus_ce_ms | §4.3 :44, 표 1 | ALIGNED |
| EA-006 | top-10 재현 CE 180/180, Jev 2/180, 겹침 91.51% | latency | summary.json repeatability; raw.jsonl | §4.3 :46 | ALIGNED (negative result 공개됨) |
| EA-007 | Token F1 CI [+0.02,+2.27], p≈0.0525, 모든 지표 유의로 해석 안 함 | main | comparisons[4] | §4.4 :50 | ALIGNED |
| EA-008 | 입력량 절감 없음 | main | A5/descriptive-statistics.csv | §4.4 :52 | ALIGNED |
| EA-009 | 필터링 τ를 답변 전에 고정, 재생성 CE 10·Jev 45 | filtering | e2e-summary.json checks; e2e/predictions answer_source | §4.4 :54 | ALIGNED |
| EA-010 | 표 2 8×6 셀 | filtering | summary.json cv_overall; e2e-summary.json means | 표 2 | ALIGNED |
| EA-011 | Jev+FR Token −0.28 [−1.10,+0.44], LF −1.02 [−2.23,+0.15] | filtering | e2e-summary.json paired_bootstrap_points["jev_fr-jev_r"] | §4.4 :67 | ALIGNED |
| EA-012 | CE+FR Token F1 감소 구간은 0을 포함하지 않음 | filtering | ["ce_fr-ce_r"].token_f1.ci95 = [−1.186, −0.067] | §4.4 :67 | ALIGNED |
| EA-013 | 비열등성 마진 없음 → 유지·동등성으로 해석 안 함 | filtering | e2e-summary note "not a non-inferiority test" | §4.4 :67 | ALIGNED |
| EA-014 | 443건 단계 분류 33/75/42→13/60→72/233→250 | main | A4/denominators.json first_loss_counts | §4.5 :73, 그림 3 | ALIGNED |

check (4) 공개 여부(참고): 주요 negative result는 모두 원고에 나온다. EM/완전회수 CI가 0을 포함한다는 점, Jev top-10 재현율 1.11%, E2E LF 하한 −2.23, CE+FR Token F1 감소, 입력량 절감 없음, 지연 2.25배가 그것이다. 원고에 없는 것은 e2e의 `jev_fr-jev_r.gold_set_coverage` −1.77 [−3.51, −0.43](0을 포함하지 않음)과 Recall CI [−3.81, −1.16]이다. Recall 감소 자체(−2.43)는 원고에 있고, 원고가 유지·동등성 해석을 명시적으로 배제하므로 과장은 없다(Note N6).

## Issue List (Sorted by Severity)

### SERIOUS (Must Fix)
| ID | # | Category | Location | Issue Description | Correct Information | Source |
|----|---|----------|----------|------------------|--------------------|----|
| — | — | — | — | 해당 없음 | — | — |

### MEDIUM (Must Fix)
| ID | # | Category | Location | Issue Description | Correct Information | Source |
|----|---|----------|----------|------------------|--------------------|----|
| IL-MEDIUM-1 | 1 | C4 check (0) MALFORMED (파이프라인 산출물, 원고 문장 아님). 라운드 1 IL-MEDIUM-1이 부분 해소됨 | `research/chapter4/pipeline/pipeline_state.md:7–15` | 선언은 생겨서 D7은 통과한다. 그러나 실험 3건의 provenance 항목에 `repro_lock`, `planned_vs_executed`, `negative_results`, `known_limitations` 키가 없다. 역할 정의상 MALFORMED 항목은 FAIL이다 | 각 실험에 4개 키를 추가한다. 예: **main** — repro_lock: `results/koblex-reproduction-v1/protocol-lock.json`(sha256 99d5c5cc…, seed 20261108, k=100, top_n=10, gpt-4o-2024-08-06, jev-1.14.0, dragonkue/bge-reranker-v2-m3-ko@2aca5884…); planned_vs_executed: 3조건×226 executed:true; negative_results: EM CI [−1.77,+5.19], 완전회수 CI [−2.90,+4.53], 1-hop F1 −1.17; known_limitations: 기존 시험 결과 관찰 후 탐색 분석, 정확 문자열 지표, 27개 gold 미매핑. **latency** — repro_lock: `results/koblex-latency-v1/protocol.json`(order_seed 20261109, warmup 3, reps 3, MPS/float32/batch 50, concurrency 4); negative_results: Jev 지연 2.25배, top-10 재현 2/180; known_limitations: 배포 조건 비교, scorer-only, 60문항. **filtering+E2E** — repro_lock: summary.json rule(5-fold, cv_seed 20261109, 허용 1점, 20 분위수 격자) + e2e-summary(bootstrap seed 20261108, 10,000회); planned_vs_executed: CV 시뮬레이션·E2E 재생성(CE 10/Jev 45)·LF 평가 executed:true; negative_results: Jev LF −1.02 [−2.23,+0.15], CE Token F1 −0.54 [−1.19,−0.07], Jev 완전회수 −1.77 [−3.51,−0.43]; known_limitations: 비열등성 마진 없음, 같은 226문항 안의 CV | ARS `integrity_verification_agent.md` §C4 (0) |
| IL-MEDIUM-2 | 2 | 사용자 부정 제약 노출 경로 + 링크 자료 stale (보충 자료가 링크한 원장) | `chapter4-supplement.md:51` → `research/chapter4/manuscript-facts.json:34, :392, :398` | 보충 자료 본문은 깨끗하다(사람 평가 언급 0건). 그러나 `:51`이 "기존 수치와 사례별 평가값의 출처는 [수치 원장](manuscript-facts.json)"이라며 링크한 원장에 `"…/A6/human-review-boundary.json"`, `"new_human_judgments": 0`, `"excluded": ["unperformed human review"]`가 남아 있다. 이 원장은 2026-11-09 23:03 이후 갱신되지 않았다. 그래서 (a) E2E 필터링 답변 수치(표 2의 Token F1·LF-Eval, :67)가 없고, (b) 절 키가 옛 구조다(`"4.3": hop` — 현재 hop은 4.2에 있음). 제약 대상인 본문·보충 텍스트 자체는 깨끗하므로 SERIOUS가 아닌 MEDIUM으로 분류했다. 다만 보충 자료와 함께 배포되면 독자에게 그대로 노출된다 | 둘 중 하나: (1) `:51`의 링크를 지우고 출처를 `results/…` 원자료 경로로만 적는다. (2) 원장을 다시 생성해 human 관련 키 3곳을 지우고, E2E 출처(`e2e-summary.json` sha256)와 현재 절 구조를 반영한다. `results/` 쪽 원자료(`A6/human-review-boundary.json`, casebook의 `in_existing_human_sample` 필드)는 수정 금지 범위이므로 그대로 두되, 원고가 그 파일이나 필드를 가리키지 않게 한다(현재도 가리키지 않음) | `grep` 결과; `stat` 결과 manuscript-facts.json mtime 2026-11-09 23:03:53 |

### MINOR (Recommended Fix at Stage 2.5; Must Fix at Stage 4.5)
| ID | # | Category | Location | Issue Description | Suggestion |
|----|---|----------|----------|------------------|----|
| — | — | — | — | 해당 없음 | — |

### Notes (비차단, 이슈 수에 미포함)
| ID | 위치 | 내용 |
|---|---|---|
| N1 | `chapter4.md:11` | "3.19점 높았다"는 반올림 전 차이(3.1879)와 맞다. 표시값으로 빼면 61.75−58.57 = 3.18이 된다. 오류는 아니며, 원하면 "반올림 전 값으로 계산"이라는 각주를 4.1에 한 줄 넣을 수 있다 |
| N2 | `chapter4.md:67` | "CE+필터링 … Token F1 −0.54점"은 반올림 전 −0.5414와 맞다. 표 2 표시값으로 빼면 45.65−46.20 = −0.55다. N1과 같은 성격이다 |
| N3 | 그림 2 (PNG/PDF) | y축 라벨이 "Shortlist quality (%)"다. 4.1 규약에서 Recall은 '점'이다. 캡션이 "Recall은 문항별 평균(점) … 같은 0–100 축"이라고 밝히므로 허용 범위다. 그림을 다시 만들 일이 생기면 "(0–100)"으로 바꾸기를 권한다 |
| N4 | 보충 `:114`, 본문 `:7` | 60문항 표본은 "미리 고정한" 것으로만 서술되어 있다. 원천(`research/koblex_source_audit_20261108.json`)상 seed 20261108의 hop 비례 층화 무작위 표본(15/34/11)이다. 사람 평가를 언급하지 않고 "hop별 층화 무작위(seed 20261108)"라고 쓰면 재현 정보가 완전해진다. 원천 summary.json limits의 "pre-registered" 표현과 보충의 "사전등록을 뜻하지 않는다"는 보수적 해명이므로 유지한다(라운드 1 N2) |
| N5 | 보충 `:49` | 링크한 `A6/casebook.jsonl` 행에는 원고가 지목한 필드 외에 `in_existing_human_sample`, `lf_judge_reason_unverified` 필드가 있다. 수정 금지 원자료이고 원고는 해당 필드를 언급하지 않으므로 note로만 기록한다 |
| N6 | `chapter4.md:65–67` | e2e에서 Jev+필터링의 Recall 감소 CI [−3.81, −1.16]과 완전회수 감소 −1.77 CI [−3.51, −0.43]은 0을 포함하지 않는다. 원고는 Recall 점추정(−2.43)만 보고하고 유지·동등성 해석을 배제하므로 과장은 아니다. 다만 "Recall 감소의 구간은 0을 포함하지 않았다"를 덧붙이면 CE Token F1 서술과 대칭이 맞는다 |
| N7 | `chapter4.md:44` | "따라서 관측된 후보 유지 수준의 개선과 함께 지연 증가가 확인되었다"의 "따라서"는 논리 접속이 약하다(지연 수치에서 품질 개선이 따라 나오지 않음). 바로 다음 문장이 별도 실행임을 밝히므로 왜곡은 아니다. "즉" 또는 "요약하면"을 권한다 |
| N8 | `tmp/pdfs/chapter4/authoring-build.log` | Underfull \hbox 6건(4.1 첫 문단 5건: 줄바꿈되지 않는 `\texttt` 모델 ID; 4.4 :31 1건). Overfull 0, 미정의 참조 0, "Rerun" 경고 없음. 시각적 문제 없음 |
| N9 | 전반 | ARS Figure Package/claim-registry/evidence_rows 산출물이 없어 C3는 legacy 경로, E1.1은 `not_run`으로 처리했다(수동 전수 대조로 보완). Phase D는 외부 전송 금지로 NOT_SEARCHED |

## 라운드 1 이슈 해소 여부

| 라운드 1 ID | 현재 상태 | 확인 근거 |
|---|---|---|
| IL-SERIOUS-1 (본문 "재생성하지 않았다" 허위·E2E 누락) | **해소** | `chapter4.md:54`(절차), 표 2의 Token F1·LF-Eval 열, `:67`(4개 대비의 점추정·CI) 모두 e2e-summary.json과 일치한다. "재생성하지" 문구 0건(grep). `:69`는 "비용·지연 변화는 측정하지 않았다"로 바뀌었다 |
| IL-SERIOUS-2 (보충 S7 허위·범위 과대) | **해소** | S7 제목 `:95`, `:101`(gold 출현 기준, 293/443·322/443), `:103`(E2E 출처, seed 20261108, 151그룹, 빈 문맥 생성 — e2e/predictions에서 CE 1·Jev 4건 모두 `regenerated` 확인), `:107` 수록 범위 |
| IL-MEDIUM-1 (C4-D7 선언 부재) | **부분 해소 → IL-MEDIUM-1(라운드 2)로 이월** | 선언은 생겨 D7 PASS. provenance 항목의 필수 키가 없어 check (0) MALFORMED |
| 사람 평가 언급 삭제(사용자 지시) | **원고 텍스트는 해소, 링크 원장은 미해소 → IL-MEDIUM-2** | 본문·보충·section tex·PDF 텍스트·그림 README·provenance.json에서 사람/평가자/블라인드/전문가/human/expert/review(“preview.tex” 제외)는 0건. `manuscript-facts.json`에 3건 남음 |
| IL-MINOR-1 (pool별 라벨) | **해소** | `:65` "문항별 gold 출현 443건 기준 유지 비율", 그림 3과 분모가 같다고 명시. 66.14 = 293/443, 72.69 = 322/443 (stage-summary.csv) |
| IL-MINOR-2 ("선택 수 감소") | **해소** | `:52` "선택 수의 차이가 아닌" |
| IL-MINOR-3 (Token F1 주어) | **해소** | `:50` "Token F1은 CE 46.20점에서 Jev 47.31점으로" |
| IL-MINOR-4 (단위 혼용) | **해소** | `:7`에 규약을 정의했다. `:11,:17,:25,:65,:67`, 보충 `:11,:86,:90`이 모두 규약을 따른다(문항 평균 = 점, 문항 비율 = %·%p). 남은 것은 그림 2 축 라벨뿐이다(N3, 캡션으로 해명) |
| IL-MINOR-5 (사례 원문 과대) | **해소** | `:81` "원문의 위치", 보충 `:49`가 casebook의 해당 필드를 지목하며 필드가 실재한다 |
| IL-MINOR-6 (LaTeX 하드코딩) | **해소** | section tex 본문 참조 5곳이 모두 `그림~\ref{}`/`표~\ref{}`. aux: fig:ch4_2 → 1, fig:ch4_3 → 2, fig:ch4_5 → 3, tab:ch4_3 → 1, tab:ch4_4 → 2. md 번호와 일치하고 PDF 텍스트에 "??" 0건. 조사도 맞다("그림 3과", "그림 2의"). 통합 논문에서 번호가 바뀌면 조사가 어긋날 수 있다(예: "그림 5과"). 통합 시 재확인할 것 |
| IL-MINOR-7 (provenance 불완전·stale) | **해소** | `manuscript_column_figures` 해시 12/12 일치. fig_4_3 캡션과 README의 stale 문구가 갱신됨(README :49 "지연은 완료되었으며 … 표 1") |
| IL-MINOR-8 (CE ID 축약) | **해소** | 본문 `:5`, 보충 `:9`에 `dragonkue/bge-reranker-v2-m3-ko`. protocol-lock signature.ce.model과 일치 |
| N1 (CE 입력 형식 진단 공개) | 반영 확인 | ce-diagnostic-summary.json: 30문항, 4변형, "not a new held-out test". 진단 파일(10:56)이 protocol-lock(10:58)보다 먼저 생성되어 "진단을 거쳐 정하였다"는 시간 순서와 맞다 |
| N2 (사전등록 표현) | 유지 확인 | N4 참조 |

## AI Research Failure Mode Checklist

| Mode | Outcome | Evidence | Blocks? |
|------|---------|----------|---------|
| 1. Implementation bug passing AI self-review | CLEAR | 핵심 수치를 원 로그에서 다시 계산했다. raw.jsonl 360행(warmup 6 제외)의 문항 평균·중앙값·p95·top10 일치·비용 0.6100542, e2e LF metrics.jsonl 평균 67.127/69.128, e2e/predictions의 answer_source 개수 216/10·181/45와 유지 근거 467/426이 요약 파일과 정확히 일치한다. 공개 코드의 목록 참조 버그는 원고가 "재현 참조"로 분리해 공개한다. CI는 조건마다 다르게 나타난다(동일 CI 반복 없음) | no |
| 2. Hallucinated citation | CLEAR | 참고문헌 1건(Lee et al., 2025, arXiv:2509.01324)을 로컬 원문 PDF/텍스트(`style-study-v1/papers/2509.01324.txt`, 매니페스트 pdf_sha256 167f2025…)로 확인했다. 제목, 저자 5명과 순서, 연도(v1 2025-09-01), 226문항, PARSER, LF-EVAL 모두 일치하고 인용 문맥도 맞다. 외부 검색은 하지 않았다(제약) | no |
| 3. Hallucinated experimental result | CLEAR | 수치 추적 126행이 모두 원자료로 추적된다. NOT_TRACEABLE 0. 실험 3건 모두 완료 산출물(completed.json, LF COMPLETE ×3, e2e 226×2)이 있다 | no |
| 4. Shortcut reliance | CLEAR (flag-only 대상) | 주장 범위가 정확 문자열 지표의 일치 수준으로 한정된다(`:11`, 보충 `:86`). 공개 코드 버그 효과(9.85)를 모델 교체 효과와 분리했다. 지연은 배포 조건 비교임을 명시했다. 27개 미매핑 gold의 영향은 197/29문항으로 나눠 보고했다 | no |
| 5. Bug reframed as novel insight | CLEAR | "놀랍게도"류 서술이 없다. 의외의 결과(Jev top-10 재현 1.11%)를 통찰로 포장하지 않고 재현성 한계로 기술했다(`:46`) | no |
| 6. Methodology fabrication | CLEAR (라운드 1 SUSPECTED → 해소) | 방법 수치를 모두 config/protocol과 대조했다: K=100, top-10, pool당 1개 선택, 151그룹, 10,000회, seed 20261108/20261109, MPS·float32·batch 50, concurrency 4, warmup 3, 3회 반복, 무작위 순서, 순차 실행(benchmark 스크립트 L16·L145–148), 800자 clip, LF rubric(contradict/omit/expected output, sha256 95bf7c61… 일치), 공백 단위 Token F1(koblex.py L116–118), o200k_base 줄바꿈 연결(prepare_chapter4.py L150), 5-fold, 20 분위수 격자, 1점 허용, 답변 전 τ 고정, 변경 문항만 재생성, 빈 문맥 생성. "하지 않았다"류 진술 7개(다중비교 보정, 비용·지연 측정, 서비스 비용, 법률 판정, LLM 재선택 등)도 원자료와 모순되지 않는다 | no |
| 7. Frame-lock at early stage | CLEAR | 원고 전반에 탐색적 성격(기존 시험 결과 확인 후 분석)과 해석 한계를 일관되게 밝히고, 비열등성·동등성·비용 절감 주장을 하지 않는다. 사후 판단 표현이 없다 | no |

## Tool Limitation Disclaimer

> 이 보고서의 독창성 검사(Phase D)는 사용자 제약(외부 전송 금지) 때문에 실행하지 않았다(NOT_SEARCHED). 참고문헌 검증은 저장소에 보관된 원문 사본으로 했으며 Semantic Scholar/WebSearch를 쓰지 않았다. 제출 전 전문 표절 검사 도구(Turnitin/iThenticate) 사용을 권한다. Phase E 등록표는 모델이 매개한 수동 추출이며 의미적 추출 완전성은 기계적으로 증명할 수 없다.

## Verification Audit Trail

경로 약어: **AJ** = `results/koblex-reproduction-v1/analysis.json`(cmp[i] = comparisons[i]); **PL** = `…/protocol-lock.json`; **CFG** = `configs/koblex-reproduction.yaml`; **SS** = `…/chapter4-prep-v1/A4/stage-summary.csv`; **DEN** = `…/A4/denominators.json`; **PF** = `…/A4/pool-feasibility-summary.json`; **QS** = `…/A4/question-stages.jsonl`; **WTL** = `…/A3/win-tie-loss.json`; **DS** = `…/A5/descriptive-statistics.csv`; **CU** = `…/A5/cache-separated-usage.csv`; **CB** = `…/A6/casebook.jsonl`; **PC** = `…/A6/proposed-three-candidates.json`; **CD** = `…/ce-diagnostic-summary.json`; **LP/LS/LR** = `results/koblex-latency-v1/protocol.json`/`summary.json`/`raw.jsonl`; **FS** = `results/koblex-filtering-v1/summary.json`; **E2E** = `…/e2e-summary.json`(PB = paired_bootstrap_points); **PMK/PRE** = `post_matched_keep_rate.csv`/`pre_matched_keep_rate.csv`; **EP** = `…/e2e/predictions/*.jsonl`. "재계산" = python으로 원자료에서 직접 계산한 값.

### A. 수치 추적 (C1/C2) — 본문·표·캡션

| ID | 위치 | 원고 수치 | 출처·키 | 원값 → 재계산 | 판정 |
|---|---|---|---|---|---|
| N-001 | :5 | 226문항 | AJ summaries.*.questions | 226 | MATCH |
| N-002 | :5 | dragonkue/bge-reranker-v2-m3-ko | PL signature.ce.model | 동일 | MATCH |
| N-003 | :5 | jev-1.14.0 | PL signature.jev.model | 동일 | MATCH |
| N-004 | :5 | gpt-4o-2024-08-06 (선택·생성·평가) | PL generation.model; e2e lf manifest model | 동일 | MATCH |
| N-005 | :5 | 후보 100개 | CFG top_k; PL retriever k=100 | 100 | MATCH |
| N-006 | :5 | 상위 10개, 하나 선택 | CFG top_n; PF rule "pool capacity 1" | 10 / 1 | MATCH |
| N-007 | :5 | 478개 후보 목록 | DS selected_list_count sum | 478 | MATCH |
| N-008 | :5 | 시험 문항 30개, 네 가지 형식 | CD questions, variants | 30 / 4 | MATCH |
| N-009 | :7 | 세 조건 각 226 답변·평가 | AJ lf_eval_status COMPLETE ×3 | 226×3 | MATCH |
| N-010 | :7 | 95% CI, 151그룹, 10,000회 | AJ cmp[*].clusters/repetitions | 151 / 10000 | MATCH |
| N-011 | :7 | 60문항, 15/34/11 | LP sample; LR 비워밍업 qid hop 집계 | 60; 15/34/11 | MATCH |
| N-012 | :7 | 52개 의존 그룹 | LS jev_minus_ce_ms.clusters | 52 | MATCH |
| N-013 | :11 | F1 61.75 / 58.57 | AJ jev/ce_fixed.retrieval.f1 | 0.61753 / 0.58565 | MATCH |
| N-014 | :11 | 3.19점 | AJ cmp[0].mean_difference | 0.031879 → 3.19 (표시값 차 3.18, N1) | MATCH |
| N-015 | :11 | P 63.46→66.85 | AJ *.precision | 0.63459 / 0.66851 | MATCH |
| N-016 | :11 | R 57.74→60.69 | AJ *.recall | 0.57743 / 0.60693 | MATCH |
| N-017 | 그림1 캡션 | %p vs 점 구분 | fig_4_2 data.json 4지표 | f1/recall/em/coverage | MATCH |
| N-018 | :17 | F1 CI [+0.75, +5.68] | AJ cmp[0].ci95 | [0.7469, 5.6762] | MATCH |
| N-019 | :17 | Recall CI [+0.39, +5.51] | AJ cmp[1].ci95 | [0.3912, 5.5067] | MATCH |
| N-020 | :17 | EM 27.88→29.65% | AJ *.em | 0.27876 / 0.29646 | MATCH |
| N-021 | :17 | 완전회수 34.07→34.96% | AJ *.gold_set_coverage | 0.34071 / 0.34956 | MATCH |
| N-022 | :17 | 두 CI가 0 포함 | AJ cmp[2] [−1.77,+5.19], cmp[3] [−2.90,+4.53] | 0 포함 | MATCH |
| N-023 | :17 | 77→79개 | SS final all_gold_questions | 77 / 79 | MATCH |
| N-024 | :19 | 32/177/17 | WTL counts.f1 | 32/177/17 (합 226) | MATCH |
| N-025 | :19 | 1-hop 78.07→76.90 | AJ by_hop.1.f1 | 0.78070 / 0.76901 | MATCH |
| N-026 | :19 | 2-hop 53.33→57.24 | AJ by_hop.2.f1 | 0.53333 / 0.57244 | MATCH |
| N-027 | :19 | 3-hop 47.91→54.83 | AJ by_hop.3.f1 | 0.47914 / 0.54830 | MATCH |
| N-028 | :19 | 3-hop 완전회수 1/42 | AJ by_hop.3.gold_set_coverage ×2 | 0.0238×42 = 1 | MATCH |
| N-029 | :19 | 386 / 27 / 29문항 | DEN unique_gold_global, unmapped; AJ unavailable_gold_affected.questions | 386/27/29 | MATCH |
| N-030 | :19 | 197문항 64.12→67.21 | AJ fully_mapped.f1 | 0.64124 / 0.67206 | MATCH |
| N-031 | :19 | 29문항 20.80→24.71 | AJ unavailable_gold_affected.f1 | 0.20805 / 0.24713 | MATCH |
| N-032 | :21 | 48.72 | AJ parser_ce_raw.f1 | 0.48717 | MATCH |
| N-033 | :21 | 9.85 | AJ cmp[6].mean_difference | 0.09848 (표시값 차 9.85) | MATCH |
| N-034 | :25 | BM25 Recall 77.21점 | SS bm25 macro | 0.77212 | MATCH |
| N-035 | :25 | 69.47 / 74.63, +5.16 | SS shortlist macro | 0.69469 / 0.74631; 차 5.162 | MATCH |
| N-036 | :25 | 112(49.56%) → 130(57.52%) | SS shortlist all_gold | 112/226 = 49.558; 130/226 = 57.522 | MATCH |
| N-037 | 그림2 캡션 | 226문항, 오차막대 없음 | fig_4_3 data.json n, CI 필드 없음 | 226 | MATCH |
| N-038 | :31 | 동시 선택 가능 104 / 120 | PF shortlist all_gold_jointly_selectable | 104 / 120 | MATCH |
| N-039 | :31 | 실제 77 / 79 | SS final | 77 / 79 | MATCH |
| N-040 | :34 | 워밍업 3, 3회, float32, 배치 50, 동시 4 | LP | 3/3/float32/50/4 | MATCH |
| N-041 | :34 | 360개 본 측정, 실패·재시도 0 | LR 재계산 warmup=false 180+180, status 전부 ok, Σretries 0; LS failed 0/0 | 360; 0; 0 | MATCH |
| N-042 | 표1 | CE 5.01/4.82/8.87 | LS per_question_ms.ce; LR 재계산 | 5008.97/4816.85/8870.05 ms | MATCH |
| N-043 | 표1 | Jev 10.65/10.79/16.53 | LS jev; LR 재계산 | 10649.73/10794.56/16527.20 ms | MATCH |
| N-044 | :44 | +5.64초, CI [+5.15, +6.17] | LS jev_minus_ce_ms | 5640.76; [5148.5, 6165.9] | MATCH |
| N-045 | :44 | 2.25배 [2.11, 2.39] | LS geometric ratio | 2.2523 [2.1056, 2.3948] | MATCH |
| N-046 | :46 | CE 100% 180/180, Jev 1.11% 2/180 | LR 재계산 Σtop10_same | 180; 2 (2/180 = 1.111%) | MATCH |
| N-047 | :46 | 91.51% | LR 재계산 mean(top10_set_overlap) | 0.915093 | MATCH |
| N-048 | :50 | Token F1 46.20→47.31 | AJ *.token_f1 | 0.46195 / 0.47313 | MATCH |
| N-049 | :50 | LF 67.57→70.15 | AJ *.lf_eval | 0.67571 / 0.70153 | MATCH |
| N-050 | :50 | CI [+0.02, +2.27] / [+0.37, +4.79] | AJ cmp[4], cmp[5] | [0.0179, 2.2737] / [0.3746, 4.7916] | MATCH |
| N-051 | :50 | 앞 800자 | AJ compatibility_answer_clip_chars; koblex_lf_eval.py L120 | 800 | MATCH |
| N-052 | :50 | p ≈ 0.0525 | AJ cmp[4].p_centered_bootstrap_two_sided | 0.052495 | MATCH |
| N-053 | :52 | 문맥 203.67→215.60 | DS context_tokens mean | 203.668 / 215.597 | MATCH |
| N-054 | :52 | API 입력 2302.67→2314.58 | DS api_input_tokens mean | 2302.668 / 2314.584 | MATCH |
| N-055 | :52 | 출력 72.16 / 73.98 | DS api_output_tokens mean | 72.159 / 73.978 | MATCH |
| N-056 | :52 | 중앙값 164 / 170.5, 차 중앙값 0 | DS context_tokens median; paired median | 164 / 170.5 / 0 | MATCH |
| N-057 | :52 | 478 / 478 | DS selected_list_count sum; paired diff 0 | 478/478 | MATCH |
| N-058 | :54 | 151그룹 5-fold, 1점 이내 | FS rule.folds, tolerance_f1_points | 5 / 1.0 | MATCH |
| N-059 | :54 | 동일 크기 분위수 격자 | FS rule.cv_grid (20 keep rates per scorer) | 20 | MATCH |
| N-060 | :54 | 재생성 CE 10, Jev 45 | E2E checks.*.regenerated; EP answer_source 재계산 | 10 / 45 | MATCH |
| N-061 | :54 | 재사용 CE 216, Jev 181, LF 동일 | E2E reused_answers, reused_lf_identical | 216 / 181 / true | MATCH |
| N-062 | 표2 캡션 | 226문항 | FS cv_overall.*.questions; EP 226행 | 226 | MATCH |
| N-063 | 표2 CE | 478/58.57/63.46/57.74/46.20/67.57 | FS ce.unfiltered; E2E means.ce_r | 478/58.565/63.459/57.743/46.195/67.571 | MATCH |
| N-064 | 표2 CE+필터링 | 467/58.54/64.56/57.15/45.65/67.13 | FS ce.filtered_cv; E2E means.ce_fr; EP kept 재계산 467; LF metrics 재계산 67.127 | 일치 | MATCH |
| N-065 | 표2 Jev | 478/61.75/66.85/60.69/47.31/70.15 | FS jev.unfiltered; E2E means.jev_r | 478/61.753/66.851/60.693/47.313/70.153 | MATCH |
| N-066 | 표2 Jev+필터링 | 426/61.43/69.80/58.26/47.03/69.13 | FS jev.filtered_cv; E2E means.jev_fr; EP kept 426; LF 재계산 69.128 | 일치 | MATCH |
| N-067 | :65 | 89.12% | FS jev.filtered_cv.kept_fraction | 0.891213 (426/478) | MATCH |
| N-068 | :65 | F1 −0.32, CI [−1.76, +1.07] | FS paired_bootstrap.jev_FR_minus_jev_R.f1_points; E2E PB | −0.3245 [−1.756, 1.066] | MATCH |
| N-069 | :65 | P +2.95, R −2.43 | FS precision_points/recall_points | +2.9499 / −2.4336 | MATCH |
| N-070 | :65 | 근거 0개 CE 1, Jev 4 | FS zero_evidence_questions; EP 빈 provisions 재계산 | 1 / 4 | MATCH |
| N-071 | :65 | 90% 유지 F1 CE 57.21 / Jev 61.66 | PMK target 0.9 | 57.208 / 61.665 | MATCH |
| N-072 | :65 | 약 절반 | PRE @0.5 shortlist_size_mean_per_pool | 5.00 / 5.03 | MATCH |
| N-073 | :65 | CE 66.14→51.47%, Jev 72.69→69.30% | PRE shortlist_gold_recall @1.0/0.5 | 66.140/51.467; 72.686/69.300 | MATCH |
| N-074 | :65 | 443건 기준 | SS shortlist micro 293/443, 322/443 | 0.66140 / 0.72686 | MATCH |
| N-075 | :67 | Jev+FR Token 47.31→47.03, −0.28 [−1.10, +0.44] | E2E PB jev_fr-jev_r.token_f1 | −0.2837 [−1.1001, 0.4431] | MATCH |
| N-076 | :67 | LF 70.15→69.13, −1.02 [−2.23, +0.15] | E2E PB jev_fr-jev_r.lf_eval | −1.0242 [−2.2279, 0.1458] | MATCH |
| N-077 | :67 | CE+FR Token −0.54 [−1.19, −0.07] | E2E PB ce_fr-ce_r.token_f1 | −0.5414 [−1.1858, −0.0670] (표시값 차 −0.55, N2) | MATCH |
| N-078 | :67 | CE+FR LF −0.44 [−1.22, +0.14] | E2E PB ce_fr-ce_r.lf_eval | −0.4437 [−1.2209, 0.1450] | MATCH |
| N-079 | :67 | Jev+FR−CE+FR Token +1.38 [+0.09, +2.69] | E2E PB jev_fr-ce_fr.token_f1 | 1.3753 [0.0900, 2.6859] | MATCH |
| N-080 | :67 | Jev+FR−CE+FR LF +2.00 [−0.36, +4.32] | E2E PB jev_fr-ce_fr.lf_eval | 2.0010 [−0.3591, 4.3231] | MATCH |
| N-081 | :67 | Jev+FR−CE Token +0.83 [−0.39, +2.00] | E2E PB jev_fr-ce_r.token_f1 | 0.8339 [−0.3950, 1.9957] | MATCH |
| N-082 | :67 | Jev+FR−CE LF +1.56 [−0.83, +3.86] | E2E PB jev_fr-ce_r.lf_eval | 1.5572 [−0.8347, 3.8649] | MATCH |
| N-083 | :67 | 하한 −2.23 | N-076 | −2.2279 | MATCH |
| N-084 | :69 | 약 0.61달러 | LS jev_cost_usd_measured_reps; LR 재계산 비워밍업 Σcost | 0.6100542 | MATCH |
| N-085 | :73 | 443건 | DEN gold_occurrences_per_arm | 443 | MATCH |
| N-086 | :73 | 미매핑 33, BM25 미회수 75 (공통) | DEN first_loss_counts | 33/33, 75/75 | MATCH |
| N-087 | :73 | shortlist 탈락 42→13 | DEN shortlist_absent | 42 / 13 | MATCH |
| N-088 | :73 | 미선택 60 / 72 | DEN shortlist_present_unselected | 60 / 72 | MATCH |
| N-089 | :73 | 최종 233→250 | DEN selected | 233 / 250 (합 443) | MATCH |
| N-090 | :73 | 386개 | DEN unique_gold_global | 386 | MATCH |
| N-091 | 그림3 캡션 | 443건 | fig_4_5 data.json denominator | 443 | MATCH |
| N-092 | :79 | 사례 A F1 50→100, LF 65.29→99.18 | CB qa_124_2hop_480_rand paired_metrics | 0.5/1.0; 0.65293/0.99185 | MATCH |
| N-093 | :79 | 사례 B F1 80→40, LF 71.79→52.67 | CB qa_324_2hop_515 | 0.8/0.4; 0.71786/0.52667 | MATCH |
| N-094 | :81 | 사례 C gold 3, 목록 2 | CB qa_443_3hop_703 stages n_gold/n_pools | 3 / 2 | MATCH |
| N-095 | :81 | 사례 C F1 40→0, Token F1 18.60→25.88 | CB 동 | 0.4/0.0; 0.186/0.2588 | MATCH |

### A′. 수치 추적 — 보충 자료

| ID | 위치 | 원고 수치 | 출처·키 | 원값 | 판정 |
|---|---|---|---|---|---|
| S-001 | :9 | BM25 100, 상위 10, 목록당 1 | CFG; PL; PF | 100/10/1 | MATCH |
| S-002 | :11 | 30문항, 4형식 | CD | 30 / 4 | MATCH |
| S-003 | :15 | 앞 800자 | koblex_lf_eval.py L120; AJ clip | 800 | MATCH |
| S-004 | :17 | 151, 10,000, 양끝 2.5% | AJ cmp[*] | 151/10000/95% | MATCH |
| S-005 | :31 | o200k_base | A5/tokenizer.json encoding | o200k_base | MATCH |
| S-006 | :33 | 재사용 CE 72, Jev 122 | CU execution_cache_hit=True | 72 / 122 | MATCH |
| S-007 | :39 | 443 / 386 | DEN | 443 / 386 | MATCH |
| S-008 | :41–47 | 사례 ID 3개, 선정 규칙 | PC (distance_to_median 0, 버킷 n 32/17/11); prepare_chapter4.py L470–471 (중앙값 근접, query_id 사전순) | 일치 | MATCH |
| S-009 | 표(S6) | 문맥 평균 203.67/215.60, 중앙값 164/170.5, IQR 133.75/142.50, 입력 2302.67/2314.58, 출력 72.16/73.98 | DS | 일치 | MATCH |
| S-010 | :73 | 차이 평균 +11.93, 중앙값 0, IQR 2.50 | DS paired context_tokens | 11.929 / 0 / 2.5 | MATCH |
| S-011 | :73 | 478, 고유 407/409, 중복 71/69 | DS | 일치 | MATCH |
| S-012 | 표(S6) | 33/75/42/60/233 vs 33/75/13/72/250, 합 443 | DEN | 일치 | MATCH |
| S-013 | :86 | 77.21점, 61.06%(138/226) | SS bm25 | 0.77212; 138/226 = 61.062 | MATCH |
| S-014 | :86 | 정답 외 선택 CE 126, Jev 116 | QS n_exact_non_gold_selected_unique > 0 재계산 | 126 / 116 | MATCH |
| S-015 | :90 | −1.17/+3.91/+6.92 | AJ by_hop f1 차 재계산 | −1.170/+3.911/+6.916 | MATCH |
| S-016 | :90 | 10⁻¹² 허용오차, 1/42 | WTL tolerance; AJ | 1e-12; 1/42 | MATCH |
| S-017 | :92 | 사례 C 목록 2, 사례 A·B 조문 | CB conditions.provisions | 일치(A: CE 42조2항+시행규칙 56조2항, Jev 42조2항+45조1항; B: 공통 253조) | MATCH |
| S-018 | :97 | 151, 5-fold, seed 20261109, 1.00~0.05 20개, 1점 | FS rule | 일치 | MATCH |
| S-019 | :99 | CE τ 0 또는 ~3.7e-6~3.8e-6, Jev 0.30~0.40 | FS chosen_tau_per_fold | CE {0, 3.713e-6, 3.8196e-6}, Jev {0.30,0.31,0.32,0.34,0.40} | MATCH |
| S-020 | :99 | 467/478 = 97.70%, 426/478 = 89.12% | FS kept_items_total | 97.699 / 89.121 | MATCH |
| S-021 | :101 | 293/443 = 66.14%, 322/443 = 72.69% | SS shortlist | 일치 | MATCH |
| S-022 | :103 | CE 10/Jev 45 재생성, 216/181 재사용, 226행, seed 20261108, 10,000, 151 | E2E checks, note; EP | 일치 | MATCH |
| S-023 | :107 | 85mm | build_manuscript_figures.py L1 | 85 mm | MATCH |
| S-024 | :109 | A4, 10pt, 2단, 20mm | preview.tex L3, L8 | 일치 | MATCH |
| S-025 | :114 | 60, 15/34/11, warmup 3, 360, seed 20261109 | LP; LR | 일치 | MATCH |
| S-026 | :114 | 후보 쌍 평균 176.98 | LS pairs_per_question.mean | 176.983 | MATCH |
| S-027 | :116 | 52그룹, 10,000회, seed 20261108, 로그비 bootstrap 후 지수 변환 | LS clusters; analyze_koblex_latency.py L43, L54–55 | 일치 | MATCH |
| S-028 | :118 | MPS, float32, batch 50, concurrency 4, 제외 단계 | LP ce/jev/excluded | 일치 | MATCH |
| S-029 | :120 | 180/180, 2/180, 0.9150925926 | LS; LR | 0.9150925926 | MATCH |
| S-030 | :122 | CV 16.93% / 3.43% | LS within_question_cv | 0.16932 / 0.03426 | MATCH |
| S-031 | :122 | 0.6100542달러, 실패·재시도 0 | LS; LR | 일치 | MATCH |

수치 추적 126행(본문·표·캡션 95, 보충 31; 묶음 행 포함) — **126 MATCH / 0 MISMATCH / 0 NOT_TRACEABLE.**

### B. 주장 추적 (Phase E / C4)

| ID | 위치 | 주장(요지) | 근거 | 판정 |
|---|---|---|---|---|
| C-01 | :5 | 재정렬 모델만 교체 | PL purpose "replacement of CE scoring only"; Jev도 같은 입력 형식 | VERIFIED |
| C-02 | :5 | 두 조건이 예상 법령·BM25 후보 공유 | SS bm25 행이 두 조건에서 같음; ranking 입력 candidates 공유 | VERIFIED |
| C-03 | :5 | 선택 개수를 정답 근거 수로 정하지 않음 | PL correction "no gold used"; pool당 1개 | VERIFIED |
| C-04 | :5 | CE 입력 형식을 탐색 진단을 거쳐 정함 | CD; 진단 10:56 → 잠금 10:58 | VERIFIED |
| C-05 | :7 | 공개 코드는 첫 번째 목록 번호를 참조 | PL raw_reference "contexts_list[0][choice]" | VERIFIED |
| C-06 | :7 | 기존 시험 결과 확인 후 탐색적 분석 | PL observed_prior_test_results true; AJ status POST_AUDIT… | VERIFIED |
| C-07 | :7 | 다중 비교 무보정 | AJ cmp confirmatory false, 보정 필드 없음 | VERIFIED |
| C-08 | :11 | 정확 문자열 집합 비교, 문항 동일 가중 | AJ estimand "unweighted question mean"; koblex.py | VERIFIED |
| C-09 | :17 | EM·완전회수 CI 0 포함 | N-022 | VERIFIED |
| C-10 | :19 | hop별 값은 관측 평균이며 검정 결과 아님 | AJ by_hop에 CI 없음 | VERIFIED |
| C-11 | :19 | 미매핑 문항을 전체 분석에서 제외하지 않음 | AJ notes "missing gold remains in denominator" | VERIFIED |
| C-12 | :21 | 원 논문 실행에도 같은 문제가 있었는지 미확인 | PL deployment_difference; 판정 근거 없음 | VERIFIED |
| C-13 | :25 | shortlist 수치는 최종 선택과 구별되는 후보 유지 수준 | SS stage 구분 | VERIFIED |
| C-14 | :31 | 동시 선택 가능 수가 줄어드는 이유는 목록당 1개 제약 | PF rule | VERIFIED |
| C-15 | :34 | 문항 내 중복 제거 후 점수화, 정렬·top-10까지 계측 | LP duplicate_policy, timed_region | VERIFIED |
| C-16 | :34 | 캐시 비활성, 순서 무작위화 | LP cache false, order_seed; benchmark L145–148 | VERIFIED |
| C-17 | :34 | 분석 단위는 문항별 3회 평균 | LR 재계산과 LS 일치 | VERIFIED |
| C-18 | :44 | 품질·시간을 같은 실행에서 동시 검증한 결과 아님 | 별도 폴더, 60 vs 226 | VERIFIED |
| C-19 | :44 | 배포 조건에 의존, 모델 고유 속도 아님 | LS limits | VERIFIED |
| C-20 | :44 | 생성·BM25·선택·답변·로드 제외 | LP excluded | VERIFIED |
| C-21 | :46 | 재호출 시 동일 품질 보장 안 됨 | Jev 2/180 | VERIFIED |
| C-22 | :50 | LF-Eval은 정답 답변과 gold를 기준으로 결론·누락·모순 평가 | rubric evaluation_steps; koblex_lf_eval.py L116, L120–121 (expected_output, context = gold provisions) | VERIFIED |
| C-23 | :50 | Token F1은 공백 단위 중복 | koblex.py L116–118 | VERIFIED |
| C-24 | :50 | 모든 자동 지표가 유의하게 개선되었다고 해석하지 않음 | p 0.0525 > 0.05 | VERIFIED |
| C-25 | :52 | 증가는 선택 수 차이가 아니라 선택 내용 변화 때문 | 목록 수 paired diff 0 | VERIFIED |
| C-26 | :52 | 입력량 절감은 관찰되지 않음 | DS 평균 +11.92 | VERIFIED |
| C-27 | :52 | 재사용 응답을 포함하므로 신규 청구액이 아님 | CU | VERIFIED |
| C-28 | :54 | τ를 답변 생성 전에 정하고 고정 | E2E status/note "before answers"; EP의 tau 값이 FS fold τ와 일치 | VERIFIED |
| C-29 | :54 | 같은 프롬프트·모델로 변경 문항만 재생성 | EP generation_trace returned_model gpt-4o-2024-08-06; 변경 수 = 재생성 수(10/45) | VERIFIED |
| C-30 | :54 | 같은 절차로 Token F1·LF-Eval 평가 | e2e lf manifest(동일 rubric sha, clip 800, temperature 0) | VERIFIED |
| C-31 | :54 | 재사용 문항의 LF 점수가 기존과 같음 | E2E reused_lf_identical true ×2 | VERIFIED |
| C-32 | :65 | 그림 3과 분모 같고 그림 2와 다름 | 443 micro vs 226 macro | VERIFIED |
| C-33 | :67 | CE+FR Token F1 감소 구간은 0을 포함하지 않음 | N-077 | VERIFIED |
| C-34 | :67 | Jev의 두 감소는 0과 구분되지 않음 | N-075/076 CI가 0 포함 | VERIFIED |
| C-35 | :67 | 사전 비열등성 마진 없음 → 유지·동등성으로 해석 안 함 | E2E note; FS limits | VERIFIED (과장 없음) |
| C-36 | :69 | 필터링에 따른 비용·지연 변화는 측정 안 함 | e2e에 비용·지연 비교 분석 없음(문자 수 평균만 있음) | VERIFIED |
| C-37 | :69 | LF-Eval은 제공 근거의 주장 지지를 직접 평가하지 않음 | rubric context = gold provisions | VERIFIED |
| C-38 | :69 | 0.61달러는 CE 장비·후속 생성 비용을 포함하지 않음 | LS limits "no cost model for local CE" | VERIFIED |
| C-39 | :73 | 출현을 최초 탈락 단계 하나에 배타 배정 | DEN 합 443 | VERIFIED |
| C-40 | :79 | 사례 선정은 버킷 중앙값에 가장 가까운 문항 | PC distance 0; 코드 L470–471 | VERIFIED |
| C-41 | :79 | 사례 A: Jev가 42조2항을 유지하고 45조1항을 추가 | CB conditions; stages selected_gold 1→2 | VERIFIED |
| C-42 | :79 | 사례 B: 79조1항이 Jev shortlist에서 탈락, 83조1항 선택 | CB jev first_loss shortlist_absent 1; provisions에 83조 1항 | VERIFIED |
| C-43 | :81 | 사례 C: gold 하나는 미매핑, 하나는 BM25 미회수, Jev는 나머지도 미선택 | CB jev first_loss {corpus_absent 1, bm25_absent 1, shortlist_present_unselected 1} | VERIFIED |
| C-44 | :81 | 법률적 부적절성을 확정한 것 아님 | PC legal_review_status NOT_REVIEWED | VERIFIED |
| C-45 | 보충 :11 | 진단은 미노출 시험이 아님 | CD interpretation | VERIFIED |
| C-46 | 보충 :17 | Token F1 p와 percentile CI는 같은 방식의 쌍이 아님 | AJ cmp[4] 구조 | VERIFIED |
| C-47 | 보충 :23,:25 | 수정 내용·원 논문 실행 판정 안 함 | PL correction | VERIFIED |
| C-48 | 보충 :33 | 실행 시간에는 캐시·대기가 포함됨 | AJ timing "QUALITY_TIMES_NOT_UNCACHED_BENCHMARK" | VERIFIED |
| C-49 | 보충 :41 | C는 F1과 Token F1의 엄격한 반대 방향 | CB strict_discordance.token_f1 true | VERIFIED |
| C-50 | 보충 :57 | Lee et al. (2025)이 KoBLEX·ParSeR·LF-Eval의 원문 | 로컬 원문 p.1(226 instances, PARSER, LF-EVAL, arXiv:2509.01324v1) | VERIFIED |
| C-51 | 보충 :97,:99 | 학습 fold 허용 하락폭은 검증 성능 보장이나 비열등성 검정이 아님 | FS limits | VERIFIED |
| C-52 | 보충 :101 | 선택 전 필터링은 LLM 재선택을 하지 않음 | FS limits "LLM choice would change" | VERIFIED |
| C-53 | 보충 :103 | 근거가 모두 제거된 문항은 빈 문맥으로 생성 | EP 빈 provisions 5건 모두 answer_source = regenerated | VERIFIED |
| C-54 | 보충 :107 | 수치 신규 추론·CI 추가 계산 없음 | provenance new_statistical_tests | VERIFIED |
| C-55 | 보충 :114 | 두 방법을 동시에 실행하지 않음 | benchmark_koblex_latency.py L16 "methods run sequentially" | VERIFIED |
| C-56 | 보충 :116 | 중앙값·p95는 60개 평균값의 분포 | LR 재계산과 LS 일치 | VERIFIED |
| C-57 | 보충 :120 | 겹침 정의 | benchmark 스크립트; LR 행별 값의 평균 = LS | VERIFIED |
| C-58 | 보충 :122 | 변동계수는 후보 재현성과 다른 개념 | LS 별도 필드 | VERIFIED |

### C. md ↔ tex ↔ PDF 동기화 (C2)
- `section4_1..5.tex` 산문 20문단을 정규화했다(`\%`→%, `$\to$`→→, `$-$`→−, `\texttt{}`→백틱, `\ref`→aux 번호). 그 뒤 `chapter4.md` 산문 20문단과 문단 단위로 비교한 결과 **완전 일치**다. 그림 캡션 3개와 표 캡션 2개도 글자 단위로 일치한다. 표 1(6셀)과 표 2(24셀)의 값도 일치한다.
- `\ref` 5곳이 모두 해결되고 번호가 md와 같다. 해결 결과: `fig:ch4_2` → 그림 1(p.1), `fig:ch4_3` → 그림 2(p.1), `tab:ch4_3` → 표 1(p.2), `tab:ch4_4` → 표 2(p.2), `fig:ch4_5` → 그림 3(p.3). 4.4의 `그림~\ref{fig:ch4_5}`는 앞쪽에서 뒤 그림을 가리키는 참조인데, 2-pass 빌드라 문제없다.
- `output/pdf/chapter4-final.pdf`는 `chapter4-draft.pdf`와 바이트 단위로 같다. pypdf로 확인한 결과 **3쪽**이다. PDF 텍스트에 "??" 0건이다. 핵심 신규 수치(47.03, −2.23, 69.13, 45.65, 0.0525, 0.61)가 있다. 본문 숫자 multiset의 차이는 절 번호와 그림 내부 라벨뿐이다. 사람 평가 관련 어휘 0건.
- 빌드 로그: "Output written … (3 pages)". Overfull 0, Undefined reference 0, Rerun 경고 0, Underfull 6(N8).

### D. 사용자 부정 제약(사람 평가 언급 금지) 스캔
- 검색어: 사람, 평가자, 블라인드, 판단, human, review, expert, 전문가, 검토자, annotat, 주석자, rater, 인간.
- 대상: `chapter4.md`, `chapter4-supplement.md`, `section4_*.tex`, PDF 추출 텍스트, `figures/section-figures-v1/README.md`, `provenance.json`.
- 결과: 해당 0건. 걸린 것은 "preview.tex"의 부분 문자열 "review"와 그림 3 provenance·README의 "법률 판단 오류로 단정하지 않는다"뿐이며, 둘 다 사람 평가가 아니다.
- 링크된 `manuscript-facts.json`: 3건 → IL-MEDIUM-2.

### E. 참고문헌 검증 (Phase A/B)
- Lee, J., Kim, D., Hwang, S., Kim, H., & Lee, G. G. (2025). KOBLEX: Open Legal Question Answering with Multi-hop Reasoning. arXiv:2509.01324.
- 확인 경로: `research/chapter4/style-study-v1/papers/2509.01324.txt` 1쪽(제목, 저자 Jihyung Lee·Daehui Kim·Seonjeong Hwang·Hyounghun Kim·Gary Geunbae Lee, "arXiv:2509.01324v1 [cs.CL] 1 Sep 2025") + `papers-manifest.json`(pdf_sha256 167f2025…).
- A1/A2: VERIFIED. B1(문맥 "KoBLEX, ParSeR 및 LF-Eval의 원문", "기존 성능표를 전재한 것이 아님"): VERIFIED. 외부 조회는 하지 않았다.
