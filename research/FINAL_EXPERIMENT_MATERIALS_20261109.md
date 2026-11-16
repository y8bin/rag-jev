# 최종 실험 결과 자료 통합 정리

조사 시각: 2026-11-09T13:12:34.412019+00:00. 범위: 현재 작업공간의 research, results, data, output, scripts, src, tests, configs 및 인계 문서. 삭제된 과거 실험은 복구하지 않았다. 외부 서비스·다른 폴더는 조사 범위에 포함하지 않았다.

## 1. 먼저 읽을 자료

| 용도 | 자료 |
|---|---|
| 현재 주 실험 결과 보고서 | [research/KOBLEX_REPRODUCTION_RESULTS_20261109.md](KOBLEX_REPRODUCTION_RESULTS_20261109.md) |
| 통합 수치·대응 bootstrap의 기준 원자료 | [results/koblex-reproduction-v1/analysis.json](../results/koblex-reproduction-v1/analysis.json) |
| 현재 제4장 본문 | [research/chapter4/chapter4.md](chapter4/chapter4.md) |
| 제4장 보충자료 | [research/chapter4/chapter4-supplement.md](chapter4/chapter4-supplement.md) |
| 조판 PDF | [output/pdf/chapter4-draft.pdf](../output/pdf/chapter4-draft.pdf) |
| 추가 분석 A1~A6 안내 | [results/koblex-reproduction-v1/chapter4-prep-v1/README.md](../results/koblex-reproduction-v1/chapter4-prep-v1/README.md) |
| 추가 필터링 시뮬레이션 | [results/koblex-filtering-v1/README.md](../results/koblex-filtering-v1/README.md) |

## 2. 주 실험 결과

공식 한국어 QA 226문항, 3조건, 답변 678개 및 LF-Eval 678개가 완료되었다. 주 비교는 수정 CE 대 Jev다. 공개 코드 CE는 첫 후보 목록 참조 문제를 보존한 별도 참조 조건이다. 공통 BM25 후보 100개 → scorer 상위 10개 → LLM의 pool별 1개 선택 → 답변 생성 구조이며, 예상 법령·후보 pool은 478개다.

| 지표 | 공개 코드 CE | 수정 CE | Jev | Jev−수정 CE | 탐색적 95% CI |
|---|---:|---:|---:|---:|---:|
| 근거 F1 | 48.72 | 58.57 | 61.75 | +3.19 | [+0.75, +5.68] |
| 근거 Recall | 45.35 | 57.74 | 60.69 | +2.95 | [+0.39, +5.51] |
| 근거 EM | 17.70 | 27.88 | 29.65 | +1.77 | [-1.77, +5.19] |
| 완전 회수율 | 20.80 | 34.07 | 34.96 | +0.88 | [-2.90, +4.53] |
| Token F1 | 40.70 | 46.20 | 47.31 | +1.12 | [+0.02, +2.27] |
| LF-Eval | 58.30 | 67.57 | 70.15 | +2.58 | [+0.37, +4.79] |

점수는 원값 ×100. EM·완전 회수율 차이는 %p, 그 외는 점이다. 151개 의존 그룹 대응 bootstrap 10,000회이며 다중 비교를 보정하지 않은 사후 탐색 결과다. EM·완전 회수율 CI는 0을 포함한다. Token F1의 별도 centered-bootstrap p≈0.0525이므로 모든 지표의 유의한 개선으로 묶지 않는다.

## 3. 자료별 위치와 역할

| 자료 묶음 | 위치 | 내용·사용 기준 |
|---|---|---|
| 원시 실험 출력 | [results/koblex-reproduction-v1/](../results/koblex-reproduction-v1/) | parametric.jsonl, candidates.jsonl, ranking-ce.jsonl, ranking-jev.jsonl, parser_{ce_raw,ce_fixed,jev_fixed}.jsonl: 생성·검색·점수화·선택의 추적 기록. |
| 실제 답변 | [results/koblex-reproduction-v1/predictions/](../results/koblex-reproduction-v1/predictions/) | 조건별 226행. 최종 답변 및 generation_trace 사용량. |
| 공식 결정적 평가 | [results/koblex-reproduction-v1/metrics/](../results/koblex-reproduction-v1/metrics/) | 조건별 metrics.jsonl, summary.json. 이 단계의 LF NOT_RUN은 전체 미완료를 의미하지 않는다. |
| LLM 평가 | [results/koblex-reproduction-v1/lf-eval/](../results/koblex-reproduction-v1/lf-eval/) | 조건별 metrics.jsonl, manifest.json, summary.json. 통합 완료는 analysis.json과 함께 확인. |
| A1 수치 원장 | [results/koblex-reproduction-v1/chapter4-prep-v1/A1/](../results/koblex-reproduction-v1/chapter4-prep-v1/A1/) | numeric-ledger.*, question-metrics.*: 원값·CI·출처 pointer 및 678행 지표. |
| A2 하위집단 | [results/koblex-reproduction-v1/chapter4-prep-v1/A2/](../results/koblex-reproduction-v1/chapter4-prep-v1/A2/) | hop별·매핑 여부별 지표, 분모·문항 목록, 그림 원자료. |
| A3 대응 변화 | [results/koblex-reproduction-v1/chapter4-prep-v1/A3/](../results/koblex-reproduction-v1/chapter4-prep-v1/A3/) | paired-outcomes, win-tie-loss, joint-directions, discordant-queries. |
| A4 단계별 탈락 | [results/koblex-reproduction-v1/chapter4-prep-v1/A4/](../results/koblex-reproduction-v1/chapter4-prep-v1/A4/) | 443건/조건 gold 출현, corpus→BM25→shortlist→최종 선택, pool 동시 선택 제약. |
| A5 자원 사용 | [results/koblex-reproduction-v1/chapter4-prep-v1/A5/](../results/koblex-reproduction-v1/chapter4-prep-v1/A5/) | 문맥·API 입력/출력 토큰, 중복, 캐시 분리, 평균·중앙값·IQR. |
| A6 사례·검토 | [results/koblex-reproduction-v1/chapter4-prep-v1/A6/](../results/koblex-reproduction-v1/chapter4-prep-v1/A6/) | 226문항 casebook, 대표 사례, 법률 검토 대기 183문항. 전문가 판정 결과가 아님. |
| 사람 평가 | [results/koblex-reproduction-v1/human-review/](../results/koblex-reproduction-v1/human-review/) | 60문항×3조건=180답변, 평가자 A/B 양식. 실제 판단 0개. private/condition-key.jsonl은 블라인드 해제키로 평가자에게 공유하지 않음. |
| 진단·감사 | [research/KOBLEX_REPRODUCTION_AUDIT_20261109.md](KOBLEX_REPRODUCTION_AUDIT_20261109.md) | ce-diagnostic*, ce-numerics*, candidate-audit.json, identical-answer-judge-audit.json과 연결. |
| 실행 고정·변경 기록 | [results/koblex-reproduction-v1/](../results/koblex-reproduction-v1/) | protocol-lock.json, runtime-settings.json, *amendment.json, answers-execution-addendum.json, cleanup-manifest.json. |
| 완료·무결성 | [results/koblex-reproduction-v1/](../results/koblex-reproduction-v1/) | final-status.json, computational-completion.json, integrity-audit-current.json. A1~A6에는 별도 completion/validation/source-manifest가 있음. |
| 제4장 원고·출처 | [research/chapter4/](chapter4) | chapter4.md, chapter4-supplement.md, chapter4.tex, section4_1~5.tex, manuscript-facts.json, draft-validation.json, WRITING_NOTES.md. |
| 그림 | [research/chapter4/figures/](chapter4/figures) | hop_f1.png/pdf/svg/csv, provenance JSON, plot_hop_f1.py. |
| 이전 편집본·문체 참고 | [research/chapter4/style-study-v1/](chapter4/style-study-v1) | before-*는 편집 이전 스냅샷. papers/는 문체 참고 논문이며 현재 실험 결과가 아님. |
| 데이터·공식 코드 | [data/koblex/](../data/koblex/) | prepared-v1의 questions/queries/gold/manifest, downloads 법령 corpus, upstream 공식 소스·프롬프트·평가 코드. |
| 설정·재현 코드 | [configs/koblex-reproduction.yaml](../configs/koblex-reproduction.yaml) | scripts/koblex.py, scripts/experiment/, src/legal_rag_jev/koblex*.py, research/prompts/, 환경 JSON·requirements, 관련 tests/. |
| 예산·실행 캐시 | [results/koblex-reproduction-v1/](../results/koblex-reproduction-v1/) | final-budget.json, budget/ledger.sqlite, framework-cache/. 캐시 응답은 추적 근거이며 독립 새 실험 결과가 아님. |

## 4. 추가 분석에서 확인된 결과

- 근거 F1의 Jev 우세/동률/CE 우세: 32/177/17문항. 1-hop F1은 CE 78.07, Jev 76.90으로 낮아졌고 2-hop은 53.33→57.24, 3-hop은 47.91→54.83이다. 3-hop 완전 회수는 양쪽 모두 1/42다.
- 고유 gold 386개 중 27개가 corpus와 exact mapping되지 않아 29문항에 영향을 준다. 문항별 gold 출현 443건과 구별한다.
- 문맥 평균 토큰은 CE 203.67→Jev 215.60, 전체 입력 평균은 2302.67→2314.58이다. 본 실험에서 입력량 절감은 관찰되지 않았다. 캐시를 재사용한 행의 사용량은 신규 청구량이 아니다.
- 본문 사례 A/B/C의 식별자와 선정 절차는 chapter4-supplement.md S4, 긴 원문은 A6/casebook.jsonl에 있다. 법률 전문가 검토는 미완료다.

## 5. 필터링과 지연 자료의 현재 상태

### 필터링: 완료된 오프라인 탐색 시뮬레이션

자료: [results/koblex-filtering-v1/summary.json](../results/koblex-filtering-v1/summary.json), 같은 폴더의 CSV 4개와 cv-heldout-ce/jev.jsonl. 코드: [scripts/simulate_koblex_filtering.py](../scripts/simulate_koblex_filtering.py). 151그룹 5-fold 안에서 scorer별 분위수 문턱값을 선택했다.

- CE: 478→467개 유지(97.70%), F1 58.57→58.54.
- Jev: 478→426개 유지(89.12%), F1 61.75→61.43. Precision 66.85→69.80, Recall 60.69→58.26.
- Jev F1 차이 −0.32점의 95% CI는 [−1.76, +1.07]. 0을 포함한다는 이유만으로 동등성·비열등성을 주장할 수 없다.
- 답변을 재생성하지 않았으므로 필터링 후 Token F1/LF-Eval·실제 비용·응답 지연 개선은 미측정이다. pre와 post의 분모도 다르므로 주 실험 shortlist Recall과 직접 혼합하지 않는다.

### 지연: 부분 관측만 존재

조사 시점 raw.jsonl 47행(워밍업 6행, 측정 41행)이 존재한다. 계획은 60문항×2방법×3반복=360개 본 측정이며, 집계 summary는 없다. 현재 로그를 최종 지연 결과로 인용하지 않는다. 파일은 실행 중 추가될 수 있다.

프로토콜: [results/koblex-latency-v1/protocol.json](../results/koblex-latency-v1/protocol.json). 원시값: [results/koblex-latency-v1/raw.jsonl](../results/koblex-latency-v1/raw.jsonl). 로그: [tmp/latency-run.log](../tmp/latency-run.log). benchmark/analyze 코드는 scripts/benchmark_koblex_latency.py 및 scripts/analyze_koblex_latency.py다. 측정 구간은 scorer+pool별 정렬/top-10이고 모델 로드·BM25·LLM 선택·답변 생성은 제외하므로 E2E 지연이 아니다.

## 6. 문서 시점 충돌과 인용 기준

- SESSION_HANDOFF.md의 “A1~A6 미실행, 본문 미작성”은 현재 파일과 다르다. A1~A6 completion/validation과 현재 chapter4.md/PDF가 후속 산출물이다.
- 기존 결과 보고서·인계·제4장은 추가 필터링 시뮬레이션과 부분 지연 측정을 반영하지 않을 수 있다. “필터링 미실행”은 원 주 실험에는 맞지만 후속 오프라인 시뮬레이션까지 없다는 뜻으로 쓰면 안 된다.
- 주 실험의 집계는 analysis.json, 추가 분석은 각 산출물과 manifest, 원고는 manuscript-facts.json을 기준으로 교차 확인한다. 저장된 PASS는 과거 검증 기록이며 이번 정리에서 전체 실험을 다시 실행한 것은 아니다.
- 품질 향상, 필터링 근거 수 감소, 지연 측정, 실제 사람 판단은 별도 증거 범위다. 이를 합쳐 “품질·비용·속도 모두 검증 완료”라고 쓰지 않는다.

## 7. 전체 파일 목록

이 문서와 같은 위치의 FINAL_EXPERIMENT_FILE_INDEX_20261109.csv에 관련 파일의 상대 경로·분류·크기·수정 시각을 기록했다. 실행 캐시·BM25 index·예산 DB도 목록에 포함하되 비밀 환경변수 파일과 모델/패키지 설치 캐시는 제외했다. 캐시 응답 본문과 블라인드 해제키 내용은 복사하지 않았다. 원 자료는 이동·수정하지 않았다.
