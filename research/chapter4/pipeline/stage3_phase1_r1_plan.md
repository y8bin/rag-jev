# Stage 3 Phase 1 — Peer Reviewer 1 (Methodology) 사전 채점 계획

- 작성 시점: 원고(chapter4.md / supplement / PDF) 열람 **전**. 근거는 Reviewer Configuration Card #2와 panel-wide standing constraints뿐이다.
- 별도 sprint contract JSON이 제공되지 않았으므로, 아래 차원은 `references/quality_rubrics.md`의 Methodological Rigor / Evidence Sufficiency / Argument Coherence(결론-증거 정합 부분)와 카드 #2 Review Focus에서 도출한 자체 계약이다.
- Venue: `criteria_binding_unavailable` — 특정 저널 기준 인용 없이 분야 일반(응용 NLP/IR 실증 연구) 기준을 적용한다.
- Calibration: `NOT_CALIBRATED`.

## Contract Paraphrase

1. **D1 추론 설계·통계 보고**: paired cluster bootstrap이 의존 구조(문항 그룹)를 올바르게 반영하는지, CI와 p값이 같은 절차에서 나오며 서로 모순 없이 해석되는지, 다중 비교·사후 분석 성격이 문장 강도에 반영되는지.
2. **D2 데이터 누수·선택 편향**: 설정 선택(CE 입력 형식, 필터링 문턱값, 사례 선정)이 평가 대상과 같은 데이터에서 이루어져 낙관적 편향을 만드는지, 그리고 그 사실이 공개되고 결론에서 할인되는지.
3. **D3 측정 타당성·재현성**: 비결정적 원격 API(Jev)의 단일 실행 수치, 지연 측정의 조건 confound, LLM-as-judge(생성기=평가기)의 자기선호 편향, 절단 규칙 등 측정 도구 자체의 한계가 수치 해석을 얼마나 제한하는지.
4. **D4 결론-증거 정합**: 각 결론 문장(특히 RQ1·RQ3)의 강도가 보고된 효과 크기·CI·무보정 탐색 성격과 맞는지.

## Scoring Plan

### D1: 추론 설계·통계 보고 (Methodological Rigor 하위)
dimension_id: D1
what_to_look_for: 재표본 단위(151 의존 그룹) 정의와 근거, B·seed·CI 방식(percentile 등), p값 산출 방식(centered bootstrap)과 CI 방식의 일치, 효과크기·문항별 승/패/동률 보고, 다중 비교 수·보정 여부, 사전 등록/protocol lock 대비 탐색 분석 구분
what_triggers_block: 주요 결론의 근거가 되는 CI/p가 서로 다른 절차에서 나와 결론이 뒤집히거나(예: CI는 0 배제, p>0.05), 재표본 단위가 의존 구조를 무시해 CI가 과소추정됨이 확인될 때
what_triggers_warn: 절차는 타당하나 percentile CI와 centered p의 불일치를 설명하지 않거나, 무보정 다중 비교를 서술상 확증적 언어로 사용할 때
what_triggers_fatal: 보고 수치가 원자료(results/analysis.json 등)와 불일치하거나 통계 절차가 원자료로 재현 불가능한 경우

### D2: 데이터 누수·선택 편향
dimension_id: D2
what_to_look_for: CE 입력 형식 선택에 쓴 30문항과 평가 집합의 관계, 필터링 문턱값 CV가 평가 226문항 내부인지 및 nested 여부, 사례 선정 규칙의 사전 고정 여부와 대표성, 비교 조건 간 비대칭 튜닝(CE만 튜닝 혹은 Jev만 튜닝)
what_triggers_block: 튜닝/선택이 평가 집합에서 이루어졌는데 그 결과를 일반화 가능한 성능으로 주장할 때
what_triggers_warn: 누수가 공개·인정되었으나 크기 추정(예: 선택 집합 제외 재분석)이나 결론 할인이 없을 때
what_triggers_fatal: 비공개 누수가 핵심 비교(CE vs Jev)의 방향을 좌우할 정도로 확인될 때

### D3: 측정 타당성·재현성
dimension_id: D3
what_to_look_for: Jev 반복 실행 재현율(순서/집합)과 그것이 품질 수치 분산에 주는 함의, 지연 측정의 표본·조건(로컬 MPS vs 원격 API, 품질 실행과 분리), LF-Eval 평가기=생성기 동일 모델, 800자 절단, gold 미매핑 문항 처리, 모델 버전 고정
what_triggers_block: 측정 도구의 편향이 비교 조건 간 비대칭적으로 작용할 근거가 있는데 논의가 없을 때
what_triggers_warn: 한계는 서술되었으나 그 크기를 기존 자료로 추정할 수 있음에도 하지 않았을 때(예: 반복 실행 분산을 CI에 반영하지 않음)
what_triggers_fatal: 보고 수치가 재현 불가능한 단일 draw임에도 그 사실이 숨겨져 있을 때

### D4: 결론-증거 정합
dimension_id: D4
what_to_look_for: 요약·결론 문장에서 "향상/개선/유지" 등의 동사 강도, EM·완전 회수 CI 0 포함 여부와 서술, 비열등성 마진 없는 "유지" 주장, hop별 subgroup 해석의 과잉 여부, 지연 trade-off 서술의 범위 한정
what_triggers_block: CI가 0을 포함하는 지표에서 개선을 단정하거나, 마진 없이 동등성/유지를 주장할 때
what_triggers_warn: 단정은 피했으나 문장 배치·요약에서 독자가 확증적 결과로 읽을 여지가 클 때
what_triggers_fatal: 결론이 보고된 방향과 반대이거나 원자료와 모순될 때

## 증거 수집 계획
- chapter4.md 본문의 모든 CI·p·승패 수치 → results/analysis.json, chapter4-prep-v1/ 와 대조(읽기 전용)
- supplement의 bootstrap 설정·CV 절차·사례 선정 규칙·재현 실험 기술 확인
- 저장된 문항별 자료로 가능한 추가 분석(예: hop 층화 CI, 반복 실행 draw 간 F1 차이, 선택 30문항 제외 재분석) 가능성 확인 → 제안 시 "기존 자료만 필요" 표기
- Standing constraints: 제4장만 심사, 타 장 필요 사항은 "팀 조율 메모"로 분리, 사람 평가 요구 금지, 새 유료 실험은 optional future work로만

criteria_binding_unavailable

[CONTRACT-ACKNOWLEDGED]
