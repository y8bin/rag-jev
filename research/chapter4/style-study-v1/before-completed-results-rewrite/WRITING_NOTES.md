# 제4장 LaTeX 초안

## 최종 축약본 — 2026-11-09

최초 집필 계획의 약 3쪽 이내를 기준으로 본문을 다시 줄였다. Markdown은 9,072자에서 6,150자로 약 32% 줄었고, 표 3개·그림 1개의 구성을 복원하였다. 같은 A4·10pt·2단·20mm 여백으로 조판한 결과는 2쪽이다. 절별 계획 분량은 대략적인 배분이며, 이번 편집은 3쪽 상한 안에서 전체 설명을 간결하게 만드는 데 우선순위를 두었다.

영문 용어 대신 정답 근거·검색 후보·상위 후보·최종 선택을 사용하고, 평균 회수 개선과 완전 회수의 차이를 중심으로 결과를 연결하였다. 상세 사용량·단계별 집계는 [보충자료](chapter4-supplement.md)에 보존하였다. [현재 Markdown](chapter4.md), `section4_1.tex`–`section4_5.tex`, [PDF](../../output/pdf/chapter4-draft.pdf)를 동기화하였다. 본문·표의 소수 수치와 LaTeX의 수치가 일치하는지 확인했고, 최종 PDF 두 쪽을 렌더링하여 확인하였다.

[최종 검증 기록](draft-validation.json)이 현재 버전을 가리킨다. 아래의 3쪽 조판 설명 및 앞선 문체·이해도 검증 기록은 이전 버전의 이력이다.

4.1~4.5 본문 조각은 `chapter4.tex`에서 순서대로 연결한다. 2026-11-09 문체 수정에서는 arXiv 논문 10편의 결과 관련 절을 읽고 전 절의 문단 전개와 문장을 다듬었다. 다른 장 원고와 최종 RQ 문구는 변경하지 않았다.

문체 검토 자료는 [원문 수집 원장](style-study-v1/papers-manifest.json), [논문별 읽기 기록과 적용 원칙](style-study-v1/READING_NOTES.md), [수정 내역](style-study-v1/REVISION_REPORT.md)에 남겼다. 수정 전 LaTeXㆍPDFㆍ수치 원장ㆍ검증 기록은 `style-study-v1/before-revision/`에 보관했다. 이 문헌들은 문체 참고 자료이며 현재 실험 점수의 출처는 기존 원자료다.

| 절 | 제목 | 계획상 분량 |
|---|---|---:|
| 4.1 | 실험 조건 및 비교 기준 | 약 0.30쪽 |
| 4.2 | 재정렬 모델 교체에 따른 근거 선택 성능 | 약 0.75쪽 |
| 4.3 | 질문 조건에 따른 성능 차이 | 약 0.45쪽 |
| 4.4 | 자동 답변 품질 및 자원 사용 특성 | 약 0.75쪽 |
| 4.5 | 오류 유형 및 관측 사례 | 약 0.75쪽 |

현재 검토용 `preview.tex`는 A4ㆍ10ptㆍ2단ㆍ20mm 여백이다. 이 임시 양식으로 전체 3쪽을 확인했다. 최종 학회 양식이 확정된 상태는 아니며, 절별 분량은 표ㆍ그림 배치에 따라 조정할 수 있다. 수치를 줄이거나 해석을 바꾸어 분량을 맞추지 않았다.

문체 수정 후에도 총 3쪽을 유지했다. 매핑 상태별 결과는 조건별 분석인 4.3으로 모았으며, 4.2는 전체 근거 선택 결과에 집중한다. 표 3개와 hop 그림의 내용은 수정 전과 같다.

## 삽입과 컴파일

상위 논문의 preamble에 한국어 환경과 `graphicx`를 포함하고 저장소 루트에서 다음 조각을 삽입한다.

```latex
\input{research/chapter4/chapter4.tex}
```

검토용 조판은 저장소 루트에서 실행한다.

```bash
.venv/bin/python research/chapter4/figures/plot_hop_f1.py
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=tmp/pdfs/chapter4 research/chapter4/preview.tex
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=tmp/pdfs/chapter4 research/chapter4/preview.tex
```

`tmp/pdfs/chapter4`는 컴파일 전에 생성한다. 사용자 검토용 PDF는 `output/pdf/chapter4-draft.pdf`에 저장했다. 최종 논문에 삽입할 때는 `preview.tex`의 4절 번호 설정을 본문에 복사하지 않는다.

## 그림

`figures/plot_hop_f1.py`는 사용자 지정 [figures4papers](https://github.com/ChenLiu-1996/figures4papers)의 `scientific-figure-making` 스킬을 적용했다. 고정 commit은 `b709de17da7e8f9a72e51a5de5bced924a01eeab`이고, 필요한 스킬ㆍAPIㆍ튜토리얼ㆍ디자인 규칙은 `figures/skill-references/`에 보존했다. upstream 안내에 따라 공유 Python 모듈을 가정하지 않고 스타일 API를 로컬 구현했다.

원자료는 `chapter4-prep-v1/A2/hop-f1-figure-data.csv`의 6행이다. 원자료 사본ㆍ스크립트ㆍPDF/SVG/PNGㆍ해시와 도구 버전은 `figures/hop_f1.provenance.json`으로 연결한다. 색 외에 마커와 선 모양으로 조건을 구분했고, 오류 막대나 유의성 표시는 추가하지 않았다. 현재 그림 폭은 검토용 양식의 단 폭 약 85mm를 가정한다.

## 과학적 해석과 검토 대기

- 본문 수치는 기존 `analysis.json` 및 고정된 `chapter4-prep-v1/A1~A6`에서 가져왔다. 새 유료 실행ㆍ사람 판단ㆍ추가 통계 검정은 하지 않았다. 기존 결과와 잠금을 수정하지 않았다.
- 4.4는 자동 Token F1/LF-Eval과 입력 요구량의 기술통계다. 캐시 사용량을 새 청구액으로 합산하거나 지연ㆍ운영비 절감으로 해석하지 않았다. 실제 사람 평가는 판단 0개 상태를 유지했다.
- 4.5의 A/B/C는 각각 `qa_124_2hop_480_rand`, `qa_324_2hop_515`, `qa_443_3hop_703`이다. A6에서 고정한 중앙값 근접 규칙으로 뽑은 후보를 사용했다. 자동 judge의 reason을 법률 전문가 판정으로 사용하지 않았다.
- 세 사례는 모두 사람 평가 표본 밖의 별도 정성 검토 대상이다. 사면 유형ㆍ경합 관계, 절차 제도의 적용, gold 외 근거의 타당성은 기존 법률 검토 목록에서 계속 미판정으로 관리한다. 원 질문ㆍgoldㆍ조문ㆍ답변ㆍ출처 행은 A6 casebook에 보존되어 있다.
- 제1ㆍ3장의 RQ/방법 정합성 및 최종 학회 양식은 기존 `RQ_TOC_COORDINATION.md`의 조율 사항이다. 이번 작성은 사용자가 허용한 제4장 목차와 본문 범위에 한정했다.
