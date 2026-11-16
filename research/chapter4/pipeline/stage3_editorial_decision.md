# Stage 3 Phase 2 — 편집 결정서 (Editorial Decision Letter, 제4장)

- 작성: `editorial_synthesizer_agent` (Phase 2 종합). 새 심사 의견을 만들지 않으며, 모든 항목은 아래 다섯 seat 보고서의 특정 지적 ID에 연결된다.
- 입력: `stage3_reviewer_cards.md`(사용자 승인 카드), `stage3_review_{eic,r1,r2,r3,da}.md`, `stage3_phase1_*_plan.md`, `pipeline_state.md`. 원고 `research/chapter4/chapter4.md`, `chapter4-supplement.md`는 READ-ONLY로 대조만 하였다.
- 상세 수정 항목: `stage3_revision_roadmap.md` (RM-01 ~ RM-30)
- `calibration_status: NOT_CALIBRATED` / target binding: `criteria_binding_unavailable` (ETRI Journal 영문 번역 투고 유력, 국내 AI 학회 대안 — 특정 venue 규정은 적용하지 않음)
- 교차 모델 결정 점검(#518): 사용자 지시로 사용하지 않음(`ARS_CROSS_MODEL` 미설정).
- Review Panel Provenance(#540): 형식화된 provenance artifact가 제공되지 않았다. 다섯 seat은 같은 세션 모델 계열의 역할 분리 페르소나이며, 각 seat은 원고 열람 전 계획을 commit하고 동료 보고서를 보지 않았다고 자기 보고하였다. 이 기록만으로는 실행 독립성 6개 축을 검증할 수 없으므로 모든 축을 `unknown`으로 둔다. 역할 분리는 오류 과정의 독립성을 뜻하지 않는다(상관된 오류 가능성 있음).

---

저자(팀) 귀하,

제4장 "실험 결과 및 분석" 원고는 다섯 개의 역할 분리 심사 seat(Journal-Fit Reviewer, 방법론 R1, 도메인 R2, ML 시스템·배포 R3, Devil's Advocate)이 검토하였습니다.

## 결정: **Minor Revision (소폭 수정)**

```
dimension_verdicts: [D1=warn(R1 narrative: PARTLY_MEETS), D2=warn(R2), D3=warn(DA), D4=warn(R3), D5=warn(EIC), D6=warn(EIC)]
fired_conditions: []  (sprint-contract 실패 조건 미정의 — no-contract 경로의 정성 기준 적용)
da_critical_adjudications: []
editorial_decision=minor_revision
```

다섯 seat 모두 Minor Revision을 권고하였고, 어떤 seat도 block·fatal 판정을 내리지 않았습니다. Devil's Advocate는 CRITICAL 0건을 명시하였습니다(DA §1, §8).

---

## 1. 심사자 요약 매트릭스

| 항목 | EIC (Journal-Fit) | R1 (방법론) | R2 (도메인) | R3 (배포) | DA |
|---|---|---|---|---|---|
| 권고 | Minor | Minor | Minor (경계 사례로 명시) | Minor | Minor (CRITICAL 0) |
| Confidence(자기 보고) | 4 | 4 | 4 | 4 | — |
| 핵심 강점 | 결함 수정·교체 효과 분리, 단계별 탈락 분해, 결론 절제 | 3-arm 설계, cluster paired bootstrap, 탐색적 프레이밍 | 공식 코드 결함의 정확한 식별, 사례·원자료 정합 | 지연 프로토콜, 배포 조건 한정, 비결정성 공개 | 메커니즘(shortlist 유지→최종 근거)이 재분석에서 지지됨 |
| 핵심 약점 | 메시지 선명도(RQ 답 문장·요약 부재), 4.4 지면 편중, 필터링 보고 비대칭 | 필터링 선택적 구간 보고, 격자 사후 변경 미공개, 다중성·경계값 | 재현 충실성 위치 설정, 개선 원천 분리 | E2E 규모 단서, 자원 범위, 비결정성의 운영 함의 | 단일 Jev 실행 조건부 CI, 필터링 비대칭·교차 비교 |
| 지적 수 | W1–W11 + 질문 4 | C1–C15 + 질문 4 | W1–W10 + 질문 4 | W1–W9 + 질문 4 | P1-1~P2-10 |

Confidence는 자기 보고 불확실성 표기일 뿐이며 합의 집계·결정에 쓰지 않았습니다.

## 2. 합의 분석 (Consensus Analysis)

집계 분모는 non-DA 4개 seat(EIC, R1, R2, R3)입니다. "언급 없음"은 동의도 반대도 아닙니다. DA는 별도 표기합니다.

### [CONSENSUS-3] 강한 다수
- **SC-04 Jev 품질 수치는 비결정적 원격 API의 저장된 단일 실행 값이며, 보고된 CI는 문항 표본 변동만 반영한다 — 이 해석 조건이 4.3 말미에만 있고 RQ1 결과와 연결되지 않는다.** EIC-W6, R1-C6, R3-W4(a) 제기 / R2 언급 없음 / DA-P1-1(M1) 동조. → RM-03

### 확증된 지적 (2/4, 반대 없음)
- **SC-01 필터링 절의 보고 비대칭**: Jev+필터링의 0 배제 감소(Recall CI [−3.81, −1.16], 완전 회수 −1.77%p CI [−3.51, −0.43])가 본문에 없음. EIC-W4(P0·Major), R1-C1(P0·Major) / DA-P1-2(M2) 동조. 구간 값은 seat 재계산이 아니라 `results/koblex-filtering-v1/summary.json`·`e2e-summary.json`의 저장 값임(EIC·R1·DA가 같은 값 인용). → RM-01
- **SC-03 필터링의 동기 부재와 지면 대비 정보가치, 조건 간 교차 비교의 불일치**: EIC-W3, R3-W3(동기) / DA-P1-3(M3), DA-P2-6 동조, R1-C10(CE+필터링 구간 강조) 관련. → RM-04
- **SC-08 Token F1의 경계적 결과 서술과 p값 선택 보고**: R1-C4, EIC-W10 / DA-P2-6 동조. → RM-07
- **SC-11·12 hop별 해석**: R1-C14, R2-W3 / DA-P2-4 동조. → RM-12
- **SC-13 CE 입력 형식 진단의 편향 방향·공식 코드 일치**: R1-C9, R2-W7(a) / DA-P2-9 동조. → RM-13
- **SC-14 사례 C 해석 문장**: EIC-W11, R2-W6. DA §5는 "존재 명제로 논리적으로 타당"이라고 보아 이견(아래 분쟁 4). → RM-14
- **SC-15 용어·단위·번역 일관성**: EIC-W7·W9·Minor(l.19), R2-W9·Minor(캡션 대응) / R3 팀 메모 5. → RM-15
- **SC-10 RQ2 shortlist Recall 차이의 불확실성 미표기 / 그림 2의 정보량**: R1-C8, EIC-W8 / DA-P2-5 동조. 처리 방식은 분쟁 2. → RM-10
- **SC-21 지연의 이식성(쌍당 지연·동시성 의존)**: R1-C13, R3-W5. → RM-20

### 단일 seat 지적 (1/4) — 근거와 기준으로 개별 평가
- EIC-W1·W5 RQ별 답 문장과 장 요약, trade-off 통합(R3 상세 의견 "실무 영향"이 방향을 보강) → RM-05
- EIC-W2 기여 위계(결함 수정 +9.85점) — R1-S1, R2-S1, R3-S5, DA §5가 강점으로 같은 사실을 인정 → RM-06
- R1-C2 필터링 격자 사후 변경 미공개 — R3-W9가 같은 사실(CE 점수가 0 근처)을 언급 → RM-02
- R1-C3·C12 다중성 정량화와 비교 계열 정의(DA-P2-6 관련) → RM-08
- R1-C5 LF-Eval과 근거 Recall의 결합(DA-P2-7 동조) → RM-09
- R1-C7 지연 표본 60문항의 품질 차이 → RM-18
- R2-W1 재현 충실성의 위치 설정 → RM-16(부분 수용) + 거절·보류 표
- R2-W2 개선 원천 분리(DA 재분석 R1이 방향 지지) → RM-11
- R2-W4 미매핑 gold 원인, R2-W5 정답 외 근거 분류, R2-W7(b) Jev 지시문, R2-W8 미선택 분해, R2-W10 어절 단위 Token F1 → RM-22·23·26·27, 거절·보류 표
- R3-W1 E2E 규모 단서, R3-W2 자원 범위, R3-W6 p95 표기, R3-W7 비용 정규화, R3-W8 거버넌스, R3-W9 문턱값 척도 → RM-17·20·21·30, 팀 메모, 거절·보류 표
- R1-C11 답변 재사용 문항(DA 재분석 R4와 수치 불일치: 121 vs 119), R1-C15 판정기 점검 → RM-24·25

### DA 지적 처리
- **CRITICAL: 없음.** DA가 직접 "CRITICAL은 없다"고 밝혔고, 가장 강한 반론도 결론 반전이 아니라 적용 범위(단일 실행 조건부)를 본문에서 묶으라는 요구로 수렴한다고 스스로 평가하였습니다.
- MAJOR M1(P1-1) → RM-03, M2(P1-2) → RM-01, M3(P1-3) → RM-04로 모두 수용.
- P2-8(절 제목의 "Decision Model" 범주 일반화) → 팀 RQ 문구와 연동하여 RM-29(조건부).
- P2-10(학습 데이터 노출 가능성) → DA 스스로 증거 없음·결론 위협 아님을 명시. 제4장 본문 수정 요구로 채택하지 않고 팀 조율 메모 T10으로 이관.

## 3. 분쟁과 편집자 조정

### 분쟁 1 — 유보 문장 추가(R1·DA·R3) vs 메시지 선명도·간결성(EIC): **방향 충돌(direction)**
- EIC-W1·W3·W10: 이 장은 이미 유보 과밀로 under-stating 경향이며, 답 문장이 없고 4.4가 지면을 과도하게 쓴다.
- R1(C3–C9, C11, C15), R2(W3–W5, W8), R3(W1, W2, W5–W7), DA(P1-1, P2-4~7): 각각 1–2문장 또는 표 행 추가를 요구한다. 모두 본문에 넣으면 3쪽(A4·2단·10pt, 현재 3쪽째 약 1/3 여유)을 넘는다.
- **조정**: 본문에는 (a) 결론의 해석 범위를 바꾸는 사실(단일 실행 조건부 CI, LF-Eval의 비독립성, 필터링의 0 배제 감소, 진단 형식의 편향 방향, 경계적 Token F1)만 **한 구절 단위**로 넣고, (b) 수치 세부·분해·보정 p·민감도·운영 단가는 보충자료로 보낸다. 본문 증가분은 그림 2 삭제와 4.4 필터링 압축으로 상쇄하며, 수정 후 본문의 순 증가를 0 이하로 묶는다(로드맵 "지면 영향" 절). 이 배치는 R1이 스스로 제안한 배치(R1 §6 "Journal-Fit 좌석과의 긴장에 대한 메모": C3·C4·C6·C11 세부는 S1·S9로, C1·C2·C5 핵심 문장은 본문)와 EIC-W3 선택지 A, R3 요약의 "유보 문장보다 정규화된 운영 수치"라는 방향을 함께 만족한다.
- 근거: 증거 우선 원칙 — 결론 강도를 바꾸는 정보는 본문, 재현·검증용 세부는 보충자료라는 구분은 어느 seat의 지적도 기각하지 않으면서 지면 제약을 지킨다.

### 분쟁 2 — 그림 2 처리: EIC-W8 (삭제 또는 단계 그림) vs R1-C8 (차이+CI 형식으로 변환)
- 유형: 수정 방향 차이. 두 seat 모두 현재 그림 2(본문 수치 4개 반복, 오차막대 없음)가 부족하다는 데는 동의.
- **조정**: 그림 2를 본문에서 삭제하고(그림 자료집으로 이동), shortlist Recall 차이의 CI는 본문 문장에 넣는다(RM-10). R1이 원한 불확실성 표기는 문장으로 충족되고, EIC가 원한 지면은 요약 문단(RM-05)에 쓰인다. 지면이 남으면 EIC-W8(B) 단계 그림은 허용하나 요구하지 않는다.

### 분쟁 3 — R2-W1·W2의 우선순위: R2 P0/Major vs 다른 seat의 침묵·DA의 P2 평가
- W1(원 논문 수치 병기): 원 논문 ParSeR 절대 수치는 저장소에서 검증된 값이 없다. `data/koblex/upstream/README.md`는 표준 검색 대비 상대값(+37.91 F1, +30.81 LF-Eval)만 담고 있고, `experiments/lf-eval/README.md`의 수치(예: Retrieval F1 0.7889)는 출력 형식 예시이지 ParSeR 결과가 아니다. R2 자신도 "원 논문 수치표는 세션 자료에 없어 대조하지 못했다", "해석이 결정적이지 않다"고 밝혔다. **조정**: 원 논문 수치 병기는 `requires-verified-source`로 보류하고 방법 장 소관(팀 메모 T4)으로 이관한다. 공개 코드 CE 값과의 근접성으로 원 실행의 결함 여부를 추론하는 해석은 생성 모델 snapshot·장치·API 차이로 교란되므로 채택하지 않는다. 실행 차이 목록(장치, 모델 snapshot, API, 라이브러리 버전)은 저장된 protocol-lock 등으로 기술 가능하므로 보충자료 S5에 P1로 수용(RM-16).
- W2(개선 원천 분리): 원고에 사실 오류는 없고 해석 보강이다. DA 재분석 R1이 같은 방향(순효과가 shortlist 단계 차이에서 발생)을 지지한다. **조정**: P1로 수용하되 본문은 조건부 선택률 한 문장, 순위 위치 통계·분해는 보충자료 P2(RM-11, RM-23).

### 분쟁 4 — 사례 C 문장: EIC-W11·R2-W6 (어조 중립화) vs DA §5 (존재 명제로 타당)
- 유형: 존재 여부 차이. DA의 논리(반례 1개로 "보장하지 않음"은 성립)는 맞다. 그러나 R2의 지적은 논리가 아니라 전제(근거 F1 40→0 = 더 나쁜 근거 선택)에 관한 것이며, 원고 자신의 원칙("정답 외 조문의 법률적 부적절성… 확정한 것은 아니다")과 긴장이 있다.
- **조정**: R2 제안대로 "두 자동 지표가 반대 방향으로 변한 사례"로 중립화(RM-14). 길이 변화 없음. DA의 지적은 기록으로 남기며, 문장의 논리적 타당성 자체를 부정하는 것은 아님.

### 분쟁 5 — R3-W1(E2E 규모 어림)·R3-W7(LLM 호출 비용 대비)의 본문 반영
- R3는 응답 trace의 호출별 지연을 입력 토큰 구간으로 분류해 "재정렬이 임계 경로의 최대 단계일 수 있다"는 어림을 제안한다. 분류는 R3 스스로 "심사자의 휴리스틱"이라 밝혔고, 보충자료 S3는 실행 시간이 캐시·속도 제한 대기를 포함해 공정 비교에 쓸 수 없다고 적고 있다.
- **조정**: 본문 반영은 거절. 검증되지 않은 규모 추정이 본문에 들어가면 DA·R1이 경계한 주장 상한("재정렬 단계" 한정)을 넘을 위험이 크다. 호출 단위 `latency_ms`의 의미(대기 제외 여부)를 저자가 확인한 경우에 한해 보충자료 S9 참고치로 허용(RM-30, P2). 대신 본문에는 자원 집계가 생성 단계 기준이라는 범위 한정(R3-W2)을 P1로 수용(RM-17).

### 분쟁 6 — 심사자 재계산 수치의 상호 불일치
- 동일 근거·동일 답변 재사용 문항 수: R1(AR8·C11) 121문항 vs DA(재분석 R4) 119문항. 원고 S3는 Jev 재사용 122문항.
- **조정**: 어느 값도 원고에 옮기지 않는다. 저자가 원자료에서 결정적으로 재계산하여 정의(선택 집합 동일 vs 캐시 재사용)를 명시한 뒤에만 사용(RM-24). 이 사례는 아래 공통 조건 G1의 근거이기도 하다.

## 4. 결정 근거

다섯 seat 모두 Minor Revision을 권고했고, 결정에 영향을 주는 판정은 전부 warn/PARTLY_MEETS 수준입니다. block·fatal 판정과 DA CRITICAL은 없습니다. 지적된 문제는 결론의 방향을 바꾸지 않습니다. 오히려 R1(진단 문항 제외 민감도, shortlist CI)과 DA(효과 위치 분해)의 재분석은 주 결론(평균 근거 회수와 shortlist gold 유지의 개선, 재정렬 단계 지연 약 2.25배)을 지지하는 방향이었습니다.

Major로 표기된 지적(EIC-W4, R1-C1·C2, R2-W1·W2, R3-W1·W2·W4)은 모두 보고 투명성·해석 범위·위치의 문제이며, 기존 저장 결과의 재분석이나 서술 수정으로 해결됩니다. 핵심 설계나 논증의 재구성, 새 데이터, 새 유료 실험은 필요하지 않습니다. 이는 `editorial_decision_standards.md`의 Minor Revision 기준(핵심 논증·방법 재구성 없음, 보충·명료화 중심)에 해당합니다.

다만 두 항목은 반드시 고쳐야 합니다. (1) 필터링 절에서 Jev에 불리한 0 배제 구간의 누락(RM-01)은 R1이 "반영되지 않으면 D4가 DOES_NOT_MEET로 내려가 Major로 바뀔 수 있다"고 명시한 사항이고, (2) 결과 관찰 후 필터링 격자를 바꾼 이력(RM-02)은 연구자 자유도의 공개 의무 사항입니다. 둘 다 몇 문장과 표 열 하나로 해결됩니다.

## 5. 수정 차단 항목 (Blocking Issues, 2건)

| 참조 | 차단 항목 | 출처 | Evidence anchor | 해결 항목 |
|---|---|---|---|---|
| B1 | Jev+필터링의 0 배제 감소(Recall, 완전 회수) 구간 누락 — 보고 비대칭 | EIC-W4, R1-C1, DA-P1-2 | `dataset: results/koblex-filtering-v1/e2e-summary.json paired_bootstrap_points/jev_fr-jev_r/gold_set_coverage/ci95` | RM-01 |
| B2 | 필터링 문턱값 격자의 결과 관찰 후 변경 미공개 | R1-C2 (사실 근거: R3-W9) | `file: results/koblex-filtering-v1/README.md` "수정 이력" | RM-02 |

## 6. 필수·권장·선택 항목 요약

- **필수(P0, must_fix)**: RM-01, RM-02
- **권장(P1, should_fix)**: RM-03 ~ RM-18
- **선택(P2, consider)**: RM-19 ~ RM-30
- **거절·보류**: 로드맵 "거절·보류" 표(원 논문 수치 병기, 반복 실행·E2E 측정 등 유료 작업, 본문 그림 재작성 등 — 사유 명시)
- **다른 장 소관**: 로드맵 "팀 조율 메모" T1–T12 (수정 요구 아님)

### 모든 항목에 적용되는 공통 조건
- **G1 심사자 산출 수치 사용 금지(검증 전)**: seat이 직접 재계산·재집계한 값(R1 §7 AR3–AR11, R2의 조건부 선택률·hop별 상한·미매핑 구획 수치, R3의 trace 분류·단가·겹침 꼬리, DA 재분석 R1–R6)은 **"requires deterministic re-computation by the reviser from raw files before use"** 상태입니다. 저자가 원자료에서 스크립트로 결정적으로 재계산한 값만 원고에 넣습니다. 이미 원자료에 저장된 값(예: `e2e-summary.json`의 CI)도 파일에서 다시 추출하여 대조합니다.
- **G2 사람 평가 언급 금지**: 본문·보충자료 어디에도 사람·법률 전문가 평가를 추가하거나 언급하지 않습니다(사용자 결정). 어느 seat도 이를 요구하지 않았습니다. `analysis.json`의 `human_review` 필드와 `human-review/` 디렉터리는 사용하지 않습니다.
- **G3 새 유료 실험·API 호출 없음**: 모든 수정은 저장 결과의 읽기 전용 재분석 또는 서술 수정입니다. 유료 작업은 "optional future work"로만 표기합니다.
- **G4 원자료·protocol lock 불변**: 재분석 산출물은 새 디렉터리(예: `results/koblex-reproduction-v1/chapter4-revision-v1/`)에 스크립트와 함께 저장하고 기존 파일은 수정하지 않습니다.
- **G5 지면**: 수정 후 `preview.tex`(A4, 10pt, 2단, 여백 20mm) 기준 3쪽 이내를 결정적으로 재확인합니다.

## 7. 다음 단계

수정은 academic-paper revision 단계(Stage 4)에서 수행하고, 수정 후 새 수치는 Stage 2.5와 같은 방식으로 원자료 대조를 거친 뒤 Stage 3' 재심사(같은 카드 재사용)로 확인합니다. 각 RM 항목에 대해 `templates/revision_response_template.md` 형식으로 수용·부분 수용·거절 사유를 답변해 주십시오. 거절·보류 표의 항목도 답변서에서 한 줄씩 확인해 주시기 바랍니다.

---

## 부록: Seat별 요지

- **Journal-Fit (EIC)** — Minor, Confidence 4. 정직성은 높으나 메시지 선명도가 문제: RQ 답 문장·요약 부재, 결함 수정 효과의 매몰, 4.4 필터링 지면 편중과 보고 비대칭.
- **R1 (방법론)** — Minor, Confidence 4. 설계 중심부는 건전. P0: 필터링 선택적 구간 보고, 격자 사후 변경 미공개. P1: 다중성·Token F1 경계값·LF-Eval 결합·단일 draw·shortlist CI.
- **R2 (도메인)** — Minor(경계), Confidence 4. 공식 코드와 사실 일치. 재현 충실성의 위치 설정과 개선 원천 분리를 Major로 제기.
- **R3 (배포)** — Minor, Confidence 4. 지연 프로토콜은 우수. E2E 규모 단서, 자원 범위(선택 호출 누락), 비결정성의 운영 함의를 P1로 제기.
- **DA** — CRITICAL 없음, D3 warn. 장이 정당화하는 최대치는 "저장된 단일 Jev 실행에서 shortlist 정답 유지가 늘고 일부가 최종 근거·자동 점수로 이어졌다"이며, 재분석은 이 메커니즘을 지지.

---

## Attachment: Suggested-Reference Check (advisory, #1001)

The suggested-reference check did not run: the user restricted external transmission, and the script would send the R2/R3 suggested titles to external bibliographic indexes; the chapter cites none of the suggested works (all remain [UNVERIFIED] search leads in the seat reports, routed to team memo T5).

## Attachment: Reviewer Claim Check (advisory, #1002)

The reviewer claim check did not run: it requires dispatching the generated prompt to a no-tools subagent of the session model, which this synthesizer run cannot spawn.

## Attachment: Acronym Check (advisory, #849)

`python3 scripts/check_acronyms.py --input research/chapter4/chapter4.md --lang en` (로컬 실행, 외부 전송 없음; 한국어 보고 옵션이 없어 영어로 출력). 스크립트 출력이며 심사 지적이 아니므로 로드맵 항목을 만들지 않는다. 약어 정의는 대부분 다른 장(방법 장)에서 이루어질 수 있다.

### Acronym check (advisory; no reply needed)
Coverage: body (partial)
Not in this input: English abstract, Chinese abstract.
Not checked:
- Body, line 5: CE (the initials before its parentheses do not spell it)

| Scope | Line | Rule | Acronym | Uses |
|---|---|---|---|---|
| Body | 5 | Not defined | BM25 | 5 |
| Body | 5 | Not defined | KoBLEX | 1 |
| Body | 5 | Not defined | LLM | 2 |
| Body | 5 | Not defined | ParSeR | 1 |
| Body | 7 | Not defined | EM | 4 |
| Body | 7 | Not defined | LF | 12 |
| Body | 34 | Not defined | API | 2 |
| Body | 34 | Not defined | MPS | 1 |
