# Stage 3 Phase 1 — Peer Reviewer 2 (Domain) 심사 보고서: 제4장

- Seat: Peer Reviewer 2 — Domain (`domain_reviewer_agent`, 카드 #3: 한국어 법률 NLP·법령 검색)
- 대상: `research/chapter4/chapter4.md`(본문), `chapter4-supplement.md`(S1–S9). PDF는 렌더링 도구(poppler)가 없어 직접 열람하지 못했고, 본문 그림 PNG 원본(그림 3)만 확인하였다.
- 사전 commit 계획: `pipeline/stage3_phase1_r2_plan.md` (원고 열람 전 작성). 계획과 다른 판단은 없어 Scoring Plan Dissent는 생략한다.
- 대조 자료(읽기 전용): `data/koblex/upstream/`(공식 README, ParSeR `selection_retrieval.py`·`utils.py`, LF-Eval `eval_pipeline.py`), `data/koblex/downloads/statute.jsonl`, `results/koblex-reproduction-v1/`(protocol-lock, ce-diagnostic-summary, chapter4-prep-v1/A4·A6). API 호출과 웹 검색은 하지 않았다.
- 범위 제약 준수: 제4장만 심사. 다른 장 소관 사항은 아래 "팀 조율 메모"에 분리. 사람·법률 전문가 평가 요구 없음. 새 유료 실험은 optional future work로만 표기.
- 아래 "심사자 재집계" 수치는 저자 원자료(A4 파일, statute.jsonl)를 심사자가 직접 다시 센 값이다. 원고에 넣기 전에 저자가 자체 코드로 재확인해야 한다.

contract_role: domain
## Dimension Scores

### D1: methodology_rigor
score: not_assessed

### D2: domain_accuracy
score: warn
trigger: "사실 오류는 없으나 재현 차이·평가 단위 한계·개선 원인(재정렬기 자체 vs 선택기 상호작용)의 분리가 불충분하게 서술되어"

### D3: argumentative_coherence
score: not_assessed

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

### 요약 (Summary Assessment)

제4장은 KoBLEX 226문항에서 ParSeR의 재정렬기를 `dragonkue/bge-reranker-v2-m3-ko` Cross-Encoder(CE)에서 Decision Model `jev-1.14.0`으로 바꾼 paired component-swap 결과를 보고한다. 도메인 관점에서 본 사실 정확성은 높다. 심사자가 공식 코드와 대조한 결과, (i) 공개 코드의 `contexts_list[0][choice]` 참조 결함, (ii) 예상 법령별 BM25 k=100 → 재정렬 top-10 → 목록당 1개 LLM 선택 구조, (iii) `hierarchy + content` 정확 문자열 집합 비교에 의한 근거 P/R/F1/EM, (iv) 앞 800자 절단이 모두 원고 서술과 일치하였다. 사례 A/B/C의 조문 서술도 casebook 원자료와 일치하였다. 원고는 "정답 근거와의 일치"와 "법률적 타당성"을 일관되게 구분하며, 자동 관측을 법률 판단으로 확대하지 않으려 한다.

다만 도메인 독자가 결과의 의미를 판단하는 데 필요한 연결이 세 군데 빠져 있다. (1) 재현 충실성: 공개 코드 CE(F1 48.72)를 원 논문 보고값 및 실행 조건 차이와 함께 위치시키지 않았다. 이 비교는 "원 실행에도 결함이 있었는가"에 관해 현재 가용한 유일한 간접 증거이기도 하다. (2) 개선 원천의 분리: 그림 3과 A4 원자료만으로도 계산할 수 있는 조건부 선택률과 hop별 구조적 상한을 보고하지 않아, 개선이 재정렬기 자체에서 오는지 LLM 선택기와의 상호작용에서 오는지가 서술 수준에 머문다. (3) 평가 단위: "corpus 미매핑" 27개 gold는 corpus에 없는 조문이 아니라, 거의 모두 조 본문과 각 호 목록의 구획 차이로 생긴 문자열 불일치였다. 이 사실과 정답 외 선택 근거의 구조적 성격(같은 조의 다른 항, 위임 하위법령 등)을 기존 자료로 기술할 수 있는데도 하지 않았다. 셋 다 새 실험 없이 기존 산출물과 서술 수정으로 해결할 수 있으며, 핵심 결론은 유지된다.

### Overall Recommendation

**Minor Revision** (도메인 seat 기준. 경계 사례로, 아래 Major 2건 W1·W2는 새 실험 없이 서술 보강과 기존 자료 재집계로 해결할 수 있어 Major Revision까지는 필요하지 않다고 판단하였다.)

Confidence Score: 4 — KoBLEX 공식 코드와 원자료를 직접 대조했다. 원 논문 PDF의 수치표는 세션 자료에 없어 확인하지 못했다.

Calibration Status: `NOT_CALIBRATED`

### Strengths

#### S1: 공식 코드 결함의 정확한 식별과 효과 분리
공개 코드의 후보 목록 참조 결함을 정확히 짚었다. 업스트림 `process_completions`가 실제로 `contexts_list[0][choice]`를 사용한다. 원고는 결함을 보존한 조건을 "재현 참조"로 분리하고, 수정 효과(+9.85점)와 모델 교체 효과(+3.19점)를 섞지 않았다. 원 실행에도 결함이 있었는지는 판정하지 않았다고 명시하여, 공개 스냅샷과 원 논문 실행을 구별하는 절제도 갖추었다. 법률 RAG 재현 연구에서 드물게 정확한 기여이다.
- **Evidence Anchor**: `text: §4.2 ¶4 "수정 CE와의 9.85점 차이는 후보 목록 참조 수정 효과이며, Jev 교체 효과와 구별된다."`

#### S2: 공식 평가 규칙의 충실한 적용과 정답 일치·법률 타당성의 구분
근거 평가는 공식 `evaluate_retrieval`과 같은 집합 연산(정확 문자열, 중복 1회)이다. 원고는 이 지표가 "gold와의 일치"일 뿐 정답 외 조문의 법률적 타당성을 판정하지 않는다는 점을 본문(§4.2)과 사례(§4.5)에서 반복해 밝힌다. 사례 분석도 LF-Eval 평가기의 설명을 법률 판정으로 쓰지 않았다(S4).
- **Evidence Anchor**: `text: §4.5 ¶3 "이러한 사례는 자동 관측에 근거하며, 정답 외 조문의 법률적 부적절성이나 실제 주장 미지지를 확정한 것은 아니다."`

#### S3: 후보 유지와 최종 선택을 나눈 단계별 탈락 분석
그림 3과 §4.3의 "목록당 1개 선택" 상한(CE 104 / Jev 120 vs 실제 77 / 79)은 multi-hop 법령 QA의 오류를 BM25 미회수·재정렬 탈락·선택 실패로 나누어 보여준다. 이는 ParSeR 계열 파이프라인의 병목을 진단하는 데 실질적으로 유용한 틀이다. 분모(gold 출현 443 vs 고유 386 vs 문항별 평균 Recall)의 차이도 명시하였다.
- **Evidence Anchor**: `figure: 그림 3 (fig_4_5_gold_loss_stages_column), gold 출현 443건의 배타적 단계 분류`

#### S4: 사례 서술의 원자료 정합성
사례 A(식품위생법 제42조제2항 유지와 제45조제1항 추가), 사례 B(민사소송법 제79조제1항 탈락, 제83조제1항 선택), 사례 C(gold 3개, 목록 2개)를 casebook 원자료와 대조한 결과 모두 일치하였다. 사례 선정 규칙(중앙값 근접, query_id 사전순 동률 처리)도 사전에 기술되어 있다.
- **Evidence Anchor**: `dataset: results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl (qa_124_2hop_480_rand, qa_324_2hop_515, qa_443_3hop_703)`

### W1: 재현 충실성의 위치 설정 부재 — 원 논문 보고값과 실행 조건 차이가 제4장에 없음
- **Severity**: Major
- **우선순위**: P0
- **Evidence Anchor**: `text: §4.2 ¶4 "공개 스냅샷의 문제가 원 논문의 실제 실행에도 있었는지는 확인되지 않았다."`
- **Confidence**: 4 — 공식 코드와 protocol-lock은 직접 확인했다. 원 논문 수치표는 세션 자료에 없어 대조하지 못했다.

문제: 제4장은 "ParSeR 재현" 위에 교체 효과를 쌓지만, 재현이 원 논문과 어느 정도 맞는지 독자가 판단할 정보가 없다. S5는 "기존 성능표를 전재한 것이 아니"라고만 밝힌다. KoBLEX를 아는 심사자라면 먼저 원 논문의 ParSeR(GPT-4o) 근거 F1·LF-Eval·Token F1과 공개 코드 CE 48.72점, 수정 CE 58.57점의 관계를 물을 것이다. 이 비교는 도메인적으로 두 가지 의미가 있다. (a) 재현 기준선의 타당성 확인이다. (b) 원 실행에도 결함이 있었는지에 대한 간접 증거가 된다. 공개 코드 CE 값이 원 논문 보고값에 가깝다면 원 실행도 결함을 포함했을 가능성을 시사하고, 수정 CE에 가깝다면 반대를 시사한다. 지금은 이 증거를 쓰지 않은 채 "확인되지 않았다"로 끝난다. 또한 protocol-lock에 기록된 원본 대비 실행 차이가 제4장에 요약되어 있지 않다. 차이는 다음과 같다. CE 장치가 원 코드의 CUDA에서 MPS로 바뀌었다(지연 절에만 등장). 생성 모델이 `gpt-4o` alias에서 `gpt-4o-2024-08-06` snapshot으로 고정되었다. Chat Completions 대신 Responses API를 사용했다. bm25s 버전을 고정했고 원 실행 버전은 알 수 없다.

제안: §4.2 마지막 문단 또는 §4.1에 1–2문장을 추가하라. 원 논문이 보고한 ParSeR(GPT-4o)의 해당 지표 값을 공개 코드 CE·수정 CE와 나란히 제시하고, 차이 방향이 결함 존재 여부에 대해 무엇을 시사하는지와 그 해석이 생성 모델 snapshot·장치 차이 때문에 결정적이지 않다는 점을 함께 밝히면 된다. 보충자료 S5에는 원본 대비 실행 차이 목록(장치, 모델 snapshot, API, 라이브러리 버전, temperature 0.01·top_p 0.9 동일 여부)을 표로 정리하라. 원 논문 수치는 저자가 원문에서 직접 옮겨야 하며, 심사자는 값을 제시하지 않는다.

### W2: 개선 원천(재정렬기 자체 vs 선택기·목록 구조)의 분리가 서술 수준에 머묾
- **Severity**: Major
- **우선순위**: P0
- **Evidence Anchor**: `text: §4.3 ¶3 "따라서 Jev는 상위 후보에서 정답 근거를 더 많이 유지했지만, 후속 선택과 목록 구조의 제약이 남았다."`
- **Confidence**: 4 — 그림 3 수치와 A4 원자료로 심사자가 재집계했다.

문제: 이 장의 도메인적 핵심 질문은 "Jev가 더 좋은 근거를 고르게 한 이유가 재정렬 품질인가, LLM 선택기와의 궁합인가"이다. 원고는 shortlist 유지 개선(+5.16점)과 구조적 상한을 제시하지만, 둘을 잇는 수치인 **shortlist에 남은 gold가 선택될 조건부 비율**을 보고하지 않았다. 그림 3에서 바로 계산하면 CE 233/(233+60)=79.5%, Jev 250/(250+72)=77.6%이다(심사자 계산). 조건부 선택률은 비슷하거나 Jev가 약간 낮으므로, 최종 근거 개선은 대부분 shortlist 유지 개선(재정렬 탈락 42→13)에서 나오며 선택기와의 상호작용 이득은 관찰되지 않는다고 읽을 수 있다. 이 해석은 원고의 주장을 오히려 더 명료하게 지지한다. 또 Jev의 우위가 "gold를 top-10 안에 넣는 것"에서 오는지 "top-10 안에서 더 높은 순위에 두는 것"에서 오는지도 구분되지 않는다. LLM 선택기는 순위 위치에 민감할 수 있으므로 이는 도메인적으로 의미 있는 구분이다.

제안: (1) §4.3 또는 §4.5에 조건부 선택률 한 문장을 추가하라. 문항 단위 대응 구간이 필요하면 R1 소관인 기존 bootstrap 절차를 재사용하면 된다. (2) 기존 `ranking-ce.jsonl`·`ranking-jev.jsonl`과 A4 `pool-constraints`로 목록별 gold의 shortlist 내 순위 분포(예: 목록당 gold가 있을 때의 평균 순위 또는 MRR@10)와 "gold가 top-10에 있을 때 선택된 순위 위치"를 보충자료에 기술통계로 제시하라. 두 분석 모두 API 호출 없이 기존 산출물로 가능하다. (3) 결론 문장을 "Jev의 이득은 주로 재정렬 단계의 후보 유지에서 발생하며, shortlist 내 선택 단계에서의 추가 이득은 관찰되지 않았다"처럼 원천을 특정하는 형태로 바꾸는 것을 검토하라. 단, 재집계 결과가 이를 지지할 때에 한한다.

### W3: 3-hop "1/42"의 해석에 필요한 hop별 구조적 상한이 빠짐
- **Severity**: Minor
- **우선순위**: P1
- **Evidence Anchor**: `text: §4.2 ¶4 "특히 3-hop 완전 회수는 두 조건 모두 1/42문항이었다."`
- **Confidence**: 4 — A4 `question-stages.jsonl`을 심사자가 재집계했다.

문제: 이 문장만 보면 3-hop에서 두 조건이 똑같이 실패한 것처럼 읽힌다. 그러나 A4 원자료를 재집계하면 3-hop의 "shortlist에서 모든 gold를 동시에 선택할 수 있는 문항"은 CE 2/42, Jev 11/42였다. shortlist 합집합에 모든 gold가 있는 문항은 CE 7, Jev 17이었다. 즉 Jev는 3-hop에서 구조적 상한을 크게 높였지만 그 상한이 최종 완전 회수로 이어지지 않았다. 3-hop에서는 병목이 재정렬에서 선택 단계로 옮겨갔다는 것이 도메인적으로 더 정확한 서술이다. 또한 3-hop 42문항 중 9문항(2-hop 8/127, 1-hop 2/57)은 생성된 예상 법령 목록 수가 gold 수보다 적어, 목록당 1개 선택 구조에서는 처음부터 완전 회수가 불가능했다(심사자 재집계). 이것은 예상 법령 생성 단계의 구조적 한계이며 재정렬기와 무관하다.

제안: §4.2의 해당 문장 뒤에 hop별 shortlist 동시 선택 가능 문항 수(CE/Jev)와 "목록 수 < gold 수" 문항 수를 한 문장으로 추가하라. 지면이 부족하면 S6 "질문별·추론 단계별 차이"에 표로 넣고 본문에서는 참조만 하라.

### W4: "corpus 미매핑" 27개 gold의 실체 — 조문 구획(조 본문 vs 각 호) 불일치로 보임
- **Severity**: Minor
- **우선순위**: P1
- **Evidence Anchor**: `text: §4.2 ¶4 "고유 gold 386개 중 27개는 corpus에서 동일 문자열을 찾을 수 없어 29문항에 영향을 주었다."`
- **Confidence**: 4 — 공식 `koblex.jsonl`의 contexts와 `statute.jsonl`을 심사자가 직접 대조했다.

문제: 서술 자체는 정확하지만, 독자는 "corpus에 해당 조문이 없다"로 오해하기 쉽다. 심사자 대조 결과는 다르다. 27개 모두 같은 `hierarchy`(법률명·조·표제)를 가진 corpus 행이 존재했다. 26개는 corpus 행 문자열이 gold 문자열의 부분 문자열(조 본문 도입부)이었고, 25개는 gold 안에 줄바꿈으로 이어진 각 호 목록(예: "다음 각 호의 어느 하나에 해당하는 자는… 1. … 2. …")이 포함되어 있었다. 공백 정규화로 해결되는 경우는 0개였다. 즉 이 불일치는 KoBLEX gold(조 본문과 각 호 일체)와 corpus(항 단위, 각 호 분리 또는 생략) 사이의 구획 단위 차이에서 생긴 벤치마크 고유의 평가 산물로 보인다. 공식 평가 코드도 같은 정확 일치를 쓰므로 원 논문 수치에도 같은 천장이 있었을 것이다. 두 조건에 똑같이 작용하므로 비교 방향에는 영향이 없지만(원고의 완전 매핑 197문항 분석이 이를 뒷받침한다), 법률 도메인 독자에게는 원인 설명이 필요하다.

제안: (1) §4.2 또는 S6에 "미매핑 gold는 corpus에 조문이 없는 경우가 아니라, gold가 조 본문과 각 호를 한 문자열로 담은 반면 corpus는 이를 나누어 수록한 구획 차이에서 비롯되었다"는 취지의 원인 서술을 넣어라. 저자 재확인이 전제이다. (2) 선택 사항으로, 기존 자료만 써서 "gold의 도입부와 일치하는 corpus 행을 정답으로 간주"하는 접두 매핑 민감도 분석을 S6에 기술통계로 제시할 수 있다. 공식 지표를 대체하지 않는 보조 분석으로 명시해야 한다. (3) 그림 3의 "No corpus match" 라벨에도 같은 취지의 각주를 고려하라.

### W5: 정답 외 선택 근거의 구조적 성격이 기술되지 않음 — 사람 평가 없이 가능한 near-miss 분류
- **Severity**: Minor
- **우선순위**: P1
- **Evidence Anchor**: `text: §4.2 ¶1 "정답 외 근거의 법률적 타당성을 판정하지는 않는다."`
- **Confidence**: 3 — 사례 3건과 S6 집계는 확인했으나, 전체 분포는 심사자가 재집계하지 않았다.

문제: 정답 외 근거가 선택된 문항은 CE 126개, Jev 116개로 전체의 절반을 넘는다(S6). 원고는 법률적 타당성 판정을 정당하게 유보하지만, 그 결과 Precision 상승(+3.39점)이 "무관한 조문을 덜 고른 것"인지 "같은 조·같은 법률의 인접 조문 대신 gold를 고른 것"인지 알 수 없다. 법령 검색에서는 같은 조의 다른 항, 같은 법률의 인접 조, 위임 하위법령(시행령·시행규칙)이 gold와 기능적으로 겹치는 경우가 흔하다. 예컨대 사례 A에서 CE가 고른 정답 외 근거는 같은 법률의 시행규칙 제56조제2항(생산실적 보고 상대방)이었고, 사례 C에서 Jev가 고른 정답 외 근거는 형법 제39조제3항과 사면법 제5조제1항이었다.

제안: 사람 평가 없이, 문자열·계층 정보만으로 정답 외 선택 근거를 다음 범주로 나눈 기술통계를 S6에 추가하라. (a) gold와 같은 조의 다른 항, (b) 같은 법률의 다른 조, (c) gold 법률의 시행령·시행규칙(법률명 접두 일치), (d) 다른 법률. 이 분류는 법률적 타당성 판정이 아니라 구조적 근접성의 관측이라고 명시해야 한다. CE와 Jev의 분포 차이는 Precision 변화의 도메인적 성격을 보여준다. 기존 `predictions/`와 `statute.jsonl`로 가능하며 API 비용이 없다.

### W6: 사례 C의 해석 문장이 사례가 보여주는 것과 어긋날 수 있음
- **Severity**: Minor
- **우선순위**: P1
- **Evidence Anchor**: `text: §4.5 ¶3 "표현 중복의 증가가 더 나은 근거 선택을 보장하지 않음을 보여준다."`
- **Confidence**: 3 — casebook의 선택 조문을 확인했다. 법률적 적절성은 판정하지 않는다.

문제: 이 문장은 근거 F1 40→0을 "더 나쁜 근거 선택"으로 전제한다. 그러나 casebook에 따르면 사면이 쟁점인 질문에 대해 Jev는 형법 제39조제3항(경합범 중 일부 죄의 사면 시 다른 죄의 형 재결정)과 사면법 제5조제1항(사면의 효과)을 선택했다. 이들은 질문의 핵심 어휘와 직접 겹치는 조문이며, CE는 형법 제81조 장 표제 행을 선택했다. 원고의 단서 문장("정답 외 조문의 법률적 부적절성… 확정한 것은 아니다")과 함께 읽으면, 이 사례는 "Token F1과 근거 F1이 반대로 움직인다"는 지표 불일치의 사례이자 정확 일치 평가가 주제상 근접한 대체 조문을 0점으로 처리하는 사례이기도 하다. 현재 문장은 그중 한 방향만 단정한다.

제안: 해당 문장을 "근거 F1과 Token F1이 반대 방향으로 변하여, 두 자동 지표가 서로 다른 측면을 반영함을 보여준다. 이 사례에서 Jev가 선택한 정답 외 조문(형법 제39조제3항, 사면법 제5조제1항)의 법률적 적절성은 판정하지 않았다"처럼 중립적으로 바꾸어라. 이는 사례 해석이 자동 관측을 넘어서지 않게 하려는 원고 자체의 원칙에도 부합한다.

### W7: CE 입력 형식 선택과 Jev 지시문의 비대칭이 제4장에 드러나지 않음
- **Severity**: Minor
- **우선순위**: P1
- **Evidence Anchor**: `text: §4.1 ¶1 "CE 입력 형식(원 질문만 사용)은 시험 문항 30개에서 네 가지 형식을 비교한 탐색적 진단을 거쳐 정하였다."`
- **Confidence**: 4 — `ce-diagnostic-summary.json`, protocol-lock, 업스트림 `selection_retrieval.py`를 대조했다.

문제: (a) 선택된 "원 질문만 사용" 형식은 업스트림 `rerank()`가 `(q, t)` 쌍으로 원 질문만 넣는 방식과 같다. 따라서 이 진단은 사실상 공식 설정을 확인한 것이고, 시험 문항 기반 튜닝이라는 우려를 크게 줄인다. 그런데 원고는 이 점을 말하지 않아 오히려 test-set 선택처럼 읽힌다. (b) protocol-lock에 따르면 Jev에는 "직접 답변을 뒷받침하는가"를 묻는 관련성 지시문이 주어졌다. 이 기준은 LLM 선택 프롬프트의 기준("directly support the answer")과 사실상 같다. CE에는 지시문이 없다. 이는 지시문 조건 재정렬기와 일반 관련성 재정렬기의 비교라는 뜻이며, W2의 "선택기와의 궁합" 해석과 직결된다. (c) KoBLEX 질문은 배경 시나리오의 인물(갑·을·병)을 지칭하는데 두 재정렬기 모두 배경 없이 원 질문만 받는다. 배경 포함 형식은 CE 진단에서만 비교되었고 Jev에서는 확인되지 않았다.

제안: §4.1 해당 문장에 "이 형식은 공식 코드의 재정렬 입력과 같다"는 구절을 추가하라. Jev 지시문의 존재와 그 내용이 선택 프롬프트 기준과 정렬되어 있다는 점도 한 구절로 밝혀라. 지시문 정의 자체는 방법 장 소관이므로 팀 조율 메모 참조. 배경 포함 입력에서의 Jev 비교는 **optional future work**(유료 API 호출 필요)로만 언급하라.

### W8: 그림 3의 "Selection loss"가 선택기 오류와 구조적 용량 제약을 합침
- **Severity**: Minor
- **우선순위**: P2
- **Evidence Anchor**: `figure: 그림 3 "Selection loss" 범주 (CE 60 / Jev 72) 및 캡션`
- **Confidence**: 4 — 그림 PNG 원본과 A4 `pool-constraints.jsonl` 필드를 확인했다.

문제: 캡션은 "미선택은 목록별 선택 수 제약의 영향도 받는다"고 쓰지만, 막대 하나 안에 (i) 같은 목록에 gold가 2개 이상 있어 구조적으로 하나만 고를 수 있었던 경우와 (ii) 선택 가능했으나 LLM이 다른 후보를 고른 경우가 섞여 있다. Jev에서 미선택이 60→72로 늘어난 것이 (i)의 증가(더 많은 gold가 같은 목록에 몰림) 때문인지 (ii) 때문인지는 W2의 해석과 직결된다.

제안: A4 `pool-constraints`의 목록별 `shortlist_gold_unit_ids` 개수로 (i)과 (ii)를 나눈 수치를 S6 표에 추가하라. 지면이 허락하면 그림 3을 6범주로 나누어라. 그림 라벨이 영어이고 본문이 한국어이므로, 국문 투고 시 라벨 언어도 통일하라.

### W9: 도메인 용어의 단위 정확성 — "예상 법령", "공식 hop별", 근거·조문·법령 혼용
- **Severity**: Minor
- **우선순위**: P2
- **Evidence Anchor**: `text: §4.2 ¶4 "공식 hop별 F1은 1-hop에서 78.07→76.90"`
- **Confidence**: 4 — 한국 법령 체계의 용어 관례와 KoBLEX README의 항 단위 수록 설명에 근거한다.

문제: (a) "예상 법령"은 원 논문의 parametric provision에 해당하는데, 한국 법률 용어에서 "법령"은 법률·시행령·시행규칙 전체를 가리키는 상위 개념이다. 생성되는 것은 개별 조문 형태의 문구이므로 "예상 조문" 또는 "예상 법령 조문"이 단위상 더 정확하다. (b) "공식 hop별"의 "공식"은 데이터셋 `n_hops` 라벨을 뜻하는 것으로 보이나, 공식 지표나 공식 코드 산출로 오독될 수 있다. (c) 평가 단위가 항(또는 조) 단위 조문임에도 본문은 "근거", "gold", "정답 근거", "조문", "법령"을 섞어 쓴다. 영문 번역 시 provision, statute, evidence, gold가 흔들릴 위험이 있다.

제안: §4.1 첫 문단에 "평가 단위는 corpus 행(항 단위 조문)"이라는 한 구절을 넣고, "근거"는 그 단위를 가리킨다고 고정하라. "공식 hop별"은 "데이터셋의 hop 라벨별"로 바꾸어라. "예상 법령"의 용어 결정은 팀 조율 메모 참조.

### W10: 한국어 공백 단위 Token F1의 도메인적 해석 한계가 수치 해석에 반영되지 않음
- **Severity**: Minor
- **우선순위**: P2
- **Evidence Anchor**: `text: §4.4 ¶1 "Token F1은 정답과 생성 답변의 공백 단위 표현 중복을 측정하며"`
- **Confidence**: 3 — 한국어 교착어 특성에 관한 일반 지식에 근거한다. 이 데이터에서 크기를 측정하지는 않았다. [FIELD-NORM UNVERIFIED]

문제: 공식 코드를 따른 것은 정당하다. 다만 한국어의 공백 단위(어절)는 조사·어미가 붙은 형태라 같은 법률 개념도 "식품의약품안전처장에게"와 "식품의약품안전처장은"처럼 다른 토큰이 된다. 그래서 Token F1의 +1.11점 차이나 필터링 후 −0.28~−0.54점 차이는 표현 형태 변화에 민감하다. 원고는 "공백 단위"를 밝혔지만 이 특성이 소폭 차이의 해석에 주는 함의는 쓰지 않았다.

제안: §4.4 첫 문단에 "한국어 어절 단위이므로 조사·어미 변화에도 점수가 달라질 수 있어, 소폭 차이는 표현 형태의 변화를 포함한다"는 한 구절을 추가하라. 형태소 단위 Token F1 재계산은 기존 답변으로 API 없이 가능하지만, 공식 지표를 대체하지 않는 **optional** 보조 분석으로만 제안한다.

### Criterion-Bound Judgements (rubric)

| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| D2 domain_accuracy — 원 벤치마크·파이프라인 기술의 사실 정확성 | 카드 #3 Focus 1; 계약 D2 | MEETS | §4.1 ¶1, S1, S2; 업스트림 `selection_retrieval.py` | BM25 k=100, top-10, 목록당 1개 선택, 참조 결함 서술이 공식 코드와 일치 | 원 논문 PDF 수치표 미대조 | no — 사실 오류 없음 |
| D2 — 재현 충실성의 위치 설정 | 카드 #3 Focus 1 | PARTLY_MEETS | W1 (§4.2 ¶4, S5) | 원 논문 보고값·실행 차이 미제시 | 원 논문 값 자체는 심사자 미확인 | yes — Major |
| D2 — 평가 단위의 도메인 타당성 | 카드 #3 Focus 2 | PARTLY_MEETS | W4, W5, W9 | 한계는 정직하게 선언했으나 미매핑 원인과 정답 외 근거의 구조가 미기술 | 심사자 재집계 수치는 저자 확인 필요 | yes — Minor 다수 |
| D2 — 결과 해석(개선 원천·hop·사례) | 카드 #3 Focus 3 | PARTLY_MEETS | W2, W3, W6, W8 | 원천 분리에 필요한 조건부 선택률·hop별 상한이 없고, 사례 C 해석이 한 방향으로 기울어 있음 | 재집계는 기존 산출물로 가능 | yes — Major(W2) |
| Originality (재현·경계 검증 연구로서) | quality_rubrics Dim 1 | MEETS | S1, S3 | 참조 결함 식별과 단계별 탈락 분석은 법률 RAG 재현 연구로서 고유한 기여 | 기여 포지셔닝 판정은 Journal-Fit 소관 | no |
| Evidence Sufficiency (도메인 주장 범위) | quality_rubrics Dim 3 | PARTLY_MEETS | W2, W3 | "근거 선택 성능 향상"의 원천 주장에 필요한 연결 증거가 일부 빠짐 | 통계 추론 세부는 R1 소관 | yes |
| Argument Coherence (도메인 해석) | quality_rubrics Dim 4 | MEETS | S2, W6 | 유보와 결론이 대체로 정합적이며, 사례 C 문장 하나가 예외 | — | no |
| Writing Quality (도메인 용어) | quality_rubrics Dim 5 | PARTLY_MEETS | W9, W8 | 단위 용어 혼용, 그림 라벨의 언어 불일치 | 번역 시 영향 확대 | no — Minor |
| Literature Integration | quality_rubrics Dim 6 | NOT_ASSESSED | — | 제4장에는 관련연구가 없음. 팀 조율 메모로 이관 | 다른 장 소관 | no |
| Significance (법률 RAG 실무 함의) | quality_rubrics Dim 7 | MEETS | S3, §4.3 | 재정렬 단계가 병목의 일부임을 정량화했고, 과장은 없음 | 운영 함의는 R3 소관 | no |

### 번호별 지적 요약 (등급 / 위치 / 변경 제안)

| # | 등급 | 위치 | 한 줄 요지 | 구체적 변경 |
|---|---|---|---|---|
| 1 (W1) | P0 / Major | §4.2 ¶4, §4.1, S5 | 원 논문 보고값·실행 차이 미제시 | 원 논문 ParSeR(GPT-4o) 값을 공개 코드 CE·수정 CE와 병기하고, S5에 실행 차이 표 추가 |
| 2 (W2) | P0 / Major | §4.3 ¶3, 그림 3 | 개선 원천 분리 부족 | 조건부 선택률(79.5% vs 77.6%), shortlist 내 gold 순위 기술통계 추가 |
| 3 (W3) | P1 / Minor | §4.2 ¶4, S6 | 3-hop 1/42의 구조 맥락 부재 | hop별 동시 선택 가능 수(3-hop CE 2 / Jev 11), 목록 수 < gold 수 문항 수 추가 |
| 4 (W4) | P1 / Minor | §4.2 ¶4, 그림 3, S6 | 미매핑 gold의 원인 미설명 | 조 본문·각 호 구획 차이임을 서술하고, 선택적으로 접두 매핑 민감도 분석 |
| 5 (W5) | P1 / Minor | §4.2 ¶1, S6 | 정답 외 근거의 구조 미기술 | 같은 조·같은 법률·하위법령·타 법률 near-miss 분포(사람 평가 없음) |
| 6 (W6) | P1 / Minor | §4.5 ¶3 | 사례 C 해석이 한 방향으로 단정 | 지표 불일치 사례로 중립화 |
| 7 (W7) | P1 / Minor | §4.1 ¶1 | 입력 형식의 공식 코드 일치, Jev 지시문 비대칭 미기재 | 두 구절 추가. 배경 포함 Jev 비교는 optional future work |
| 8 (W8) | P2 / Minor | 그림 3 | Selection loss에 용량 제약과 선택기 오류가 섞임 | 두 하위 범주로 분리, 라벨 언어 통일 |
| 9 (W9) | P2 / Minor | §4.1, §4.2 ¶4 | 단위 용어 혼용 | 평가 단위 고정 문구, "공식 hop별"을 "hop 라벨별"로 수정 |
| 10 (W10) | P2 / Minor | §4.4 ¶1 | 어절 단위 Token F1의 해석 함의 | 한 구절 추가. 형태소 단위 재계산은 optional |

### 팀 조율 메모 (다른 장 소관 — 제4장 수정 요구 아님)

1. **Decision Model / Jev의 정의와 지시문(방법 장)**: Jev에 주어진 관련성 지시문 원문과, 그것이 LLM 선택 프롬프트 기준과 정렬된다는 설계 의도를 방법 장에 명시해야 제4장 W2·W7의 해석이 닫힌다. Jev가 기존 LLM 기반 reranker 계열(pointwise·pairwise·listwise prompting, 지시문 조건 검색 모델)과 어디서 같고 다른지도 관련연구 장에서 위치시켜야 한다(아래 문헌 lead 참조).
2. **ParSeR·KoBLEX 기술(관련연구·방법 장)**: 예상 법령(parametric provision) 생성, bm25s 설정(`stopwords="en"`, 형태소 분석 없는 한국어 토큰화)은 업스트림 설계이다. BM25 미회수 75건의 해석에 필요하므로 방법 장에서 "원 설정 그대로 재현"임을 밝혀 두면 제4장이 짧아진다.
3. **용어집(전 장 공통, 번역 대비)**: 예상 법령/예상 조문(parametric provision), 근거/조문(provision), gold, shortlist, 완전 회수(all-gold recall) 등의 국·영 대응을 한 곳에서 고정할 것.
4. **RQ 정의(서론 장)**: RQ1 제목의 "근거 선택 성능"을 "gold 조문 일치 기준의 근거 선택 성능"으로 정의 단계에서 한정하면, 제4장의 반복 단서를 줄일 수 있다.
5. **원 논문 수치 인용(관련연구 또는 방법 장)**: W1의 원 논문 보고값을 다른 장에서 인용한다면 제4장과 같은 값·같은 지표 정의를 써야 한다.

### Missing Key References

제4장에는 참고문헌이 없으므로 아래는 모두 관련연구 장으로 넘기는 search lead이다. 서지 정보는 심사자 기억에 의존하며 **모두 [UNVERIFIED]**이다. 별도 확인 전에는 인용하지 말 것.

- [UNVERIFIED] LLM 기반 listwise 재정렬: Sun et al., "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents" (2023) — Jev를 LLM reranker 계열 안에 위치시킬 때 참고
- [UNVERIFIED] Pairwise ranking prompting: Qin et al., "Large Language Models are Effective Text Rankers with Pairwise Ranking Prompting" (2023/2024)
- [UNVERIFIED] Seq2seq pointwise 재정렬: Nogueira et al., "Document Ranking with a Pretrained Sequence-to-Sequence Model" (2020)
- [UNVERIFIED] 지시문 조건 검색 모델: Weller et al., "FollowIR: Evaluating and Teaching Information Retrieval Models to Follow Instructions" (2024) — W7의 지시문 비대칭 논의
- [UNVERIFIED] CE 계열 기반: Chen et al., "BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation" (2024) — bge-reranker-v2-m3 계열 배경
- [UNVERIFIED] 한국어 법률 벤치마크: Hwang et al., "A Multi-Task Benchmark for Korean Legal Language Understanding and Judgement Prediction" (2022); Kim et al., "Developing a Pragmatic Benchmark for Assessing Korean Legal Language Understanding in Large Language Models" (2024)
- [UNVERIFIED] 법률 RAG 근거 신뢰성: Magesh et al., "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools" (2024/2025); Pipitone & Alami, "LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain" (2024)
- 검색 lead(특정 문헌 아님): COLIEE statute law retrieval task overview 논문군 — 조문 단위 법령 검색 평가 관례 비교용

~~~yaml suggested-references
- title: "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents"
  authors: ["Sun, W."]
  year: "2023"
  doi: null
  arxiv_id: null
- title: "Large Language Models are Effective Text Rankers with Pairwise Ranking Prompting"
  authors: ["Qin, Z."]
  year: "2024"
  doi: null
  arxiv_id: null
- title: "Document Ranking with a Pretrained Sequence-to-Sequence Model"
  authors: ["Nogueira, R.", "Jiang, Z.", "Lin, J."]
  year: "2020"
  doi: null
  arxiv_id: null
- title: "FollowIR: Evaluating and Teaching Information Retrieval Models to Follow Instructions"
  authors: ["Weller, O."]
  year: "2024"
  doi: null
  arxiv_id: null
- title: "BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation"
  authors: ["Chen, J."]
  year: "2024"
  doi: null
  arxiv_id: null
- title: "A Multi-Task Benchmark for Korean Legal Language Understanding and Judgement Prediction"
  authors: ["Hwang, W."]
  year: "2022"
  doi: null
  arxiv_id: null
- title: "Developing a Pragmatic Benchmark for Assessing Korean Legal Language Understanding in Large Language Models"
  authors: ["Kim, Y."]
  year: "2024"
  doi: null
  arxiv_id: null
- title: "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools"
  authors: ["Magesh, V."]
  year: "2024"
  doi: null
  arxiv_id: null
- title: "LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain"
  authors: ["Pipitone, N.", "Alami, G. H."]
  year: "2024"
  doi: null
  arxiv_id: null
~~~

### Questions for Authors

1. 원 논문이 보고한 ParSeR(GPT-4o)의 근거 F1·LF-Eval·Token F1은 공개 코드 CE(48.72)와 수정 CE(58.57) 중 어느 쪽에 가까운가? 생성 모델 snapshot 차이를 고려할 때 그 비교를 어느 강도로 해석할 계획인가?
2. 미매핑 gold 27개가 조 본문과 각 호의 구획 차이 때문이라는 심사자 관찰(26/27이 corpus 행을 접두로 포함)을 저자 코드로도 재현할 수 있는가? 각 호가 corpus에 별도 행으로 존재하는가?
3. Jev 지시문은 선택 프롬프트의 기준을 의도적으로 맞춘 것인가? 맞췄다면 이는 "재정렬기 교체"가 아니라 "재정렬 기준의 정렬"이라는 해석 차이를 낳는데, 제4장에서 어떻게 표현할 것인가?
4. 3-hop에서 Jev가 shortlist 동시 선택 가능 문항을 11개로 늘렸는데도 완전 회수가 1개에 그친 원인을 선택 단계(같은 목록 내 경쟁, 순위 위치)에서 기존 자료로 진단할 수 있는가?

### Minor Issues

- §4.1 "총 478개의 후보 목록"과 gold 출현 443건의 관계(목록 수가 gold 수와 독립적으로 정해짐)를 한 구절로 연결하면 §4.3의 상한 논의가 더 쉽게 읽힌다.
- 사례 B의 법률 서술("복수 당사자 청구 절차")은 casebook과 일치한다. 제79조(독립당사자참가)와 제83조(공동소송참가)가 같은 법률의 소송참가 규정이라는 구조적 사실은 법률 판단 없이 서술할 수 있다. 지면이 허락하면 오류 유형(동일 법률 인접 조문)으로 요약할 수 있다.
- 그림 1–3의 영문 라벨과 국문 본문 간 용어 대응(Reranking loss = shortlist 탈락 등)을 캡션에서 한 번 명시하라.
