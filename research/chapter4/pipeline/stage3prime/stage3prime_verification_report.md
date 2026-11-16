# Verification Review Report

- 대상: 제4장 "실험 결과 및 분석" (KoBLEX ParSeR, 공개 코드 CE / 수정 CE / Decision Model Jev)
- 단계: Stage 3′ Phase 2B — 답변서 공개 후 주장 대조와 결정 도출 (`re_review_mode_protocol.md`, ARS academic-paper-reviewer 3.24.2, § Phase 2B, § Decision Derivation, § Re-Review Output Format)
- 작성일: 2026-11-14
- 고정 입력(해시 재계산으로 일치 확인):
  - `stage3prime/phase1_criteria.md` sha256 `8c3f8db8f880223b1b96b98e304eb9a2a70844892f71c0ef6bd8de0da0304660` (precommitment_hash)
  - `stage3prime/phase2a_evidence_verdicts.md` sha256 `4219f563ddc84d1c678e5a118841214b6f34145947da231d8904969dad78244c` ([EVIDENCE-COMMITTED])
- 이번 단계에서 새로 공개된 입력: `stage4_response_to_reviewers.md`(답변서), `stage4_delta_report.md`(델타 보고). 둘 다 저자가 쓴 설득 문서로 보고, 원고·원자료에서 위치를 확인한 내용만 근거로 삼았다.

---

## Judge Record (#539)

- **Verification judge**: Claude Opus 5.5 (`claude-opus-5-5`), 이번 세션 자체. Phase 1·2A·2B 모두 같은 계열.
- **Round-1 panel provenance**: `invalid — carrier absent` (Schema 6 `review_panel_provenance` 아티팩트가 Round 1에서 생성되지 않음). 여섯 축 모두 `unknown`.
- **Blind cross-model pass**: `not_configured` (사용자 지시로 교차 모델 검증을 쓰지 않음, orchestrator 결정 3). 실행 수준의 단일 계열 고지를 적용한다.
- **Pre-committed criteria**: `8c3f8db8f880223b1b96b98e304eb9a2a70844892f71c0ef6bd8de0da0304660`
- **Prompt/rubric surfaces**: `academic-paper-reviewer/references/re_review_mode_protocol.md` § Three-Gate Orchestration(Phase 2B), § Decision Derivation(Step 1–3), § Commitment Ledger Verification, § Re-Review Output Format. 계약 버전은 3.24.2 문서 기준.
- **계약 적용 방식**: Schema 7 JSON core, author-adjudication sidecar, revision-evidence-bundle 1.0, input manifest 1.1, apply report 1.3, traceability sidecar가 **없다**. 세 단계 계약 규칙(Phase 1 기준 고정 → 2A 증거 판정 → 2B 대조)과 결정 도출 규칙을 **수작업으로 적용**했고 checker(`scripts/check_re_review_synthesis.py`)는 실행하지 않았다(orchestrator 결정 1). 계약 checker를 그대로 돌리면 G0(`manifest_incomplete`)로 중단되었을 것이므로, 아래 결정은 수작업 도출 결과이며 checker 재계산을 거치지 않았다는 점을 밝힌다.
- **Reviewer configuration**: `round1_cards_reused`
- **Routing**: `card_mapped` (ID 접두어 정규화, 로드맵 l.6 규약; Phase 1 §0.3-2, orchestrator 결정 2)
- **Apply-report chain**: 해당 산출물 없음. 수작업 적용이며 원본 원고(`pipeline/pre_stage4/`)는 제공되어 비교에 사용함. 계약 어휘의 `not_run_no_reports`에 해당.
- **Evidence seen by the judge**: 수정본(`research/chapter4/chapter4.md`, `chapter4-supplement.md`, tex, PDF) + 원본 원고(`pre_stage4/`) + 수정 로드맵·편집 결정서·심사자 카드 + 재계산 산출물(`results/koblex-reproduction-v1/chapter4-revision-v1/`) + 원자료 + 답변서·델타 보고(Phase 2B에서만).
- **Judging budget**: Phase 2B 약 15회 도구 호출(해시 재계산, 줄 단위 대조, 코드·그림·로그 확인). 생성 단계와 별도. 토큰 수는 따로 계측하지 않음.
- **Dissent / escalation exception**: 둘 다 0건(Phase 2A 기록 그대로).
- **Adjustment records**: 0건. 2B에서 바뀐 판정이 없다.

This verification round ran on the same model family that drove the revisions; over-optimization to this judge's latent biases is possible (Ren et al. 2026, arXiv:2607.13104 §8.1.2).

---

## Decision

**Accept** (`decision_state: Accept`, `reject_recommended: false`). 다음 단계는 Stage 4.5(최종 무결성 점검)이다. 아래 잔여 항목은 결정과 무관하며 Stage 4.5에서 처리할 목록이다.

---

## Revision Response Checklist

Phase 2A 판정은 동결되어 있다. 아래 "최종 판정"은 모두 2A 판정과 같고, 답변서로 바뀐 판정은 없다(adjustment 0건). "Verified?"는 FULLY→YES, PARTIALLY→PARTIAL, NOT/MADE_WORSE→NO, CANNOT_VERIFY→CANNOT_VERIFY로 대응시켰다. "주장 대조"는 답변서 주장이 2A 판정과 원고에서 뒷받침되는지 본 결과이다.

### must_fix — Required Revisions

| Transport ref | Original Review Comment | Author triage | Author's Claim | Response Status | Revision Location | Verified? | Cross-model (#539) | Quality Assessment |
|---|---|---|---|---|---|---|---|---|
| R1 (RM-01) | 필터링 절에서 Jev+필터링의 0 배제 감소(Recall, 완전 회수) 구간을 빼 보고 비대칭이 생김 (EIC-W4, R1-C1, DA-P1-2; 결정서 차단 항목 B1) | will_address (accepted) | "ch:L60에 Recall·완전 회수 CI와 F1이 선택 기준이라는 구절, ch:L51–58 표 2 완전 회수 열, sup:L186 필터링 후 완전 회수 33.19% 동일" | FULLY_ADDRESSED | 본문 l.51–60, 보충 S7 l.180–199 | ✅ Yes | not_configured | 주장 위치 3곳 모두 원고에 있음(l.60 CI 6개, 표 2 완전 회수 열, S7 l.186). 2A 판정과 일치. 과장 없음 |
| R2 (RM-02) | 필터링 문턱값 격자를 결과 관찰 후 바꾼 사실 미공개 (R1-C2; 결정서 차단 항목 B2) | will_address (accepted) | "sup:L182에 격자 변경 이력·변경 시점·R1 질문 3 답, ch:L49 참조 구절" | FULLY_ADDRESSED | 보충 S7 l.182, 본문 l.49 | ✅ Yes | not_configured | S7 l.182가 변경 전 격자, 변경 계기(CE 점수 0.05 미만), "이 결과를 확인한 뒤", 허용폭·목적함수 사전 기록 부재를 모두 진술. 2A 판정과 일치. 과장 없음 |

### should_fix — Suggested Revisions

| # | Original Review Comment | Author's Claim (답변서 §1) | Response Status (최종 = 2A) | Verified? | 주장 대조 / Notes |
|---|---|---|---|---|---|
| RM-03 | Jev 단일 실행 조건을 앞에 배치 | accepted — ch:L7 끝 두 문장, ch:L41 중복 축소 | FULLY_ADDRESSED | ✅ | 일치. l.7 마지막 두 문장, l.41 축소 확인 |
| RM-04 | 4.4 필터링 압축·동기·교차 비교 이동 | accepted — ch:L49·L60, sup:L184–201 | FULLY_ADDRESSED | ✅ | 일치. 2A 분량 측정 49.4%(기준 ≤55%) |
| RM-05 | RQ별 답 문장과 장 요약 | **partially** — ch:L11·L25·L45 첫 문장을 RQ 답으로, ch:L74 종합 문단, "4.6" 제목 미사용(T8·tex 범위) | PARTIALLY_ADDRESSED (residual_obligation_class: consider) | PARTIAL | 상태 표기는 2A와 일치(과장 아님). 다만 답변서는 2A가 찾은 잔여 결함 세 가지(4.4 첫 문장 수치 없음, 4.3 첫 문장의 "더 많이", 요약 5문장)를 밝히지 않았다 — 불충분 공개(PLO-1) |
| RM-06 | 기여 구분 지도 | accepted — ch:L7, ch:L21, sup:L61–75 | FULLY_ADDRESSED | ✅ | 일치 |
| RM-07 | Token F1 경계 서술·p값 일관화 | accepted — ch:L45, sup:L31–42 | FULLY_ADDRESSED | ✅ | 일치. 본문 p값 0개 |
| RM-08 | 다중성 해석 규칙·비교 계열 | accepted — ch:L7, sup:L31–42 | FULLY_ADDRESSED | ✅ | 일치. Holm 최소 0.074, BH 0.0496 재계산 일치 |
| RM-09 | LF-Eval 비독립성 | accepted — ch:L45, sup:L23 | FULLY_ADDRESSED | ✅ | 일치 |
| RM-10 | shortlist Recall CI, 그림 2 삭제 | accepted — ch:L25, 그림 번호 갱신, sup:L29·L209, 그림 자료집 README/provenance | FULLY_ADDRESSED | ✅ | 일치. 그림 자료집 README l.49가 본문 제외 사실을 기록함을 2B에서 추가 확인 |
| RM-11 | 개선 원천 한 문장 | accepted — ch:L27 | FULLY_ADDRESSED | ✅ | 일치 |
| RM-12 | hop별 서술 근거 | accepted — ch:L19, sup:L164–172 | FULLY_ADDRESSED | ✅ | 일치 |
| RM-13 | CE 입력 형식 진단 | accepted — ch:L5, sup:L17, sup:L91 | FULLY_ADDRESSED | ✅ | 일치 |
| RM-14 | 사례 C 중립화, 4.5 목적 | accepted — ch:L64, ch:L72 | FULLY_ADDRESSED | ✅ | 일치 |
| RM-15 | 용어·단위 정리 | accepted — ch:L5·L7·L19·L15·L68, sup:L44–57 | FULLY_ADDRESSED | ✅ | 일치 |
| RM-16 | 재현 실행 조건 차이 표 | accepted (값 정정 포함) — sup:L105–122, API 행 "둘 다 Chat Completions" | FULLY_ADDRESSED | ✅ | 일치. 로드맵 문구 정정 주장은 `providers.py` l.393·저장 응답 객체로 2A가 이미 확인 |
| RM-17 | 자원 집계 범위 한정 | accepted — ch:L47, sup:L128–143 | FULLY_ADDRESSED | ✅ | 일치. "선택 단계 4행"은 S6 l.138–141 |
| RM-18 | 지연 표본 60문항 품질 차이 | accepted — sup:L217 | FULLY_ADDRESSED | ✅ | 일치 |

### consider — Nice to Fix (결정 무관)

| # | Author's Claim | Response Status (최종 = 2A) | 주장 대조 |
|---|---|---|---|
| RM-19 | accepted (보충만) — sup:L223 | FULLY_ADDRESSED | 일치 |
| RM-20 | accepted — ch:L37, sup:L219 | FULLY_ADDRESSED | 일치(seat 표의 R3-W5는 "partially"로 적혀 있어 답변서 내부 표기가 엇갈림, PLO-2) |
| RM-21 | accepted — 본문 총액 삭제, sup:L225 | FULLY_ADDRESSED | 일치 |
| RM-22 | accepted (보충만) — sup:L162 | FULLY_ADDRESSED | 일치(R2-W4 "partially"와 엇갈림, PLO-2) |
| RM-23 | accepted (보충만) — sup:L153–158 | FULLY_ADDRESSED | 일치 |
| RM-24 | accepted (보충만) — sup:L83 | FULLY_ADDRESSED | 일치(R1-C11 "partially"와 엇갈림, PLO-2) |
| RM-25 | accepted (보충만) — sup:L21·L25 | FULLY_ADDRESSED | 일치 |
| RM-26 | accepted (보충만) — sup:L21 | FULLY_ADDRESSED | 일치 |
| RM-27 | partially — sup:L9 지시문 원문·CE 비대칭, 설계 의도는 T1 | CANNOT_VERIFY | 답변서가 가리키는 sup:L9는 2A가 이미 본 위치이며, 수용 기준("방법 장과 표현 일치")은 다른 장 자료가 없어 여전히 확인할 수 없다. 판정 변경 없음 |
| RM-28 | accepted — 문장 삭제·빈 줄·ch:L7·ch:L39 | FULLY_ADDRESSED | 일치 |
| RM-29 | deferred-to-team (T2) | CANNOT_VERIFY | 일치(절 제목 변경 없음, T2 결정 기록 없음) |
| RM-30 | partially — (a) 불가, (b) sup:L221, (c) sup:L137 | FULLY_ADDRESSED | 답변서가 2A보다 낮게 표기(과소 주장). 판정은 원고 증거로 정해지므로 변경 없음. (a) 불가 근거인 "타이머가 세마포어 진입 전에 시작"은 `providers.py` l.104(`start = time.perf_counter()`)와 l.106(`async with self.semaphore`)로 2B에서 확인 |

### 추적 집계

| 우선순위 | 항목 수 | FULLY | PARTIALLY | NOT | MADE_WORSE | CANNOT_VERIFY | 답변서 주장과 판정 일치 | 과장(overclaim) |
|---|---|---|---|---|---|---|---|---|
| must_fix | 2 | 2 | 0 | 0 | 0 | 0 | 2/2 | 0 |
| should_fix | 16 | 15 | 1 (RM-05) | 0 | 0 | 0 | 16/16 | 0 |
| consider | 12 | 10 | 0 | 0 | 0 | 2 (RM-27, RM-29) | 10/12 일치, 2건(RM-27·RM-30)은 답변서가 더 낮게 표기 | 0 |
| 계 | 30 | 27 | 1 | 0 | 0 | 2 | — | **0** |

- 판정 변경(adjustment record): 0건. 상향 근거(`author_pointer_located_evidence`, `valid_rebuttal`, `scope_correction`)를 쓸 대상이 없었다. 2A가 PARTIAL로 둔 RM-05에 대해 답변서는 새 위치를 제시하지 않았고(ch:L11·L25·L45·L74는 2A가 이미 본 위치), CANNOT_VERIFY인 RM-27·RM-29도 원고 측 새 증거가 없다.

---

## 답변서 주장 대조 (Phase 2B)

### 1. RM 단위 과장(overclaim): 0건
답변서가 "accepted"라고 적은 RM 중 2A에서 PARTIAL·NOT·MADE_WORSE·CANNOT_VERIFY인 항목은 없다. 2A가 PARTIAL로 판정한 RM-05는 답변서도 "partially"로 적었다. 2A가 CANNOT_VERIFY로 둔 RM-27·RM-29는 답변서가 각각 "partially", "deferred-to-team"으로 적어 완료를 주장하지 않았다.

### 2. seat 지적 단위 주장 중 원고로 확인한 것 (대표)

| 답변서 주장 | 확인 결과 |
|---|---|
| 서두: 새 구간 계산 전에 저장 구간 26개를 같은 값으로 재현(G6) | `revision-analysis.json` `verification`: `n: 26`, `all_exact: true` — 확인 |
| 서두: 사람 평가 관련 용어 0건(G2) | 2A G2 검색 결과와 일치 — 확인 |
| EIC-Minor(그림 3 범례): 새 그림 2에서 범례가 막대와 겹치지 않음 | `fig_4_5_gold_loss_stages_column.png` 확인: 범례는 오른쪽 위 빈 공간에 있고 막대와 겹치지 않음 — 확인 |
| EIC-Q1: 결과 관찰 후 탐색 분석임이 4.1·S7에 명시 | 본문 l.7 "평가(test) 문항의 결과를 이미 관찰한 뒤 수행한 탐색적 분석", S7 l.182 — 확인 |
| R1-Q2: 272쌍은 캐시 재사용 | S1 l.25 — 확인 |
| R3-W1(a)·R3-Q1: `latency_ms`가 대기 시간 포함 | `providers.py` l.104·l.106 — 확인 |
| R3-Q2: 두 실행 시각(캐시 파일 수정 시각 기준) | S9 l.223 — 확인 |
| R3-Q4: 선택 호출 입력 16,435 vs 16,591, 차이 평균 +156·중앙값 +84.5 | S6 l.140, l.143 — 확인 |
| 델타 §1: 본문 문자 수 7,630→7,575, 단어 수 1,858→1,866, 보충 8,484→18,377 | `wc -m`/`wc -w` 재계산 — 확인 |
| 델타 §1: PDF sha256 `a689ba8e…b240`, 빌드 로그 Overfull 0, 3쪽 | sha256 재계산 일치, `authoring-build.log` Overfull 0, "(3 pages)" — 확인 |
| 델타 §3: 새 산출물 4개 sha256 | 4개 모두 재계산 일치 — 확인 |
| 답변서 §4·델타 §5: 심사자 값과 재계산값 차이(13/20→12/20, 121/56/49→119/58/49, R3 선택 호출 규모 등) | 원고에는 재계산값만 들어갔음을 2A §1에서 확인 — 확인 |

### 3. 원고로 확인되지 않거나 일부만 확인된 주장 (판정·결정 무관)

| 주장 | 상태 | 비고 |
|---|---|---|
| 델타 §3 "원자료 불변(G4): 파일 43,757개 sha256 비교 — 변경 0, 추가 0" | 일부만 확인 | 검증자는 G4 README 입력 35개, `protocol-lock.json`, `analysis.json` 해시만 대조했다(2A G4). 43,757개 전체 비교의 기록은 제공되지 않았다. G4 판정은 2A의 독립 대조로 이미 충족이며, 이 주장 자체를 근거로 쓰지 않았다 |
| 델타 §1 "페이지 이미지(PDFKit 렌더)로 2·3쪽을 확인" | 일부만 확인 | 그림 파일과 빌드 로그로 확인했고, 렌더 이미지 자체는 보지 않았다 |
| 답변서 RM-05 "ch:L11·L25·L45 첫 문장을 RQ 답으로" | 표현은 사실, 공개는 불충분 | L45 첫 문장에 수치가 없고 L25 첫 문장의 shortlist 부분에 수치가 없다는 점을 밝히지 않음(PLO-1). 상태를 "partially"로 적었으므로 과장으로 보지 않음 |

### 4. 원고 근거 없이 판정을 바꾸려는 주장: 없음

---

## Commitment Ledger Verification

`revision_coach_agent` Step 3.5의 `commitment_extracted` 목록이 없다(Stage 3 checkpoint에서 사용자가 코칭을 건너뜀, `pipeline_state.md`). 따라서 이 단계는 **실행 대상 없음**으로 기록한다. 참고로 답변서는 거절·보류 D-01~D-17과 팀 메모 T1~T12를 §2·§3에서 항목별로 명시적으로 인정하고 있어, acknowledgment 성격의 약속은 모두 문서상 확인된다. `COMMITMENT_GAP` 0건.

---

## New Issues (Discovered During Revision)

| # | Attribution | Severity | Location | Description |
|---|---|---|---|---|
| — | — | — | — | Phase 2A에서 동결된 new issue 0건(regression·previously_missed·indeterminate 모두 0). Phase 2B는 new issue 집합을 바꿀 수 없다 |

### post_letter_observations (결정 무관, 다음 라운드·Stage 4.5 참고)
- **PLO-1** 답변서 RM-05 항목이 2A의 잔여 결함(4.4 첫 문장 수치 없음, 4.3 첫 문장 "더 많이", 요약 5문장)을 밝히지 않는다. 상태는 "partially"로 정확하다.
- **PLO-2** 답변서 내부 표기 불일치: RM 표의 RM-20·RM-22·RM-24는 "accepted"인데 seat 표의 R3-W5·R2-W4·R1-C11은 "partially"이다. seat 지적이 RM보다 범위가 넓고(본문 구절 생략 등) 사유가 함께 적혀 있어 오해 소지는 작지만, 최종본에서는 맞춰 두는 것이 좋다.
- **PLO-3** RM-30은 답변서가 "partially"로 적었으나 2A는 FULLY_ADDRESSED이다(과소 주장). 판정은 바꾸지 않는다.
- **PLO-4** 2A OBS-5(원고 수치 ↔ 재계산 출력 1:1 대조표 부재)는 델타 보고 §4("원고에 새로 들어간 재계산 수치" 표: 원고 위치 → `revision-analysis.json` 키)가 상당 부분 채운다. 다만 이 표는 저자 측 문서이고 G4 디렉터리 README에는 없다. G1은 2A에서 이미 충족이므로 판정 영향 없음.
- **PLO-5** 델타 §3의 43,757개 파일 불변 주장은 검증자가 일부(37개 파일)만 독립 확인했다.

---

## Decision Rationale

수작업으로 프로토콜 § Decision Derivation을 적용했다(checker 미실행, Judge Record 참조).

**Step 1 — 게이트**
- G0(manifest): 계약 manifest가 없다. orchestrator 결정 1에 따라 수작업 적용으로 진행하며 abort하지 않는다. 이 이탈은 Judge Record에 기록했다.
- G1(silent verdict change): 30개 항목 모두 최종 판정 = 2A 판정. adjustment 없는 변경 0건 → 통과.
- G2(pending user input): dissent 0, cross-model 미설정으로 diverges 행 0, escalation exception 0, CANNOT_VERIFY 재적용 대기 0 → 통과. (consider의 CANNOT_VERIFY 2건은 결정 무관이며 대기 상태를 만들지 않는다.)

**Step 2 — 기본 결정(먼저 맞는 규칙)**
- B1: 성립하지 않음. Phase 1이 기록한 대로 critical 심각도 driving finding이 없어 must_fix MADE_WORSE 경로는 불가능하고, critical regression new issue도 0건이다.
- B2: must_fix 2개 중 NOT/MADE_WORSE 0개(0%) → 불성립.
- B3: must_fix에 NOT/MADE_WORSE/CANNOT_VERIFY 없음, major regression 없음 → 불성립.
- B4: PARTIALLY_ADDRESSED는 should_fix RM-05 하나이고 `residual_obligation_class: consider` → must_fix 잔여 없음, 불성립.
- B5: must_fix PARTIAL 없음; `should_fix_addressed_rate` = 16/16 = **100%**(FULLY 15 + PARTIALLY 1, 기준 80% = 13개 이상); should_fix MADE_WORSE 없음; minor regression 없음 → 불성립.
- **B6 발동 → Accept.** must_fix 2/2 FULLY_ADDRESSED, rate 100%, should_fix MADE_WORSE 없음, must_fix 잔여 PARTIAL 없음, regression new issue 없음.

**Step 3 — 하한**: 승인된 escalation exception 0건 → 기본 결정 유지.

**결과**: `decision_state = Accept`, `reject_recommended = false`, 발동 규칙 **B6**. 상태 전이: Stage 3′ → Stage 4.5.

---

## Residual Issues (If Any)

결정에 영향을 주지 않는다. Stage 4.5에서 고칠지 판단할 목록이며, 고치는 경우에도 3쪽 제한(G5)과 수치 일치(G1)를 다시 확인해야 한다.

### A. Phase 2A 잔여 (RM-05, residual_obligation_class: consider)
1. **4.4 첫 문장에 수치 없음** (본문 l.45 "자동 답변 지표는 소폭 높아졌으나 Token F1의 개선은 경계적이었고, 입력량 절감은 관찰되지 않았다."). 첫 문장에 Token F1·LF-Eval 차이 값을 넣는다. 값은 `analysis.json` `comparisons`의 차이를 그대로 써야 한다. 표에서 바로 뺀 값(47.31−46.20=1.11)과 S9 l.217의 226문항 값(+1.12)이 반올림 때문에 다르므로 저장 차이값을 기준으로 맞출 것.
2. **4.3 첫 문장의 "더 많이"** (본문 l.25). shortlist 유지 차이 수치(예: shortlist Recall +5.16점)를 첫 문장에 넣는다.
3. **요약 문단 5문장** (본문 l.74). 기준은 3–4문장이다. 예를 들어 마지막 두 문장(지연, 9.85점)을 합치거나 하나를 줄인다. 주장 상한 (i)–(iv)는 유지해야 한다.

### B. Phase 2A 관찰 OBS-1–5
4. **OBS-1** 요약 l.74 "그 일부가 평균 근거 F1 3.19점 상승으로 이어졌다"는 경로를 해석하는 문장이다. 필요하면 "…와 함께 관찰되었다" 수준으로 완화한다(선택).
5. **OBS-2** S1 l.33 표에서 BH 0.0496이 "0.050"으로 표시된다. 표에 0.0496을 그대로 쓰거나 표 전체를 넷째 자리로 맞춘다.
6. **OBS-3** S9 l.219의 "Apple M5 Pro" 출처인 `results/koblex-latency-v1/README.md`가 S9 첫 문장(l.213)의 출처 목록에 없다. 목록에 README를 추가한다.
7. **OBS-4** S1 l.23 "평가기의 선호가 있다면 두 조건에 대칭적으로 작용한다"를 "작용할 것으로 본다" 수준으로 완화하는 것을 고려한다.
8. **OBS-5** 원고 수치 ↔ 재계산 출력 1:1 대조표가 허용 산출물 안에 없다. 델타 보고 §4 표(PLO-4)를 `chapter4-revision-v1/README.md`에 옮기거나 링크해 대조 근거를 산출물 디렉터리 안에 둔다.

### C. 확인 불가 consider 항목 (팀 결정 대기)
9. **RM-27** Jev 지시문 표현이 방법 장과 일치하는지: T1(방법 장 담당) 확인 후 반영.
10. **RM-29** 절 제목의 "Decision Model" 표기: T2 결정 후 반영.

### D. 답변서 정리 (원고 변경 아님)
11. RM-05 항목에 잔여 결함 세 가지를 명시하거나, 위 1–3을 고친 뒤 상태를 갱신한다(PLO-1).
12. RM 표와 seat 표의 상태 표기를 맞춘다: RM-20/R3-W5, RM-22/R2-W4, RM-24/R1-C11(PLO-2). RM-30은 원고 기준으로 "accepted"로 바꿀 수 있다(PLO-3).
13. 델타 §3의 43,757개 파일 불변 주장은 비교 기록(목록 해시 등)을 산출물로 남기거나, 검증 범위를 실제 대조 범위로 줄여 적는다(PLO-5).

답변서 과장(overclaim)으로 인한 잔여 항목은 없다(과장 0건).

[MATRIX-COMMITTED]
