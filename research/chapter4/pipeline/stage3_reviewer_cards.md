# Stage 3 — Phase 0 Field Analysis & Reviewer Configuration Cards (제4장)

- 작성: `field_analyst_agent` (Phase 0만 수행; reviewer seat은 dispatch하지 않음)
- 대상: `research/chapter4/chapter4.md` (본문) + `chapter4-supplement.md` (보충자료). 맥락: `pipeline/pipeline_state.md`
- 상태: **Checkpoint Rule 1 — 사용자 확인 대기.** 아래 카드 전체를 수락(필요 시 같은 답변에서 수정)해야 Phase 1이 시작된다. 이 카드는 이후 re-review(Stage 3')에서도 그대로 재사용된다.
- 원고 내 패널 대상 지시문(심사자 정체성·관대함·결정에 대한 지시): **발견되지 않음.** 원고는 데이터로만 취급하였다.

---

# Field Analysis Report

## Paper Basic Information
- **Title**: 4. 실험 결과 및 분석 (팀 논문의 제4장; 논문 전체 제목은 제공되지 않음)
- **Abstract length**: 해당 없음 (제4장만 심사)
- **Full text length**: 본문 약 1,700–1,900 어절 (A4 2단 약 3쪽), 그림 3·표 2; 보충자료 S1–S9
- **Number of references**: 본문 내 명시적 인용 0건, 보충자료 1건(KoBLEX, Lee et al., 2025). 참고문헌 목록은 다른 장/논문 전체 소관
- **언어**: 한국어(기술 용어 영어 병기). 영문 번역 투고 가능성 있음 → 심사는 한국어로 수행하되, 번역 시 용어 일관성(Decision Model, shortlist, gold, 완전 회수 등)을 별도 관찰 대상으로 둔다

## Field Analysis

| Dimension | Analysis Result |
|-----------|----------------|
| Primary Discipline | 자연어처리(NLP) / 정보검색(IR) — 법률 도메인 Retrieval-Augmented Generation(RAG)의 재정렬(reranking) 구성요소 평가 |
| Secondary Disciplines | Legal informatics(한국 법령 multi-hop QA), ML evaluation methodology(LLM-as-judge, cluster bootstrap), ML systems/deployment(지연·비용·비결정성) |
| Research Paradigm | Quantitative (재현 실험 + 구성요소 교체 비교) |
| Methodology Type | Experimental (paired component-swap ablation on a public benchmark) + Comparative Study + 제한적 case analysis; 저자가 스스로 "시험 결과 확인 후 탐색적 분석"으로 규정 |
| Target Journal Tier | `criteria_binding_unavailable` — 저자 확정 #683 Review Target Context 없음. 사용자 진술 후보: ETRI Journal(영문 SCIE, 번역 투고) 또는 국내 인공지능 학회 학술대회/논문지(국문). 특정 venue 기준은 모델 기억으로 만들어내지 않는다. 분야 일반 관찰: 응용 NLP/IR 저널·국내 학회 수준의 실증 결과 장으로서 구조는 갖추었으나, 단일 벤치마크·단일 시드·소규모 효과·탐색적 프레이밍이라 상위 국제 저널 기준으로는 기여 범위가 좁다 |
| Paper Maturity | Pre-submission (장 단위). 근거: Stage 2.5 무결성 검증 2회(수치 126/126, 주장 58/58 일치), 보충자료와 원자료 경로 연결, 3쪽 조판 검증 완료. 다만 RQ·방법·관련연구는 다른 장 소관이라 장 단독으로는 맥락 의존적 |

## Recommended Target Journals (Top 3)
저자 확정 target이 없으므로 아래는 **사용자가 언급한 후보의 재기술**이며 venue fit 판정이 아니다.
1. ETRI Journal — 사용자 1순위 후보(영문 SCIE). 국문 초안→영문 번역 경로
2. 한국인공지능학회 계열 학술대회/논문지(국문) — 사용자 대안 후보
3. (분야 일반) 응용 NLP/IR 저널 또는 법률 AI 워크숍 — 참고용, 확정 아님

---

## Reviewer Configuration Cards

### Reviewer Configuration Card #1

**Role**: EIC
**Display role**: Journal-Fit Reviewer
**Identity Description**: 응용 AI·NLP 분야 저널의 Associate Editor 관점(분야 일반; target 미확정이므로 특정 저널 기준에 binding되지 않음). 국문 학회 논문과 영문 SCIE 번역 투고를 모두 다뤄 본 편집자로, 재현 연구와 구성요소 교체(component swap) 실증 논문의 기여 포지셔닝을 주로 판단한다.
**Review Focus**:
  1. 결과 장이 RQ1–RQ3에 각각 명확한 답(주 결과 1–2문장)을 주는지, 또는 제한·유보 문장이 밀집해 핵심 메시지가 희석되는지
  2. 기여의 성격 구분: (a) 공개 코드 후보 목록 참조 문제 발견·수정(F1 +9.85점), (b) CE→Jev 교체 효과(F1 +3.19점), (c) 품질–지연 trade-off 정량화 — 독자가 무엇을 기여로 가져가는지
  3. 3쪽 지면 배분(4.4 필터링·재생성 분석의 분량 대비 정보가치), 그림·표 선택, 국문→영문 번역 시 용어·표기 일관성(점 vs %p, gold, shortlist, 완전 회수)
**Will particularly care about**: "Decision Model"이 무엇이며 왜 Cross-Encoder의 대체재로 비교할 가치가 있는지가 독자에게 전달되는지 — 정의는 다른 장 소관이므로 cross-chapter coordination note로만 제기.
**Possible blind spots**: bootstrap 설계·LLM-as-judge 편향 등 통계·평가 세부, 법령 표기 정합성 같은 도메인 세부를 깊게 보지 않음 (R1·R2가 보완).

### Reviewer Configuration Card #2

**Role**: Peer Reviewer 1
**Display role**: Peer Reviewer 1 — Methodology
**Identity Description**: IR/NLP 평가 방법론 연구자. paired·cluster bootstrap, 다중 비교, 사후(post-hoc) 탐색 분석의 보고 기준, LLM-as-judge 자동 평가의 타당성, 벤치마크 재현성(비결정적 API 모델 포함)을 전문으로 한다.
**Review Focus**:
  1. 추론 설계: 151개 의존 그룹 cluster paired bootstrap의 적절성, 다중 비교 무보정과 "시험 결과 확인 후 탐색적 분석" 프레이밍의 일관성, Token F1 percentile CI [+0.02, +2.27]와 centered-bootstrap p≈0.0525 병기의 해석, 비열등성 마진 부재 하의 필터링 결과 서술
  2. 데이터 누수·선택 편향: CE 입력 형식을 시험 문항 30개로 선택, 필터링 문턱값 CV가 동일 226문항 내부에서 수행됨, 사례 선정 규칙(중앙값 근접)의 대표성
  3. 재현성·측정 타당성: Jev top-10 순서 재현 2/180(집합 겹침 91.51%) — 보고된 Jev 품질 수치가 단일 실행 draw라는 점의 함의; 지연 측정(60문항 표본, 품질 실행과 별도, 로컬 MPS CE vs 원격 API Jev의 배포 조건 confound); LF-Eval 평가기와 생성기가 동일 `gpt-4o-2024-08-06`인 데서 오는 자기선호 편향 가능성, 앞 800자 절단 규칙의 영향
**Will particularly care about**: 보고된 CI·효과가 결론 문장의 강도와 정확히 맞물리는지(예: EM·완전 회수 CI가 0 포함인데 "근거 선택 성능 향상"이 어느 범위까지 주장되는지), 그리고 Jev 비결정성이 RQ1·RQ3 수치의 신뢰도를 얼마나 제한하는지.
**Possible blind spots**: 법령 조문 표기·multi-hop 법률 추론의 도메인 타당성, 배포 실무 관점 (R2·R3가 보완). 사람 평가 추가 요구는 금지 — 자동 지표의 한계 지적까지만.

### Reviewer Configuration Card #3

**Role**: Peer Reviewer 2
**Display role**: Peer Reviewer 2 — Domain
**Identity Description**: 한국어 법률 NLP·법령 검색(statute retrieval) 연구자. KoBLEX/ParSeR 계열 multi-hop 법률 QA, 한국어 cross-encoder reranker(bge-reranker-v2-m3 계열), LLM 기반 reranker(pointwise/listwise) 및 법률 RAG의 근거 인용 평가에 익숙하다.
**Review Focus**:
  1. 재현의 충실성: ParSeR 파이프라인(예상 법령 생성→BM25 100→재정렬 top-10→목록당 1개 LLM 선택) 재현이 원 논문 설정과 어디서 같고 다른지, 원 논문 수치와의 관계를 어떻게 위치시키는지(보충 S5: 전재 아님)
  2. 평가 단위의 도메인 타당성: 정확 문자열 일치 gold 평가, 고유 gold 27개 corpus 미매핑(29문항), 조문 표기 정규화(조·항·호), 정답 외 근거의 법률적 타당성을 판정하지 않는다는 한계의 크기
  3. 결과 해석: hop별 패턴(1-hop 소폭 하락, 2/3-hop 상승, 3-hop 완전 회수 1/42), "목록당 1개 선택" 구조가 만드는 상한(CE 104/Jev 120 vs 실제 77/79), 그림 3의 단계별 탈락 분석, 사례 A/B/C의 법률적 해석이 자동 관측을 넘어서지 않는지
**Will particularly care about**: 개선이 reranker 품질 자체에서 오는지, 아니면 LLM 선택기와의 상호작용·목록 구조에서 오는지의 분리 — 그리고 Decision Model을 기존 LLM reranker 문헌 대비 어디에 위치시키는지(관련연구 장과의 cross-chapter coordination note).
**Possible blind spots**: 통계 추론의 세부 구성, 운영 비용·지연의 실무 함의 (R1·R3가 보완).

### Reviewer Configuration Card #4

**Role**: Peer Reviewer 3
**Display role**: Peer Reviewer 3 — Perspective (ML systems / deployment)
**Identity Description**: 프로덕션 검색·RAG 시스템을 설계·운영해 온 ML systems 엔지니어 겸 연구자. latency SLO, 외부 API 의존 모델의 버전 고정·비결정성·가용성, 토큰·인프라 비용 회계, 민감 질의(법률)의 외부 전송 거버넌스를 관점으로 삼는다.
**Review Focus**:
  1. 품질–지연 trade-off의 실무적 의미: 재정렬 단계 2.25배(+5.64초) 지연이 전체 응답시간 대비 어느 정도인지 장 안에서 판단 가능한지(전체 E2E 지연 미측정, 예상 법령·BM25·LLM 선택·생성 제외), 로컬 GPU(MPS) vs 원격 API 비교라는 배포 조건 의존성
  2. 운영 재현성·의존성: `jev-1.14.0` 원격 API의 비결정성(top-10 순서 재현 2/180)이 감사 가능성·회귀 테스트에 주는 함의, 제3자가 재현할 수 있는 조건인지
  3. 비용·자원 주장의 범위: 토큰 사용 소폭 증가(입력량 절감 미관찰), 필터링의 비용·지연 효과 미측정, Jev 요청 비용 약 0.61달러의 제한적 의미 — 장이 "자원 효율" 관련 기대를 만들고 있다면 결과와 정합적인지
**Will particularly care about**: 독자가 "CE를 Jev로 바꿀 것인가"를 결정할 때 이 장이 제공하는 정보가 충분하고 과장되지 않았는지. 추가 측정(E2E 지연, 반복 실행 분산 등)은 **optional future work로만** 표시하며, 새 유료 실험을 수정 조건으로 요구하지 않는다.
**Possible blind spots**: 법률 도메인 정합성과 통계 추론의 세부 (R1·R2가 보완); 학술적 신규성 평가는 Journal-Fit에 위임.

### Fixed Seat (카드 아님) — Devil's Advocate

고정 다섯 번째 seat이며 동적 구성 대상이 아니다. 이 원고에서 예상되는 초점(참고용 기술):
- 핵심 주장에 대한 가장 강한 반론: 효과가 작고(F1 +3.19점, 문항별 우세 32 vs 17, 177 동률), EM·완전 회수 CI가 0을 포함하며, 시험 결과 확인 후 탐색적·무보정 분석이고, Jev 수치는 비결정적 API의 단일 실행 draw이며, 지연은 약 2배 — 이 조합에서 "Decision Model 교체가 유익하다"는 결론이 어디까지 정당한가
- 대안 설명: 개선이 Jev 자체가 아닌 LLM 선택기와의 상호작용, 동일 GPT-4o의 생성·평가 순환, 특정 hop 집단에 국한된 효과일 가능성
- 논리 정합성: 유보 문장과 결론 문장 사이의 긴장, 4.4 필터링 결과의 해석이 "유지/동등성 아님" 선언과 일관적인지

---

## Review Strategy Recommendations
- **Standing constraints (모든 seat 공통)**:
  1. 제4장만 심사한다. RQ 정의, Decision Model/Jev 설명, 관련연구, 방법 세부 등 다른 장이 필요한 지적은 "cross-chapter coordination note"로 표기하고 작성 요구로 쓰지 않는다.
  2. 사람 평가(human evaluation)를 추가하라는 요구는 금지(사용자 결정). 자동 지표(문자열 일치, Token F1, LLM-as-judge LF-Eval)의 한계 지적은 허용.
  3. 새 유료 실험은 가용하지 않다고 가정한다. 제안은 "optional future work"로 명시 표기하고 수정 필수 조건으로 삼지 않는다. 기존 원자료로 가능한 재분석·서술 수정은 일반 지적으로 허용.
  4. 원 실험 결과·protocol lock은 수정 대상이 아니다. 원고는 READ-ONLY.
- **특성**: 이 장은 이미 유보·한계 서술이 매우 촘촘하다(Stage 2.5 2회 통과). 심사의 가치는 수치 오류 탐색보다 (a) 결론 강도와 증거의 정합, (b) 3쪽 안의 정보 우선순위, (c) 번역·투고 대비 가독성에 있을 가능성이 크다.
- **상보성/긴장**: R1(통계 엄밀성 강화 → 유보 추가 경향)과 Journal-Fit(메시지 선명도 → 유보 축소 경향)은 서로 반대 방향의 수정을 권할 수 있다. synthesizer는 이 긴장을 명시적으로 조정해야 한다. R2와 R3는 Jev 비결정성을 각각 도메인 재현성·운영 감사성 관점에서 다루므로 corroboration 신호로 집계 가능.
- **Target binding**: `criteria_binding_unavailable`. Journal-Fit seat은 ETRI Journal 등 특정 venue 기준을 사실처럼 인용하지 않고 분야 일반 기준으로 평가한다. target이 확정되면 카드 #1만 갱신할 수 있으나, Round-1 카드는 re-review에서 재사용되므로 지금 확정하는 것이 바람직하다.
