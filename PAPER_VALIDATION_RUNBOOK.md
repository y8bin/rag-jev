# 논문 검증 고도화 실행 기록과 다음 단계

기준일: 2026-10-14. [최종 전략](final_research_strategy.md)과 [감사 문서](EXPERIMENT_REQUIREMENTS_AUDIT.md)를 기준으로 완료된 실행기를 확인하고 구현·테스트를 보완했다. **실제 원문과 사람 gold가 아직 없어 연구 파일럿·시험·성능 결론은 진행하지 않았다.**

## 완료한 코드 검증

| 감사 항목 | 이번에 구현·검증한 내용 | 실제 연구에서 남은 것 |
|---|---|---|
| G05·E03 | v2 핵심 주장·완전성 판정, primary/strict 지표 분리, v1 주 지표 자동 전환 방지 | 법률 사례 교육·완전성 판정·최종 rubric 동결 |
| E05 | 주장별 인용 일치도, 핵심/완전성 일치도, 0/1/2 가중 kappa | 두 평가자 원판정·조정 파일 |
| I06 | 각 FR − 자체 R의 품질·비용 paired 차이·CI | 실제 시험 표본과 reviewed 라벨 |
| G04·I03 | 지표별 margin·단측 alpha 설정, 두 제약 공동 충족 출력 | margin 근거·power·공동 주장 범위 확정 |
| I05·H07 | 누락 비용의 평균·추론 보류, 성공/실패 지연 분리 | 청구·usage·실제 fresh 지연 자료 |
| C07·I04 | 파일럿 연결 성분 보호, dev 재사용 옵션, split manifest, 안정된 층화 표본·구성 기록 | 그룹 적절성·누출·표본 추론 범위 검토 |
| J05 | 명시적 FR 불가능 분기, 불가능 방법만 제외·고정 N 계속 | 해당 분기를 시험 전 계획에 확정 |
| H03 | 원격 Qdrant 시간 단가 분리, 미확인은 null | Cloud 청구·저장·네트워크·자원 배분 검증 |
| J04·L01·L02 | 첨부 계획/자료 해시 잠금, 설치 패키지 전체·commit/dirty 기록, 환경 pin snapshot | 정확한 모델·서버·장비 명세와 새 환경 설치 재검증 |
| J01·L03 | pilot/dev 설정, 오프라인 readiness, 문서 현황 갱신 | 실제 데이터 경로·최종 개발 선택·시험 lock |

기존 테스트 70개 통과를 확인한 뒤 추가 회귀 검증으로 **88 passed**를 확인했다. 실제 CLI를 격리된 합성 Qdrant 인덱스에서 실행해 15행·실패 0과 연구 유효성 false를 확인했다(`results/preparation/engineering_20261014/runs/20261014T022851_4764d168`). 모든 설정 YAML·자료 JSON/JSONL 양식과 Markdown 링크를 검사했고 `git diff --check`도 통과했다. 오프라인 준비 보고서는 `results/preparation/pilot_readiness.json`에 보존했다. 자동 테스트·합성 CLI 검증은 외부 서비스 인증이나 법률 타당성의 증거가 아니다.

## 0. 먼저 받을 실제 자료

| 제공 담당 | 필요한 자료 | 저장 위치/양식 | 완료 확인 |
|---|---|---|---|
| 연구 책임자 | 범위·대상 분포·담당·권리·예산·파일럿 진행 기준 | [범위 명세](research/research_scope.md) | 미확정 항목과 승인일 작성 |
| 데이터 담당 | 원문 스냅샷·판본·출처·효력·그룹·권리·추출 QA | `data/raw/corpus.jsonl`, `data/manifest/corpus_manifest.json` ([양식](research/templates/corpus_manifest.template.json)) | 해시·목록·원문 표본 대조 |
| 원격 컬렉션 담당(사용 시) | point ID·payload·벡터 export, embedding/revision·차원·출처·문서 연결 | 원본 export를 별도 보존 후 관리 인덱스로 재구축/검증 | 기존 탐색 모드를 연구 결과로 사용하지 않음 |
| 법률 작성자 | 실제 질문 10~20개, 기준 답·필수 요건·충분 집합·작성 이력 | `data/processed/queries_pilot.jsonl`, `data/manifest/query_provenance.jsonl` ([양식](research/templates/query_provenance.template.jsonl)) | 실제 원문 기준 독립 검토 |
| 평가 담당 | 평가자 2명·조정 담당·지침·실제 교육 사례 | [평가 지침](research/annotation_guidelines.md), 원판정·조정 파일 | 후보/답변/조정 시간 측정 |
| 실행·비용 담당 | 모델 revision·실제 반환 식별자·단가 출처·usage/청구·장비·예산 | `data/manifest/model_cost_manifest.json` ([양식](research/templates/model_cost_manifest.template.json)) | API 계약·청구 단위·실패 비용 대조 |
| 분석 담당 | 독립 그룹·paired 불일치·ICC 가정·최소 효과·power·margin·표본 범위 | [분석 계획](research/statistical_analysis_plan.md) | 시험 크기·분석 가족·결과 규칙 동결 |

이 양식은 초안이다. 빈 값·예시 query ID를 실제 연구 산출물로 취급하지 않는다. 질문 스키마에 없는 작성·판정 이력은 query ID sidecar에 넣는다. 실제 원문·키·판정·원결과는 Git 제외 경로에 보관한다.

## 1. 오프라인 확인과 원문 준비

저장소 루트에서 실행한다. `.env`가 이미 있으므로 덮어쓰지 않는다. 아래 readiness는 모델 로드·네트워크·유료 호출을 하지 않는다.

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m legal_rag_jev --config configs/pilot.yaml readiness --output results/preparation/pilot_readiness.json
```

현재 연구 입력이 없으므로 `missing_input`과 `index_not_built`가 예상된다. `local_checks_passed`는 구조·설정 확인일 뿐 법률 검토 완료 표식이 아니다. 자료를 받은 뒤 진행한다.

```bash
.venv/bin/python -m legal_rag_jev --config configs/pilot.yaml ingest --input data/raw/corpus.jsonl
.venv/bin/python -m legal_rag_jev --config configs/pilot.yaml chunk
# 사람이 정규화 원문과 청크를 대조하고 pilot 질문·구간 gold 작성
.venv/bin/python -m legal_rag_jev --config configs/pilot.yaml validate
```

효력 종료일은 제외 상한이다. OCR·표·단서·예외·개정판 연결과 골드 구간의 완전 회수를 사람이 확인한다. K/N·모델 후보를 바꾸면 개발 선택 근거와 새 run ID를 남긴다. 데이터 담당의 권리·범위 검토가 끝나기 전 원문을 외부 API로 보내지 않는다.

## 2. 실제 연결 확인과 파일럿

**이 단계는 실제 모델/API 호출과 비용이 발생한다.** 현재 자동 실행하지 않았다. 실제 10~20문항과 단가·usage·계약이 준비되면 실행 담당이 진행한다.

```bash
.venv/bin/python -m legal_rag_jev --config configs/pilot.yaml smoke
.venv/bin/python -m legal_rag_jev --config configs/pilot.yaml build-index
.venv/bin/python -m legal_rag_jev --config configs/pilot.yaml run --split pilot --run-id retrieval_001
.venv/bin/python -m legal_rag_jev --config configs/pilot.yaml export-annotations --run results/pilot/retrieval_001 --kind relevance --output results/pilot/relevance_review_001
```

공통 후보를 이중 판정·조정하고 `import-relevance --output data/processed/queries_pilot_reviewed.jsonl`로 별도 보존한다. pilot과 pilot-answers 설정의 queries를 reviewed 파일로 맞춘다. 기준 질문/후보를 모두 바르게 해석했는지 확인한 뒤 생성한다.

```bash
.venv/bin/python -m legal_rag_jev --config configs/pilot-answers.yaml smoke
.venv/bin/python -m legal_rag_jev --config configs/pilot-answers.yaml run --split pilot --run-id answers_001
.venv/bin/python -m legal_rag_jev --config configs/pilot-answers.yaml export-annotations --run results/pilot-answers/answers_001 --kind answers --output results/pilot-answers/answer_review_001
# 두 평가자의 tasks.jsonl 사본 판정 → agreement → 조정 → import-answers → evaluate
```

10~20문항에서 공통 후보·생성 JSON·실제 반환 모델·usage/청구·실패/재시도를 확인한다. 이후 약 100문항으로 늘려 후보 회수, 평가자 불일치, 독립 그룹, 사람 처리량을 측정한다. 실패를 0점으로 바꾸거나 성공 기록으로 덮어쓰지 않는다. 기존 연결 확인의 실패 기록과 탐색 성공 기록은 연구 데이터로 재사용하지 않는다.

## 3. 독립 개발·시험 준비

pilot 외에 아직 모델 선택에 쓰지 않은 질문 그룹을 확보한다. `queries_all.jsonl`의 이미 노출된 질문은 pilot, 새 문항은 초기 dev 표시로 입력한다. 연결 성분을 분할하므로 실제 분포는 목표 문항 비율과 다를 수 있다.

```bash
# pilot.yaml의 queries를 전체 작성 파일 경로로 지정한 별도 split 설정에서 실행
.venv/bin/python -m legal_rag_jev --config configs/split.yaml split --output data/processed/queries_split.jsonl
```

`configs/split.yaml`은 `queries_all.jsonl`을 읽는 준비된 설정이다. 이미 pilot인 연결 성분은 기본 pilot에 남는다. 개발 재사용을 사전에 정했다면 `--reuse-pilot-in-dev`를 쓴다. 어느 경우든 시험에는 재배정되지 않는다. 미노출 연결 성분이 2개 미만이면 분할이 중단된다. 출력 `.split_manifest.json`의 그룹 수·구성·매핑을 검토한다.

dev 설정의 queries를 split 파일로 지정해 `retrieve`·`lexical-pool` 후보를 모으고, 사람 판정·대체 gold 검토 후 `queries_reviewed.jsonl`로 확정한다. test 후보도 방법별 결과를 공개하기 전에 판정한다. 실제 출처·모델/비용·작성 이력 manifest를 준비하고 dev 설정의 `protocol_documents` 경로를 확인한다.

```bash
.venv/bin/python -m legal_rag_jev --config configs/dev.yaml validate
.venv/bin/python -m legal_rag_jev --config configs/dev.yaml sweep --grid-size 5
# 출력 SWEEP_PATH의 모든 사전 지정 표본/조건을 v2로 사람 판정
.venv/bin/python -m legal_rag_jev --config configs/dev.yaml evaluate --run SWEEP_PATH
.venv/bin/python -m legal_rag_jev --config configs/dev.yaml tune --run SWEEP_PATH --output-config configs/final.yaml
```

FR threshold가 null이라는 readiness 지적은 sweep 이전에 정상이다. 단가·사람 판정 누락은 정당한 중단 조건이다. 실제 margin·표본·모델·K/N·추가 진단과 분석 계획을 시험 전 확정한다. FR 불가능 분기를 사전 지정했고 만족값이 없다면 다음 명령으로 고정 N 연구를 계속할 수 있다.

```bash
.venv/bin/python -m legal_rag_jev --config configs/dev.yaml tune --run SWEEP_PATH --output-config configs/final.yaml --allow-infeasible
```

`threshold_selection.json`에 제외된 FR과 이유가 남는다. 최종 방법 수를 사실대로 보고한다. 문턱값을 임의로 입력하거나 시험을 보고 margin을 바꾸지 않는다.

## 4. 잠금 시험, 추가 검증, 논문

미확정 표·초안 상태를 모두 해소하고 시험 라벨·분할·인덱스·환경·첨부 계획을 확정한다. 주 분석의 정의가 바뀌었으므로 예전 run/lock을 새 구현의 증거로 이어 붙이지 않는다.

```bash
.venv/bin/python -m legal_rag_jev --config configs/final.yaml freeze --output results/protocol_lock.json
.venv/bin/python -m legal_rag_jev --config configs/final.yaml run --split test --lock results/protocol_lock.json --run-id final_test
```

같은 시험 질문의 모든 조건을 블라인드 v2 판정·조정한 뒤 `import-answers`, `evaluate`, `statistics`, `plot`, `errors`를 순서대로 실행한다. 답변 rubric과 첨부 분석 계획의 변경도 lock 불일치를 일으킨다. 시험 결과 공개 전에 필요한 진단의 설정·표본·gold도 고정한다.

필수 진단은 동일 Jev의 relevance/applicability 묶음 비교, 공통 입력 토큰 예산, 구간 gold 기반 길이 통제, 시점/관할 혼합 후보 및 fresh 반복 지연이다. 자연 검색과 통제 후보를 구분한다. 실제 규모의 Qdrant 전체 결과 반환·로드 무결성 검사 비용은 아직 측정하지 않았으며 대규모 성능 최적화 완료로 표시하지 않는다.

논문에는 데이터·독립 그룹·판정 통계, 고정 N 검색, v2 답변, FR 품질·비용·불가능 조건, CI·실패·usage 누락, ablation·지연·오류·한계를 보고한다. 원문 공개 가능 범위와 새 환경에서의 재설치 검증을 포함한 보존 묶음을 준비한다. 환경 pin 파일은 설치 버전 스냅샷이며 패키지 파일 해시를 가진 범용 lockfile은 아니다.
