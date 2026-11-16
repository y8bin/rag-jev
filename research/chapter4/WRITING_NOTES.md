# 제4장 집필 기록

현재 본문은 완료된 실험 결과를 반영한 논문형 개정본이다. 4.1~4.5의 구조와 RQ1~3 대응은 유지하되, 완료된 지연 벤치마크를 반영해 4.3은 재정렬 성능·지연시간 비교로 갱신했다. 사람 평가 결과는 수록하지 않았다. 필터링은 기존에 완료된 오프라인 시뮬레이션으로 명확히 구분하여 4.4에 추가했다.

본문: chapter4.md. 동기화된 LaTeX: section4_1.tex~section4_5.tex. 통합 입력: chapter4.tex. 검토 PDF: ../../output/pdf/chapter4-draft.pdf. 본문 그림 3개, 표 2개이며 전체 figure 5개는 figures/section-figures-v1/에 유지한다. 긴 사례와 평가 절차는 chapter4-supplement.md를 참조한다.

이전 원고는 style-study-v1/before-completed-results-rewrite/에 보존했다. 실험 원자료·실행 잠금은 수정하지 않았으며 새 API 호출·실험·사람 판단·검정은 수행하지 않았다.

재현: 저장소 루트에서 `.venv/bin/python scripts/render_chapter4_manuscript.py`. 렌더링 후 페이지 수와 실제 페이지 이미지를 확인한다. 페이지 수는 A4·10pt·2단·여백 20mm의 현재 검토 양식 기준이다.

최종본은 output/pdf/chapter4-final.pdf에도 저장한다. 기존 226문항 품질과 별도 60문항 지연을 구별하고, Jev의 top-10 재현성 변화를 명시했다. 추가 전 원고는 style-study-v1/before-latency-final/에 보존했다.
