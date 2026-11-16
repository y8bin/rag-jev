# Stage 3 Phase 1 — Journal-Fit Reviewer (eic) paper-blind pre-commitment

- Seat: Reviewer Configuration Card #1 (Journal-Fit Reviewer, eic)
- Contract: `shared/contracts/reviewer/full.json` (reviewer_full, panel_size 5)
- 작성 시점: 원고(chapter4.md / supplement / PDF / figures) 열람 **이전**. 카드 #1과 contract만 참조.
- 본 계획 이후 원고를 열람하며, 계획과 다른 판단이 필요하면 Phase 2 리뷰에 `## Scoring Plan Dissent`(1개 차원 한정)로 명시한다.

## Contract Paraphrase

D1 methodology_rigor — 연구 설계, 데이터 처리, 통계 보고, 재현 가능성이 해당 분야 동료심사 기준을 충족하는지를 보는 차원이다. 편집 관점에서 중요하지만 이 좌석의 채점 대상이 아니며 Methodology 심사자에게 위임한다(not_assessed).

D2 domain_accuracy — 주장이 현행 도메인 근거와 정합하고 선행연구를 정확히 대표하며 도메인 용어·결과에 사실 오류가 없는지를 본다. Domain 심사자 소관이며 이 좌석은 채점하지 않는다(not_assessed).

D3 argumentative_coherence — 핵심 주장이 내적으로 일관되고 증거가 주장을 뒷받침하며 중심 논증을 무너뜨리는 오류가 없는지를 본다. DA·Methodology 소관이며, 이 좌석은 구조적 정합성(결론이 질문에 답하는지)을 서술로만 언급하고 점수는 매기지 않는다(not_assessed).

D4 cross_disciplinary_relevance — 인접 분야 독자에게 framing·정의·함의가 접근 가능하고 학제 간 주장이 입증되는지를 본다. Perspective 심사자 소관이다(not_assessed).

D5 writing_and_structure — 원고의 조직, 설명의 명료성, 그림·표 품질, 투고처 관례 준수를 본다. 이 좌석이 소유한다. 장 단위·3쪽 지면·국문 초안→영문 번역 경로라는 조건에서, 독자가 핵심 결과를 빠르게 찾을 수 있게 배치되었는지와 용어 일관성이 판단 핵심이다. venue가 미확정이므로 특정 venue 서식 규칙은 적용하지 않고 분야 일반 관례로만 판단한다.

D6 venue_fit_and_contribution — 원고가 구성된 투고처에 적합하고 독자에게 독창적·유의미한 기여를 하는지를 본다. 이 좌석이 소유하며 mandatory 차원이다. target venue binding이 없으므로 venue 적합성 주장은 하지 않고, 분야 일반 기준(응용 NLP/IR 실증 결과 장)으로 기여의 식별 가능성·의미·과장 여부를 판단한다.

## Scoring Plan

### D5: writing_and_structure
dimension_id: D5
what_to_look_for: 각 연구 질문에 대한 주 결과가 소절 첫머리 1-2문장으로 식별되는지, 유보·한계 문장의 밀도가 핵심 메시지를 가리는지, 3쪽 지면의 소절별 분량 배분이 정보가치에 비례하는지, 그림·표가 본문 주장과 1:1로 대응하고 단독 판독 가능한지(캡션·축·단위), 수치 단위 표기(점/%p/%)와 핵심 용어의 국문·영문 일관성
what_triggers_block: 독자가 장 본문만으로 어느 연구 질문에 어떤 답이 나왔는지 식별할 수 없거나, 그림·표와 본문 수치가 서로 모순되어 결과 판독 자체가 불가능한 경우
what_triggers_warn: 핵심 결과는 식별 가능하나 유보 문장 밀집·지면 배분 불균형·용어/단위 표기 불일치·캡션 불충분 중 하나 이상이 독해나 번역 투고에 실질적 비용을 만드는 경우

### D6: venue_fit_and_contribution
dimension_id: D6
what_to_look_for: 장이 독자에게 넘기는 기여가 무엇인지(재현 과정의 발견, 구성요소 교체 효과, 비용·지연 trade-off 등)가 구분되어 제시되는지, 각 기여의 크기와 불확실성이 결론 문장 강도와 맞물리는지, 응용 NLP/IR 실증 결과로서 독자가 실무·연구 결정에 쓸 수 있는 정보인지, 기여 범위(단일 벤치마크 등)가 정직하게 경계지어졌는지
what_triggers_block: 결론 문장이 제시된 증거 범위를 체계적으로 넘어서 기여를 과장하거나, 장이 주장하는 주 기여가 결과에서 실질적으로 입증되지 않아 수정 없이는 기여 진술을 유지할 수 없는 경우
what_triggers_warn: 기여는 입증되나 기여 유형 간 구분이 흐리거나, 효과 크기 대비 프레이밍이 약간 강하거나 약해 독자가 가져갈 메시지가 불분명하거나, 기여 범위가 좁아 분야 일반 독자의 관심을 끌기 위한 포지셔닝 보강이 필요한 경우
what_triggers_fatal: 장의 핵심 결과가 데이터·분석 오류로 무효이거나 주 기여가 이미 알려진 결과의 단순 반복에 불과해 어떤 서술 수정으로도 기여 진술이 성립하지 않는 경우

criteria_binding_unavailable

## 판정 운영 메모 (contract 외 보조, 원고 비의존)

- 카드 #1 Review Focus 1-3을 위 D5/D6의 what_to_look_for에 매핑: Focus 1(RQ별 주 결과·유보 밀도) → D5, Focus 2(기여 성격 구분) → D6, Focus 3(지면·그림표·번역 용어) → D5.
- 다른 장(RQ 정의, Decision Model 정의, 관련연구, 방법)이 필요한 지적은 "팀 조율 메모"로 분리하고 수정 요구·점수 근거로 쓰지 않는다.
- 사람 평가 추가 요구 금지. 새 유료 실험은 optional future work 표기로만.
- 심각도 매핑(사용자 요청 형식): P0 must-fix ≈ Critical/주요 정합성 결함, P1 should-fix ≈ Major/중요 개선, P2 optional ≈ Minor.

[CONTRACT-ACKNOWLEDGED]
