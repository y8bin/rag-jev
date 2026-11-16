# 그림 제작 인계 — figures4papers

사용자 지정: <https://github.com/ChenLiu-1996/figures4papers>. 스킬 경로는 **`scientific-figure-making/SKILL.md`**다. 이번에는 본문·그림을 제작하지 않고 원자료만 준비했다.

- 확인한 commit: `b709de17da7e8f9a72e51a5de5bced924a01eeab`.
- [고정 commit의 SKILL.md](https://github.com/ChenLiu-1996/figures4papers/blob/b709de17da7e8f9a72e51a5de5bced924a01eeab/scientific-figure-making/SKILL.md), [로컬 읽기용 스냅샷](figures4papers-SKILL.snapshot.md).
- Matplotlib 논문용 그림, 출판용 글꼴·팔레트·spine·범례·PDF/SVG 내보내기를 다루는 스킬임을 확인했다. 실제 제작 때 해당 스킬과 필요한 `references/`만 읽고 적용한다.
- 전역 스킬 설치·라이브러리 설치는 이번 작업에서 수행하지 않았다. 외부 저장소는 **후속 그림 도구의 출처 확인**에만 사용했고 A1~A6의 과학적 입력/지표/선정 규칙에는 사용하지 않았다.
- 스냅샷 내부 `references/` 상대 링크는 원 저장소 기준이다. 참조 파일을 일괄 복사하지 않았으며 실제 제작 때 고정 commit에서 필요한 파일을 읽는다.

현재 계획의 그림 1 원자료: [hop별 F1 CSV](A2/hop-f1-figure-data.csv). 주 비교 2조건×3 hop=6행이며 raw_mean은 0~1, display_x100은 0~100, n은 57/127/42다. 오류 막대용 subgroup CI는 계산하지 않았으므로 임의로 추가하지 않는다. 1-hop 감소도 유지하고 층별 유의성·상호작용을 암시하지 않는다.

제작 전에 학회 양식·단/양단·실제 폭과 글꼴 크기를 확정한다. 단순 막대로 주 성능 표의 전체 숫자를 반복하지 않도록 hop 조건별 차이를 전달하는 구성을 검토한다. 저장된 CSV와 원자료 해시를 사용하고 정확한 표현은 RQ/목차 조율 후 정한다. 그림이 생성되면 코드·입력 CSV 해시·스킬 commit·PDF/SVG·미리보기 검증을 함께 별도 산출물로 남긴다.
