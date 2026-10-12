---
version: 1
slug: "src-legal-rag-jev-viewer-static-index-html"
primary_target: "src/legal_rag_jev/viewer_static/index.html"
related_targets: ["src/legal_rag_jev/viewer_static/app.js","src/legal_rag_jev/viewer_static/app.css"]
---

# Jev 실험 뷰어 — 메인 화면 (질문·답변 대비)

Scope: `legal-rag viewer`의 전체 화면. 메인은 질문→조건별 답변 대비, 보조로 실행 기록 열람(요약·질문별·오류·실행 정보)과 설정 비교.
Mode: Operate.

Audience/job: 연구 팀원이 자기 노트북에서 (1) 직접 질문을 던져 다섯 조건의 근거 선택과 답변이 어떻게 갈리는지 탐색하고, (2) CLI로 돌린 실행의 질문·답변·근거·비용·오류를 같은 형식으로 검토한다.
Constraints: 직접 질문은 실제 API 호출이며 비용이 든다. 탐색 기록은 `results/_explore/`에 따로 저장하고 연구 지표·통계에 넣지 않는다. FR 문턱값이 없는 설정에서는 FR 조건을 건너뛰고 그 사실을 화면에 적는다. null은 0이 아니다.
Memorable moment: 기준 조건과 근거 선택이 같은 칸은 "(기준과 같음)"으로 접히고, 달라진 근거에만 밑줄이 그어져 Jev와 CE의 차이가 한눈에 남는다.
Unresolved: 팀 공유 서버 운영 여부(지금은 아님).

## Direction contract

THESIS: 질문 하나에 대한 조건별 답과 근거를 신구조문대비표처럼 나란히 놓고, 기준 조건(CE-R)과 달라진 곳에만 밑줄을 긋는다. 말풍선이 쌓이는 챗봇 화면과 카드형 SaaS 대시보드를 거부한다.

OWN-WORLD: 관보·법령집 조판. 흰 지면에 잉크 #141414, 표는 위아래 2px 잉크 굵은 괘선과 1px 회색 #d4d4d4 가는 괘선, 머리행은 옅은 회색 바탕에 가운데 정렬. 변경 표시는 법령 파랑 #1d4fa3 밑줄, 실패·무효는 #b3261e 취소선. 질문·답변·조문 본문은 명조(Noto Serif KR), UI·숫자는 Pretendard 표 숫자. 조건 색은 머리행의 작은 표지에만.

STORY: 팀원은 설정을 고르고 질문한다(또는 기록을 연다) → 다섯 조건의 답이 한 표에 나란히 나온다 → 근거 행에서 기준과 다른 선택만 밑줄로 보인다 → 후보 풀 전체 행렬과 비용·오류로 내려간다.

FIRST VIEWPORT: 왼쪽 264px 레일에 "새 질문", 탐색 기록, 실행 기록. 본문 위쪽은 질문 작성부: 명조 큰 입력란, 아래 한 줄에 설정·기준일·관할과 오른쪽 끝 "질문하기" 주 버튼. 그 아래 대비표가 본문 폭 전체: 머리행 "기준 · CE-R | Vector | CE-FR | Jev-R | Jev-FR", 행은 답변 / 근거 / 비용·시간.

FORM: 신구조문대비표 — 내 후보 목록의 1순위(IMPECCABLE'S PICK으로 제시, 사용자가 선택). seed key 1cc479fc.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
