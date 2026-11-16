# Stage 3′ 재심사 — Phase 2A 증거 판정 (Evidence Verdict, 답변서 비열람)

- 대상: 제4장 "실험 결과 및 분석" (KoBLEX ParSeR, 공개 코드 CE / 수정 CE / Decision Model Jev)
- 단계: Stage 3′ Phase 2A — `re_review_mode_protocol.md`(ARS academic-paper-reviewer 3.24.2) § Phase 2A
- 작성일: 2026-11-14
- 산출물 성격: Phase 1에서 고정한 기준(`phase1_criteria.md`)에만 대어, 원본과 수정본을 비교해 항목별 판정과 근거를 확정한 기록이다. 답변서(`stage4_response_to_reviewers.md`)와 delta 보고(`stage4_delta_report.md`)는 읽지 않았다. 최종 결정(Accept/Minor/Major)은 이 단계에서 도출하지 않는다(Phase 2B 소관).

---

## 0. Judge Record 관련 기록

| 항목 | 값 |
|---|---|
| precommitment_hash | `8c3f8db8f880223b1b96b98e304eb9a2a70844892f71c0ef6bd8de0da0304660` (`research/chapter4/pipeline/stage3prime/phase1_criteria.md`, 작업 시작 시 `shasum -a 256`으로 재계산하여 일치 확인) |
| 계약 산출물 | Schema 7 JSON core, author-adjudication sidecar, revision-evidence-bundle, input manifest 1.1, apply report 1.3이 **없다**. 계약 규칙(Phase 1 기준 고정 → 2A 증거 판정 → 2B 대조)을 **수작업으로 적용**하였다. checker(`check_re_review_synthesis.py`)는 실행하지 않았다(orchestrator 결정 1). |
| Routing | `card_mapped` (ID 접두어 정규화, 로드맵 l.6 규약; Phase 1 §0.3-2 제안 그대로, orchestrator 결정 2) |
| Reviewer configuration | `round1_cards_reused` (field_analyst 재실행 없음) |
| Blind cross-model pass | `not_configured` — 단일 모델 계열(orchestrator 결정 3) |
| Apply-report chain | 해당 산출물 없음(수작업 적용; 원본 원고 `pre_stage4/`는 제공되어 비교에 사용) |
| 단일 계열 고지 | This verification round ran on the same model family that drove the revisions; over-optimization to this judge's latent biases is possible (Ren et al. 2026, arXiv:2607.13104 §8.1.2). |
| Dissent | 없음. 모든 must_fix·should_fix 항목을 Phase 1 operationalization 그대로 적용하였다. |
| Escalation exception | 없음 |

### 0.1 읽은 입력
- 기준: `phase1_criteria.md`(해시 일치), `stage3_revision_roadmap.md`, `pipeline_state.md`, 프로토콜 파일.
- 원본: `research/chapter4/pipeline/pre_stage4/chapter4.md`(81행), `chapter4-supplement.md`(122행).
- 수정본: `research/chapter4/chapter4.md`(74행), `chapter4-supplement.md`(225행), `section4_1.tex`~`section4_5.tex`, `chapter4.tex`, `preview.tex`, `output/pdf/chapter4-final.pdf`(pypdf로 텍스트 추출), `tmp/pdfs/chapter4/chapter4-draft.log`.
- 원자료·재계산 출력: `results/koblex-reproduction-v1/analysis.json`, `protocol-lock.json`, `ce-runtime.json`, `runtime-settings.json`, `ce-diagnostic-plan.json`, `predictions/*.jsonl`(선택 호출 usage), `responses/`(응답 객체 형식 1건), `chapter4-prep-v1/A1/question-metrics.jsonl`, `A4/question-stages.jsonl`, `A4/gold-occurrences.jsonl`, `A6/casebook.jsonl`, `chapter4-prep-v1/analysis-spec.json`, `chapter4-revision-v1/`(README, `revision-analysis.json`, `shortlist-bootstrap.json`), `results/koblex-latency-v1/`(`summary.json`, `protocol.json`, `raw.jsonl`, README), `results/koblex-filtering-v1/`(`summary.json`, `e2e-summary.json`, CSV 2종, README), `research/prompts/koblex_lf_eval.json`, `research/koblex_source_audit_20261108.json`(그룹 정의), `data/koblex/upstream/experiments/parser/openai/*.py`, `src/legal_rag_jev/koblex_analysis.py`·`providers.py`(코드 확인).

### 0.2 읽지 않은 입력 (persuasion-blind)
- `research/chapter4/pipeline/stage4_response_to_reviewers.md`, `research/chapter4/pipeline/stage4_delta_report.md`.
- 참고: `pipeline_state.md` l.36에 Stage 4의 한 줄 요약이 있어 읽혔다. 판정은 이 요약을 근거로 쓰지 않고 원고·원자료 대조만으로 내렸다.

### 0.3 수치 검증 방법
- 독립 재계산: 잠금 함수 `legal_rag_jev.koblex_analysis.paired_bootstrap`(151그룹, 10,000회, seed 20261108)을 읽기 전용으로 import하고, 원자료(`A4/question-stages.jsonl`, `A1/question-metrics.jsonl`, `gold-occurrences.jsonl`, latency `raw.jsonl`, `predictions/*.jsonl`, `analysis.json` 저장 p값)에서 직접 다시 계산하였다(스크립트는 scratchpad에 두었고 저장소 파일은 바꾸지 않음).
- 원자료 직접 추출: `analysis.json` `summaries`/`comparisons`, filtering `summary.json` `cv_overall`, `e2e-summary.json` `means`/`paired_bootstrap_points`, CSV 2종, latency `summary.json`.
- 나머지 보조 기술통계(순위, 미매핑 원인, 재사용 수, 날짜 등)는 G4 디렉터리 출력 `revision-analysis.json`과 대조하였다(G1 기준은 "원자료 또는 G4 디렉터리의 재계산 출력과 1:1 대응").

---

## 1. 수치 대조표 (새로 들어가거나 바뀐 수치)

표기: ✓ = 소수 둘째 자리까지 일치(원고 반올림 규칙 동일), [독립] = 검증자가 원자료에서 재계산, [저장] = 원자료 파일에서 직접 추출, [G4] = `revision-analysis.json`과 대조.

| 원고 위치 | 원고 값 | 대조 결과 | 방식 |
|---|---|---|---|
| 본문 l.25 shortlist Recall 차이 | +5.16 [+2.61, +7.94] | 5.162 [2.6087, 7.9439] ✓ (151그룹·10,000회·seed 20261108) | [독립] |
| 본문 l.25 모든 gold shortlist 문항 | 112→130, +7.96%p [+3.89, +12.38] | 112/130, 7.9646 [3.8868, 12.3762] ✓ | [독립] |
| 본문 l.27 조건부 선택률 | CE 79.52%(233/293), Jev 77.64%(250/322) | 233/293=79.52, 250/322=77.64 ✓ | [독립] gold-occurrences |
| 본문 l.27 동시 선택 가능 / 완전 회수 | 104/120, 77/79 | ✓ | [독립] question-stages |
| 본문 l.19 hop별 우세/동일/열세 | 0/56/1, 20/95/12, 12/26/4 | ✓ (허용오차 1e-12) | [독립] question-metrics |
| 보충 S6 l.172 hop별 기여 비율 | −9.3%, 68.9%, 40.3% | ✓ | [독립] |
| 보충 S6 l.166 표 (shortlist 전체 gold, 동시 선택 가능, 완전 회수, 목록 수<gold) | 49/49·56/64·7/17; 48/48·54/61·2/11; 48/47·28/31·1/1; 2·8·9 | 합계 112/130, 104/120, 77/79와 정합; 행별 값 ✓ | [G4] + 합계 [독립] |
| 본문 l.55–58 표 2 (완전 회수 열 포함 4행×7열) | 34.07/33.19/34.96/33.19 등 | `e2e-summary.json` `means`, `summary.json` `cv_overall` ✓ | [저장] |
| 본문 l.60 Jev+필터링 차이 | F1 −0.32[−1.76,+1.07], P +2.95[+1.05,+5.01], R −2.43[−3.81,−1.16], 완전 회수 −1.77[−3.51,−0.43], Token F1 −0.28[−1.10,+0.44], LF −1.02[−2.23,+0.15] | `paired_bootstrap_points/jev_fr-jev_r` ✓ | [저장] |
| 본문 l.60 유지율 | Jev 89.12%, CE 97.70% | `kept_fraction` 0.8912, 0.9770 ✓ | [저장] |
| 보충 S7 l.188 표 (조건 내 차이 12쌍) | CE 열·Jev 열 | `ce_fr-ce_r`, `jev_fr-jev_r` ✓ | [저장] |
| 보충 S7 l.199 교차 비교 | F1 +2.89[+0.26,+5.60], 완전 회수 0.00[−4.02,+4.00], Token F1 +1.38[+0.09,+2.69], LF +2.00[−0.36,+4.32]; vs CE: +2.86[+0.24,+5.54], −0.88[−4.85,+3.11], +0.83[−0.39,+2.00], +1.56[−0.83,+3.86] | `jev_fr-ce_fr`, `jev_fr-ce_r` ✓ | [저장] |
| 보충 S7 l.199, l.201 | 90% 유지 F1 57.21/61.66; 선택 전 66.14→51.47, 72.69→69.30 | `post_matched_keep_rate.csv`(0.9행), `pre_matched_keep_rate.csv`(1.0·0.5행) ✓ | [저장] |
| 보충 S2 l.65 표 | 3조건 × P,R,F1,EM,완전 회수,Token F1,LF-Eval | `analysis.json` `summaries.*.retrieval`/`token_f1`/`lf_eval` ✓ (21개 값) | [저장] |
| 보충 S2 l.75 수정 CE−공개 코드 CE | F1 +9.85[+6.85,+13.02], R +12.39[+9.28,+15.83], EM +10.18[+4.70,+15.86], 완전 회수 +13.27[+8.62,+18.34], Token F1 +5.49[+3.78,+7.30], LF +9.27[+6.20,+12.30] | `analysis.json` `comparisons` ✓ | [저장] |
| 보충 S1 l.33 p값 표 | 0.012/0.025/0.348/0.678/0.052/0.023 | 저장 p ✓ | [저장] |
| 보충 S1 l.33 Holm·BH | Holm 0.074/0.113/0.696/0.696/0.157/0.113; BH 0.050(0.0496)/0.050/0.418/0.678/0.079/0.050 | 저장 p로 검증자가 Holm step-down·BH step-up 재계산 ✓ | [독립] |
| 보충 S1 l.42 | 공개 코드 대비 p 모두 ≤0.0004 | 최대 0.00040 ✓ | [저장] |
| 보충 S1 l.42 MC 민감도 | seed 20261109–20261128, 하한 −0.05~+0.03, 12/20 음수 | 최소 −0.047, 최대 +0.026, 12/20 ✓ (R1의 13/20은 쓰지 않음) | [독립] |
| 보충 S1 l.31 Precision 차이 | +3.39 [+0.77, +6.02] | ✓ | [독립] |
| 보충 S1 l.17 진단 제외 196문항(139그룹) | F1 +3.34[+0.68,+6.07], LF +2.66[+0.26,+5.05], Token F1 +1.26[+0.04,+2.49] | ✓ (139그룹) | [독립] |
| 보충 S1 l.17 진단 F1 | 33.94 / 17.94 / 18.09 | `RM13_diagnostic_exclusion.diagnostic_variants_f1_points` ✓ | [G4] |
| 보충 S4 l.91 | 사례 A만 진단 30문항에 포함 | `ce-diagnostic-plan.json` `sample_ids`: qa_124_2hop_480_rand 포함, B·C 미포함 ✓ | [독립] |
| 보충 S1 l.23 | Pearson 0.53; LF 기여 0/+0.85/+1.74 (119/58/49문항); 58문항 34상승·17하락 | Pearson 0.530 ✓ [독립]; 분해 ✓ | [독립]/[G4] |
| 보충 S1 l.21, l.25 | 800자 초과 0개; 272쌍 동일 digest·캐시 재사용 | ✓ | [G4] |
| 보충 S3 l.83 | 재사용 CE 72·Jev 122, 121(CE)+1(공개 코드 CE), 119/121/124/102 | ✓ | [G4] |
| 보충 S6 l.137–141 | 문맥 비중 8.84/9.31%, 선택 호출 2.12회, 호출당 7770.61/7844.49, 문항당 16435.19/16591.45, 출력 2.52/2.33, 차이 평균 +156.26·중앙값 +84.5 | `predictions/*.jsonl` `selection_traces[].usage`에서 호출 478/478, 7770.61/7844.49, 16435.19/16591.45, 2.52/2.33 ✓ | [독립]/[G4] |
| 보충 S6 l.153–158 | 미선택 분해 30/30, 36/36; 최고 순위 2.17/1.97, 1위 비율 63.82/62.11%, 선택 순위 1.90(293)/1.66(308) | ✓ | [G4] |
| 보충 S6 l.160 | shortlist Recall 우세/동일/열세 30/189/7 | ✓ | [G4] |
| 보충 S6 l.162 | 미매핑 27개: 같은 hierarchy 27, 접두 26, 각 호 25, 공백 정규화 0 | ✓ | [G4] |
| 보충 S9 l.213 | 후보 쌍 83~287개 | latency `raw.jsonl` 최소 83, 최대 287, 평균 176.98 ✓ | [독립] |
| 보충 S9 l.217 | 60문항 차이 F1 +1.39, LF +0.87, Token F1 +0.47 | ✓ (raw.jsonl 본 측정 문항 60개 × question-metrics) | [독립] |
| 보충 S9 l.219 | 쌍당 27.60/60.22ms, Jev 사분위 59.19~60.93ms, 동시 요청 4(품질 실행과 같음) | latency `summary.json` `per_pair_ms`, `runtime-settings.json` concurrency 4 ✓ | [저장] |
| 보충 S9 l.223 | 겹침 최솟값 0.60, 하위 10% 0.85, 1.00 35회, ≤0.85 36회; 날짜 2026-11-09 02:05~02:43 / 13:05~13:53 UTC | raw.jsonl: min 0.6, p10 0.85, 35, 36 ✓; 날짜 ✓ | [독립]/[G4] |
| 보충 S9 l.225 | 0.6100542달러, 180회, 31,857쌍, 0.0034/문항, 0.019/1,000쌍 | raw.jsonl 합계 0.6100542, 31,857쌍 ✓; 0.6100542/180=0.00339, /31.857=0.0191 ✓ | [독립] |
| 보충 S4 l.99 | 사례 C Jev 정답 외 조문: 형법 제39조제3항, 사면법 제5조제1항 | `A6/casebook.jsonl` qa_443_3hop_703 `conditions.parser_jev_fixed.provisions` ✓ | [저장] |
| 보충 S5 표 | CUDA, `gpt-4o` alias, Chat Completions, 0.01·0.9·2000, bm25s·stopwords `en`, `contexts_list[0][choice]`, batch 50, max_length 8192, MPS float32, bm25s 0.2.14 | 업스트림 `utils.py` l.143(cuda), l.154–155, l.179–187; `run_pipeline.py` l.49; `selection_retrieval.py` l.34, l.71; `protocol-lock.json` signature; `ce-runtime.json`; `providers.py` l.393 `/chat/completions`; `responses/*.json` `"object": "chat.completion"` ✓ | [저장] |

불일치 0건. 근사 구간 [+2.6, +8.0], R1 13/20, R3 $0.00339 등 seat 산출값을 재계산 없이 옮긴 사례 없음(원고 값은 모두 재계산 출력과 일치하며, MC 결과는 seat 값과 다른 12/20으로 보고됨).

---

## 2. P0 — must_fix 판정

### RM-01 (R1) 필터링 절의 0 배제 감소 구간 보고 — **FULLY_ADDRESSED**
- verified_by: EIC / applied_criterion: phase1 precommitted
- change_summary: 4.4 필터링 결과 문단을 다시 써서 Jev+필터링의 F1·Precision·Recall·완전 회수·Token F1·LF-Eval 차이를 모두 점추정+CI로 보고하고, 표 2에 완전 회수 열을 추가했으며, CE+필터링 차이는 같은 형식으로 S7 표에 옮겼다.
- 증거(operationalization 1–6):
  1. 본문 l.60: "근거 F1 차이는 −0.32점(CI [−1.76, +1.07]점)…Precision은 2.95점(CI [+1.05, +5.01]점) 높아졌고, Recall은 2.43점(CI [−3.81, −1.16]점), 완전 회수율은 1.77%p(CI [−3.51, −0.43]%p) 낮아졌다". 원본 l.65는 Precision·Recall에 CI가 없었다. 본문 4.4에 CI 없는 근거 지표 차이 0개.
  2. 0 배제 구간이 숫자로 제시됨(위 인용).
  3. 대칭성: 본문은 두 조건 모두에 "0을 포함하지 않았다" 같은 강조가 없다(grep 0건). CE+필터링 차이는 S7 l.188 표에서 Jev와 같은 열 형식(점추정+CI)으로 제시된다. CE 쪽 0 배제 결과(Token F1 [−1.19, −0.07])만 골라 생략한 것이 아니라 CE+필터링 차이 전체가 RM-04 이동 지시에 따라 S7로 갔고, 본문 l.60은 "조건 간 비교는 S7에 따로 제시"라고 위치를 밝힌다. 따라서 반대 방향 비대칭(악화 판별자)에 해당하지 않는다.
  4. 표 2 l.53–58 "완전 회수" 열 4행: 34.07/33.19/34.96/33.19 — 파일 값 일치(§1).
  5. l.60 "F1이 문턱값 선택 기준이었으므로 0 근처인 것은 부분적으로 설계상의 귀결이다".
  6. S7 l.186 "필터링 후 완전 회수율은 CE+필터링과 Jev+필터링이 모두 33.19%로 같아졌다."
- 악화 판별: "유지·동등" 서술 없음(l.60 "품질의 유지나 동등성으로 해석하지 않으며"). 원본 Recall −2.43 서술 유지.
- evidence_anchor: `research/chapter4/chapter4.md` l.51–60; `research/chapter4/chapter4-supplement.md` l.180–199; `section4_4.tex` 표 `tab:ch4_4`.

### RM-02 (R2) 필터링 문턱값 격자의 사후 변경 공개 — **FULLY_ADDRESSED**
- verified_by: R1 / applied_criterion: phase1 precommitted
- change_summary: S7에 "격자 변경 이력" 단락을 새로 넣고, 원본 본문의 "scorer별 점수 척도를 고려해 동일한 크기의 분위수 격자를 사용하였다"를 지우고 S7 참조 구절로 바꿨다.
- 증거:
  1. S7 l.182: (a) "처음에는 두 scorer에 같은 0.00~0.95 절대 격자를 적용했다", (b) "CE가 선택한 근거의 점수는 대부분 0.05 미만이어서 CE 필터링이 사실상 불가능했고", (d) "이 결과를 확인한 뒤", (c) "기존 설계 문서의 척도별 격자(같은 크기) 원칙에 따라 scorer별 분위수 격자로 바꾸었다".
  2. 같은 단락: "허용 하락폭 1점·20개 격자·최소 유지 목적함수가 첫 실행 전에 정해졌다는 별도 기록은 없다. 따라서 이 선택들도 결과 관찰 후의 분석 선택으로 취급한다."
  3. 본문 l.49: "(결과 관찰 후 바꾼 격자 이력과 상세 절차는 S7)".
  4. `results/koblex-filtering-v1/README.md` l.18 "수정 이력"(절대 격자 → CE 0.05 미만 → 기존 설계의 척도별 격자로 변경)과 모순 없음.
- 악화 판별: "사전 설계대로" 서술 없음; 결과를 확증적으로 재서술하지 않음.
- evidence_anchor: `chapter4-supplement.md` l.182; `chapter4.md` l.49.

---

## 3. P1 — should_fix 판정

### RM-03 Jev 단일 실행 조건 선배치 — **FULLY_ADDRESSED** (verified_by EIC)
- change_summary: 4.1 끝에 단일 실행·CI 범위 문장을 추가하고 4.3 말미의 중복 문장을 줄였다.
- 증거: 본문 l.7 "Jev는 원격 API로 다시 호출하면 상위 10개가 달라질 수 있으므로(4.3), 이하 Jev 품질 수치는 저장된 단일 실행의 값이다. 보고한 CI는 문항 표본 변동만 반영하며 실행 간 변동은 포함하지 않는다." — (a)(b)(c) 모두, 첫 CI(l.17)보다 앞. 반복 실행은 수행·제안으로 언급되지 않음(optional future work 표기 조건 해당 없음). 4.3 l.41은 "따라서 재호출 시 동일한 선택·답변 품질은 보장되지 않는다"로 축소(원본 l.46의 "기존 Jev 품질 수치는 저장된 실행 결과에 대한 값이며" 삭제), 2/180·91.51%는 유지.

### RM-04 4.4 필터링 압축·동기·교차 비교 이동 — **FULLY_ADDRESSED** (verified_by EIC)
- change_summary: 4.4 필터링 부분을 목적 문장+방법 요지+주 결과+비열등성 거부로 줄이고 교차 비교·선택 전 필터링·90% 기술통계를 S7로 옮겼다.
- 증거:
  1. 분량: 원본 4.4 셋째~여섯째 문단(원본 l.54, 65, 67, 69) 공백 제외 1,214자 → 수정본 대응 문단(l.49, l.60) 600자 = **49.4%** (기준 ≤55%). 원본 여섯째 문단 내용은 LF-Eval 단서 → S1 l.23, 비용 → S9 l.225, 비용·지연 미측정 → l.60으로 흩어졌다.
  2. 목적 문장: l.49 첫머리 "선택 근거 수를 줄일 때 자동 품질이 어떻게 변하는지 탐색하기 위해".
  3. 교차 비교 CI 본문 0건(원본 l.67의 "Jev+필터링과 CE+필터링의 차이는 Token F1 +1.38점(CI [+0.09, +2.69])" 삭제).
  4. S7 l.199(교차 비교 전부, 강도 차이 97.70%/89.12%, 10/45문항, 90% 유지 57.21/61.66), l.201(선택 전 66.14→51.47, 72.69→69.30), l.184(근거 0개 문항 1/4) — 이동 수치 모두 존재.
  5. 본문의 CE+필터링 "구간은 0을 포함하지 않았다" 삭제(grep 0건); S7 l.197 "CE+필터링의 Token F1 차이(−0.54점)는 답변이 바뀐 10문항에서만 발생하므로".
  6. l.60 "사전에 정한 비열등성 마진이 없으므로 이 결과를 품질의 유지나 동등성으로 해석하지 않으며".
  7. 본문 전체에 "0을 포함하지 않았다" 형 강조 0건.
- 악화 판별: 목적 문장에 자원 절감 함의 없음; 정보 손실 없음.

### RM-05 RQ별 답 문장과 장 요약 — **PARTIALLY_ADDRESSED** (verified_by EIC)
- change_summary: 4.2·4.3·4.4 첫 문장을 결론형으로 바꾸고 4.5 끝에 "종합하면" 요약 문단을 추가했으며, 4.3·4.4의 반복 유보를 요약으로 흡수했다.
- 충족 증거:
  - 4.2 첫 문장(l.11) "Jev 교체로 평균 최종 근거 F1은 3.19점 높아졌으나, 필요한 근거를 모두 확보한 문항의 증가는 0과 구분되지 않았다." — 수치 포함.
  - 4.3 첫 문장(l.25) "Jev는 재정렬 후 상위 10개 후보(shortlist)에 gold를 더 많이 남겼고, 재정렬 단계 지연은 약 2.25배였다." — 지연 수치 포함.
  - 요약(l.74): 수치 3.19, 2.25, 226, 60, 9.85 모두 본문 다른 곳에 있음(요약 최초 수치 0개). 상한 (i) "저장된 단일 Jev 실행", (ii) "EM·완전 회수 차이는 불확실", (iii) "재정렬 단계 지연…배포 조건에 의존", (iv) "입력량 절감은 관찰되지 않았다" 모두 있음. 품질·지연을 비율로 결합하지 않고 "품질(226문항)과 다른 실행·표본(60문항)에서 측정"이라고 분리. "우수/유리/효율/비용 절감" 표현 0건.
  - 반복 유보 축소: 원본 l.44 "다만 품질은 전체 226문항의 기존 결과이고…", l.46 일부, l.69 "본 절의 결과는…한정된다"가 본문 절에서 빠지고 내용은 요약·4.1에 남음.
- residual_gap: (1) **4.4 첫 문장(l.45) "자동 답변 지표는 소폭 높아졌으나 Token F1의 개선은 경계적이었고, 입력량 절감은 관찰되지 않았다."에 수치가 없다** — operationalization 1("각각의 첫 문장이 해당 RQ의 답을 수치와 함께 진술")의 4.4 부분 미충족(수치는 둘째 문장에 있음). (2) 4.3 첫 문장은 shortlist 유지에 대해서는 수치 없이 "더 많이"로만 진술한다(지연 수치만 있음). (3) 요약이 5문장으로 기준의 "3–4문장"을 한 문장 넘는다(내용은 상한 준수).
- residual_obligation_class: **consider** (첫 문장 수치 보강과 문장 수 조정만 남은 표현 수준 잔여; 주장 상한·정보 정확성 문제 아님).

### RM-06 기여 구분 지도 — **FULLY_ADDRESSED** (verified_by EIC)
- 증거: 본문 l.7 "비교는 공개 코드 CE, 이를 수정한 CE, Jev의 세 조건으로 구성된다…앞의 두 조건 차이는 후보 목록 참조 수정 효과이고, 수정 CE와 Jev의 차이는 재정렬기 교체 효과이다." S2 l.65–73 3조건×7지표 표, `analysis.json`과 21개 값 일치(§1). 유보 유지: 본문 l.21, S2 l.75 "원 논문의 실제 실행에도 같은 문제가 있었다고 판정한 것은 아니다". 본문 3조건 표 없음.

### RM-07 Token F1 경계 서술·p값 일관화 — **FULLY_ADDRESSED** (verified_by R1)
- 증거: 본문 p값 0개(원본 l.50 "centered-bootstrap 양측 p값은 약 0.0525" 삭제; grep "p값" 본문 0건). l.45 "Token F1의 개선은 경계적이었고…Token F1은 CE 46.20점에서 Jev 47.31점으로(CI [+0.02, +2.27]점)". "개선되었다" 단정 없음. S1 l.33 6지표 p값 표가 저장 값과 일치. 선택 요소 MC 민감도(l.42) 재계산 일치(12/20). 보고 CI는 잠금 seed 유지(D-05 위반 없음).

### RM-08 다중성 해석 규칙과 비교 계열 — **FULLY_ADDRESSED** (verified_by R1)
- 증거: 본문 l.7 "다중 비교는 보정하지 않았으므로 개별 구간이 0을 배제하더라도 가설 생성적 근거로만 해석한다." 본문 전체에서 "확인되었다/입증/유의하게/우수" 0건. S1 l.31 계열 정의(6개, Precision 제외 이유와 참고 CI). S1 l.33·42 Holm·BH가 검증자 재계산과 일치(Holm 최소 0.074, BH 0.0496).

### RM-09 LF-Eval 비독립성 명시 — **FULLY_ADDRESSED** (verified_by R1)
- 증거: 본문 l.45 "LF-Eval은 gold 조문의 사용을 채점 기준에 포함하므로 근거 회수 개선과 독립적인 증거가 아니다." 본문·요약에 "두 독립 증거/수렴" 서술 없음(요약 l.74는 "자동 답변 지표도 소폭 높아졌으나"로 병렬 서술만). S1 l.23 (a) `research/prompts/koblex_lf_eval.json`의 `criteria` 인용 — 파일 원문 "a score of 10 means the response correctly and thoroughly uses all of the given legal provisions"와 일치, (b) "생성기와 평가기는 모두 `gpt-4o-2024-08-06`이지만…두 조건에 대칭적으로 작용한다". 선택 요소 상관 0.53·분해는 재계산과 일치.

### RM-10 shortlist Recall CI와 그림 2 삭제 — **FULLY_ADDRESSED** (verified_by R1)
- 증거: 본문 l.25 "(CI [+2.61, +7.94]점)", "7.96%p 증가하였다(CI [+3.89, +12.38]%p)" — 검증자 독립 재계산과 일치, `shortlist-bootstrap.json` 메타데이터 clusters 151, repetitions 10000, seed 20261108, post_hoc true. S1 l.29 "결과를 관찰한 뒤 같은 코드…같은 그룹·반복 수·seed로 산출한 탐색적 구간". `analysis-spec.json`(l.21 "new_inference: none")과의 관계: 원본 보충자료의 "새로운…통계 검정을 추가하지 않는다"(원본 l.3), "신뢰구간을 추가 계산하지 않았다"(원본 l.107)를 지우고 수정본 l.3에 "수정 단계에서…추가 산출한 구간과 기술통계는 결과를 관찰한 뒤 계산한 탐색적 값"을 명시해 모순을 없앴다(파일명 미언급이나 실질 공개 — equivalence 인정). 원본 그림 2 삭제: 본문 그림 2개, 그림 1(l.13–15)·그림 2(l.66–68, 원 그림 3) 재번호, 본문 참조 "(그림 1)", "(그림 2)" 일치, PDF에 "그림 3" 0건. S8 l.207–209가 이동을 반영. 근사 구간 [+2.6, +8.0] 미사용.

### RM-11 개선 원천 한 문장 — **FULLY_ADDRESSED** (verified_by R2)
- 증거: 본문 l.27 "shortlist에 남은 gold 출현 중 최종 선택된 비율은 CE 79.52%(233/293), Jev 77.64%(250/322)로 비슷하였다. 따라서 Jev의 이득은 주로 재정렬 단계의 후보 유지에서 나타났고, shortlist 안의 선택 단계에서 추가 이득은 관찰되지 않았다." 분자·분모 독립 재계산 일치, 해석 방향(Jev ≤ CE)이 결과와 맞음. 그림 2 캡션 l.68 "미선택은 목록별 선택 수 제약의 영향도 받는다" 유지.

### RM-12 hop별 서술 근거 보강 — **FULLY_ADDRESSED** (verified_by R2)
- 증거: 본문 l.19 hop별 "(Jev 우세/동일/CE 우세 0/56/1문항)", "(20/95/12)", "(12/26/4)" — 독립 재계산 일치. "전체 차이는 주로 2·3-hop 문항에서 관측되었다." — 기여 비율 68.9%·40.3%가 지지. 새 subgroup CI 없음. S6 l.166–172 hop별 동시 선택 가능(3-hop 2/11)과 목록 수<gold 수(9)로 3-hop 1/42 맥락 설명, G4 출력 일치.

### RM-13 CE 입력 형식 진단 — **FULLY_ADDRESSED** (verified_by R2)
- 증거: 본문 l.5 "이 형식은 공식 코드의 재정렬 입력과 같고 진단에서 CE에 가장 유리했으며, Jev에도 같은 입력을 적용하였다." (세 요소). S1 l.17 진단 제외 196문항(139그룹) 민감도, 독립 재계산 일치. S4 l.91 "사례 A는 CE 입력 형식 진단에 쓰인 30문항에 포함되고, B와 C는 포함되지 않는다" — `ce-diagnostic-plan.json`과 일치. 공식 코드 대조: 업스트림 `selection_retrieval.py` l.31–34 `pairs = [(q, t) ...]`, `utils.py` l.154 `item['hierarchy'] + item['content']` — S1 서술과 일치. 사전 계획처럼 서술하지 않음("탐색적 진단", "미노출 시험이 아니다").

### RM-14 사례 C 중립화와 4.5 목적 문장 — **FULLY_ADDRESSED** (verified_by R2)
- 증거: l.72 "근거 F1은 40→0으로 낮아졌지만 Token F1은 18.60→25.88로 상승하여, 두 자동 지표가 서로 다른 측면을 반영하는 사례이다." (원본 l.81 "표현 중복의 증가가 더 나은 근거 선택을 보장하지 않음을 보여준다" 삭제). 단서 유지·강화: "Jev가 선택한 정답 외 조문의 법률적 적절성이나 실제 주장 지지 여부는 판정하지 않았다." l.64 첫머리 "4.2–4.4의 평균 차이가 어떤 문항 수준 변화로 구성되는지 보이기 위해". S4 l.99 조문명이 casebook과 일치.

### RM-15 용어·단위 정리 — **FULLY_ADDRESSED** (verified_by EIC)
- 증거: l.19 "데이터셋 hop 라벨별"(본문 "공식 hop" 0건). "시험" 본문 0건; l.5 "평가 문항 30개", l.7 "평가(test) 문항의 결과를 이미 관찰한 뒤 수행한 탐색적 분석". 그림 라벨 대응: 그림 1 캡션 "Complete coverage는 완전 회수", 그림 2 캡션 "Reranking loss는 shortlist 탈락, Selection loss는 미선택", S1 l.44–57 용어 대응표(점/%p 포함). 본문 "모든 gold 포함" 0건, "완전 회수"로 통일("모든 gold가 shortlist에 남은 문항"은 다른 개념). %p 단위 일관(l.25 "7.96%p").

### RM-16 재현 실행 조건 차이 표 — **FULLY_ADDRESSED** (verified_by R2)
- 증거: S5 l.109–122 표 8행(장치, 최대 길이, 입력·batch, 생성 모델, 생성 API, temperature·top_p·max_tokens, BM25, 참조 수정), 각 행에 확인 위치. 행별 대조(§1 마지막 행) 모두 일치. 로드맵 예시 "Chat Completions → Responses"와 달리 파일(`providers.py` l.393 `/chat/completions`, 저장 응답 `"object": "chat.completion"`)과 일치하는 "Chat Completions | Chat Completions"로 적고, 잠금 파일의 `api: responses` 기록과의 차이를 l.122에 공개 — Phase 1의 "파일이 로드맵 문구보다 우선" 조건 충족. 원 논문 절대 수치 없음.

### RM-17 자원 집계 범위 한정 — **FULLY_ADDRESSED** (verified_by R3)
- 증거: 본문 l.47 "답변 생성 단계 기준으로…따라서 생성 단계에서 입력량 절감은 관찰되지 않았고, LLM 선택 호출의 입력도 줄지 않았다(S6)." S6 l.137–143 선택 호출 행(호출 수, 호출당·문항당 입력, 출력)과 "각 조건의 예측 행에 저장된 선택 호출 기록의 사용량을 그대로 합산" — 검증자가 `predictions/*.jsonl` `selection_traces`에서 재계산해 일치. 휴리스틱 호출 분류 미사용. 비용 절감 함의 없음.

### RM-18 지연 표본 60문항 품질 차이 — **FULLY_ADDRESSED** (verified_by R1)
- 증거: S9 l.217 "같은 60문항에서 기존 품질 실행의 Jev−CE 차이는 근거 F1 +1.39점, LF-Eval +0.87점, Token F1 +0.47점이었다(기술통계…)" — 독립 재계산 일치. "본문은 226문항의 품질과 60문항의 지연을 하나의 비율로 결합하지 않는다." CI·p값 없음. 요약 l.74도 결합하지 않음.

---

## 4. P2 — consider 판정 (applied_criterion: not_precommitted; 결정 무관)

사용자 범위: "보충자료 추가 또는 길이 중립 문구만". 본문 변경은 아래 "범위" 열에 기록.

| RM | 판정 | 증거 | 범위 적합성 |
|---|---|---|---|
| RM-19 | FULLY_ADDRESSED | S9 l.223: 최솟값 0.60, 하위 10% 0.85, 35회/36회, 두 실행 시각, "호출 간 비결정성인지 시점 간 서비스 변화인지는 이 자료로 구분할 수 없다", "`raw.jsonl`에는 반복별 top-10 row ID 목록이 저장되어 있지 않아" — raw.jsonl 재계산 일치 | 보충 추가 + 본문 l.41 "(분포는 S9)" 참조 구절(약 7자) — 길이 사실상 중립 |
| RM-20 | FULLY_ADDRESSED | 표 1 l.37 "문항 평균의 제95백분위수"; S9 l.219 쌍당 지연, Apple M5 Pro(latency README l.11), 동시 요청 4 선정 이유, 양방향 이식성 | 표 행 라벨이 "제95백분위수"보다 6자 길어짐(로드맵이 지정한 문구 그대로, 행 수 증가 없음). 관찰만 |
| RM-21 | FULLY_ADDRESSED | 본문의 "약 0.61달러" 문장 삭제(RM-04 압축과 함께), S9 l.225 총액·문항당 0.0034·1,000쌍당 0.019달러 — 재계산 일치. GPT-4o 비교 없음 | 본문 감소(치환 대신 삭제 — 길이 감소 방향으로 범위 내) |
| RM-22 | FULLY_ADDRESSED | S6 l.162 미매핑 원인(27/26/25/0) — G4 출력 일치 | 보충만 |
| RM-23 | FULLY_ADDRESSED | S6 l.153–158 미선택 분해·순위 기술통계 — G4 출력 일치. 그림 재작성(D-11) 없음 | 보충만 |
| RM-24 | FULLY_ADDRESSED | S3 l.83 재사용 정의와 122/121/119/124/102의 관계 | 보충만 |
| RM-25 | FULLY_ADDRESSED | S1 l.25 캐시 재사용·재현성 미검증 명시; l.21 800자 초과 0개 | 보충만 |
| RM-26 | FULLY_ADDRESSED | S1 l.21 어절 단위 민감성 구절. 형태소 재계산(D-10) 없음 | 보충만 |
| RM-27 | CANNOT_VERIFY | S1 l.9에 Jev 관련성 지시문 원문(잠금 파일 `jev_instructions`와 일치). 수용 기준 "방법 장과 표현 일치"는 다른 장(T1) 미열람으로 확인 불가 | 보충 추가, 범위 내 |
| RM-28 | FULLY_ADDRESSED | 원본 l.52 "사용량 토큰은 Token F1의 공백 단위와 다르며" 삭제; 원본 l.32–33 빈 줄 정리; l.7 "151개 그룹 중 표본에 해당하는 52개"; l.39 "문항당 평균 5.64초" | 길이 미세 증가(수 자)·감소 혼재, 순감소 |
| RM-29 | CANNOT_VERIFY | 절 제목 변경 없음(l.9, l.23). 수용 기준 "팀 결정과 일치"의 T2 결정 기록이 입력에 없음 | 해당 없음 |
| RM-30 | FULLY_ADDRESSED | (b) 경로: S9 l.221 문항당 LLM 호출 구조와 `latency_ms`가 대기 시간을 포함해 참고치로 쓰지 않았다는 서술(`providers.py` 확인 내용과 일치). 본문 E2E 규모 추정 없음. (c) 9%는 본문이 아닌 S6 l.137 "생성 입력 중 문맥 비중 8.84%/9.31%" | 보충만 |

P2 범위 이탈: 없음(본문에 새 문장 추가 0건; 참조 구절·표 라벨·단위 표기만).

---

## 5. 공통 조건 G1–G6

| ID | 판정 | 근거 |
|---|---|---|
| G1 | 충족 (수치 불일치 0건) | §1 대조표의 새·변경 수치 전부 원자료 또는 G4 출력과 일치. 근사 구간·seat 산출값 미사용. 단, 로드맵이 요구한 "원고 수치와 1:1 대조표"는 허용 입력(G4 디렉터리 README는 키–RM 대응만 제공)에서 찾지 못했다. 위반 조건(불일치·미검증 수치)은 성립하지 않으므로 new issue로 올리지 않고, 이 문서 §1을 검증자 대조표로 남긴다. |
| G2 | 충족 | 수정본 본문·보충·tex·PDF 추출 텍스트에서 `사람|human|Human|인간|annotat|평가자|전문가|판정자|주석|라벨러|수작업|검수|변호사|법조인|review` 검색: 유일한 일치는 보충 l.209의 `preview.tex`(오탐). "사람 평가", "사람평가", "인간 평가", "annotator", "평가자" 0건. `human_review`·`human-review/` 언급 0건. 재계산 스크립트는 human-review 필드를 읽지 않는다고 명시(스크립트 l.13). 참고: 지연 표본의 출처는 `protocol.json`상 감사 파일의 `human_review_sample` 키이나, 원고는 이를 "hop별 층화 무작위로 미리 추출한 60문항"으로만 기술하여 G2와 충돌하지 않는다(원본과 같은 기술). |
| G3 | 충족 | 보충 l.3 "새로운 실험이나 모델 호출은 없다"; `revision-analysis.json` `api_calls: 0`, `network_calls: 0`; 스크립트 import에 네트워크·API 클라이언트 없음. 반복 Jev 실행·E2E 재측정·재생성 결과 없음. |
| G4 | 충족 | G4 README의 입력 35개 sha256을 현재 파일로 재계산 — 35/35 일치. `protocol-lock.json` sha256 `99d5c5cc…`(pipeline_state·Stage 2.5 기록과 일치), `analysis.json` `7609288f…` 일치. 원자료 수정 시각은 2026-11-09로 수정 작업(11-13) 이전. 새 산출물은 `chapter4-revision-v1/`에만 있음. (`results/`는 git 비추적이라 git diff로는 확인 불가 — 해시 대조로 대신함) |
| G5 | 충족 | `output/pdf/chapter4-final.pdf` 3쪽(`mdls` 3, pypdf 3, 로그 "Output written…(3 pages)"); `preview.tex` 10pt·a4paper·twocolumn·margin=20mm; 로그 Overfull 0, Warning 0, 미정의 참조 0; PDF 텍스트 "??" 0, "그림 3" 0; 그림 1·2, 표 1·2 번호와 본문 참조 일치. PDF·tex는 같은 시각(11-13 20:15) 생성, tex 내용이 md와 일치. |
| G6 | 충족 | 새 구간(shortlist 2, Precision 1, 진단 제외 3)은 잠금 함수·151그룹(부분 표본은 그 부분집합 139그룹)·10,000회·seed 20261108 사용 — 검증자 재계산으로 확인. S1 l.29에 "결과를 관찰한 뒤…같은 그룹·반복 수·seed로 산출한 탐색적 구간" 명시, 본문 l.25에도 "결과 관찰 후 같은 절차로 추가 산출". 기존 보고 CI 교체 없음(MC 다른 seed는 민감도 참고로만, "보고 구간은 잠금 seed의 값을 유지"). |

---

## 6. 범위 밖 내용(§1.2) 유입 점검

| 경계 | 결과 |
|---|---|
| D-01 원 논문 수치·결함 추론 | 없음. 본문 l.21·S2 l.75 유보 유지, S5 l.107 "기존 성능표를 전재한 것이 아니라" |
| D-05 잠금 CI 교체 | 없음 |
| D-06 본문 E2E 규모 추정 | 없음("임계 경로", "1.5–2배" 0건; S9 l.221은 LLM 단계 지연 참고치 사용을 명시적으로 거부) |
| D-07 GPT-4o 비용 비교 | 없음 |
| D-15 shortlist 축소 레버 함의 | 없음 |
| D-17/G2 사람 평가 | 없음 |
| D-02·03·04·16 유료 작업 수행 결과 | 없음 |
| 주장 상한(우수·multi-hop 유리·효율·비용 절감) | 0건 |

---

## 7. New-issue 기록 (Phase 2A 종료 시 동결)

**regression / previously_missed / indeterminate 귀속 new issue: 0건.**

검토했으나 new issue로 올리지 않은 관찰(결정 무관, 다음 라운드 참고):
- OBS-1 (표현): 요약 l.74 "그 일부가 평균 근거 F1 3.19점 상승으로 이어졌다"는 shortlist 유지 → 최종 F1의 경로를 서술하는 해석 문장이다. 조건부 선택률(l.27)이 방향을 지지하고 주장 상한을 넘지 않아 이슈로 보지 않았다.
- OBS-2 (표기): S1 l.33 표에서 BH 값 0.0496이 셋째 자리 반올림으로 "0.050"으로 표시된다. 바로 아래 l.42가 0.0496을 밝히므로 오독 위험은 낮다.
- OBS-3 (출처 표기): S9 l.219 "Apple M5 Pro"는 `results/koblex-latency-v1/README.md` l.11에 근거하나 S9 첫 문장의 출처 목록에는 README가 없다. 로드맵 RM-20이 README를 데이터 출처로 지정했으므로 결함으로 보지 않았다.
- OBS-4 (서술 강도): S1 l.23 "평가기의 선호가 있다면 두 조건에 대칭적으로 작용한다"는 로드맵 RM-09가 요구한 문장이다. 생성 답변의 내용 차이와 평가기 선호의 상호작용 가능성까지 배제하는 것은 아니므로, 후속 라운드에서 "대칭적으로 작용할 것으로 본다" 수준의 완화를 고려할 수 있다.
- OBS-5 (G1 절차): 원고 수치 ↔ 재계산 출력의 1:1 대조표가 허용 입력에서 확인되지 않았다(§5 G1). 수치 자체는 모두 일치.

---

## 8. 판정 집계

| 우선순위 | 항목 수 | FULLY_ADDRESSED | PARTIALLY_ADDRESSED | NOT_ADDRESSED | MADE_WORSE | CANNOT_VERIFY |
|---|---|---|---|---|---|---|
| P0 (must_fix) | 2 | 2 (RM-01, RM-02) | 0 | 0 | 0 | 0 |
| P1 (should_fix) | 16 | 15 | 1 (RM-05, residual consider) | 0 | 0 | 0 |
| P2 (consider) | 12 | 10 | 0 | 0 | 0 | 2 (RM-27, RM-29) |

- should_fix 중 FULLY 또는 PARTIALLY: 16/16 (Phase 2B의 rate 계산 입력용 사실 기록이며, 결정 도출은 하지 않는다).
- Dissent 0건, escalation exception 0건, new issue 0건.

[EVIDENCE-COMMITTED]
