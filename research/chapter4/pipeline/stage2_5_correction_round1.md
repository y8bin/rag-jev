# Stage 2.5 무결성 수정 라운드 1 — 제4장

- 모드: academic-paper revision (블록 단위 수정, 재집필 없음). 일자 2026-11-13.
- 변경하지 않은 것: `results/`, `data/`, `scripts/experiment/`, `configs/`, protocol-lock. 모델·API 호출이나 실험 없음. 그림은 다시 생성하지 않았다(해시와 문서만 갱신).
- 빌드: `.venv/bin/python scripts/render_chapter4_manuscript.py` → `output/pdf/chapter4-draft.pdf` = `chapter4-final.pdf`, **3쪽**(A4, 10pt, 2단, 여백 20mm). Overfull 0건, 미정의 참조 0건, 누락 글리프 0건. Underfull 경고가 남은 곳은 4.1 첫 문단(줄바꿈되지 않는 `\texttt` 모델 ID)과 4.4 E2E 문단 한 줄이다. 둘 다 시각적으로 허용 범위다.
- 4.4의 새 수치는 모두 `results/koblex-filtering-v1/e2e-summary.json`에서 반올림 전 값으로 계산한 뒤 소수 둘째 자리로 반올림해 다시 확인했다.

| ID | 변경 내용 (file:line) | 상태 |
|---|---|---|
| IL-SERIOUS-1 | `chapter4.md:54`: 절차를 서술한다. 교차검증 τ는 답변 생성 전에 정해 고정했다. 근거가 바뀐 CE 10개·Jev 45개 문항만 같은 프롬프트와 `gpt-4o-2024-08-06`으로 재생성했다. 나머지 CE 216개·Jev 181개 문항은 재사용했고, 재사용 문항의 LF 점수가 같음을 확인했다. `:56–63`: 표 2에 Token F1·LF-Eval 열을 추가했다. `:67`: 대응 bootstrap 차이와 CI를 넣었다(Jev-FR−Jev-R, CE-FR−CE-R, Jev-FR−CE-FR, Jev-FR−CE-R). 마진이 없으므로 유지·동등성으로 해석하지 않는다고 밝혔고, LF 하한 −2.23을 적었으며, CE의 Token F1 구간이 0을 포함하지 않는다는 점도 적었다. `:69`: "재생성하지 않았으므로" 문장을 지우고, 비용·지연 변화는 측정하지 않았다고 썼다. | 해결 |
| IL-SERIOUS-2 | `chapter4-supplement.md:95`: S7 제목을 "선택 후 필터링과 답변 재생성"으로 바꿨다. `:101`: 거짓 문장을 지우고 gold 출현 기준을 명시했다. `:103`: E2E 출처, 절차, seed 20261108, 151그룹, 해석 제한을 담은 문단을 새로 넣었다. `:107`: 수록 범위에 필터링 답변 재평가를 명시했다. | 해결 |
| 사람 평가 삭제(사용자 지시) | 보충 `:49`: 블라인드 양식·180답변 문단을 사례 원문 위치와 "법률적 적절성은 판정하지 않았다"는 중립 문장으로 바꿨다. `:51`: "사람 판단"을 삭제했다. `:101`: 삭제했다. `:107`: "사람 평가 수치"를 삭제했다. `:114`: "사전에 고정한 60문항 표본(1/2/3-hop 15/34/11)"으로 바꿨다. 그림 README의 "사람 근거 충실도"도 삭제했다. 본문과 보충 자료를 grep한 결과 사람/평가자/블라인드/전문가/human은 0건이다. | 해결 |
| IL-MINOR-1 | 본문 `:65`: "pool별"을 "문항별 gold 출현 443건 기준 유지 비율"로 바꾸고, 이 비율이 그림 3과 분모가 같고 그림 2와는 다르다고 적었다. 보충 `:101`: 293/443, 322/443을 명시했다(A4/stage-summary.csv와 대조해 확인). | 해결 |
| IL-MINOR-2 | 본문 `:52`: "이 증가는 선택 수의 차이가 아닌". | 해결 |
| IL-MINOR-3 | 본문 `:50`: "Token F1은 CE 46.20점에서 Jev 47.31점으로". | 해결 |
| IL-MINOR-4 | 본문 `:7`에 단위 규약을 한 번 정의했다(문항별 평균은 0–100 점, 문항 비율은 %·%p). `:25`: 77.21·69.47·74.63점, 차이 5.16점. `:29`: 그림 2 캡션에서 축(%)과 단위의 관계를 설명했다. 보충 `:11`, `:86`도 같은 규약으로 맞췄다. | 해결 |
| IL-MINOR-5 | 본문 `:81`: "사례 식별자와 선정 규칙, 원문의 위치는 보충자료에 제시하였다." 보충 `:49`: `results/koblex-reproduction-v1/chapter4-prep-v1/A6/casebook.jsonl`의 필드를 가리키도록 했다. | 해결 |
| IL-MINOR-6 | `scripts/render_chapter4_manuscript.py`: Markdown의 "그림 N/표 N"을 미리 훑어 라벨 대응표(fig:ch4_2/3/5, tab:ch4_3/4)를 만든다. 표에 `\label`을 내보내고, 본문 참조는 `그림~\ref{}`/`표~\ref{}`로 바꾼다. 열이 6개를 넘는 표는 `\footnotesize`로 조판한다. tex에 남은 하드코딩 번호는 0건이다. | 해결 |
| IL-MINOR-7 | `provenance.json`: fig_4_3 캡션의 stale 문구를 고치고 `manuscript_column_figures`(빌더 해시, data.json 입력 해시, `_column` pdf/png/svg 출력 sha256)를 추가했다. `README.md:25,45–51`: stale 문구를 고치고 단 너비 판본 절을 추가했다. | 해결 |
| IL-MINOR-8 | 본문 `:5`와 보충 `:9`에 `dragonkue/bge-reranker-v2-m3-ko` 전체 ID를 넣었다. revision 해시는 넣지 않았다(3장 방법 절의 소관). | 해결 |
| N1 | 본문 `:5`에 한 문장, 보충 `:11`에 출처(`ce-diagnostic-summary.json`, 30문항, 4형식, 미노출 시험 아님)를 넣었다. | 반영 |
| N2 | 보충 S9의 "사전등록 아님" 문구를 유지했다. 출처 쪽 summary.json은 수정 금지 범위다. | 유지 |
| IL-MEDIUM-1 | 파이프라인 산출물(experiment_provenance[]) 문제이며 원고 수정 범위 밖이다. pipeline_state.md에 intake declaration 표가 이미 있다. | 이 라운드 범위 밖 |
