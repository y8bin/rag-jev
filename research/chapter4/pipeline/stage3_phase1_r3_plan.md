## Contract Paraphrase

D1 (methodology_rigor): 연구 설계, 데이터 처리, 통계 보고, 재현 가능성 장치가 해당 분야 심사 기준을 충족하는지에 관한 차원이다. methodology seat 소관이며, 나는 운영 재현성 관점의 관찰을 Review Body에 남길 수는 있으나 이 차원에 점수를 매기지 않는다.

D2 (domain_accuracy): 주장이 현재 도메인 증거와 맞고, 선행 연구가 정확히 표현되며, 도메인 용어·결과에 사실 오류가 없는지에 관한 차원이다. domain seat 소관이며 나는 점수를 매기지 않는다.

D3 (argumentative_coherence): 핵심 논지가 내부적으로 일관되고 증거가 주장을 지지하며 논리적 오류가 없는지에 관한 차원이다. DA와 methodology seat 소관이며 나는 점수를 매기지 않는다.

D4 (cross_disciplinary_relevance): 인접 분야 독자(여기서는 ML systems·배포 실무자)가 틀·정의·함의를 이해하고 사용할 수 있는지, 그리고 학제적·실무적 함의 주장이 증거로 뒷받침되는지에 관한 차원이다. 나의 유일한 채점 차원이며, 배포 의사결정자가 결과 장에서 얻는 정보(지연·비용·비결정성·외부 의존성·거버넌스)가 충분하고 과장되지 않았는지를 기준으로 판단한다.

D5 (writing_and_structure): 원고 구성, 서술 명료성, 그림·표 품질, venue 관례 준수에 관한 차원이다. EIC(Journal-Fit) seat 소관이며 나는 점수를 매기지 않는다.

D6 (venue_fit_and_contribution): 설정된 venue에 맞고 그 독자에게 독창적·유의미한 기여를 하는지에 관한 차원이다. EIC seat 소관이며 나는 점수를 매기지 않는다.

## Scoring Plan

### D4: cross_disciplinary_relevance
dimension_id: D4
what_to_look_for: 배포 결정에 필요한 운영 지표(지연의 측정 범위와 조건, 비용 회계, 외부 API 모델의 버전 고정과 비결정성, 재현·감사 가능성, 민감 데이터 외부 전송)가 정의·측정 범위와 함께 명시되는지, 실무 함의 문장이 측정된 범위를 넘지 않는지, 인접 분야 독자가 용어와 단위를 오해 없이 읽을 수 있는지
what_triggers_block: 실무·배포 관련 핵심 함의(예: 교체 권고, 비용·효율 이점)가 측정되지 않았거나 측정 조건과 상충하는 증거에 기대어 단정적으로 제시되어, 배포 의사결정자가 결과를 잘못 적용할 가능성이 큰 경우
what_triggers_warn: 운영 지표는 보고되었으나 측정 범위·배포 조건 의존성·비결정성의 운영 함의가 결과 서술 안에서 충분히 연결되지 않아 독자가 스스로 한계를 재구성해야 하는 경우, 또는 인접 분야 독자에게 핵심 용어·단위가 모호한 경우

criteria_binding_unavailable

[CONTRACT-ACKNOWLEDGED]
