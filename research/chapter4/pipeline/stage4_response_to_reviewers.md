# Stage 4 — 심사 의견 답변서 (Response to Reviewers, 제4장)

- 대상: `research/chapter4/chapter4.md`(수정본), `research/chapter4/chapter4-supplement.md`(수정본). 수정 전 원고는 `pipeline/pre_stage4/`.
- 범위(사용자 결정): P0·P1(RM-01~RM-18) 전부 반영. P2(RM-19~RM-30)는 보충자료 추가와 길이 중립 본문 문구만 반영. 다른 장에 의존하는 조건부 P2는 팀 메모로 둠. 거절·보류(D-01~D-17)는 유지하고 사유를 기록.
- 재계산: 모든 새 수치는 `scripts/chapter4_revision_analysis.py`가 원자료에서 결정적으로 다시 계산한 값이며(G1), 출력은 `results/koblex-reproduction-v1/chapter4-revision-v1/`. 새 구간은 잠금 bootstrap 코드(`legal_rag_jev.koblex_analysis.paired_bootstrap`, 151그룹, 10,000회, seed 20261108, percentile)를 그대로 import해 산출했고, 먼저 저장 구간 26개를 같은 값으로 재현했다(G6). 사후 산출임을 보충 S1에 명시.
- 위치 표기: `ch:Ln` = 수정본 `chapter4.md`의 줄, `sup:Ln` = 수정본 `chapter4-supplement.md`의 줄. Stage 4.5에서 본문을 줄인 뒤의 줄 번호로 갱신했다(사례 문단 통합으로 사례 C l.72→l.70, 종합 문단 l.74→l.72; 나머지 인용 줄과 보충자료 줄 번호는 변동 없음).
- 상태 표기: **accepted** / **partially** / **rejected** / **deferred-to-team**(T 메모) / **optional-future-work** / **noted**(강점·정보 제공 항목, 조치 불요).
- G2(제외 범위 내용) 준수: 수정 후 본문·보충·tex에서 해당 용어 검색 0건(Stage 4.5 재확인 포함).

---

## 1. RM 항목별 처리 요약

| RM | 처리 | 변경 위치 |
|---|---|---|
| RM-01 | accepted | ch:L60(Recall·완전 회수 CI, F1이 선택 기준이라는 구절), ch:L51–58(표 2 완전 회수 열), sup:L186(필터링 후 완전 회수 33.19% 동일) |
| RM-02 | accepted | sup:L182(격자 변경 이력·변경 시점·R1 질문 3 답), ch:L49(참조 구절) |
| RM-03 | accepted | ch:L7 끝 두 문장(단일 실행·CI 범위), ch:L41(4.3 말미 중복 축소) |
| RM-04 | accepted | ch:L49·L60(목적 문장, 압축), sup:L184–201(교차 비교·필터링 강도·선택 전 필터링·90% 기술통계·CE 10문항 문장 이동) |
| RM-05 | accepted (Stage 4.5에서 잔여 보완) | ch:L11·L25·L45 첫 문장을 RQ 답으로, ch:L72 종합 문단. Stage 3′ 검증이 지적한 잔여 세 가지를 이번 라운드에서 고침: (1) 4.4 첫 문장(ch:L45)에 Token F1 +1.12점·LF-Eval +2.58점과 CI(`analysis.json` 저장 차이값), (2) 4.3 첫 문장(ch:L25)의 "더 많이"를 shortlist Recall +5.16점과 CI로 교체, (3) 종합 문단을 4문장으로 줄이고 "그 일부가 … 이어졌다"를 "이와 함께 … 높아졌으나"로 완화(새 수치 없음, 주장 상한 유지). 별도 "4.6 요약" 제목은 쓰지 않음(T8, `chapter4.tex`/`preview.tex`가 수정 범위 밖) |
| RM-06 | accepted | ch:L7(기여 구분 문장), ch:L21, sup:L61–75(3조건×7지표 표, 수정 효과 CI) |
| RM-07 | accepted | ch:L45(결론 먼저, 본문 p값 삭제), sup:L31–42(p값 표, MC 민감도) |
| RM-08 | accepted | ch:L7(가설 생성적 해석 구절), sup:L31–42(계열 정의, Holm·BH, Precision CI) |
| RM-09 | accepted | ch:L45(비독립 구절), sup:L23(기준 인용, 대칭성, r=0.53, 분해) |
| RM-10 | accepted | ch:L25(CI 2개 + 사후 산출 표기), 그림 2(shortlist) 본문 삭제 → 그림 번호 갱신(ch:L68), sup:L29·L209, 그림 자료집 README/provenance |
| RM-11 | accepted | ch:L27(조건부 선택률, 원천 문장) |
| RM-12 | accepted | ch:L19(hop별 우세/동일/열세, 2·3-hop 문장), sup:L164–172(hop 표) |
| RM-13 | accepted | ch:L5(공식 코드 일치·편향 방향), sup:L17(민감도), sup:L91(사례 A 포함) |
| RM-14 | accepted | ch:L64(4.5 목적), ch:L70(사례 C 중립화) |
| RM-15 | accepted | ch:L5·L7("평가(test) 문항"), ch:L19("데이터셋 hop 라벨별"), ch:L15·L68(라벨 대응), sup:L44–57(용어표), "모든 gold 포함"→"완전 회수" 통일 |
| RM-16 | accepted (값 정정 포함) | sup:L105–122(실행 차이 표). 로드맵의 "Chat Completions→Responses" 행은 원자료와 맞지 않아 "둘 다 Chat Completions"로 기재(§4 불일치 참조) |
| RM-17 | accepted | ch:L47("답변 생성 단계 기준", 선택 호출 입력도 줄지 않음), sup:L128–143(선택 단계 사용량 4행) |
| RM-18 | accepted | sup:L217(60문항 품질 차이) |
| RM-19 | accepted (보충만) | sup:L223(겹침 꼬리, 날짜, row ID 미저장, 원인 구분 불가) |
| RM-20 | accepted | ch:L37(표 1 행 이름), sup:L219(쌍당 지연, 하드웨어, 동시성 4 근거, 양방향 서술). 표 1 쌍당 지연 행은 본문 길이 때문에 보충에만 둠(R3-W5와 같은 처리) |
| RM-21 | accepted | 본문 총액 문장은 4.4 압축으로 삭제(길이 감소), 단가·총액은 sup:L225 |
| RM-22 | accepted (보충만) | sup:L162. 그림 캡션 각주는 생략(선택 사항), 접두 매핑 민감도는 D-10(R2-W4와 같은 처리) |
| RM-23 | accepted (보충만) | sup:L153–158(미선택 분해, 순위 통계) |
| RM-24 | accepted (보충만) | sup:L83(재사용 정의와 세 값의 관계, "102문항에서만 차이"). 본문 구절은 길이 증가라 생략 |
| RM-25 | accepted (보충만) | sup:L21(800자 초과 0개), sup:L25(272쌍은 캐시 재사용 → 평가기 재현성 미검증) |
| RM-26 | accepted (보충만) | sup:L21 |
| RM-27 | partially | Jev 지시문 원문과 CE 비대칭을 sup:L9에 기재. 본문 구절은 길이 증가라 생략, 설계 의도는 T1 |
| RM-28 | accepted | 사용량 토큰 문장 삭제, 빈 줄 정리, ch:L7 "151개 그룹 중 표본에 해당하는 52개", ch:L39 "문항당 평균 5.64초" |
| RM-29 | deferred-to-team | T2(RQ 문구) 결정 전까지 절 제목 유지 |
| RM-30 | accepted | (a) 불가(수용 기준상 선택 사항): 호출별 `latency_ms`가 동시성 대기·재시도 대기를 포함함을 코드로 확인 → 사용 안 함. (b) 호출 구조를 sup:L221에 기술. (c) 문맥 비중 8.84%/9.31%는 sup:L137(본문은 길이 증가라 생략) |

---

## 2. Seat별 point-by-point 답변

### 2.1 EIC (Journal-Fit)

| ID | 요지 | 상태 | 조치·위치 / 사유 |
|---|---|---|---|
| EIC-W1 | RQ 답 문장·장 요약 부재 | accepted | 4.2–4.4 첫 문장을 수치가 들어간 RQ 답으로(ch:L11, L25, L45), 장 끝 4문장 종합 문단(ch:L72). 별도 "4.6" 제목은 T8과 tex 수정 범위 때문에 쓰지 않음(RM-05) |
| EIC-W2 | 기여 위계(+9.85) | accepted | ch:L7 기여 구분 문장, ch:L21, ch:L72 마지막 문장, sup S2 3조건 표(RM-06). 본문 3조건 표는 D-08로 거절(지면) |
| EIC-W3 | 필터링 지면·동기 | accepted | 선택지 A에 가깝게 압축, 목적 문장 추가, 교차 비교·선택 전 필터링·90% 통계를 S7로 이동(RM-04) |
| EIC-W4 | 0 배제 구간 누락 | accepted | ch:L60, 표 2 완전 회수 열(RM-01) |
| EIC-W5 | trade-off 통합 | partially | ch:L72 종합 문단에 한 번 통합. 1단 요약 표는 D-08로 거절. 품질·지연을 비율로 짝짓지 않음(R1-C7) |
| EIC-W6 | 비결정성 배치 | accepted | ch:L7 끝(RM-03) |
| EIC-W7 | 용어·단위 | accepted | sup 용어표, 캡션 라벨 대응, "완전 회수" 통일. 그림 2(shortlist) 삭제로 y축 "%" 문제 해소(RM-15) |
| EIC-W8 | 그림 2 정보량 | accepted | 그림 삭제(A안), CI는 문장으로(RM-10) |
| EIC-W9 | "시험" 다의성 | accepted | ch:L5·L7 "평가(test) 문항"(RM-15) |
| EIC-W10 | Token F1 p값 문장 | accepted | 결론 먼저, 본문 p값 삭제, p는 S1 표(RM-07) |
| EIC-W11 | 사례 C 어조, 4.5 목적 | accepted | ch:L64, ch:L70(RM-14) |
| EIC-Q1 | 필터링이 답하는 질문, 사전 계획 여부 | accepted | 목적 문장 ch:L49. 결과 관찰 후 추가한 탐색 분석임은 4.1·S7에 명시. RQ3 범위 정합은 T2 |
| EIC-Q2 | 공개 코드 CE 다른 지표 미수록 이유 | accepted | 지면 때문이었으며 S2 표로 전부 제시 |
| EIC-Q3 | 0 배제 구간 생략 의도 | accepted | 의도적 편집이 아니었고 보고 비대칭으로 판단해 본문에 추가(RM-01) |
| EIC-Q4 | 고정 영문 용어 | accepted | sup:L44–57 용어표. 전 장 용어집은 T9 |
| EIC-Minor l.7 | 그림 2 y축 % | accepted | 해당 그림 삭제 |
| EIC-Minor l.19 | "공식 hop별" | accepted | "데이터셋 hop 라벨별"(ch:L19) |
| EIC-Minor l.32–33 | 빈 줄 2개 | accepted | 정리 |
| EIC-Minor l.52 | 사용량 토큰 문장 중복 | accepted | 삭제(RM-28) |
| EIC-Minor 그림 3 범례 | 겹침 확인 | accepted | 수정본 PDF 2쪽(새 그림 2) 렌더링 확인, 범례가 막대와 겹치지 않음 |
| EIC 팀 메모 1–8 | Decision Model 정의, RQ 문구, 인용, 4.1 중복, 결론 분담, 결함 위상, 이해관계 고지, venue | deferred-to-team | T1, T2, T5, T3, T8, T6, T10, T12 |
| EIC FW | Jev 반복 실행, E2E 지연 | optional-future-work | D-02, D-03 |

### 2.2 R1 (방법론)

| ID | 요지 | 상태 | 조치·위치 / 사유 |
|---|---|---|---|
| R1-S1–S7 | 강점 | noted | — |
| R1-C1 | 필터링 0 배제 감소 누락 | accepted | ch:L60, 표 2, sup:L186(완전 회수 동일화), Precision CI도 본문에 포함(RM-01) |
| R1-C2 | 격자 사후 변경 | accepted | sup:L182, ch:L49 참조(RM-02) |
| R1-C3 | 다중성 정량화 | accepted | ch:L7 구절, sup:L31–42 Holm·BH(재계산: Holm 최소 0.074, BH 0.0496 — R1 값과 일치)(RM-08) |
| R1-C4 | Token F1 MC 의존·p 선택 보고 | accepted | 본문 "경계적", p값은 S1 표에 6개 일괄, MC 민감도 S1(재계산 12/20, §4). 반복 수 50,000 교체는 D-05로 거절 |
| R1-C5 | LF-Eval 결합·자기 평가·800자 | accepted | ch:L45 구절, sup:L23(기준 인용, 대칭성, r=0.53, 분해), sup:L21(800자 초과 0개)(RM-09, RM-25) |
| R1-C6 | 단일 draw | accepted | ch:L7(RM-03), raw.jsonl의 row ID 미저장은 sup:L223. 정량화는 D-02 |
| R1-C7 | 60문항 품질 차이 | accepted | sup:L217, 본문 요약은 품질·지연을 비율로 결합하지 않음(RM-18) |
| R1-C8 | shortlist 차이 CI | accepted | ch:L25(잠금 seed 재계산 [+2.61, +7.94], 모든 gold 유지 [+3.89, +12.38]%p), 사후 산출 명시(RM-10). 그림의 차이+CI 변환은 D-12 |
| R1-C9 | 진단 누수 방향·민감도 | accepted | ch:L5, sup:L17(196문항/139그룹 +3.34 [+0.68, +6.07]), sup:L91(사례 A)(RM-13) |
| R1-C10 | 재생성 문항 CI | accepted | 본문 강조 삭제, sup:L197 "10문항에서만 발생"·방향만 기술. 잡음 기준선 추정은 D-16 |
| R1-C11 | 재사용 문항 | accepted (보충만) | 정의와 수를 sup:L83에 명시(본문 구절은 길이 때문에 생략)(RM-24) |
| R1-C12 | Precision CI·계열 | accepted | sup:L31(계열에서 Precision 제외 이유, CI [+0.77, +6.02]) |
| R1-C13 | 동시성 의존 | accepted | sup:L219(쌍당 지연 일정, 양방향 서술). 동시성 sweep은 D-04 |
| R1-C14 | hop별 Simpson형 주의 | accepted | ch:L19 "전체 차이는 주로 2·3-hop". hop별 CI는 요구대로 보고하지 않음(RM-12) |
| R1-C15 | 판정기 안정성 | accepted | sup:L25: 272쌍 모두 같은 요청 digest·캐시 재사용 → 재현성 미검증으로 기재(RM-25) |
| R1-Q1 | 비교 계열 | accepted | sup:L31: 6개(F1, Recall, EM, 완전 회수, Token F1, LF-Eval), Precision 제외 |
| R1-Q2 | 272쌍 재호출 vs 캐시 | accepted | 캐시 재사용(재계산: 272/272 같은 digest, 캐시 응답) |
| R1-Q3 | 허용폭·목적함수의 사전성 | accepted | sup:L182: 저장 기록상 확인 불가 → 결과 관찰 후 선택으로 취급 |
| R1-Q4 | 원 ParSeR CE 입력 | accepted | 공식 `rerank()`는 원 질문–조문 쌍이며 선택 형식과 같음(sup:L17, S5 표). 진단의 `stored_json_background`는 이전 내부 형식이지 공식 설정이 아님 |
| R1-§7 AR1–AR11 | 재계산 영수증 | noted | 원고에 쓴 값은 모두 저자 재계산값. 대조는 §4 |
| R1 팀 메모 | bootstrap 사양·지시문·재현 충실성·RQ3·결론 | deferred-to-team | T3, T1, T4, T2, T7 |

### 2.3 R2 (도메인)

| ID | 요지 | 상태 | 조치·위치 / 사유 |
|---|---|---|---|
| R2-S1–S4 | 강점 | noted | — |
| R2-W1 | 재현 충실성(원 논문 수치 병기 + 실행 차이) | partially | 실행 차이 표 sup:L105–122(RM-16). 원 논문 수치 병기는 D-01(저장소에 검증된 절대값 없음; 방법 장 소관 T4) |
| R2-W2 | 개선 원천 분리 | accepted | ch:L27 조건부 선택률(79.52%/77.64%)과 원천 문장(RM-11), 순위 통계 sup:L158(RM-23) |
| R2-W3 | 3-hop 구조 상한 | accepted | sup:L164–172 표(3-hop 동시 선택 가능 2/11, 목록 수<gold 수 9/8/2 — 재계산 일치)(RM-12) |
| R2-W4 | 미매핑 gold 원인 | accepted (보충만) | 원인 서술 sup:L162(27/27 같은 hierarchy, 26 접두, 25 각 호, 공백 정규화 0; Stage 4.5에서 본문의 완전 매핑/영향 문항 F1도 이 문단으로 이동). 접두 매핑 민감도는 D-10, 그림 각주는 생략(RM-22) |
| R2-W5 | 정답 외 근거 구조 분류 | rejected (보류) | D-09: 새 분석 계열, 법률 타당성 판정으로 오독될 위험 |
| R2-W6 | 사례 C 해석 | accepted | ch:L70; 조문명은 sup:L99(RM-14) |
| R2-W7 | (a) 공식 입력 일치 (b) Jev 지시문 (c) 배경 입력 | partially | (a) ch:L5; (b) sup:L9 원문·비대칭 기재, 설계 의도는 T1; (c) D-16 future work |
| R2-W8 | Selection loss 분해 | partially | 수치 분해 sup:L153–154(RM-23). 그림 6범주화는 D-11, 라벨 언어는 T12 |
| R2-W9 | 용어 단위 | partially | "데이터셋 hop 라벨별", 용어표에 "corpus 행 단위" 정의. "예상 법령/예상 조문" 결정은 T9 |
| R2-W10 | 어절 단위 Token F1 | partially | sup:L21 구절(본문은 길이 때문에 생략). 형태소 재계산은 D-10 |
| R2-Q1 | 원 논문 수치와의 근접성 | deferred-to-team | D-01/T4 |
| R2-Q2 | 미매핑 26/27 재현 | accepted | 저자 코드로 재현(26/27 접두, 27/27 같은 hierarchy) |
| R2-Q3 | Jev 지시문 정렬 의도 | deferred-to-team | 지시문 원문은 sup:L9, 설계 의도는 T1 |
| R2-Q4 | 3-hop 선택 단계 진단 | partially | 3-hop 상한·목록 수 제약은 S6 표. 같은 목록 내 경쟁 분해는 전 hop 합산으로 S6(목록별 hop 분해는 하지 않음) |
| R2-Minor 1 | 478 목록과 443 출현 관계 | accepted (암묵) | S6 "목록 수 < gold 수" 열과 S4 분모 설명으로 연결. 본문 구절은 길이 때문에 생략 |
| R2-Minor 2 | 사례 B 조문 구조 | rejected | 법률 판단 없이 쓸 수 있으나 지면, 그리고 오류 유형 분류는 D-09 범위 |
| R2-Minor 3 | 라벨 대응 캡션 | accepted | ch:L15, ch:L68, 용어표 |
| R2 팀 메모 1–5 | 지시문·ParSeR 기술·용어집·RQ·원 논문 수치 | deferred-to-team | T1, T4, T9, T2, T4 |
| R2 참고문헌 | [UNVERIFIED] lead | deferred-to-team | T5, 확인 전 인용 안 함 |

### 2.4 R3 (ML 시스템·배포)

| ID | 요지 | 상태 | 조치·위치 / 사유 |
|---|---|---|---|
| R3-S1–S5 | 강점 | noted | — |
| R3-W1 | E2E 규모 단서 | partially | (a) 거절: 호출별 `latency_ms`는 `providers.py`에서 동시성 세마포어 진입 전에 타이머를 시작해 대기 시간을 포함 → 규모 참고치로 부적합(D-06); (b) 호출 구조 sup:L221; (c) D-03 |
| R3-W2 | 자원 범위(선택 호출) | accepted | ch:L47 "답변 생성 단계 기준" + 선택 호출 입력도 줄지 않음, sup:L138–143 선택 단계 사용량(RM-17). (b) 9% 문장은 보충 표(sup:L137)로만 |
| R3-W3 | 필터링 동기·자원 효과 | partially | 목적 문장 ch:L49. 문맥 토큰 감소량 보고는 하지 않음(필터링 후 생성 사용량을 재집계하지 않았고 비용·지연 미측정 진술 유지) |
| R3-W4 | 비결정성 운영 함의 | partially | (a) ch:L7; (b)(c) sup:L223(꼬리·날짜·구분 불가); (d) 감사 함의 문장은 논의 장(T11) |
| R3-W5 | 배포 명세·쌍당 지연 | accepted | sup:L219(Apple M5 Pro, 쌍당 27.60/60.22ms, 동시성 4 = 품질 실행 설정, 양방향). 표 1 행 추가는 본문 길이 증가라 생략 |
| R3-W6 | p95 오독 | accepted | 표 1 행 이름(ch:L37). 변동계수 대비는 S9에 있음(본문 추가는 길이 때문에 생략) |
| R3-W7 | 비용 정규화 | partially | 단가 sup:L225(문항당 약 $0.0034, 1,000쌍당 약 $0.019 — 재계산 일치). LLM 호출 비용과의 비교는 D-07 |
| R3-W8 | 외부 전송 거버넌스 | deferred-to-team | D-14 → T11 |
| R3-W9 | 문턱값 척도·선택 전 필터링 레버 | partially | 척도 사실(CE 점수 0.05 미만)은 sup:L182 격자 이력에 기재. "선택 호출 입력 레버" 문장은 D-15로 거절 |
| R3-Q1 | `latency_ms`의 대기 포함 여부 | accepted | 포함함(코드 확인, sup:L221) → 규모 어림에 쓰지 않음 |
| R3-Q2 | 두 실행의 날짜 | accepted | sup:L223: 품질 Jev 점수화 2026-11-09 02:05–02:43 UTC(캐시 파일 수정 시각 기준), 지연 측정 13:05–13:53 UTC |
| R3-Q3 | 동시성 4의 기준 | accepted | 품질 실행 설정과 동일(sup:L219) |
| R3-Q4 | 선택 호출 입력 차이 | accepted | 문항당 16,435 vs 16,591토큰, 차이 평균 +156·중앙값 +84.5(sup:L140–143) |
| R3-Minor l.7 | "151개 그룹 중 52개" | accepted | ch:L7 |
| R3-Minor l.44 | "문항당 평균 5.64초" | accepted | ch:L39 |
| R3-Minor l.69 | 총액→단가 | accepted | 본문 총액 삭제, sup:L225 |
| R3 팀 메모 1–5 | 원격 전용·거버넌스·효율 표현·재정렬 단계 한정·용어 | deferred-to-team | T1, T11, T7, T7, T9 |
| R3 FW 1–4 | E2E, Jev 반복, sweep, 재선택 | optional-future-work | D-03, D-02, D-04, D-15 |
| R3 참고문헌 | [UNVERIFIED] | deferred-to-team | T5 |

### 2.5 Devil's Advocate

| ID | 요지 | 상태 | 조치·위치 / 사유 |
|---|---|---|---|
| DA-P1-1 (M1) | CI의 단일 실행 조건부성 | accepted | ch:L7(RM-03). 점수화 반복은 D-02 |
| DA-P1-2 (M2) | 필터링 비대칭, F1 = 선택 기준 | accepted | ch:L60(RM-01) |
| DA-P1-3 (M3) | 교차 비교 조건 불일치, 목적 | accepted | ch:L49·L60, sup:L199(필터링 강도 차이 명시, 90% 기술통계)(RM-04) |
| DA-P2-4 | hop 서술 | accepted | ch:L19 개수 병기(RM-12). "목록 수 효과" 대안 설명은 S6 표의 목록 수 열로 자료 제공 |
| DA-P2-5 | RQ2 불확실성 | accepted | ch:L25(RM-10). R1형 분해 대신 조건부 선택률(ch:L27) 사용 |
| DA-P2-6 | 경계 구간 비대칭 | accepted | 본문의 CE+필터링 강조 삭제, Token F1 "경계적", S7 "방향만 기술" 규칙(RM-07, RM-04) |
| DA-P2-7 | LF-Eval 비독립 | accepted | ch:L45, sup:L23(RM-09) |
| DA-P2-8 | 제목의 "Decision Model" | deferred-to-team | RM-29/T2 |
| DA-P2-9 | 진단 편향 방향 | accepted | ch:L5, sup:L17(RM-13) |
| DA-P2-10 | 학습 데이터 노출 | rejected (제4장) | D-13 → T10 |
| DA 재분석 R1–R6 | 재집계 | noted | §4 대조표. R1·R4(F1 우세/열세 기준 LF 기여)는 재계산하지 않고 다른 정의(조건부 선택률, 선택 변화 유형별 분해)를 사용 |
| DA 팀 메모 | 주장 상한·기여 위상·Jev 관계·RQ·필터링 동기 | deferred-to-team | T7, T6, T10, T2, T2 |

---

## 3. 거절·보류 항목 확인 (D-01 ~ D-17)

| ID | 처리 | 사유(로드맵 유지) |
|---|---|---|
| D-01 | 보류(T4) | 원 논문 ParSeR 절대 수치가 저장소에 검증된 형태로 없음. 근접성으로 결함 여부를 추론하면 snapshot·장치 차이로 교란됨 |
| D-02 | optional future work | Jev 반복 실행은 유료 API 호출 필요 |
| D-03 | optional future work | E2E 지연은 새 실행 필요 |
| D-04 | optional future work | 동시성·GPU sweep은 새 실행 필요 |
| D-05 | 거절 | bootstrap 반복 수 변경은 잠금 보고값을 바꿈. MC 민감도는 S1 참고로만 |
| D-06 | 거절(본문) | trace 분류는 휴리스틱이며, 추가 확인 결과 호출별 `latency_ms`가 대기 시간을 포함하여 규모 어림에 쓸 수 없음 |
| D-07 | 거절 | 비교가 휴리스틱 분류와 CE 장비비 부재로 비대칭 |
| D-08 | 거절(본문) | 지면. S2 표와 종합 문단으로 대체 |
| D-09 | 보류 | 새 분석 계열, 법률 타당성 판정 오독 위험 |
| D-10 | 보류 | 접두 매핑·형태소 Token F1은 보조 분석으로 결론 영향 작음 |
| D-11 | 거절(본문) | 그림 재작성·지면. 분해 수치는 S6 |
| D-12 | 거절 | 그림 삭제와 본문 CI로 대체 |
| D-13 | 거절(제4장) | 증거 없음, T10 |
| D-14 | 보류 | 논의 장(T11) |
| D-15 | 거절 | 재선택을 실행하지 않아 근거 없는 함의 |
| D-16 | optional future work | 새 생성 호출 필요 |
| D-17 | 해당 없음 | 사용자 결정에 따라 추가하지 않음 |

---

## 4. 심사자 산출 수치와 저자 재계산값 대조 (G1)

원고에 들어간 값은 모두 오른쪽 열(저자 재계산)이다. 출처: `results/koblex-reproduction-v1/chapter4-revision-v1/revision-analysis.json`.

| 항목 | 심사자 값 | 저자 재계산 | 판정 |
|---|---|---|---|
| 재사용/동일 근거 문항 | R1 121, DA 119, 원고 S3 122 | 선택 행 집합 동일 119; corpus 중복 행 2개 포함 시 생성 입력 동일 121; Jev 생성 캐시 재사용 122(=CE와 입력 동일 121 + 공개 코드 CE와 동일 1); 답변 문자열 동일 124 | 세 값은 정의 차이로 모두 정확. sup:L83에 관계 기술 |
| LF 분해(동일/F1 동일·집합 상이/F1 변화) | R1 121/56/49, +0/+0.85/+1.74 | 119/58/49, 0/+0.85/+1.74 | 분해 기준(문맥 동일 vs 행 집합 동일)에 따라 2문항 이동; 기여값 일치 |
| ΔF1–ΔLF 상관 | R1 0.53 | 0.530 | 일치 |
| Holm 최소 / BH | R1 0.074 / 0.0496 | 0.0744 / 0.0496 | 일치 |
| Token F1 하한 MC | R1 20 seed 중 13개 <0, −0.043~+0.026 | seed 20261109–28: 12/20 <0, −0.047~+0.026 | seed 집합이 달라 차이. 재계산값 사용 |
| shortlist Recall 차이 CI | R1·DA ≈[+2.6, +8.0](다른 seed) | +5.16 [+2.61, +7.94] (잠금 seed) | 근사 일치, 재계산값 사용 |
| 모든 gold shortlist 유지 차이 CI | 미제시 | +7.96%p [+3.89, +12.38] | 신규 |
| Precision 차이 CI | R1 ≈[+0.72, +6.07] | +3.39 [+0.77, +6.02] | 근사 일치 |
| 진단 30문항 제외 | R1 196/139, F1 +3.34 [0.61, 6.06], LF +2.66 [0.23, 5.11] | 196/139, F1 +3.34 [+0.68, +6.07], LF +2.66 [+0.26, +5.05] | 점추정 일치, CI는 seed 차이 |
| 지연 60문항 품질 차이 | R1 +1.39/+0.87/+0.47 | +1.39/+0.87/+0.47 | 일치 |
| 조건부 선택률 | R2 79.5%/77.6% | 79.52%(233/293)/77.64%(250/322) | 일치 |
| 3-hop 상한 | R2 동시 선택 2/11, 합집합 7/17 | 2/11, 7/17 | 일치 |
| 목록 수 < gold 수 | R2 3-hop 9, 2-hop 8, 1-hop 2 | 9/8/2 | 일치 |
| 미매핑 gold | R2 27 같은 hierarchy, 26 접두, 25 각 호, 공백 0 | 27/26/25/0 | 일치 |
| hop 우세/동일/열세 | DA 0/56/1, 20/95/12, 12/26/4 | 같음 | 일치 |
| 필터링 구간 | EIC·R1·DA(저장값) | 파일에서 재추출 + e2e 행에서 재계산해 일치 확인 | 일치 |
| 겹침 꼬리 | R3 최솟값 0.60, 하위 10% 0.85; DA 35회=1.00, 36회≤0.85 | 0.60, 0.85, 35, 36 | 일치 |
| Jev 단가 | R3 $0.00339/문항, $0.0191/1,000쌍 | $0.003389, $0.01915 | 일치 |
| 쌍당 지연 | R3 27.6/60.2ms | 27.60/60.22ms | 일치 |
| 선택 호출 | R3: 호출당 입력 3k 초과, 953호출, 문항당 약 2.1회(휴리스틱 분류) | 조건당 478호출(문항당 2.12), 호출당 입력 CE 7,770.61·Jev 7,844.49토큰(예측 행의 기록으로 직접 대응) | 호출 수·입력 규모 모두 R3 휴리스틱과 다름. R3 값 미사용 |
| `latency_ms` 의미 | R3 질문 | 동시성 대기·재시도 대기 포함(코드 확인) | R3-W1(a) 불가 판단 근거 |
| DA R1(효과 위치 13/13, 19/1, 3), DA R4(LF +2.85/−1.11/+0.85) | DA | 재계산하지 않음 | 원고에 사용하지 않음 |
| R1 AR11 hop별 CI | R1 | 재계산하지 않음 | 요구대로 본문에 넣지 않음 |
| RM-16 API 행 | 로드맵: "Chat Completions → Responses" | 본 실행도 `/chat/completions` 호출, 저장 응답 객체 `chat.completion`; 잠금 파일 식별 필드만 `api: responses` | 로드맵 서술이 원자료와 다름. S5에 실제 경로와 표기 불일치를 기재 |

---

## 5. Stage 4.5 정리 (Stage 3′ 잔여 항목 처리)

Stage 3′ 검증 보고(`stage3prime/stage3prime_verification_report.md`)의 잔여 목록 중 원고·답변서에서 처리한 항목이다. 새 실험·모델 호출은 없다.

| 잔여 | 처리 |
|---|---|
| A1–A3 (RM-05 잔여, PLO-1) | 위 RM-05 행 참조. 4.4·4.3 첫 문장에 저장 차이값을 넣고, 종합 문단을 4문장으로 줄였다 |
| OBS-1 | 종합 문단의 "그 일부가 평균 근거 F1 3.19점 상승으로 이어졌다"를 "이와 함께 평균 근거 F1이 3.19점 높아졌으나"로 완화 |
| OBS-2 | S1 표 BH 열을 소수 넷째 자리로 표기(F1·Recall·LF-Eval 0.0496, EM 0.4178, 완전 회수 0.6777, Token F1 0.0787; `revision-analysis.json` `RM07_RM08_multiplicity.p_bh`) |
| OBS-3 | S9 첫 문장 출처 목록에 `results/koblex-latency-v1/README.md`(실행 장비) 추가 |
| OBS-4 | S1 "대칭적으로 작용한다" → "대칭적으로 작용할 것으로 본다" |
| OBS-5 / PLO-4 | 본문 수치 1:1 대조표를 산출물 디렉터리에 새 파일로 둠: `results/koblex-reproduction-v1/chapter4-revision-v1/manuscript-number-map.md`(107행, 각 행을 JSON에서 다시 읽어 확인). 기존 README는 수정하지 않음 |
| PLO-2 / PLO-3 | RM-20/R3-W5, RM-22/R2-W4, RM-24/R1-C11 상태를 "accepted"(보충만)로 맞추고 생략한 부분과 사유를 양쪽에 적음. RM-30은 "accepted"로 변경 |
| PLO-5 | 아래 참조 |
| C (RM-27, RM-29) | 팀 결정 대기(T1, T2). 변경 없음 |

**원자료 불변 주장의 범위(PLO-5).** 델타 보고 §3의 "파일 43,757개 sha256 비교 — 변경 0, 추가 0"은 비교 기록(수정 전 해시 목록)이 산출물로 남아 있지 않아 지금 다시 입증할 수 없다. 따라서 이 답변서는 그 주장을 근거로 쓰지 않으며, 확인 가능한 범위를 다음으로 한정한다. Stage 4.5에서 `revision-analysis.json`의 `inputs_sha256`에 기록된 분석 입력 35개와 `script_sha256`(재계산 스크립트)을 현재 파일과 다시 대조한 결과 36개 모두 일치하였다. 이 범위 밖의 `results/**`·`data/**`·`configs/**`·`scripts/experiment/**` 파일 불변 여부는 이번에 독립적으로 재확인하지 않았다. Stage 4.5에서 `results/**`에 대한 쓰기는 위 대조표 새 파일 하나뿐이다.

**분량.** 본문(`chapter4.md`, `wc -m`)은 7,575자에서 6,261자로 17.3% 줄였다(공백 제외 5,973자 → 4,957자, 17.0%). 표·그림에 이미 있는 값의 본문 반복, 보충자료와 중복되는 측정 절차·정의, 반복된 유보 문장을 줄였고, 본문에만 있던 완전 매핑/영향 문항 F1(64.12→67.21, 20.80→24.71)은 S6로 옮겼다. 요청된 유보(단일 Jev 실행·CI 범위, 탐색적·무보정과 S1 참조, 지연의 배포 조건 의존과 재정렬 단계 한정, 필터링 격자 사후 변경과 S7 참조, Token F1 경계성, LF-Eval 비독립성)는 모두 본문에 남겼다. PDF는 3쪽이다.

