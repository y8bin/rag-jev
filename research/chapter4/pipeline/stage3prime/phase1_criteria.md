# Stage 3′ 재심사 — Phase 1 기준 사전 확정 (Criteria Commitment, 수정본 비열람)

- 대상: 제4장 "실험 결과 및 분석" (KoBLEX ParSeR, 공개 코드 CE / 수정 CE / Decision Model Jev)
- 단계: Stage 3′ Phase 1 — `re_review_mode_protocol.md`(ARS academic-paper-reviewer 3.24.2) § Three-Gate Orchestration / Phase 1
- 작성일: 2026-11-14
- 산출물 성격: 수정본을 보기 전에 RM 항목별 검증 기준을 고정한 기록이다. 이 파일의 sha256이 `precommitment_hash` 역할을 하며, Phase 2A 판정은 이 기준에만 대어 내린다. 기준을 바꾸려면 Phase 2A에서 dissent 기록(§ Dissent Records)을 남겨야 한다.

---

## 0. 입력·비열람 기록 (Phase 1 withholding)

### 0.1 이번 단계에서 읽은 입력
| 입력 | 경로 | 프로토콜상 지위 |
|---|---|---|
| Round-1 심사자 카드(동결) | `research/chapter4/pipeline/stage3_reviewer_cards.md` | level 4, Yardstick Continuity |
| 수정 로드맵(불변) | `research/chapter4/pipeline/stage3_revision_roadmap.md` | level 1 (각 RM의 "수용 기준") |
| 편집 결정서 | `research/chapter4/pipeline/stage3_editorial_decision.md` | level 2 (차단 항목 B1·B2 표) |
| Round-1 seat 보고서(지적 ID·심각도 확인 범위) | `research/chapter4/pipeline/stage3_review_{eic,r1,da}.md` 일부, `stage3_review_{r2,r3}.md` 지적 제목 | level 3 (driving finding 심각도·anchor) |
| 파이프라인 상태(사용자 결정) | `research/chapter4/pipeline/pipeline_state.md` | 범위 결정: P0+P1 전부, P2는 보충자료 추가 또는 길이 중립 문구만; 사람 평가 금지; 제4장만 |

### 0.2 읽지 않은 입력
- 수정본 일체: `research/chapter4/chapter4.md`, `research/chapter4/chapter4-supplement.md`, 모든 `.tex`, `output/pdf/*`, `research/chapter4/pipeline/stage4_*.md`(답변서·delta 보고 포함), `results/koblex-reproduction-v1/chapter4-revision-v1/`.
- **원본(수정 전) 원고 `pre_stage4/chapter4.md`·`chapter4-supplement.md`도 읽지 않았다.** 호출자가 읽기를 허용했으나, 프로토콜 withholding matrix는 Phase 1에서 원본 원고를 ❌(비공개)로 둔다. 더 엄격한 쪽을 택했다. 원본의 문장·위치는 로드맵과 seat 보고서가 인용한 범위에서만 참조한다.
- 따라서 아래 기준은 Round-1 산출물(로드맵·결정서·카드·seat 보고서)만으로 도출된 것이며, 수정본 내용을 짐작하지 않는다.

### 0.3 계약 이탈·불완전 사항 (orchestrator 확인 필요, 판정 아님)
1. **기계용 산출물 부재**: 로드맵 l.4가 밝히듯 Schema 7 JSON core, author-adjudication sidecar가 생성되지 않았다. revision-evidence-bundle 1.0, input manifest 1.1, apply report 1.3의 존재 여부는 Phase 1에서 확인하지 않았다(수정 관련 경로 비열람). 현재 계약 checker(`check_re_review_synthesis.py`)를 그대로 돌리면 G0(`manifest_incomplete`)로 중단될 가능성이 높다. 이 문서는 사람용 로드맵을 기준으로 같은 규칙을 수작업으로 적용하는 것을 전제로 하며, 그 사실을 Judge Record에 적어야 한다.
2. **라우팅 정규화**: 로드맵의 출처 문자열은 `EIC-W4`, `R1-C1` 같은 지적 ID 형식이다. §10 문법을 글자 그대로 적용하면(토큰 전체 일치) `EIC-W4` ≠ `EIC`라서 모든 토큰이 탈락해 parse failure가 된다. 로드맵 l.6이 선언한 ID 표기 규약(`EIC-Wn`, `R1-Cn`, `R2-Wn`, `R3-Wn`, `DA-…`)에 따라 접두어를 seat 라벨로 대응시켰다(추측 없는 결정적 대응). Judge Record의 Routing 줄에는 `card_mapped (ID 접두어 정규화, 로드맵 l.6 규약)`으로 표기할 것을 제안한다. 모든 must_fix·should_fix 항목에 non-DA 라벨이 있어 미대응 라벨은 없다.
3. **교차 모델 검증 미사용**(사용자 지시). 최종 보고서에 단일 계열 고지 문장을 그대로 넣어야 한다: "This verification round ran on the same model family that drove the revisions; over-optimization to this judge's latent biases is possible (Ren et al. 2026, arXiv:2607.13104 §8.1.2)."
4. **Reviewer configuration**: `round1_cards_reused`. field_analyst는 다시 실행하지 않았다.
5. **결정서의 R<n> 참조**: 결정서는 R<n> 형식의 Acceptance-criteria 블록 대신 "수정 차단 항목" 표(B1, B2)를 둔다. must_fix 순서에서 도출한 transport ref는 R1 = RM-01(결정서 B1), R2 = RM-02(결정서 B2)이며, 두 블록이 연속이므로 `[CRITERIA-LAYER-ABSENT]`는 해당하지 않는다. should_fix에는 결정서 수준 기준이 없다(프로토콜상 정상).

---

## 1. 공통 판정 규칙

- **판정 어휘**: `FULLY_ADDRESSED` / `PARTIALLY_ADDRESSED` / `NOT_ADDRESSED` / `MADE_WORSE` / `CANNOT_VERIFY`.
- **증거 원칙**: 수정본(본문·보충자료)과 수정 산출물 파일에 실제로 있는 내용만 증거가 된다. 답변서의 진술은 Phase 2A에서 보지 않으며, Phase 2B에서도 원고에서 위치를 확인할 수 있을 때만 판정을 바꿀 수 있다.
- **equivalence_policy: allowed**: 다른 위치나 다른 표현이라도 `fully_addressed` 패턴을 실질적으로 충족하면 인정한다. `expected_change_surface`는 찾아볼 위치에 대한 가설일 뿐이며, 그 위치에서 표면적인 문구만 바꾼 것은 충족으로 보지 않는다.
- **수치 대조**: "파일 값과 일치"는 원고 수치를 지정 원자료(또는 G4 디렉터리의 재계산 출력)에서 Phase 2A 검증자가 직접 추출해 소수 둘째 자리까지 대조하는 것을 뜻한다. 반올림 규칙이 원고 전체에서 같으면 반올림 차이는 일치로 본다.
- **CANNOT_VERIFY**: 대조 대상 파일이 없거나 읽을 수 없어 원고 수치를 확인할 수 없을 때. must_fix에서는 B3(Major)로 이어진다(fail-closed).
- **should_fix 경량 형식**: 프로토콜상 should_fix에서 구속력이 있는 것은 `fully_addressed` 패턴뿐이다. 아래 P1 항목에 적은 "구성 요소"는 `fully_addressed` 패턴을 나눈 것이다. `PARTIALLY_ADDRESSED`는 구성 요소 일부만 충족(`residual_gap`과 `residual_obligation_class` 필수), `MADE_WORSE`는 프로토콜 일반 판별자(원본 원고 대비 해당 항목의 주제가 나빠짐)를 따른다. P1 항목마다 적은 "악화 예시"는 이 일반 판별자를 적용한 예시이며 별도 기준이 아니다.

### 1.1 공통 조건 G1–G6의 운용 (로드맵 l.9–18, 모든 RM에 적용)

공통 조건은 로드맵 level-1 기준이다. 개별 RM의 판정과 별도로, 위반은 Phase 2A에서 **new-issue 기록**(수정으로 생긴 것이면 `regression`)으로 남긴다. 아래 심각도는 Phase 2A 배정 지침이며, 최종 심각도는 2A가 Schema 6 기준으로 정한다.

| ID | 충족 증거 | 위반(→ new issue) | 심각도 지침 |
|---|---|---|---|
| G1 | 수정으로 새로 들어간 수치가 원자료 또는 G4 디렉터리의 재계산 출력과 1:1 대응하고, 대조표가 존재 | 새 수치가 파일과 불일치; seat 산출 [재계산 필요] 수치(예: R1 20-seed 13/20, Holm 0.074·BH 0.0496, R2 79.5%·77.6%, 26/27·25/27, R3 $0.00339, DA 121·119 등)를 재계산 출력 없이 옮김; 근사 구간 [+2.6, +8.0] 사용 | 결과 수치 불일치·미검증 수치 = major; 서술용 보조 수치 = minor |
| G2 | 본문·보충자료에 사람·법률 전문가 평가 관련 서술 0건 | 사람 평가, 사람 판정, 전문가 검토, human review, `human_review` 필드·`human-review/` 경로를 언급하거나 사용 | major (사용자 금지 사항) |
| G3 | 새 분석이 저장 자료의 재분석뿐이고, 유료 작업은 "optional future work"로만 표기 | 새 API 호출 결과(반복 Jev 실행, E2E 재측정, 재생성 등)가 원고에 등장; 유료 작업을 수행한 것처럼 기술 | major |
| G4 | 원자료·`protocol-lock.json`·기존 산출물이 바뀌지 않음(sha256 동일). 새 산출물은 `chapter4-revision-v1/` 등 새 디렉터리에 있음 | 잠금 파일·원자료 변경, 기존 저장 CI를 덮어씀 | major (재현성) |
| G5 | 본문 PDF 3쪽 이내(A4·10pt·2단·여백 20mm), Overfull·미정의 참조 0 | 3쪽 초과, 미정의 참조, 삭제된 그림·표를 가리키는 남은 참조, 그림·표 번호 불일치 | 3쪽 초과 = major; 참조·번호 오류 = minor |
| G6 | 새 구간은 잠금 절차(151개 의존 그룹, percentile bootstrap 10,000회, seed 20261108)를 쓰고, 보충자료(S1)에 "결과 관찰 후 같은 절차로 추가 산출한 탐색적 구간"이 명시됨 | 다른 seed·반복 수·그룹 정의로 구간 산출; 사후 산출임을 밝히지 않음; 기존 보고 CI를 새 반복 수로 교체(D-05 거절 사항) | 절차 불일치 = major; 표기 누락만 = minor |

### 1.2 범위 경계에서 오는 회귀 판별 (로드맵 거절·보류 표와 주장 상한)

아래 내용이 원고에 새로 들어가면 해당 RM의 `MADE_WORSE` 근거 또는 `regression` new issue가 된다. 모두 Round-1 로드맵에서 이미 거절·보류된 것이므로 새 기준이 아니다.
- D-01: 검증 출처 없는 원 논문 ParSeR 절대 수치 병기, 공개 코드 CE와의 근접성으로 원 실행 결함을 시사하는 해석.
- D-06: trace 분류 기반 "재정렬이 임계 경로 최대 단계", "전체 응답 1.5–2배" 같은 E2E 규모 추정을 본문에 기술.
- D-07: Jev 단가를 GPT-4o 호출 비용과 나란히 비교.
- D-15: "shortlist 축소가 선택 호출 입력을 줄이는 레버"라는 함의.
- 주장 상한(RM-05, T7 공유): "Decision Model이 CE보다 우수", "multi-hop에서 유리", "효율적/비용 절감" 같은 표현, 또는 단일 Jev 실행·EM·완전 회수의 불확실성·재정렬 **단계** 한정·입력량 절감 미관찰 중 하나를 넘는 결론 문장.

---

## 2. 라우팅 요약

| RM | 우선순위 | obligation_class | source_reviewer (로드맵 원문) | source_reviewer_labels | 검증 seat (`verified_by`) | driving finding 심각도 |
|---|---|---|---|---|---|---|
| RM-01 | P0 | must_fix | EIC-W4, R1-C1, DA-P1-2(M2) — SC-01 | EIC, R1, DA | EIC (Journal-Fit) | Major (EIC-W4, R1 W1) — critical 아님 |
| RM-02 | P0 | must_fix | R1-C2 (사실 근거: R3-W9 …) — SC-02 | R1 (괄호 안 R3는 괄호 제거 규칙으로 탈락) | R1 (방법론) | Major (R1 W2) — critical 아님 |
| RM-03 | P1 | should_fix | EIC-W6, R1-C6, R3-W4(a), DA-P1-1(M1) — SC-04 | EIC, R1, R3, DA | EIC | Major(해석) (R1 W6) |
| RM-04 | P1 | should_fix | EIC-W3, DA-P1-3(M3), R3-W3(동기), R1-C10, DA-P2-6 — SC-03 | EIC, DA, R3, R1 | EIC | — |
| RM-05 | P1 | should_fix | EIC-W1, EIC-W5 (R3 상세 의견 …) — 단일 seat 지적 + 보강 | EIC | EIC | Minor (EIC-W1) |
| RM-06 | P1 | should_fix | EIC-W2 (R1-S1, R2-S1, R3-S5, DA §5 …) | EIC | EIC | — |
| RM-07 | P1 | should_fix | R1-C4, EIC-W10, DA-P2-6 — SC-08 | R1, EIC, DA | R1 | Minor–Major (R1 W4) |
| RM-08 | P1 | should_fix | R1-C3, R1-C12, DA-P2-6 — SC-07 | R1, DA | R1 | Major (R1 W3) |
| RM-09 | P1 | should_fix | R1-C5(a)(b), DA-P2-7 — SC-09 | R1, DA | R1 | Major(해석) (R1 W5) |
| RM-10 | P1 | should_fix | R1-C8, DA-P2-5, EIC-W8 — SC-10 … | R1, DA, EIC | R1 | Minor (R1 W8) |
| RM-11 | P1 | should_fix | R2-W2(1)(3), DA 재분석 R1(방향 지지) — SC-11 … | R2, DA | R2 (도메인) | Major (결정서 §4) |
| RM-12 | P1 | should_fix | R2-W3, R1-C14, DA-P2-4 — SC-12 | R2, R1, DA | R2 | — |
| RM-13 | P1 | should_fix | R2-W7(a), R1-C9, DA-P2-9 — SC-13 | R2, R1, DA | R2 | Minor (R1 W9) |
| RM-14 | P1 | should_fix | R2-W6, EIC-W11 (DA §5 이견 …) | R2, EIC | R2 | — |
| RM-15 | P1 | should_fix | EIC-W7, EIC-W9, EIC Minor(l.19), R2-W9(b)(c), R2 Minor(캡션 대응) — SC-15 | EIC, R2 | EIC | — |
| RM-16 | P1 | should_fix | R2-W1(후반부: 실행 차이), R1 팀 메모(…) — … | R2, R1 | R2 | Major (R2-W1, 결정서 §4) |
| RM-17 | P1 | should_fix | R3-W2(a) | R3 | R3 (배포) | Major (결정서 §4) |
| RM-18 | P1 | should_fix | R1-C7 | R1 | R1 | Minor (R1 W7) |
| RM-19–30 | P2 | consider | (§5 표) | — | EIC (consider 정의상) | 결정 무관 |

critical 심각도의 driving finding은 없다(결정서: DA CRITICAL 0, block·fatal 0). 따라서 B1의 "critical must_fix MADE_WORSE" 경로는 이 라운드에서 성립할 수 없고, B1은 critical 심각도의 `regression` new issue로만 발동할 수 있다.

---

## 3. P0 — must_fix 사전 확정 기록 (완전 형식)

### RM-01 필터링 절의 0 배제 감소 구간 보고 (보고 비대칭 해소) — transport ref **R1**

- **verified_by**: EIC (Journal-Fit Reviewer 카드 #1). 수치 대조는 R1 카드의 추론 관점(같은 bootstrap 형식)을 참조한다.
- **inherited_criterion**
  - 로드맵 수용 기준(원문): "4.4에서 Jev+필터링에 대해 보고된 모든 근거 지표 차이가 같은 형식(점추정+CI)을 갖고, CE+필터링·Jev+필터링 사이에 구간 보고 규칙이 대칭이다. 표 2 수치가 파일 값과 일치한다."
  - 결정서(letter_item_ref R1 ↔ 차단 항목 B1, 원문): "Jev+필터링의 0 배제 감소(Recall, 완전 회수) 구간 누락 — 보고 비대칭" / evidence anchor `dataset: results/koblex-filtering-v1/e2e-summary.json paired_bootstrap_points/jev_fr-jev_r/gold_set_coverage/ci95`
  - level 3: EIC-W4(Major), R1-C1(P0·Major), DA-P1-2(M2). 원자료 경로: `results/koblex-filtering-v1/summary.json`(`cv_overall`, paired bootstrap), `e2e-summary.json`(`means`, `paired_bootstrap_points/jev_fr-jev_r/gold_set_coverage`, `ce_fr-ce_r`).
- **operationalization.fully_addressed** (모두 충족)
  1. 4.4 본문에서 Jev+필터링(필터링 전 Jev 대비)에 대해 보고된 근거 지표 차이 **각각**이 "점추정 + 95% CI" 형식을 갖는다. 최소 범위: 근거 F1, Recall, 완전 회수(모든 gold 포함률). Precision 차이를 본문에 서술했다면 Precision도 CI가 붙는다. 점추정만 있고 CI가 없는 근거 지표 차이가 4.4 본문에 하나도 없다.
  2. Recall 감소와 완전 회수 감소의 CI가 0을 배제한다는 사실이 숫자로 드러난다(구간 값 제시. 별도 강조 문구는 필요 없음). 참고 저장 값(로드맵 인용, G1에 따라 파일 재추출 대상): Recall −2.43점 [−3.81, −1.16], 완전 회수 −1.77%p [−3.51, −0.43].
  3. **대칭성**: CE+필터링과 Jev+필터링에 같은 구간 보고 규칙이 적용된다. 한쪽에만 "구간이 0을 포함하지 않았다" 같은 강조가 있거나, 한쪽 조건의 0 배제 구간만 생략된 상태가 아니다. (RM-04가 CE+필터링 Token F1 강조를 삭제하는 것과 양립 가능. 양쪽 모두 강조 없이 방향과 구간만 제시해도 대칭이다.)
  4. 표 2에 "완전 회수(%)" 열(또는 같은 정보의 열)이 있고, 4개 행(CE, CE+필터링, Jev, Jev+필터링 또는 같은 구성)의 값이 `summary.json`·`e2e-summary.json`의 저장 값과 일치한다. 참고값(로드맵·EIC-W4 인용): CE 34.07→33.19, Jev 34.96→33.19.
  5. 근거 F1이 문턱값 선택 기준이었으므로 검증 fold의 F1 차이가 0 근처인 것이 부분적으로 설계상 귀결이라는 점이 4.4에 한 구절로 있다(로드맵 필요 변경 (3), DA-P1-2).
  6. 필터링 후 두 조건의 완전 회수가 같아진다는 사실이 보충자료 S7에 기술되어 있다(로드맵 필요 변경 (4)).
  - 판정 시 1·3·4는 수용 기준의 핵심 문구이고, 5·6은 "필요 변경"에서 온 구성 요소이다. 5·6만 빠진 경우는 아래 부분 충족으로 처리한다.
- **operationalization.partially_addressed** (실제 수정이 있으나 불완전)
  - Recall과 완전 회수 중 하나에만 CI가 붙었거나, CI는 보충자료에만 있고 본문 4.4에는 점추정만 있다.
  - 본문 CI는 모두 있으나 표 2에 완전 회수 열이 없거나 한 행 이상이 파일 값과 다르다(오타 수준이 아닌 불일치는 아래 악화 판별 참조).
  - 핵심 1–4는 충족했으나 5(설계상 귀결 구절) 또는 6(S7 완전 회수 동일화)이 빠졌다 → `residual_obligation_class: should_fix`.
  - 1–4 중 하나라도 빠지면 → `residual_obligation_class: must_fix`(보고 비대칭이 남음).
- **NOT_ADDRESSED**: 4.4 본문에 Jev+필터링의 Recall·완전 회수 감소 CI가 없고 표 2에 완전 회수 열도 없다(원본과 실질적으로 같은 비대칭).
- **operationalization.made_worse_discriminator**
  - 0을 배제하는 Jev 불리 결과가 원본보다 더 가려진다: 원본에 있던 Recall −2.43점 서술이 삭제되거나, Jev+필터링 결과가 "유지", "동등", "손실 없음", "비열등"으로 서술된다(원본은 유지·동등성 해석을 거부했음).
  - 새로 넣은 CI·표 값이 파일 값과 부호·크기가 다르다(예: 0 배제 구간을 0 포함으로 잘못 옮김).
  - 비대칭이 반대 방향으로 새로 생긴다(CE 쪽 0 배제 결과만 생략).
- **expected_change_surface** (가설): 4.4 필터링 결과 문단(원본 l.65 부근), 표 2, 보충 S7.
- **equivalence_policy**: allowed.
- **NewStandardRecord**: 없음.

### RM-02 필터링 문턱값 격자의 사후 변경 공개 — transport ref **R2**

- **verified_by**: R1 (Peer Reviewer 1 — Methodology 카드 #2)
- **inherited_criterion**
  - 로드맵 수용 기준(원문): "변경 시점(결과 관찰 후)과 변경 이유가 S7에 명시되고, 본문에서 그 위치를 찾을 수 있다."
  - 결정서(letter_item_ref R2 ↔ 차단 항목 B2, 원문): "필터링 문턱값 격자의 결과 관찰 후 변경 미공개" / evidence anchor `file: results/koblex-filtering-v1/README.md` "수정 이력"
  - level 3: R1-C2(P0·Major, researcher degrees of freedom), 사실 근거 R3-W9(CE 점수가 0 근처에 몰림).
- **operationalization.fully_addressed** (모두 충족)
  1. 보충 S7에 다음 네 요소가 모두 있다: (a) 처음에는 두 scorer에 같은 절대 격자(0.00–0.95)를 적용했다는 사실, (b) 변경 이유: CE 점수 대부분이 0.05 미만이라 CE 필터링이 사실상 불가능했다는 것(또는 같은 취지), (c) 척도별 분위수 격자(같은 크기)로 바꿨다는 사실, (d) **변경이 결과를 관찰한 뒤 이루어졌다**는 시점 명시.
  2. 허용 하락폭 1점, 20개 격자, "가장 적게 남기는" 목적함수가 격자 변경 전에 정해졌는지 여부가 S7에 기술되어 있다. 확인할 수 없었다면 확인할 수 없었다고 적혀 있어도 된다(로드맵 필요 변경, R1 질문 3).
  3. 본문 4.4 격자 설명 문장 부근에 S7을 가리키는 참조(예: "(격자 변경 이력은 S7)")가 있다.
  4. S7 서술이 `results/koblex-filtering-v1/README.md` "수정 이력"과 모순되지 않는다(Phase 2A에서 README 대조).
- **operationalization.partially_addressed**
  - S7에 변경 사실은 있으나 "결과 관찰 후"라는 시점이 빠졌거나 모호하다("설계 문서에 맞춰 조정" 같은 표현만 있음) → `residual_obligation_class: must_fix`(자유도 공개의 핵심 누락).
  - 1(a–d)은 모두 있으나 본문 참조(3)가 없다 → `should_fix`.
  - 1·3은 충족했으나 다른 선택 요소(2)에 대한 언급이 없다 → `should_fix`.
- **NOT_ADDRESSED**: S7과 본문 어디에도 절대 격자에서 분위수 격자로 바꾼 이력이 없다.
- **operationalization.made_worse_discriminator**
  - 분위수 격자를 "사전 설계대로", "처음부터" 사용했다고 서술해 README 수정 이력과 모순된다(이력을 은폐하는 방향).
  - 사후 변경을 공개하면서 필터링 결과를 확증적으로 재서술한다(예: 격자 선택이 최적이었음을 근거로 결과 강도를 높임).
- **expected_change_surface** (가설): 보충 S7 첫 문단; 본문 4.4 격자 설명 문장(원본 l.54 부근).
- **equivalence_policy**: allowed.
- **NewStandardRecord**: 없음.

---

## 4. P1 — should_fix 사전 확정 기록 (경량 형식)

각 항목의 `fully_addressed`가 구속 기준이다. "구성 요소"는 부분 충족 판단에 쓰고, "악화 예시"는 일반 판별자(원본 대비 항목 주제의 악화)를 적용한 예시이다. "범위 메모"는 사용자 범위(P1 전부 반영)와 공통 조건에 관한 확인 사항이다.

### RM-03 Jev 단일 실행 조건부 해석을 RQ1 앞에 배치 — verified_by EIC
- **inherited_criterion**: "4.2의 첫 CI가 나오기 전에 독자가 단일 실행 조건과 CI의 범위를 알 수 있다. Jev 반복 실행은 언급하더라도 optional future work로만 표기한다."
- **fully_addressed**: 본문에서 **4.2의 첫 CI보다 앞서는 위치**(4.1 끝, 4.2 첫 문단 또는 그림 1 캡션 중 첫 CI보다 먼저 읽히는 곳)에 다음 세 요소를 담은 문장이 있다: (a) Jev가 원격 API이며 재호출 시 상위 10개가 달라질 수 있다는 점(또는 4.3 참조), (b) 이후 Jev 품질 수치는 저장된 단일 실행 값이라는 점, (c) 보고된 CI는 문항 표본 변동만 반영하고 실행 간 변동은 포함하지 않는다는 점. Jev 반복 실행이 언급되면 "optional future work"(또는 같은 뜻의 선택적 향후 작업)로만 표기된다. 4.3 말미의 기존 문장과 중복되는 부분은 줄어 있다(상세 수치 2/180, 집합 겹침은 4.3에 유지 가능).
- **구성 요소**: 위치 / (a)(b)(c) / 반복 실행 표기 / 4.3 중복 축소.
- **악화 예시**: 단일 실행 조건이 본문에서 사라지거나 더 뒤로 밀림; 반복 실행을 수행한 것처럼, 또는 실행 간 변동이 CI에 반영된 것처럼 기술.
- **expected_change_surface**: 4.1 끝, 4.2 첫 문단, 그림 1 캡션; 4.3 마지막 문단.

### RM-04 4.4 선택 후 필터링의 압축과 동기 명시, 교차 비교 이동 — verified_by EIC
- **inherited_criterion**: "4.4의 필터링 부분이 현재 분량의 약 절반 이하이고, 본문에 조건 간 교차 비교 CI가 없으며, 필터링의 목적 문장이 있다. 이동한 수치는 S7에서 모두 찾을 수 있다."
- **fully_addressed** (모두 충족)
  1. **분량**: 4.4 필터링 부분(원본 4.4 셋째~여섯째 문단 대응, 표 2 제외)의 본문 글자 수가 원본 대응 부분의 약 50% 이하이다. 측정은 Phase 2A에서 원본·수정본의 해당 문단 글자 수(공백 제외)를 세어 비교하며, 55% 이하는 "약 절반"으로 인정한다.
  2. **목적 문장**: 필터링 분석의 목적을 밝히는 구절이 필터링 부분 첫머리에 있다(예: "선택 근거 수를 줄일 때 자동 품질이 어떻게 변하는지 탐색하기 위해").
  3. **교차 비교 제거**: 본문에 조건 간 교차 비교 CI(Jev+필터링 vs CE+필터링, Jev+필터링 vs 필터링하지 않은 CE)가 없다. 원본 예: "Jev+필터링과 CE+필터링의 차이는 Token F1 +1.38점(CI [+0.09, +2.69])".
  4. **S7 이동**: 본문에서 빠진 교차 비교 수치, 선택 전 필터링 유지 비율, 90% 유지 기술통계가 S7에 모두 있다. S7에 두 scorer의 필터링 강도 차이(유지율 CE 97.70%, Jev 89.12%; 재생성 CE 10문항, Jev 45문항)가 함께 적혀 있다.
  5. **CE+필터링 강조 삭제**: CE+필터링 Token F1 감소에 대한 "구간은 0을 포함하지 않았다" 강조가 본문에서 삭제되었고, S7에 그 차이가 답변이 바뀐 10문항에서만 발생했다는 점이 적혀 있다(R1-C10).
  6. **비열등성 해석 거부** 문장이 본문에 남아 있다(로드맵 필요 변경 (2)의 구성 요소).
  7. **장 전체 일관 규칙**(DA-P2-6): 경계적 구간에 대해 방향만 기술하는 규칙이 4.4 외의 절과 충돌하지 않는다(다른 절에 같은 성격의 "0을 포함하지 않았다" 강조가 남아 있지 않음).
- **구성 요소**: 1–7. RM-01이 요구한 Jev+필터링 0 배제 구간은 본문 주 결과로 남아야 하므로, 압축 과정에서 RM-01 요소가 빠지면 RM-01 쪽에서 판정한다.
- **악화 예시**: 필터링 부분이 오히려 길어짐; 목적 문장이 RQ와 무관한 자원 절감 주장(입력량·비용 절감)을 함축(D-15, 주장 상한 위반); 이동한 수치가 S7에서 사라짐(정보 손실); 비열등성·동등성 해석이 새로 생김.
- **범위 메모**: 목적 문구와 RQ3 정의의 정합은 팀 메모 T2 소관이라 판정 대상이 아니다.
- **expected_change_surface**: 4.4 셋째~여섯째 문단, 표 2, 보충 S7.

### RM-05 RQ별 답 문장과 장 요약(trade-off 통합) — verified_by EIC
- **inherited_criterion**: "4.2–4.4 각각의 첫 문장만 읽어도 RQ의 답이 나온다. 요약에 원고에 없는 수치가 없고, 위 상한 표현을 모두 지킨다."
- **fully_addressed** (모두 충족)
  1. 4.2, 4.3, 4.4 각각의 **첫 문장**이 해당 RQ의 답을 수치와 함께 진술한다(4.2: 근거 선택 성능 변화와 EM·완전 회수의 불확실성; 4.3: shortlist 유지와 재정렬 단계 지연; 4.4: 답변 자동 지표와 자원 사용). 방법 설명이나 유보로 시작하지 않는다.
  2. 장 끝에 RQ1–3의 답과 품질–지연–자원 trade-off를 담은 요약이 있다(3–4문장. 결론 장과의 역할 분담(T8)에 따라 수치 중심 2문장으로 축소한 것도 인정). 별도 제목의 유무는 판정하지 않는다.
  3. 요약의 모든 수치가 본문의 다른 곳에 이미 있는 값이다(요약에서 처음 나오는 수치 0개).
  4. 요약이 주장 상한을 모두 지킨다: (i) 저장된 단일 Jev 실행이라는 조건, (ii) EM·완전 회수 차이는 불확실, (iii) 지연은 **재정렬 단계** 지연이며 배포 조건에 의존, (iv) 입력량 절감은 관찰되지 않음. 네 가지 중 해당 수치를 언급하는 것은 모두 해당 상한과 함께 나온다.
  5. 품질(226문항)과 지연(60문항, 별도 실행)을 비율·교환 비율(예: "지연 1초당 F1 x점")로 짝지어 쓰지 않는다(R1-C7).
  6. 각 절의 반복 유보 문장이 원본보다 줄었다(요약이 유보를 흡수). 유보의 **내용**은 장 안 어딘가에 남아 있어야 한다.
- **구성 요소**: 1(세 절 각각), 2, 3, 4(i–iv), 5, 6.
- **악화 예시**: 첫 문장이나 요약이 상한을 넘는 결론("Jev가 CE보다 우수하다", "multi-hop에서 유리", "효율적", "비용 절감")을 냄; 요약에 원고에 없는 수치나 품질/지연 결합 비율이 등장; 유보를 줄이면서 단일 실행 조건이나 EM·완전 회수 불확실성이 장 전체에서 사라짐.
- **expected_change_surface**: 4.2·4.3·4.4 첫 문장, 장 끝 요약(4.5 마지막 문단 또는 4.6).

### RM-06 기여 구분 지도(결함 수정 효과 vs 교체 효과) — verified_by EIC
- **inherited_criterion**: "4.1에서 두 효과의 구분이 한 문장으로 제시되고, S2 표의 값이 `analysis.json`과 일치한다."
- **fully_addressed**
  1. 4.1에 세 조건(공개 코드 CE, 수정 CE, Jev)과, 앞의 차이는 공개 코드 후보 목록 참조 수정 효과이고 뒤의 차이는 재정렬기 교체 효과라는 구분을 담은 문장이 있다.
  2. 보충 S2에 세 조건 × 주요 지표 표가 있고, 지표는 최소 P, R, F1, EM, 완전 회수, Token F1, LF-Eval이다.
  3. S2 표의 값이 `results/koblex-reproduction-v1/analysis.json` `summaries.parser_ce_raw / parser_ce_fixed / parser_jev_fixed`의 저장 값과 일치한다.
  4. 원 논문 실행에 결함이 있었는지 확인되지 않았다는 기존 유보가 유지된다.
- **악화 예시**: 결함 수정을 원 논문 실행의 결함으로 단정함(D-01 경계 위반); 본문에 3조건 표를 넣어 G5를 위반함(D-08은 본문 표를 요구하지 않음).
- **expected_change_surface**: 4.1 둘째 문단, 보충 S2.

### RM-07 Token F1 경계 결과 서술과 p값 보고 일관화 — verified_by R1
- **inherited_criterion**: "본문에 p값이 하나도 없거나(권장) 모든 주 비교 지표의 p가 같은 위치에 있다. Token F1을 "개선"이 아니라 "경계적"으로 서술한다."
- **fully_addressed**
  1. 본문의 p값 보고가 다음 둘 중 하나이다: (a) 본문 p값 0개(권장), 또는 (b) 모든 주 비교 지표의 p값이 같은 위치(같은 표나 문장)에 있음. Token F1 하나에만 p값이 붙은 상태가 아니다.
  2. 본문에서 Token F1 결과가 "경계적"(또는 같은 뜻)으로 서술되고 CI [+0.02, +2.27]점이 함께 나온다. "개선되었다"는 단정 표현이 없다.
  3. 보충 S1에 주 비교 지표 전체의 centered-bootstrap p값 표가 있고, 그 값이 `analysis.json` `comparisons[].p_centered_bootstrap_two_sided` 저장 값과 일치한다.
  4. (선택 요소, 없어도 FULLY 가능) S1의 Monte Carlo 변동 문장. R1의 20-seed 결과(13/20)는 재계산 출력이 있을 때만 사용 가능(G1).
- **악화 예시**: 보고 CI를 50,000회 등으로 바꾼 값으로 교체함(D-05, G6 위반); Token F1을 더 강하게 "유의한 개선"으로 서술함; p값 선택 보고가 다른 지표로 옮겨감.
- **expected_change_surface**: 4.4 첫 문단(원본 l.50), 보충 S1.

### RM-08 다중성 하의 해석 규칙과 비교 계열 정의 — verified_by R1
- **inherited_criterion**: "본문 서술에 확증적 동사("개선이 확인되었다")가 없고, S1에 계열 정의와 보정 결과가 있다."
- **fully_addressed**
  1. 4.1의 "다중 비교는 보정하지 않았다" 부근에 "개별 구간이 0을 배제하더라도 가설 생성적 근거로만 해석한다"와 같은 뜻의 구절이 있다.
  2. 본문 전체에 확증적 동사("개선이 확인되었다", "입증", "유의하게 우수" 등)가 없다(Phase 2A에서 본문 전체 검색).
  3. S1에 비교 계열 정의(포함 지표 목록, Precision 포함 여부 명시)가 있다.
  4. S1에 그 계열의 저장 p값에 Holm과 BH 보정을 적용한 결과가 참고로 보고되어 있고, 값이 저장 p값에서 결정적으로 재계산한 결과와 일치한다(Phase 2A 검증자가 저장 p값으로 직접 재계산해 대조). R1의 "Holm 최소 0.074, BH 0.0496"은 대조 참고용일 뿐 기준값이 아니다.
- **악화 예시**: 보정 결과를 근거로 결론을 확증적으로 격상함; 계열을 결과에 유리하게 사후 축소하면서 그 사실을 밝히지 않음.
- **expected_change_surface**: 4.1 둘째 문단, 보충 S1.

### RM-09 LF-Eval이 근거 회수와 독립 증거가 아님을 명시 — verified_by R1
- **inherited_criterion**: "본문에서 근거 F1 상승과 LF-Eval 상승을 서로 독립적인 두 증거로 읽을 수 있는 문장이 없다."
- **fully_addressed**
  1. 본문 LF-Eval 정의 부근에 LF-Eval이 gold 조문 사용을 채점 기준에 포함하므로 근거 회수 개선과 독립적인 증거가 아니라는 구절이 있다.
  2. 본문(요약 포함) 어디에도 근거 F1 상승과 LF-Eval 상승을 "두 독립 증거", "서로 다른 측면에서 모두 확인" 같은 수렴 증거로 제시하는 문장이 없다.
  3. 보충 S1에 (a) 평가 프롬프트의 해당 기준 위치(`research/prompts/koblex_lf_eval.json` 인용 위치), (b) 생성기와 평가기가 같은 모델이지만 두 조건에 대칭으로 작용한다는 문장이 있다.
  4. (선택, P2 취급 가능) ΔF1–ΔLF 상관·분해 수치는 없어도 된다. 있다면 재계산 출력과 일치해야 한다(G1).
- **악화 예시**: 장 요약(RM-05)이 근거 F1과 LF-Eval을 독립적인 수렴 증거로 묶음; 생성기=평가기 문제를 "편향 없음"으로 단정함.
- **expected_change_surface**: 4.4 첫 문단 LF-Eval 정의 문장, 보충 S1.

### RM-10 RQ2 shortlist Recall 차이의 CI 산출과 그림 2 삭제 — verified_by R1
- **inherited_criterion**: "RQ2 품질 주장에 CI가 있고, 그 값이 새 출력 파일과 일치하며, 본문 그림은 2개(현 그림 1, 3)로 줄어 번호가 갱신된다."
- **fully_addressed**
  1. 4.3 본문의 shortlist gold Recall 차이(원본 +5.16점)에 95% CI가 문장으로 붙어 있다. 모든 gold가 shortlist에 남은 문항 비율 차이(원본 112→130)에도 대응 CI가 있다.
  2. 두 CI가 `results/koblex-reproduction-v1/chapter4-revision-v1/shortlist-bootstrap.json`(또는 같은 G4 디렉터리의 동등 출력)과 일치하고, 그 출력이 잠금 절차(151그룹, 10,000회, seed 20261108, percentile)로 산출되었다(G6; Phase 2A에서 출력 파일의 절차 메타데이터 또는 스크립트로 확인).
  3. 보충 S1에 이 구간이 결과 관찰 후 같은 절차로 추가 산출한 탐색적 구간이라는 명시가 있고, `analysis-spec.json`의 "no new inference" 원칙과의 관계가 투명하게 처리되어 있다.
  4. 원본 그림 2가 본문에서 삭제되어 본문 그림이 2개이며, 번호(그림 1, 그림 2로 재번호)와 본문 내 그림 참조가 모두 갱신되어 있다. 보충 S8(그림 자료집)이 이 이동을 반영한다.
  5. R1·DA의 근사 구간 [+2.6, +8.0]을 그대로 쓰지 않았다.
- **악화 예시**: CI가 0을 포함하는데 "개선"을 단정하거나, 다른 seed·반복 수로 산출함(G6 위반); 그림 삭제 후 본문에 "그림 3" 같은 깨진 참조가 남음(G5 minor); shortlist 수치 4개가 본문에서 사라져 정보가 손실됨.
- **expected_change_surface**: 4.3 첫 문단, 원본 그림 2 위치, 보충 S1·S8, `chapter4-revision-v1/`.

### RM-11 개선 원천(shortlist 유지 vs 선택 단계) 한 문장 — verified_by R2
- **inherited_criterion**: "4.3–4.5 사이에 shortlist 유지 개선과 최종 근거 개선을 잇는 정량 문장이 있고, 그 수치가 재계산 출력과 일치한다."
- **fully_addressed**
  1. 4.3–4.5 사이에 shortlist에 남은 gold 출현 중 최종 선택된 비율(조건부 선택률)을 CE와 Jev 각각에 대해 보고하는 문장이 있다.
  2. 그 비율(분자/분모 포함)이 `chapter4-prep-v1/A4/stage-summary.jsonl`·`gold-occurrences.jsonl`에서 재계산한 G4 디렉터리 출력과 일치한다. R2의 79.5%·77.6%는 출력이 있을 때만 쓸 수 있다.
  3. "Jev의 이득은 주로 재정렬 단계의 후보 유지에서 나타났고 선택 단계의 추가 이득은 관찰되지 않았다"와 같은 해석 문장은 재계산 결과가 그 방향을 지지할 때만 있다(조건부 선택률이 Jev ≤ CE 또는 거의 같음). 지지하지 않으면 해석 문장이 없거나 결과에 맞게 바뀌어 있다.
  4. 미선택에 목록당 1개 제약이 섞여 있다는 캡션 단서가 유지된다.
- **악화 예시**: 재계산 결과와 맞지 않는 방향의 원천 해석; 조건부 선택률 차이를 Jev 선택 우위의 증거로 격상함; 목록당 1개 제약 단서 삭제.
- **expected_change_surface**: 4.3 셋째 문단 또는 4.5 첫 문단(그림 3 직후 위치, 재번호 후 그림 2).

### RM-12 hop별 결과 서술의 근거 보강 — verified_by R2
- **inherited_criterion**: "1-hop "하락"이 몇 문항에서 오는지 본문에서 알 수 있고, 3-hop 1/42의 구조적 맥락이 S6에 있다."
- **fully_addressed**
  1. 4.2 hop별 F1 문장에 hop별 Jev 우세/동률/CE 우세 문항 수가 함께 있고(최소한 1-hop 하락이 몇 문항에서 오는지 드러남), 그 값이 `chapter4-prep-v1/A1/question-metrics.jsonl`에서 재계산한 출력과 일치한다(DA의 1-hop 0/56/1은 참고일 뿐).
  2. "전체 차이는 주로 2·3-hop 문항에서 관측되었다"와 같은 뜻의 문장이 있다. 단, 재계산된 문항 수가 그 서술을 지지해야 한다.
  3. 새 subgroup CI를 본문에 넣지 않았다(요구 사항 아님; 넣었다면 다중성 해석 규칙(RM-08)이 적용되는지 확인).
  4. 보충 S6에 hop별 shortlist 동시 선택 가능 문항 수(CE/Jev)와 "예상 법령 목록 수 < gold 수" 문항 수가 있어 3-hop 완전 회수 1/42의 구조적 맥락을 설명하고, 값이 `A4/pool-constraints.jsonl`·`A4/question-stages.jsonl` 재계산 출력과 일치한다(R2의 2/42, 11/42, 9·8·2는 참고일 뿐).
- **악화 예시**: hop별 결과를 "multi-hop에서 유리"로 일반화함(주장 상한); 1-hop 하락을 숨기거나 삭제함.
- **expected_change_surface**: 4.2 셋째 문단, 보충 S6.

### RM-13 CE 입력 형식 진단: 공식 코드 일치와 편향 방향 — verified_by R2
- **inherited_criterion**: "진단이 test-set 튜닝처럼만 읽히지 않고, 편향 방향과 민감도 결과가 S1에 있다."
- **fully_addressed**
  1. 4.1 본문에 "이 형식은 공식 코드의 재정렬 입력과 같고, 진단에서 CE에 가장 유리했으며 Jev에도 같은 입력을 적용하였다"와 같은 뜻의 구절이 있다. 세 요소(공식 코드 일치, CE에 유리한 방향, Jev에 같은 입력)를 모두 담는다.
  2. 보충 S1에 진단 30문항을 제외한 문항에서의 근거 F1·LF-Eval 차이(민감도)가 있고, 재계산 출력과 일치한다(R1의 196문항/139그룹 +3.34점은 참고일 뿐).
  3. 보충 S4에 대표 사례 A가 진단 30문항에 포함되는지가 사실대로 적혀 있다(포함 여부를 재확인한 결과).
  4. 공식 코드와의 일치 주장이 `data/koblex/upstream/experiments/parser/`와 모순되지 않는다(Phase 2A 대조).
- **악화 예시**: 진단을 사전 계획된 것처럼 서술함; 편향 방향을 반대로(Jev에 유리하게) 서술함; 민감도 결과를 확증 근거로 격상함.
- **expected_change_surface**: 4.1 첫 문단 마지막 문장, 보충 S1 둘째 문단, S4.

### RM-14 사례 C 해석 문장 중립화와 4.5 목적 문장 — verified_by R2
- **inherited_criterion**: "사례 C 문장이 근거 F1 하락을 "더 나쁜 근거 선택"으로 전제하지 않는다."
- **fully_addressed**
  1. 원본 4.5 셋째 문단 "표현 중복의 증가가 … 보여준다"에 해당하는 문장이 근거 F1과 Token F1이 반대 방향으로 변해 두 자동 지표가 서로 다른 측면을 반영하는 사례라는 취지로 바뀌어 있고, 근거 F1 하락을 근거 선택의 질 저하로 전제하는 표현이 없다.
  2. Jev가 선택한 정답 외 조문의 법률적 적절성은 판정하지 않았다는 기존 단서가 유지된다.
  3. 4.5 첫 문장에 목적 구절("4.2–4.4의 평균 차이가 어떤 문항 수준 변화로 구성되는지 보이기 위해" 등)이 있다.
  4. 조문명을 병기했다면 `chapter4-prep-v1/A6/casebook.jsonl`과 일치한다(병기는 선택).
- **악화 예시**: 사례 C가 Jev 선택의 법률적 타당성을 주장하거나 부정하는 방향으로 바뀜(사람·전문가 판단을 함의하면 G2와도 충돌); 법률적 적절성 미판정 단서 삭제.
- **expected_change_surface**: 4.5 첫 문장, 4.5 셋째 문단(원본 l.81).

### RM-15 장 내부 용어·단위 정리 (번역 대비) — verified_by EIC
- **inherited_criterion**: "같은 개념에 본문 안에서 하나의 국문 용어만 쓰이고, 그림 라벨과의 대응이 캡션 또는 S1에 있다."
- **fully_addressed**
  1. "공식 hop별"이 "데이터셋 hop 라벨별"(또는 같은 뜻)로 바뀌어 있다.
  2. "시험"이 test split 의미로만 쓰이고, 탐색적 프레이밍 문장(원본 l.7)이 평가(test) 문항의 결과를 관찰한 뒤의 분석임을 대상과 함께 명시한다.
  3. 그림 영문 라벨과 본문 용어의 대응(Complete coverage = 완전 회수, Reranking loss = shortlist 탈락, Selection loss = 미선택)이 남은 그림의 캡션 또는 S1에 있다.
  4. 보충 S1에 장 내부 국·영 용어 대응표(완전 회수, shortlist, gold, 점/%p 등)가 있다.
  5. "완전 회수"와 "모든 gold 포함" 중 하나로 본문 용어가 통일되어 있다(Phase 2A에서 본문 전체 검색: 같은 개념에 두 국문 용어가 공존하지 않음). 점과 %p의 쓰임이 지표 유형에 따라 일관된다.
- **범위 메모**: 전 장 공통 용어집과 "예상 법령/예상 조문" 결정은 T9 소관이라 판정하지 않는다.
- **악화 예시**: 새 용어 혼용이 생김(예: 수정 중 추가된 문장이 통일 전 용어를 다시 씀); 그림 2 삭제 후 캡션 대응이 사라짐.
- **expected_change_surface**: 4.1(원본 l.5, l.7), 4.2(원본 l.19), 그림 캡션, 보충 S1.

### RM-16 재현 실행 조건 차이 목록 (보충자료) — verified_by R2
- **inherited_criterion**: "표의 각 행이 파일 위치와 연결되고, 원 논문 수치는 검증 출처 없이 기재하지 않는다."
- **fully_addressed**
  1. 보충 S5에 원 공개 코드 대비 실행 차이 표가 있고, 로드맵이 열거한 차원(CE 장치, 생성 모델 snapshot, API, bm25s 버전 고정, temperature·top_p 동일 여부, 공개 코드 결함 수정)을 다룬다. 저장 파일로 확인되지 않는 차원은 행을 빼거나 미확인으로 표기할 수 있다.
  2. 각 행에 근거 파일 위치(`protocol-lock.json` signature, `runtime-settings.json`, `ce-runtime.json`, `data/koblex/upstream/experiments/parser/` 등)가 연결되어 있고, 각 행의 내용이 그 파일과 일치한다(Phase 2A에서 행별 대조). **로드맵 문구 자체보다 파일이 우선한다**: 로드맵 예시(예: "Chat Completions → Responses")가 파일과 다르면, 파일과 일치하는 표기가 FULLY의 조건이다.
  3. 원 논문 ParSeR 절대 수치가 검증 출처 없이 기재되지 않았다(D-01).
- **악화 예시**: 파일로 뒷받침되지 않는 실행 차이가 사실처럼 기재됨; 원 논문 수치 병기나 원 실행 결함 추론(D-01).
- **expected_change_surface**: 보충 S5.

### RM-17 자원 집계 범위를 "생성 단계 기준"으로 한정 — verified_by R3
- **inherited_criterion**: "본문의 자원 결론 범위가 명시되고, 선택 단계 사용량은 산출되었거나 미산출이 명시된다."
- **fully_addressed**
  1. 4.4 자원 문단에 "답변 생성 단계 기준"과 같은 범위 한정 구절이 있고, "입력량 절감은 관찰되지 않았다"가 생성 단계에 대한 결론임이 문장에서 드러난다.
  2. 다음 중 하나가 있다: (a) 보충 S6(또는 S3)에 LLM 선택 호출의 조건별 평균 입력·출력 토큰 행이 있고, 저장 응답 기록에서 조건별로 결정적으로 매핑해 재계산한 출력과 일치한다; 또는 (b) S3에 "선택 단계 사용량은 산출하지 않았다"는 명시가 있다.
  3. R3의 호출 유형 분류(입력 토큰 구간 휴리스틱)를 쓰지 않았다.
- **악화 예시**: 자원 결론이 파이프라인 전체로 확대됨; 휴리스틱 분류에 기반한 수치 사용; 비용 절감 함의.
- **expected_change_surface**: 4.4 둘째 문단(원본 l.52), 보충 S3·S6.

### RM-18 지연 표본 60문항의 품질 차이(기술통계) — verified_by R1
- **inherited_criterion**: "S9에 같은 60문항의 품질 차이가 있고, 본문 요약은 226문항 품질과 60문항 지연을 하나의 비율로 결합하지 않는다."
- **fully_addressed**
  1. 보충 S9에 지연 표본 60문항에서의 품질 차이(근거 F1, LF-Eval, Token F1)가 기술통계로 있고, 값이 `results/koblex-latency-v1/protocol.json`의 표본 문항 ID와 `chapter4-prep-v1/A1/question-metrics.jsonl`로 재계산한 출력과 일치한다(R1의 +1.39/+0.87/+0.47은 참고일 뿐).
  2. 본문(요약 포함) 어디에도 226문항 품질과 60문항 지연을 하나의 비율·교환 비율로 결합한 표현이 없다.
  3. 60문항 품질 차이에 추론 통계(CI·p값)를 붙여 확증적으로 쓰지 않았다(로드맵은 기술통계를 요구).
- **악화 예시**: 60문항 품질 차이를 근거로 지연 대비 효율 주장을 만듦.
- **expected_change_surface**: 보충 S9, 장 요약.

---

## 5. P2 — consider (사전 확정 기록 없음; 결정 무관 참고 확인)

프로토콜상 consider 항목은 Phase 1 기록을 만들지 않고 Phase 2A에서 `applied_criterion: not_precommitted`로 수준 1–2 기준에 직접 대어 판정하며, 어떤 결정 단계에도 영향을 주지 않는다. 다만 사용자가 P2 반영 범위를 "보충자료 추가 또는 길이 중립 문구"로 제한했으므로, Phase 2A가 쓸 **범위 적합성 확인 사항**을 아래에 고정한다. 범위를 벗어난 P2 반영은 그 자체로 판정을 바꾸지 않으며 관찰로 기록한다. 단, 그 결과 G1–G6이나 §1.2 경계를 위반하면 해당 공통 조건의 new issue(`regression`)로 다룬다.

| RM | 범위에 맞는 반영 형태 | 범위 이탈 신호(관찰 기록) | 공통 조건 연결 |
|---|---|---|---|
| RM-19 | S9에 Jev 집합 겹침 하위 꼬리, 두 실행 날짜, 호출 간 비결정성과 시점 간 서비스 변화를 구분할 수 없다는 문장, raw.jsonl의 top-10 row ID 유무 | 본문 추가 | R3 0.60/0.85, DA 35/36회 사용 시 G1 |
| RM-20 | 표 1 행 이름을 길이가 같은 "문항 평균의 제95백분위수"로 바꿈; S9에 쌍당 지연·하드웨어·동시성 4 이유·양방향 이식성 서술 | 표 1·본문에 문장 추가 | — |
| RM-21 | 본문 "약 0.61달러"를 같은 길이의 문항당 단가로 치환 또는 병기, 총액은 S9 | GPT-4o 비용과의 비교(D-07, §1.2) | 단가 G1 |
| RM-22 | S6(캡션은 선택)에 미매핑 gold 27개 원인 서술(재확인 전제) | 본문 추가 | R2 26/27·25/27 사용 시 G1 |
| RM-23 | S6에 미선택 출현 분해와 shortlist 내 순위 기술통계 | 그림 3 6범주 재작성(D-11) | G1 |
| RM-24 | S3에 재사용 문항 수 정의·재계산값, 121/119/122 관계 설명 | 본문 구절 추가(사용자 범위상 길이 증가) | G1 |
| RM-25 | S1에 판정기 점검이 독립 재호출인지 캐시인지, 조건별 800자 초과 답변 수 | — | G1 |
| RM-26 | S1에 어절 단위 Token F1의 민감성 한 구절 | 형태소 재계산(D-10) | — |
| RM-27 | 방법 장 참조로 대체하거나 길이 중립 구절 | 본문 구절 추가 | 방법 장 표현 불일치는 T1 메모 |
| RM-28 | 사용량 토큰 문장 삭제, 빈 줄 정리, "52개", "5.64초" 표기 — 지면 감소 또는 동일 | — | — |
| RM-29 | 절 제목에 "(Jev)" 병기 여부(팀 RQ 문구 T2에 따름) | — | 길이 미세 증가는 관찰만 |
| RM-30 | (a) 대기 제외 확인 시 S9에 "E2E 측정이 아닌 참고치", 아니면 (b) S9에 호출 구조 서술 | 본문 (c) 9% 구절 추가(사용자 범위상 길이 증가); 본문 E2E 규모 추정(D-06, §1.2) | D-06은 회귀 판별 대상 |

---

## 6. 범위 밖 항목

### 6.1 거절·보류 D-01 ~ D-17
판정 대상이 아니다. 반영하지 않아도 어떤 판정·결정에도 영향을 주지 않는다. 단, 다음은 §1.2에 따라 **원고에 들어가면** 회귀 판별 대상이다: D-01(검증되지 않은 원 논문 수치, 결함 추론), D-05(잠금 CI 교체), D-06(본문 E2E 규모 추정), D-07(GPT-4o 비용 비교), D-15(shortlist 축소 레버 함의), D-17·G2(사람 평가). D-02·D-03·D-04·D-16(유료 작업)은 "optional future work"로 언급되는 것은 허용되고, 수행 결과가 나타나면 G3 위반이다. D-08·D-09·D-10·D-11·D-12·D-13·D-14는 반영 여부를 판정하지 않는다(D-12·D-11 방식이 채택되면 RM-10·RM-23 쪽에서 등가 여부를 판단).

### 6.2 팀 조율 메모 T1 ~ T12
다른 장 소관이다. 제4장 수정 요구가 아니므로 판정하지 않으며, 제4장에 해당 내용이 없다고 해서 미반영으로 보지 않는다. 다만 T7(주장 상한)의 내용은 RM-05 기준(§4)과 §1.2에 이미 포함되어 있어 그 경로로만 판정에 영향을 준다. T2(RQ 문구), T8(요약 분량), T9(전 장 용어집)는 RM-04·RM-05·RM-15에서 판정 제외 범위로 명시하였다.

---

## 7. 결정 도출 규칙 (프로토콜 § Decision Derivation, 이 라운드에 적용)

- 결정 범위: `Accept` / `Minor Revision` / `Major Revision` / `user_review_required`(보류), 또는 fail-closed 중단. **Reject는 Stage 3′ 결정이 아니다**(심각하면 `reject_recommended: true` 표기). 순서: Accept < Minor < Major.
- 항목 수: must_fix 2개(RM-01, RM-02), should_fix 16개(RM-03 ~ RM-18), consider 12개(RM-19 ~ RM-30, 결정 무관).
- **should_fix_addressed_rate** = (최종 판정이 FULLY_ADDRESSED 또는 PARTIALLY_ADDRESSED인 should_fix 수) / 16. 80% 이상이려면 **13개 이상**(12/16 = 75%는 미달). 저자 설명만 있는 NOT_ADDRESSED는 분자에 넣지 않는다. CANNOT_VERIFY는 분자에 들어가지 않는다.

**Step 1 — 관문(먼저 맞는 것 적용)**
- G0: 입력 manifest가 불완전하거나 해시가 맞지 않음 → `[RE-REVIEW-ABORT: manifest_incomplete | manifest_hash_mismatch]`. (§0.3-1 참고: 기계용 산출물 부재 시 orchestrator가 수작업 적용 여부를 먼저 정해야 한다.)
- G1: 2A 판정과 최종 판정이 다른데 adjustment 기록이 없는 행 → `[RE-REVIEW-ABORT: criteria_drift]`.
- G2: 사용자 입력 대기 상태(dissent bound 초과 시 미판정 dissent, 해소되지 않은 escalation exception 등) → `user_review_required`. 교차 모델 미사용이므로 diverges 경로는 해당 없음. dissent bound: must_fix 항목에 dissent가 하나라도 있거나, 전체 30개 항목 중 ⌈30/3⌉ = 10개 초과 dissent → 모든 dissent를 사용자 판정으로 넘긴다.

**Step 2 — 기본 결정(먼저 맞는 것 적용)**
| # | 조건 | 결과 | 이 라운드의 구체적 의미 |
|---|---|---|---|
| B1 | critical 심각도 driving finding의 must_fix가 MADE_WORSE, 또는 severity critical인 `regression` new issue | Major + `reject_recommended` | driving finding은 모두 Major 이하라 앞쪽 경로는 불가. critical regression new issue만 해당 |
| B2 | must_fix 중 50% 이상이 NOT_ADDRESSED/MADE_WORSE | Major + `reject_recommended` | must_fix가 2개이므로 **RM-01 또는 RM-02 중 하나만 NOT_ADDRESSED/MADE_WORSE여도(1/2 = 50%) 발동** |
| B3 | must_fix 중 NOT_ADDRESSED/MADE_WORSE/CANNOT_VERIFY가 있거나, major `regression` new issue | Major | B2에 걸리지 않은 must_fix CANNOT_VERIFY, 또는 G1·G2·G3·G4·G5(3쪽 초과)·G6 위반 중 major로 배정된 regression |
| B4 | must_fix 또는 should_fix의 PARTIALLY_ADDRESSED 중 `residual_obligation_class: must_fix`가 있음 | Major | 예: RM-01 핵심 1–4 일부 누락, RM-02 "결과 관찰 후" 시점 누락 |
| B5 | must_fix PARTIALLY_ADDRESSED(잔여 should_fix/consider), 또는 rate < 80%, 또는 should_fix MADE_WORSE, 또는 minor `regression` new issue | Minor | 예: RM-01의 S7 서술만 누락; should_fix 충족 12개 이하; 참조·번호 오류 같은 minor regression |
| B6 | 나머지: must_fix 모두 FULLY_ADDRESSED(반박 인정 포함), rate ≥ 80%, should_fix MADE_WORSE 없음, should_fix PARTIAL의 must_fix 잔여 없음, regression new issue 없음 | **Accept** | |

**Step 3 — 하한**: 승인된 escalation exception의 `mechanical_decision_impact`와 기본 결정 중 높은 쪽. 대기 중이거나 기각된 exception은 영향 없음.

**New issue 귀속**: `regression`(수정으로 생김, 수정본에만 있음)만 B1/B3/B5에 영향을 준다. `previously_missed`와 `indeterminate`는 보고만 하고 결정에 영향을 주지 않는다(goalpost guard). 원본에도 있던 문제를 이유로 결정을 올리려면 Phase 2A의 escalation exception(integrity/ethics/safety/legal_compliance/fatal_validity, 사용자 확인 필수)만 가능하다. Phase 2A 종료(`[EVIDENCE-COMMITTED]`) 후에는 new issue 집합을 바꿀 수 없다.

**결정 후**: Accept·Minor → Stage 4.5, Major → Stage 4′. Major이면 Socratic 잔여 코칭이 기본이나, 사용자는 건너뛸 수 있다.

---

## 8. NewStandardRecord

없음. 위 operationalization은 모두 로드맵 수용 기준·필요 변경·공통 조건(level 1), 결정서 차단 항목(level 2), seat 지적(level 3), 동결 카드(level 4)에서 도출하였다. 측정 방식을 구체화한 부분(RM-04 분량을 글자 수로 측정하고 55% 이하를 "약 절반"으로 인정, RM-08 보정값을 검증자가 재계산 대조, RM-16에서 파일이 로드맵 문구보다 우선)은 상위 기준을 넓히지 않는 측정 규칙이다.

[CONTRACT-ACKNOWLEDGED]
