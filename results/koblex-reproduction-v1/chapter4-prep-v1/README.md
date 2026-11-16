# 제4장 준비 자료 — chapter4-prep-v1

2026-11-09. **기존 파일 기반 A1→A6 완료.** 이 폴더는 분석 자료와 검토 대기 목록이며 논문 본문이나 최종 표·그림 원고가 아니다. 주 비교는 수정 CE(`parser_ce_fixed`) 대 Jev(`parser_jev_fixed`)이고, `parser_ce_raw`는 공개 코드 인덱스 문제를 보존한 참조다.

## 검증과 보존

- 현재 진입점 검증: `VERIFIED_CURRENT_STUDY`. [전수 검증](verification-audit.json): `PASS_AUTOMATED_ARTIFACT_INTEGRITY`.
- 기존 audit는 원래 검증 JSON을 다시 쓰므로, **출력 함수의 목적지만 새 폴더로 연결**했다. 기존 audit 소스·원 검증 JSON·실행 잠금은 그대로 유지했다. [방법](verification-method.json).
- 작업 전 기존 결과 및 관련 소스 43,076개 파일의 바이트 해시를 기록했다. [작업 전 원장](preservation-before.json)과 [작업 후 검증](validation.json)을 대조한다. 원 결과 파일 추가·삭제도 확인한다.
- 예산은 SQLite 읽기 전용 연결로 확인했다. 현재 요청 41,322건, 이월 집계 3행, 미정산 12건이다. 누적 확인 금액 $24.09577565, 예약 포함 $25.23273565로 기존 기록과 일치한다. [읽기 전용 예산 기록](budget-readonly.json). 새 유료 호출은 0건이다.
- 실제 사람 판단 생성 0개. A7은 실행하지 않았다. 기존 60문항 블라인드 표본·180답변 양식은 보존했다.

## 산출물 지도

| 작업 | 원자료·집계 | 단위와 주요 규칙 |
|---|---|---|
| A1 | [수치 원장](A1/numeric-ledger.json), [문항×조건 원자료](A1/question-metrics.csv) | 226문항×3조건=678행. 원값 0~1, 표시는 ×100. 기존 CI를 출처 pointer와 연결. 차이는 반올림 전 값 기준 |
| A2 | [하위집단](A2/subgroup-metrics.csv), [분모·ID 목록](A2/subgroup-membership.json), [hop 그림 원자료](A2/hop-f1-figure-data.csv) | hop 57/127/42, 매핑 197/29. 교차 층도 포함. 새로운 CI·검정 없음 |
| A3 | [문항별 대응 결과](A3/paired-outcomes.csv), [승·무·패](A3/win-tie-loss.json), [3×3 방향 표](A3/joint-directions.csv), [지표 불일치](A3/discordant-queries.csv) | Jev−수정 CE, 허용오차 1e-12. 동률 포함 방향 차이와 엄격한 반대 방향을 구분 |
| A4 | [gold 출현 원자료](A4/gold-occurrences.csv), [문항별 단계](A4/question-stages.csv), [pool별 제약](A4/pool-constraints.csv), [단계 집계](A4/stage-summary.csv), [동시 선택 가능성](A4/pool-feasibility-summary.json) | 문항 내 고유 exact gold 출현 443건/조건. 전역 고유 gold 386개와 구분. 원 행 중복 유지, 평가는 문자열 집합 |
| A5 | [문항별 자원](A5/question-resources.csv), [평균·중앙값·IQR](A5/descriptive-statistics.csv), [대응 차이](A5/paired-resource-differences.csv), [캐시 분리](A5/cache-separated-usage.csv) | 실제 전달 문맥과 전체 user message를 복원. API cache key 678개 모두 확인. tokenizer와 사용량 기록 구분 |
| A6 | [226문항 casebook](A6/casebook.jsonl), [유형 빈도](A6/observation-frequencies.csv), [전체 후보 묶음](A6/bucket-membership.json), [중앙적 대표 후보](A6/representative-candidates.csv) | 다중 라벨 관측 상태. 중앙값 근접·동률 query_id 규칙. 전문가 판정 아님 |

CSV와 같은 이름의 JSONL에는 배열·출처 참조를 구조화해 보존했다. 긴 조문·답변·gold 원문은 casebook에 있고, 모든 원본은 원 위치에 유지된다. 원자료를 다시 수집하거나 삭제한 과거 실험을 복구하지 않았다.

## 집계에서 확인한 사실

근거 F1의 Jev 우세/동률/CE 우세는 **32/177/17문항**이다. LF-Eval은 66/127/33문항이다. 근거 F1과 LF 또는 Token F1이 엄격히 반대 방향인 문항은 11개다. 이 수치는 대응 기술통계이며 독립 성공률 검정 결과가 아니다.

다음은 **443개의 문항별 gold 출현** 중 잔존 개수다. corpus 미매핑은 33회이며 전역 고유 미매핑 27개, 영향 29문항과 분모가 다르다.

| 단계 | 수정 CE | Jev |
|---|---:|---:|
| corpus | 410/443 | 410/443 |
| 공통 BM25 합집합 | 335/443 | 335/443 |
| shortlist 합집합 | 293/443 | 322/443 |
| 최종 선택 집합 | 233/443 | 250/443 |

위 표의 비율은 출현 단위 micro 비율이다. 논문의 공식 Recall은 **문항별 Recall의 비가중 평균**이므로 최종 57.74%/60.69%와 다르다. 두 값을 섞지 않는다.

BM25 합집합에 모든 gold가 있는 문항은 138개지만 pool당 한 개 선택 제약으로 동시에 모두 고를 수 있는 문항은 127개다. shortlist에서는 CE 112→104문항, Jev 130→120문항이다. 최종 모두 선택은 77/79문항이다. 따라서 shortlist에 gold가 남았다는 이유만으로 후속 법률 판단 오류를 확정하지 않는다. 최대 매칭은 구조적 진단 상한이며 gold를 사용해 새 선택 결과를 만든 것이 아니다.

선택 목록 합계는 조건마다 478개로 동일하다. 고유 선택의 문항별 합계는 수정 CE 407, Jev 409이고 목록 내 중복은 71/69회다. 문맥 토큰 평균은 **203.6681/215.5973**, 중앙값은 164/170.5다. 전체 API 입력 평균은 2302.6681/2314.5841, 출력 평균은 72.1593/73.9779다. Jev−CE 대응 문맥 차이 평균은 +11.9292토큰, 중앙값은 0이다. **이 집계에서 문맥/입력 절감이 관찰되었다고 쓰지 않는다.**

토큰량은 실제 `\n`.join(provisions) 문자열에 `tiktoken 0.14.0 / o200k_base`를 적용했다. [토크나이저 지문](A5/tokenizer.json). 전체 user message는 few-shot·질문·문맥을 포함하며, 문맥 단독 토큰과 합으로 분해할 때 경계 토큰화 차이가 있을 수 있다. 모든 678행에서 API input은 복원한 메시지 텍스트 토큰보다 7개 많았다. API output은 모델 응답 전체 사용량이며 정리된 answer 텍스트 토큰과 구분한다.

실행 응답 캐시 hit는 raw CE 0, 수정 CE 72, Jev 122행이다. 이는 제공자의 prefix `cached_input_tokens`와 다른 필드다. 캐시 행은 논리적 입력 요구량에 포함하고 새 요청 사용량과 분리했다. 성공한 비캐시 답변 생성의 사용량도 선택·scorer·judge·준비·실패/재시도·로컬 장비 비용을 모두 포함하지 않으므로 전체 청구액/서비스 비용으로 쓰지 않는다. 지연·Filtering·비열등성 결과는 생성하지 않았다.

## 검토 대기 자료의 구분

- [RQ·목차·방법 정합성 조율](RQ_TOC_COORDINATION.md): 팀과 확정해야 할 문구·범위. 이번 집계가 팀 합의를 대신하지 않는다.
- [법률 검토 안내](LEGAL_REVIEW.md), [법률 검토 대기 183문항](A6/legal-review-queue.csv): 자동 관측으로 선별한 확인 질문. 법률 오답 183개라는 뜻이 아니며, 목록 밖 43문항도 법적 정답 판정을 받은 것이 아니다.
- [대표 후보 3개](A6/proposed-three-candidates.json)는 아직 법률 검토·본문 채택 전이다. 모두 기존 사람 표본 밖이며 별도 정성 검토로 다룬다. [사람 평가 경계](A6/human-review-boundary.json).
- [그림 제작 인계](FIGURE_HANDOFF.md): 사용자가 지정한 figures4papers 스킬과 hop 그림 원자료. 이번에는 그림을 그리지 않았다.

## 출처와 재현

[분석 명세](analysis-spec.json)는 새 집계 시작 전에 기록했다. 이는 **결과를 본 뒤 고정한 탐색적 준비 규칙**이며 사전등록이나 기존 실행 잠금이 아니다. 낮은 자동 답변 점수의 0.5 기준은 사례 탐색을 위한 기술적 경계이고 검증된 법률 정확성 기준이 아니다. 기존 151그룹·10,000회·seed 20261108의 탐색적 CI만 옮겼고 추가 CI/상호작용 검정은 하지 않았다. Token F1의 기존 percentile CI와 centered-bootstrap p의 불일치도 원장에 그대로 남겼다.

[소스 manifest](source-manifest.json)에 입력 경로·바이트 SHA-256·크기를 기록했다. JSONL 출처는 1-based 행, corpus row ID는 0-based다. 수치 원장의 JSON pointer는 기존 `analysis.json` 내 원값까지 연결된다. 공식 canonical은 `hierarchy + content`이며 공백·Unicode·법령 버전의 사후 정규화를 하지 않았다.

집계 코드: `scripts/prepare_chapter4.py`. 독립 검증: `scripts/validate_chapter4_prep.py`. 기존 출력에 재실행하면 덮어쓰지 않고 중단한다. 재현하려면 비어 있는 별도 출력 경로를 지정한다.

```bash
.venv/bin/python scripts/prepare_chapter4.py --output /private/tmp/chapter4-prep-recheck
.venv/bin/python scripts/validate_chapter4_prep.py
.venv/bin/python scripts/koblex.py verify
.venv/bin/python -m pytest -q
```

집계 스크립트는 네트워크 연결을 차단하며 API cache는 읽기만 한다. 기존 실험 실행 코드를 변경하지 않았다. 검증·테스트 기록은 `validation.json`, `execution-record.json`을 참조한다.
