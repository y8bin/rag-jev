# 제4장 Stage 4 수정 재계산 (chapter4-revision-v1) — 2026-11-13

상태: **결과 관찰 후(post hoc) 탐색적 재계산. 모델·API·네트워크 호출 0건.** 기존 파일은 읽기만 했다(수정 전후 `results/**`, `data/koblex/prepared-v1/**`, `configs/**`, `scripts/experiment/**` sha256 변화 0건).

코드: `scripts/chapter4_revision_analysis.py` (sha256 `3c7f231421bebf5859d90d3db5fd5174240824f37fa64828467c50cf298459db`). 저장소 루트에서 `.venv/bin/python scripts/chapter4_revision_analysis.py`로 실행한다. 실행할 때마다 이 디렉터리의 JSON을 다시 쓴다(`revision-analysis.json`에는 생성 시각이 들어 있어 해시가 실행마다 달라진다. 수치는 결정적이다).

## 절차

- 구간은 모두 잠금 절차 `legal_rag_jev.koblex_analysis.paired_bootstrap`을 수정 없이 import해 산출했다(151개 source/gold 그룹 `research/koblex_source_audit_20261108.json`, 10,000회, seed 20261108, numpy quantile [.025, .975] percentile). 부분 표본(진단 30문항 제외 196문항)은 해당 문항의 그룹(139개)만 사용한다.
- 새 구간을 계산하기 전에 같은 코드로 `analysis.json`의 저장 구간 12개(Jev−CE, 수정 CE−공개 코드 CE × 6지표)를 평균·CI·p까지 비트 단위로, 필터링 `e2e-summary.json`의 14개(각 조건 내 필터링 차이 × 7지표)를 1e-9 이내로 재현했다(`revision-analysis.json` → `verification`, 26/26 일치). 하나라도 불일치하면 스크립트는 중단한다.
- 사람 평가 관련 필드·디렉터리는 읽지 않는다.

## 출력

| 파일 | 내용 |
| --- | --- |
| `revision-analysis.json` | 전체 재계산 값. 키: `verification`(26개 재현), `RM01_RM04_filtering`(필터링 저장값 재추출 및 e2e 행에서의 재계산), `RM10_shortlist`, `RM11_conditional_selection`, `RM23_unselected_decomposition`, `RM12_hop`, `RM13_diagnostic_exclusion`, `RM07_RM08_multiplicity`(저장 p, Holm, BH, Precision CI, Token F1 하한 Monte Carlo 민감도 seed 20261109–20261128), `RM09_RM24_lf_and_reuse`(ΔF1–ΔLF 상관, 선택 변화 유형별 LF 기여, 재사용 정의별 문항 수), `RM25_judge_and_clip`, `RM17_RM30_usage`(선택·생성 단계 사용량, 호출 지연 측정 의미), `RM18_latency_sample_quality`, `RM19_overlap_and_dates`, `RM20_RM21_latency_units`, `RM22_unmapped_gold`, `inputs_sha256` |
| `shortlist-bootstrap.json` | RM-10: shortlist 합집합 gold Recall 차이와 모든 gold가 shortlist에 남은 문항 비율 차이의 대응 구간(사후 산출) |

## 입력과 sha256

| 입력 | sha256 |
| --- | --- |
| `data/koblex/downloads/statute.jsonl` | `0f50fdfe4d7dbad388235deb338b016634ec3e51b3d760cb81e3b5f525f4b053` |
| `data/koblex/prepared-v1/gold.jsonl` | `d0f7214a9d2e33c7367d687003d68a3f360b094a035b70ffcfb41254d4ece12b` |
| `research/koblex_source_audit_20261108.json` | `089fbac95d45493a852a5fbb978e97eb9cfb47a8a607edad9729a2cdae211dcb` |
| `research/prompts/koblex_lf_eval.json` | `95bf7c61c635079c766a3bbdfc383e4adb40e3661c0df2e706b15a164c9da86a` |
| `results/koblex-filtering-v1/e2e-summary.json` | `0d5c72a97a9f2b7a661a935a3679b6c920a2fd96d9b24b950fb2a1ea7df8bba8` |
| `results/koblex-filtering-v1/e2e/lf-eval/ce_fr/metrics.jsonl` | `e0d7f82b55a89a52b9b1ced98624d62161efdb4ebf8a388852c58736d8e6fdc2` |
| `results/koblex-filtering-v1/e2e/lf-eval/jev_fr/metrics.jsonl` | `7e11b14cb10fcb227673d56c4bb6e37b935147b28e8759c86d41375db6b339c6` |
| `results/koblex-filtering-v1/e2e/metrics/ce_fr/metrics.jsonl` | `0433cfc89a80c0f8bfdb07f033bb78e5088dac96dd51ad5dd23844997f2c2244` |
| `results/koblex-filtering-v1/e2e/metrics/jev_fr/metrics.jsonl` | `2b2abd255b4ecce26b96be011d7dbe5a036ad3b6fb33f2ac506bf73d7fd0fb58` |
| `results/koblex-filtering-v1/summary.json` | `9f474388b12b7b47c00b74faa8b9f7597f359aefb91031b850fde1af8fa51623` |
| `results/koblex-latency-v1/completed.json` | `ba63a4622b833628699725a1fa6899b827483789f79977d2174e4e5f164302bd` |
| `results/koblex-latency-v1/protocol.json` | `7928eb6ca20e98f5dbba04592bc3d58a104acbe7e72378ff82853058e7a7c724` |
| `results/koblex-latency-v1/raw.jsonl` | `7d62b9f954b8f53ea39a960956d1d7e401d856eaeafdfe3acfe40324f091da08` |
| `results/koblex-latency-v1/summary.json` | `450782b06fe9da432ca17d2432e4ed78ba6d8c78f3ace27e2815fe4beaad6610` |
| `results/koblex-reproduction-v1/analysis.json` | `7609288f45915e64bc86c1041f2a526603fa2a8094e900b55110d65153cdf176` |
| `results/koblex-reproduction-v1/ce-diagnostic-plan.json` | `3a3133fd7572ca1afc0d8071db9a5b3347a06f1b1d94dc105f8b240b8f6e4c64` |
| `results/koblex-reproduction-v1/ce-diagnostic-summary.json` | `aa875ef43e63cfb28dba0beafe6bb0949d8fdcf9fd7597fa3d67bc932694cec1` |
| `results/koblex-reproduction-v1/chapter4-prep-v1/A1/question-metrics.jsonl` | `dc1ab66e6094137b2bcfabb35759927541651946b2bb0313036e72b33bab079d` |
| `results/koblex-reproduction-v1/chapter4-prep-v1/A4/gold-occurrences.jsonl` | `3e2a17d2e760f1bffefb4755a4c782aea4277f121327bf055b46d635d730727b` |
| `results/koblex-reproduction-v1/chapter4-prep-v1/A4/pool-constraints.jsonl` | `00040fb86c3b63d791bfdf486813297b1fc900c8e2dd9e8990d5ece718fc57e5` |
| `results/koblex-reproduction-v1/chapter4-prep-v1/A4/question-stages.jsonl` | `04255bf554b7961f3242e04d8d114d2366be4c36abc891e95f77165ae1f8c742` |
| `results/koblex-reproduction-v1/chapter4-prep-v1/A5/question-resources.jsonl` | `678ef0b0f447416ea0ffb70029b1eb97ecaa3b4b4115a91c8ba59054ca8b74a4` |
| `results/koblex-reproduction-v1/identical-answer-judge-audit.json` | `caf8b9c9a5d5b7b309a9b750efc183f6b03f7a3a08c804ab46cded9f5a816a71` |
| `results/koblex-reproduction-v1/lf-eval/parser_ce_fixed/metrics.jsonl` | `a799618d5507299b3098229111ed9d44e3b46009e3cca1b20c4f4899deb1c5b7` |
| `results/koblex-reproduction-v1/lf-eval/parser_ce_raw/metrics.jsonl` | `2f39319bd1a7f5585ee67530926c1357809595a38b0c2e80df44ae621064042e` |
| `results/koblex-reproduction-v1/lf-eval/parser_jev_fixed/metrics.jsonl` | `04673764b7c9098a39cdfd74d782a5cfeeae6bc858abdb466f7500d93f4d0d62` |
| `results/koblex-reproduction-v1/metrics/parser_ce_fixed/metrics.jsonl` | `2181b146d9b5dadaedd4ed7ca805023eeeeaf1b0f67665ddde510c7ed3e2acd3` |
| `results/koblex-reproduction-v1/metrics/parser_ce_raw/metrics.jsonl` | `7213e85f6977a38ad8b69aea3be6851583eabd9836d85c2ac71616d78b8393d0` |
| `results/koblex-reproduction-v1/metrics/parser_jev_fixed/metrics.jsonl` | `26dd900d60e8655c2fba40504952302bb5d34af7d2aba1cddecf16be73586082` |
| `results/koblex-reproduction-v1/parametric.jsonl` | `f95dbe57e9c4fad24685a486f65caa764614caad28bbe5016b952a07b6b260cc` |
| `results/koblex-reproduction-v1/predictions/parser_ce_fixed.jsonl` | `e4981ae96b4cfbfae75e02f06d8225607faa477b7d3fb4d825ddf48a4a018e63` |
| `results/koblex-reproduction-v1/predictions/parser_ce_raw.jsonl` | `fc2821e5c20ce06d0d6d625e63f154f54db67f6fe47cf467932c2d0333eb47d7` |
| `results/koblex-reproduction-v1/predictions/parser_jev_fixed.jsonl` | `91753fd5a3ecbf0864d162a2c0db18aedac2e81c0f6e54c4eab7eea9d2c28db2` |
| `results/koblex-reproduction-v1/runtime-settings.json` | `375b216e60bcdbbe29dab2bb42fcd911468cae74f1628d1d5f3dbe3b3a35f58c` |
| `src/legal_rag_jev/providers.py` | `82b07002fa8dedde13b14882d3a897fa4f6e04b0771865dcb047bc5440d378da` |

추가로 `results/koblex-reproduction-v1/jev-cache/*.json`(39,177개)의 파일 시스템 수정 시각만 읽었다(품질 실행 Jev 점수화 시점 추정용, 내용은 읽지 않음).
