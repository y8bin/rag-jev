# 제4장 본문 수치 대조표 (manuscript ↔ 저장 출력)

- 대상 원고: `research/chapter4/chapter4.md` (Stage 4.5 축약본, sha256 `81054480b237cbb48e8f1786153cb5de798ffb3bee833946d2f6cba75bfc05cc`)
- 범위: 본문(표 1·2, 그림 2 막대 라벨 포함)에 나오는 모든 수치. 모델·데이터 식별자(`jev-1.14.0`, `gpt-4o-2024-08-06`, `dragonkue/bge-reranker-v2-m3-ko`)는 `results/koblex-reproduction-v1/protocol-lock.json`과 `results/koblex-latency-v1/protocol.json`의 식별 필드에 해당하며 수치 행에서 제외했다. 보충자료 수치는 `research/chapter4/pipeline/stage4_delta_report.md` §4를 참조한다.
- 검증 방법: 각 행의 JSON 값을 읽기 전용 Python으로 다시 읽어 원고 표기(소수 둘째 자리 반올림, 0–1 저장값은 ×100)와 일치하는지, 그리고 그 표기가 해당 절 본문에 실제로 있는지 assert로 확인했다(107행 모두 통과). 새 계산·API 호출은 없다. 이 파일 외의 `results/**` 파일은 수정하지 않았다.
- 차이값은 표의 값끼리 뺀 값이 아니라 저장된 차이(`analysis.json` `comparisons[].mean_difference`, `revision-analysis.json`의 `estimate`)를 쓴다. 예: Token F1 차이는 저장값 0.011176 → +1.12점이며, 표 2의 47.31−46.20=1.11과 반올림 때문에 다르다.
- `comparisons[metric=m]`은 별도 표기가 없으면 treatment `parser_jev_fixed`, control `parser_ce_fixed` 항목이다. `Σ_hop`은 `RM12_hop`의 1·2·3 값을 더한 것이다.

| # | 위치 | 원고 표기 | 출처 파일 | JSON 키/경로 | 저장값 | 비고 |
|---|---|---|---|---|---|---|
| 1 | 4.1 | 226문항 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[*].questions` | 226 |  |
| 2 | 4.1 | 후보 100개 | `results/koblex-reproduction-v1/protocol-lock.json` | `signature.retriever` | k=100 per parametric provision |  |
| 3 | 4.1 | 상위 10개 | `results/koblex-reproduction-v1/protocol-lock.json` | `signature.top_n_before_llm_selection` | 10 |  |
| 4 | 4.1 | 총 478개 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM17_RM30_usage.parser_ce_fixed.selection_calls / parser_jev_fixed.selection_calls` | 478 / 478 | 목록당 선택 호출 1회 |
| 5 | 4.1 | 평가 문항 30개 | `results/koblex-reproduction-v1/ce-diagnostic-plan.json` | `len(sample_ids)` | 30 |  |
| 6 | 4.1 | 네 형식 | `results/koblex-reproduction-v1/ce-diagnostic-plan.json` | `variants` | ["stored_json_background", "plain_question_plain_law", "plain_background_plain_law", "plain_question_json_law"] |  |
| 7 | 4.1 | 151개 그룹 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[*].clusters` | 151 |  |
| 8 | 4.1 | 10,000회 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[*].repetitions` | 10000 |  |
| 9 | 4.1 | 95% 신뢰구간 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[*].ci95` | percentile 95% | S1 정의 |
| 10 | 4.1 | 0–100 척도 | `results/koblex-reproduction-v1/analysis.json` | `summaries.*` | 0–1 저장값 ×100 | 표기 규칙 |
| 11 | 4.1 | 60문항 | `results/koblex-latency-v1/summary.json` | `questions_complete` | 60 |  |
| 12 | 4.1 | 15/34/11 | `results/koblex-latency-v1/protocol.json` | `sample.hop_counts` | {"1": 15, "2": 34, "3": 11} |  |
| 13 | 4.1 | 52개 | `results/koblex-latency-v1/summary.json` | `jev_minus_ce_ms.clusters` | 52 |  |
| 14 | 4.2 | 3.19점 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=f1, jev_fixed−ce_fixed].mean_difference` | 0.03187947745469869 |  |
| 15 | 4.2 | [+0.75, +5.68] | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=f1].ci95` | [0.007468999659813845, 0.056762380952380946] |  |
| 16 | 4.2 | 2.95점 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=recall, jev_fixed−ce_fixed].mean_difference` | 0.029498525073746312 |  |
| 17 | 4.2 | [+0.39, +5.51] | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=recall].ci95` | [0.003911906015532446, 0.055067115484818324] |  |
| 18 | 4.2 | 27.88% | `results/koblex-reproduction-v1/analysis.json` | `summaries.parser_ce_fixed.retrieval.em` | 0.27876106194690264 |  |
| 19 | 4.2 | 29.65% | `results/koblex-reproduction-v1/analysis.json` | `summaries.parser_jev_fixed.retrieval.em` | 0.29646017699115046 |  |
| 20 | 4.2 | 34.07% | `results/koblex-reproduction-v1/analysis.json` | `summaries.parser_ce_fixed.retrieval.gold_set_coverage` | 0.3407079646017699 |  |
| 21 | 4.2 | 34.96% | `results/koblex-reproduction-v1/analysis.json` | `summaries.parser_jev_fixed.retrieval.gold_set_coverage` | 0.3495575221238938 |  |
| 22 | 4.2 | CI는 0을 포함 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=em / gold_set_coverage].ci95` | [-0.017699115044247787, 0.05188679245283019] / [-0.028985507246376812, 0.04526748971193416] | 0 포함 확인 |
| 23 | 4.2 | 우세 32개 | `results/koblex-reproduction-v1/chapter4-prep-v1/A3/win-tie-loss.json` | `counts.f1.Jev_higher` | 32 |  |
| 24 | 4.2 | 동일 177개 | `results/koblex-reproduction-v1/chapter4-prep-v1/A3/win-tie-loss.json` | `counts.f1.tie` | 177 |  |
| 25 | 4.2 | CE 우세 17개 | `results/koblex-reproduction-v1/chapter4-prep-v1/A3/win-tie-loss.json` | `counts.f1.CE_higher` | 17 |  |
| 26 | 4.2 | 78.07→76.90 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM12_hop.1.f1_points` | 78.0701754385965 → 76.90058479532165 |  |
| 27 | 4.2 | 0/56/1 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM12_hop.1.f1_win_tie_loss_jev_tie_ce` | [0, 56, 1] |  |
| 28 | 4.2 | 53.33→57.24 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM12_hop.2.f1_points` | 53.333333333333336 → 57.24409448818899 |  |
| 29 | 4.2 | 20/95/12 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM12_hop.2.f1_win_tie_loss_jev_tie_ce` | [20, 95, 12] |  |
| 30 | 4.2 | 47.91→54.83 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM12_hop.3.f1_points` | 47.91383219954648 → 54.82993197278911 |  |
| 31 | 4.2 | 12/26/4 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM12_hop.3.f1_win_tie_loss_jev_tie_ce` | [12, 26, 4] |  |
| 32 | 4.2 | 386개 | `results/koblex-reproduction-v1/chapter4-prep-v1/A4/denominators.json` | `unique_gold_global` | 386 |  |
| 33 | 4.2 | 27개(29문항) | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM22_unmapped_gold.unique_unmapped_gold / affected_questions` | 27 / 29 |  |
| 34 | 4.2 | 48.72점 | `results/koblex-reproduction-v1/analysis.json` | `summaries.parser_ce_raw.retrieval.f1` | 0.4871681415929203 |  |
| 35 | 4.2 | 9.85점 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=f1, ce_fixed−ce_raw].mean_difference` | 0.09848293299620733 |  |
| 36 | 4.3 | 5.16점 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM10_shortlist.shortlist_recall_diff.estimate` | 5.162241887905605 |  |
| 37 | 4.3 | [+2.61, +7.94] | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM10_shortlist.shortlist_recall_diff.ci95` | [2.608681823210532, 7.943925233644859] |  |
| 38 | 4.3 | CE 69.47점 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM10_shortlist.shortlist_recall_points.parser_ce_fixed` | 69.46902654867256 |  |
| 39 | 4.3 | Jev 74.63점 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM10_shortlist.shortlist_recall_points.parser_jev_fixed` | 74.63126843657818 |  |
| 40 | 4.3 | 112개(49.56%) | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM10_shortlist.all_gold_in_shortlist_questions.parser_ce_fixed` | 112 (/226 = 49.5575%) |  |
| 41 | 4.3 | 130개(57.52%) | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM10_shortlist.all_gold_in_shortlist_questions.parser_jev_fixed` | 130 (/226 = 57.5221%) |  |
| 42 | 4.3 | 7.96%p | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM10_shortlist.all_gold_in_shortlist_diff_pctpoints.estimate` | 7.964601769911504 |  |
| 43 | 4.3 | [+3.89, +12.38] | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM10_shortlist.all_gold_in_shortlist_diff_pctpoints.ci95` | [3.886840028817455, 12.376237623762377] |  |
| 44 | 4.3 | CE 104개, Jev 120개 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `Σ_hop RM12_hop.*.shortlist_jointly_selectable` | 104 / 120 | hop 1·2·3 합 |
| 45 | 4.3 | 77개와 79개 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `Σ_hop RM12_hop.*.complete_coverage` | 77 / 79 | = analysis.json gold_set_coverage × 226 |
| 46 | 4.3 | 79.52%(233/293) | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM11_conditional_selection.parser_ce_fixed.{conditional_selection_rate_pct, selected_occurrences, shortlist_occurrences}` | 79.5221843003413 (233/293) |  |
| 47 | 4.3 | 77.64%(250/322) | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM11_conditional_selection.parser_jev_fixed.{…}` | 77.63975155279503 (250/322) |  |
| 48 | 4.3 | 3회 | `results/koblex-latency-v1/protocol.json` | `repetitions` | 3 |  |
| 49 | 4.3 | float32 | `results/koblex-latency-v1/protocol.json` | `ce.dtype` | float32 |  |
| 50 | 4.3 | 배치 50 | `results/koblex-latency-v1/protocol.json` | `ce.batch_size` | 50 |  |
| 51 | 4.3 | 동시 요청 4개 | `results/koblex-latency-v1/protocol.json` | `jev.concurrency` | 4 |  |
| 52 | 4.3 표 1 | 5.01 / 10.65 | `results/koblex-latency-v1/summary.json` | `per_question_ms.{ce,jev}.mean` | 5008.971 / 10649.732 ms | ÷1000, 초 |
| 53 | 4.3 표 1 | 4.82 / 10.79 | `results/koblex-latency-v1/summary.json` | `per_question_ms.{ce,jev}.median` | 4816.848 / 10794.557 ms | ÷1000, 초 |
| 54 | 4.3 표 1 | 8.87 / 16.53 | `results/koblex-latency-v1/summary.json` | `per_question_ms.{ce,jev}.p95` | 8870.050 / 16527.198 ms | ÷1000, 초 |
| 55 | 4.3 | 5.64초 | `results/koblex-latency-v1/summary.json` | `jev_minus_ce_ms.mean_difference` | 5640.760 ms |  |
| 56 | 4.3 | [+5.15, +6.17] | `results/koblex-latency-v1/summary.json` | `jev_minus_ce_ms.ci95` | [5148.543, 6165.854] ms |  |
| 57 | 4.3 | 2.25배(CI [2.11, 2.39]) | `results/koblex-latency-v1/summary.json` | `jev_over_ce_geometric_mean_ratio.{estimate, ci95}` | 2.2523 [2.1056, 2.3948] |  |
| 58 | 4.3 | 약 2.25배 | `results/koblex-latency-v1/summary.json` | `jev_over_ce_geometric_mean_ratio.estimate` | 2.2523 | 첫 문장 |
| 59 | 4.3 | CE 100%(180/180회) | `results/koblex-latency-v1/summary.json` | `repeatability.ce.top10_identical_to_quality_run_fraction` | 1.0 | 180 = 60문항×3회 |
| 60 | 4.3 | Jev 1.11%(2/180회) | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM19_overlap_and_dates.{runs_identical_order, jev_measured_runs}; latency summary.json repeatability.jev.top10_identical_to_quality_run_fraction` | 2/180; 0.011111111111111112 |  |
| 61 | 4.3 | 91.51% | `results/koblex-latency-v1/summary.json` | `repeatability.jev.top10_set_overlap_mean` | 0.9150925925925928 |  |
| 62 | 4.4 | 1.12점 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=token_f1, jev_fixed−ce_fixed].mean_difference` | 0.011176106194690267 | 저장 차이값(표 2 값의 차 47.31−46.20=1.11과 반올림 차) |
| 63 | 4.4 | [+0.02, +2.27] | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=token_f1].ci95` | [0.0001788458869082441, 0.022736642223011357] |  |
| 64 | 4.4 | 2.58점 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=lf_eval, jev_fixed−ce_fixed].mean_difference` | 0.025814149936426917 | 저장 차이값 |
| 65 | 4.4 | [+0.37, +4.79] | `results/koblex-reproduction-v1/analysis.json` | `comparisons[metric=lf_eval].ci95` | [0.003745512942064026, 0.04791551001249569] |  |
| 66 | 4.4 | 203.67토큰 | `results/koblex-reproduction-v1/chapter4-prep-v1/A5/descriptive-statistics.jsonl` | `arm=parser_ce_fixed, variable=context_tokens .mean` | 203.66814159292036 |  |
| 67 | 4.4 | 215.60토큰 | `results/koblex-reproduction-v1/chapter4-prep-v1/A5/descriptive-statistics.jsonl` | `arm=parser_jev_fixed, variable=context_tokens .mean` | 215.59734513274336 |  |
| 68 | 4.4 | 2302.67토큰 | `results/koblex-reproduction-v1/chapter4-prep-v1/A5/descriptive-statistics.jsonl` | `arm=parser_ce_fixed, variable=api_input_tokens .mean` | 2302.66814159292 |  |
| 69 | 4.4 | 2314.58토큰 | `results/koblex-reproduction-v1/chapter4-prep-v1/A5/descriptive-statistics.jsonl` | `arm=parser_jev_fixed, variable=api_input_tokens .mean` | 2314.5840707964603 |  |
| 70 | 4.4 | 중앙값은 0 | `results/koblex-reproduction-v1/chapter4-prep-v1/A5/descriptive-statistics.jsonl` | `arm="Jev minus CE (paired)", variable=context_tokens .median` | 0.0 |  |
| 71 | 4.4 | 478개이므로 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM17_RM30_usage.*.selection_calls` | 478 |  |
| 72 | 4.4 | 151개 의존 그룹 | `results/koblex-reproduction-v1/analysis.json` | `comparisons[*].clusters` | 151 |  |
| 73 | 4.4 | 5-fold | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.rule.folds` | 5 |  |
| 74 | 4.4 | 1점 이내 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.rule.tolerance_f1_points` | 1.0 |  |
| 75 | 4.4 | CE 10개, Jev 45개 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.regenerated_answers` | {"ce": 10, "jev": 45} |  |
| 76 | 4.4 표 2 | CE / 478 / 58.57 / 63.46 / 57.74 / 34.07 / 46.20 / 67.57 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.kept_items + means_points.ce_r.{f1,precision,recall,gold_set_coverage,token_f1,lf_eval}` | 58.5651 / 63.4587 / 57.7434 / 34.0708 / 46.1954 / 67.5712 | 유지 근거 478 = 선택 목록 수 |
| 77 | 4.4 표 2 | CE+필터링 / 467 / 58.54 / 64.56 / 57.15 / 33.19 / 45.65 / 67.13 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.kept_items + means_points.ce_fr.{f1,precision,recall,gold_set_coverage,token_f1,lf_eval}` | 58.5356 / 64.5649 / 57.1534 / 33.1858 / 45.6540 / 67.1275 | 유지 근거 478 = 선택 목록 수 |
| 78 | 4.4 표 2 | Jev / 478 / 61.75 / 66.85 / 60.69 / 34.96 / 47.31 / 70.15 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.kept_items + means_points.jev_r.{f1,precision,recall,gold_set_coverage,token_f1,lf_eval}` | 61.7531 / 66.8510 / 60.6932 / 34.9558 / 47.3130 / 70.1526 | 유지 근거 478 = 선택 목록 수 |
| 79 | 4.4 표 2 | Jev+필터링 / 426 / 61.43 / 69.80 / 58.26 / 33.19 / 47.03 / 69.13 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.kept_items + means_points.jev_fr.{f1,precision,recall,gold_set_coverage,token_f1,lf_eval}` | 61.4286 / 69.8009 / 58.2596 / 33.1858 / 47.0293 / 69.1284 | 유지 근거 478 = 선택 목록 수 |
| 80 | 4.4 | 89.12% | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.kept_items.jev / 478` | 426/478 = 89.1213% |  |
| 81 | 4.4 | 97.70% | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.kept_items.ce / 478` | 467/478 = 97.6987% |  |
| 82 | 4.4 | −0.32점 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.f1.estimate` | -0.32448377581120935 |  |
| 83 | 4.4 | [−1.76, +1.07] | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.f1.ci95` | [-1.755986625821877, 1.065989847715736] |  |
| 84 | 4.4 | 2.95점 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.precision.estimate` | 2.949852507374632 |  |
| 85 | 4.4 | [+1.05, +5.01] | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.precision.ci95` | [1.0463171335749233, 5.007473841554559] |  |
| 86 | 4.4 | 2.43점 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.recall.estimate` | -2.433628318584071 | 부호는 문장의 "낮아졌다"로 표현 |
| 87 | 4.4 | [−3.81, −1.16] | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.recall.ci95` | [-3.807522577996715, -1.157350110011002] |  |
| 88 | 4.4 | 1.77%p | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.gold_set_coverage.estimate` | -1.7699115044247788 | 부호는 문장의 "낮아졌다"로 표현 |
| 89 | 4.4 | [−3.51, −0.43] | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.gold_set_coverage.ci95` | [-3.508771929824561, -0.43478260869565216] |  |
| 90 | 4.4 | −0.28점 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.token_f1.estimate` | -0.283716814159292 |  |
| 91 | 4.4 | [−1.10, +0.44] | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.token_f1.ci95` | [-1.100104601887484, 0.44312976190476183] |  |
| 92 | 4.4 | −1.02점 | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.lf_eval.estimate` | -1.0241747092334708 |  |
| 93 | 4.4 | [−2.23, +0.15] | `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json` | `RM01_RM04_filtering.jev_fr_minus_jev_r.lf_eval.ci95` | [-2.227935721621337, 0.14577481356033056] |  |
| 94 | 4.5 | 443건 | `results/koblex-reproduction-v1/chapter4-prep-v1/A4/denominators.json` | `gold_occurrences_per_arm` | 443 |  |
| 95 | 4.5 | CE 42건에서 Jev 13건 | `results/koblex-reproduction-v1/chapter4-prep-v1/A4/denominators.json` | `first_loss_counts.{parser_ce_fixed,parser_jev_fixed}.shortlist_absent` | 42 / 13 |  |
| 96 | 4.5 | 60건에서 72건 | `results/koblex-reproduction-v1/chapter4-prep-v1/A4/denominators.json` | `first_loss_counts.*.shortlist_present_unselected` | 60 / 72 |  |
| 97 | 4.5 | 두 조건에 공통 | `results/koblex-reproduction-v1/chapter4-prep-v1/A4/denominators.json` | `first_loss_counts.*.{corpus_absent,bm25_absent}` | 33/75 (양 조건 동일) | 수치는 그림 2 |
| 98 | 4.5 그림 2 | 33/75/42·13/60·72/233·250 | `results/koblex-reproduction-v1/chapter4-prep-v1/A4/denominators.json` | `first_loss_counts` | parser_ce_fixed: {"bm25_absent": 75, "selected": 233, "corpus_absent": 33, "shortlist_present_unselected": 60, "shortlist_absent": 42}; parser_jev_fixed: {"bm25_absent": 75, "selected": 250, "corpus_absent": 33, "shortlist_present_unselected": 72, "shortlist_absent": 13} | 그림 막대 라벨 |
| 99 | 4.5 | 50→100 | `results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl` | `query_id=qa_124_2hop_480_rand .paired_metrics.{ce,jev}.f1` | 0.5000 → 1.0000 |  |
| 100 | 4.5 | 65.29→99.18 | `results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl` | `query_id=qa_124_2hop_480_rand .paired_metrics.{ce,jev}.lf_eval` | 0.6529 → 0.9918 |  |
| 101 | 4.5 | 80→40 | `results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl` | `query_id=qa_324_2hop_515 .paired_metrics.{ce,jev}.f1` | 0.8000 → 0.4000 |  |
| 102 | 4.5 | 71.79→52.67 | `results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl` | `query_id=qa_324_2hop_515 .paired_metrics.{ce,jev}.lf_eval` | 0.7179 → 0.5267 |  |
| 103 | 4.5 | 40→0 | `results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl` | `query_id=qa_443_3hop_703 .paired_metrics.{ce,jev}.f1` | 0.4000 → 0.0000 |  |
| 104 | 4.5 | 18.60→25.88 | `results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl` | `query_id=qa_443_3hop_703 .paired_metrics.{ce,jev}.token_f1` | 0.1860 → 0.2588 |  |
| 105 | 4.5 | gold 3개에 후보 목록이 2개 | `results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl` | `query_id=qa_443_3hop_703 .stages.parser_ce_fixed.{n_gold,n_pools}` | 3 / 2 |  |
| 106 | 4.5 | 제42조제2항·제45조제1항, 제79조제1항·제83조제1항 | `results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl` | `query_id=… .conditions.parser_jev_fixed.provisions / gold_provisions` | 조문 문자열 접두 일치 확인 | 조문 식별자 |
| 107 | 4.5 종합 | 3.19점 / 2.25배 / 9.85점 / 226·60문항 | `(위 4.2·4.3·4.1 행과 동일)` | `—` | — | 새 수치 없음 |
