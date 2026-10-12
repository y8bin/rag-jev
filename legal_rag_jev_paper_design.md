# 논문 설계 — Jev 기반 법률 근거 적합성 평가 및 재정렬을 활용한 Legal RAG

> **설계 이력 안내 (2026-10-09):** 아래 본문은 최초 논문 구상이다. 실행과 논문 작성의 최신 기준은 [최종 연구 전략](final_research_strategy.md)을 따른다. 아래의 LegalBench-RAG/KBL 데이터 사용, 영어·한국어 2단계 비교, 확률 출력 전제, 최소 1개 선택, 4개 비교군 및 연구 질문 번호는 최종 전략으로 대체되었다. 실제 연구는 자체 코퍼스와 Qdrant를 사용하며, CE-FR을 포함한 5개 조건으로 검색·답변·효율을 검증한다.

## 0. 논문 한 줄 정의

본 연구는 법률 도메인 RAG에서 **Jev를 법률 근거 적합성(legal evidence applicability) 판단용 확률 기반 reranker/filter로 사용**했을 때, 기존 유사도 기반 retrieval 및 일반 reranker와 비교하여 **검색 효율성·검색 정확도·최종 답변의 근거 충실성**이 어떻게 달라지는지를 실증적으로 검증한다.

---

## 1. 연구 질문

### RQ1 — 검색 효율성

> 법률 도메인 RAG에서 Jev 기반의 법률 근거 적합성 평가 및 재정렬은 기존 유사도 기반 검색과 비교하여 적용 가능한 법률 근거의 **검색 효율성(비용·지연시간·LLM 입력량)**을 개선하는가?

### RQ2 — 검색 정확도 및 근거 충실성

> 법률 도메인 RAG에서 Jev 기반의 법률 근거 적합성 평가 및 재정렬은 기존 유사도 기반 검색과 비교하여 적용 가능한 법률 근거의 **검색 정확도와 최종 답변의 근거 충실성**을 향상시키는가?

### 보조 비교 질문

> Jev는 기존 Cross-Encoder 계열 reranker와 비교했을 때 어느 수준의 검색 품질을 유지하면서 비용 및 latency 측면의 이점을 제공하는가?

---

## 2. 가설

### H1. 효율성

- **H1-1:** Jev 기반 filtering/reranking은 고정된 Vector Top-K 전체를 최종 LLM에 전달하는 방식보다 평균 LLM 입력 토큰 수를 감소시킬 것이다.
- **H1-2:** Jev 판단 비용을 포함하더라도, 불필요한 context 감소로 인해 **end-to-end 비용**이 감소하거나 경쟁력 있는 수준을 유지할 것이다.
- **H1-3:** Jev reranking은 일반 Cross-Encoder 또는 생성형 LLM 기반 reranking과 비교했을 때 reranking latency 또는 비용 측면에서 이점을 보일 것이다.

### H2. 검색 정확도

- **H2-1:** `Vector Retrieval + Jev`는 `Vector Retrieval only`보다 Precision@K, MRR, nDCG@K 또는 LegalBench-RAG의 character-level retrieval precision/recall에서 향상된 성능을 보일 것이다.
- **H2-2:** Jev가 높은 확률을 부여한 chunk는 단순 semantic similarity가 높은 chunk보다 실제 질문의 답변 근거로 사용될 가능성이 높을 것이다.

### H3. 최종 답변의 근거 충실성

- **H3-1:** Jev를 통해 선택된 context를 사용한 답변은 Vector-only 대비 groundedness가 유지되거나 향상될 것이다.
- **H3-2:** Jev 기반 context selection은 citation accuracy 또는 citation support rate를 유지하거나 향상시킬 것이다.
- **H3-3:** 검색 정확도의 변화가 최종 답변 정확도 및 근거 충실성 변화와 통계적으로 연관될 것이다.

---

# 논문 목차 설계

## 1. Introduction

### 1.1 연구 배경

다음 흐름으로 서술한다.

1. **법률 도메인의 high-stakes 특성**
   - 법률 AI의 오류가 법적 판단, 조사, 의사결정에 직접 영향을 줄 수 있음을 설명한다.
   - Dahl et al. (2024)의 법률 hallucination 연구를 인용하여 범용 LLM의 법률 사실 오류 문제가 실증적으로 보고되었음을 제시한다.
   - 상용 법률 RAG 시스템에서도 hallucination이 완전히 사라지지 않았다는 Stanford RegLab의 결과를 제시한다.

2. **RAG의 필요성**
   - 모델 내부 지식만으로 답변하는 대신 외부 법령·판례를 검색하여 근거를 제공하는 RAG가 법률 AI에서 중요한 이유를 설명한다.
   - 생성 모델 성능뿐 아니라 retrieval 품질이 최종 신뢰성에 직접 영향을 준다는 문제를 제시한다.

3. **법률 retrieval의 특수성**
   - semantic similarity와 legal applicability가 반드시 동일하지 않음을 설명한다.
   - 동일한 법률 용어가 존재해도 관할, 적용 요건, 예외, 시점, 법적 쟁점에 따라 실제 근거로 사용할 수 없는 경우가 있음을 제시한다.

4. **기존 reranking의 한계**
   - Cross-Encoder 및 LLM reranker가 검색 정확도를 높이는 데 사용되지만 추가 연산과 latency가 발생함을 설명한다.
   - 법률 RAG의 실제 활용에서는 검색 품질뿐 아니라 비용과 처리 속도 역시 중요함을 제시한다.

5. **Jev의 연구 가능성**
   - Jev를 자유 생성 모델이 아니라 typed probabilistic decision model로 정의한다.
   - “후보 chunk가 질문에 직접 적용 가능한 법률 근거인가?”라는 좁고 구조화된 판단에 적용할 수 있음을 제안한다.
   - TypeSafe의 속도·비용 주장은 개발사 자체 평가이므로 법률 도메인에서 별도 검증이 필요하다는 점을 명확히 한다.

### 1.2 연구 목적

본 연구의 목적을 다음 세 가지로 정리한다.

- Jev를 Legal RAG의 **legal relevance/applicability reranker**로 적용할 수 있는지 검증
- 검색 정확도뿐 아니라 **비용·latency·context token 수**를 함께 평가
- retrieval 개선이 실제 최종 답변의 **groundedness와 citation accuracy**로 연결되는지 확인

### 1.3 연구 기여

논문에서는 기여를 다음과 같이 제시한다.

1. Jev/System One 방식의 확률 기반 decision model을 법률 RAG의 evidence reranking 문제에 적용하는 실험 구조 제안
2. **LegalBench-RAG**와 **KBL + KBL-RAG + LRAGE**를 결합한 영어/한국어 2단계 검증
3. 검색 품질만이 아니라 **accuracy–efficiency–groundedness trade-off**를 동시에 분석
4. 고정 Top-N reranking과 threshold 기반 filtering을 분리하여, “정확도 향상”과 “context 절감” 효과를 각각 검증

> 주의: “최초”라는 표현은 최종 논문 작성 전 추가 문헌 검색으로 novelty를 확인한 뒤 사용한다.

---

## 2. Related Work

### 2.1 Legal Hallucination in Large Language Models

포함할 내용:

- Dahl et al. (2024)의 *Large Legal Fictions*
- 범용 LLM에서 법률 hallucination이 발생하는 양상
- 상용 법률 AI에서도 RAG만으로 오류가 완전히 제거되지 않는다는 실증 연구
- 본 연구와의 연결:
  - 생성 단계만 개선하는 것이 아니라 **신뢰 가능한 evidence retrieval**이 필요함

### 2.2 Retrieval-Augmented Generation in the Legal Domain

포함할 내용:

- 법률 corpus에서 RAG가 사용되는 이유
- 법령·판례 검색과 일반 문서 검색의 차이
- 법률 문서의 구조적 특성
  - 법령: 조/항/호
  - 판례: 사실관계, 쟁점, 판시사항, 이유
- relevant와 applicable의 차이

### 2.3 Legal Retrieval and Reranking

포함할 내용:

- Dense/vector retrieval
- BM25 및 hybrid retrieval
- Cross-Encoder reranking
- LLM 기반 reranking
- 기존 방식의 장단점:
  - Vector retrieval: 빠르지만 semantic similarity 중심
  - Cross-Encoder: 높은 정밀도를 기대할 수 있으나 추가 inference 필요
  - LLM reranking: 유연한 판단이 가능하지만 비용 및 latency 증가

### 2.4 Legal RAG Benchmarks and Evaluation Frameworks

#### LegalBench-RAG

- 법률 retrieval 자체를 평가하는 benchmark
- query와 ground-truth snippet을 연결
- 정확한 character span을 이용한 deterministic precision/recall 평가 가능
- 본 연구에서는 **Jev의 순수 retrieval/reranking 성능 검증**에 사용

#### KBL / KBL-RAG

- 한국어 법률 이해 benchmark
- 법률 지식·추론·변호사시험 task
- 한국 법령과 판례 corpus를 이용한 RAG 실험 가능
- 본 연구에서는 **한국 법률 환경의 end-to-end RAG 평가**에 사용

#### LRAGE

- 법률 RAG의 corpus, retriever, reranker, LLM backbone, metric을 모듈식으로 변경해 평가하는 오픈소스 도구
- 본 연구에서는 실험 harness로 사용
- 기존 reranker와 JEV adapter를 동일 interface 아래 비교

### 2.5 Jev and System One Models

포함할 내용:

- TypeSafe의 System One Model 개념
- 문자열 생성 대신 미리 정의된 type의 판단을 반환
- yes/no(Noul), choice, score 등 구조화된 decision
- 확률 및 confidence 활용 가능
- Jev의 적합한 사용 범위를 “법률 답변 생성”이 아니라 **후보 근거의 적합성 판정**으로 제한
- 개발사 성능 주장을 연구의 사실로 전제하지 않고 독립적으로 검증한다는 점 명시

### 2.6 Research Gap

다음 논리로 정리한다.

1. 법률 RAG에서 retrieval 품질이 중요하다는 연구는 존재한다.
2. reranking의 필요성도 기존 연구에서 확인된다.
3. 그러나 법률 근거의 **적용 가능성**을 좁은 probabilistic decision으로 판정하면서,
4. 검색 정확도와 비용/latency,
5. 그리고 최종 답변 groundedness까지 함께 연결하여 평가하는 연구는 추가 검증의 여지가 있다.

이 gap에서 본 연구의 RQ1과 RQ2를 도출한다.

---

## 3. Methodology

### 3.1 Problem Definition

질문을 `q`, 1차 retrieval 결과를 `D_K = {d1, ..., dK}`라고 정의한다.

일반 Vector retrieval은:

`score_vec(q, d)`

를 기반으로 후보를 선택한다.

Jev 기반 방법에서는 각 후보에 대해:

> “이 후보 법률 문서는 사용자의 질문에 직접적인 법적 근거로 사용될 수 있는가?”

를 판단하고,

`P_JEV(applicable | q, d)`

를 relevance score로 사용한다.

### 3.2 Proposed JEV Legal Evidence Reranker

구조:

```text
Query
  ↓
Vector Retrieval Top-K
  ↓
Jev Legal Applicability Decision
  ↓
P(applicable)
  ↓
Ranking / Filtering
  ↓
Selected Legal Evidence
  ↓
LLM
```

Jev는 다음 작업만 수행하도록 제한한다.

- 직접 법적 근거 여부 판단
- applicability probability 반환

다음 작업은 하지 않는다.

- 답변 생성
- 새로운 법률 사실 생성
- citation 생성
- 법률 reasoning 서술

### 3.3 Two JEV Modes

#### JEV-R: Fixed Top-N Reranking

- Top-K 후보 모두 점수화
- `P(applicable)` 순으로 정렬
- 항상 동일한 Top-N을 LLM에 전달

목적:
- 순수 reranking 정확도를 비교
- Vector-only / Cross-Encoder와 공정하게 retrieval 품질 비교

#### JEV-FR: Filtering + Reranking

- Top-K 후보 점수화
- 개발 세트에서 결정된 threshold `τ` 이상만 선택
- 최대 N개, 최소 1개 등의 안전 규칙 적용

목적:
- 불필요한 context 제거
- LLM input token 및 generation cost 감소
- RQ1의 효율성 검증

### 3.4 Baselines

- **B0 — Vector Only**
  - Vector Top-N을 그대로 사용

- **B1 — Vector + Conventional Reranker**
  - Vector Top-K → Cross-Encoder → Top-N

- **P1 — Vector + JEV-R**
  - Vector Top-K → Jev → Top-N

- **P2 — Vector + JEV-FR**
  - Vector Top-K → Jev → threshold filtering → 최대 Top-N

### 3.5 Experimental Framework

연구는 두 단계로 구성한다.

#### Phase 1 — LegalBench-RAG

목적:
- generation 변수를 제거하고 retrieval/reranking 자체를 평가
- 영어 법률 계약 문서에서 JEV의 순수 evidence selection 성능 확인

#### Phase 2 — KBL + KBL-RAG + LRAGE

목적:
- 한국어 법률 환경에서 end-to-end RAG 평가
- 검색 결과가 실제 답변 정확도 및 groundedness에 미치는 영향 검증

---

## 4. Experimental Setup

이 장에서는 별도의 `experiment_design.md`를 기반으로 실제 조건을 기술한다.

### 4.1 Datasets

- LegalBench-RAG
- KBL
- KBL-RAG corpus

### 4.2 Retrieval Model

모든 조건에서 동일한 retriever를 사용한다.

- Dense embedding model 1개를 고정
- corpus와 index 동일
- Top-K 동일

주 실험에서는 reranking method만 변경한다.

### 4.3 Reranking Methods

- None
- Cross-Encoder
- Jev-R
- Jev-FR

### 4.4 Generation Model

- 모든 조건에서 동일한 LLM
- 동일 system prompt
- 동일 temperature
- 동일 max tokens
- 동일 citation format

### 4.5 Evaluation Metrics

#### Retrieval quality

- LegalBench-RAG native character-level precision
- character-level recall / F1
- Precision@K
- Recall@K
- MRR
- nDCG@K

#### Efficiency

- reranking latency
- retrieval + reranking latency
- LLM generation latency
- end-to-end latency
- LLM input token 수
- Jev input token 수
- 요청당 비용
- 1,000 query 기준 환산 비용

#### Final answer

- KBL answer accuracy / exact match
- groundedness
- citation support rate
- citation accuracy
- unsupported claim rate

---

## 5. Results

### 5.1 Retrieval Accuracy

표 예시:

| Method | Precision@5 | Recall@5 | MRR | nDCG@5 | Char-F1 |
|---|---:|---:|---:|---:|---:|
| Vector | | | | | |
| Cross-Encoder | | | | | |
| Jev-R | | | | | |
| Jev-FR | | | | | |

분석할 내용:

- Vector 대비 Jev 개선 여부
- Cross-Encoder 대비 Jev의 품질 차이
- 영어/한국어에서 효과가 일관적인지

### 5.2 Efficiency

| Method | Rerank ms | E2E ms | Context Tokens | Cost / Query | Cost / 1K |
|---|---:|---:|---:|---:|---:|
| Vector | | | | | |
| Cross-Encoder | | | | | |
| Jev-R | | | | | |
| Jev-FR | | | | | |

핵심 분석:

- Jev 자체 호출 비용
- Jev 사용으로 절약된 generation context 비용
- 전체 end-to-end 관점에서 실제 비용이 감소했는지

### 5.3 Final Answer Quality

| Method | Accuracy | Groundedness | Citation Support | Unsupported Claims |
|---|---:|---:|---:|---:|
| Vector | | | | |
| Cross-Encoder | | | | |
| Jev-R | | | | |
| Jev-FR | | | | |

### 5.4 Accuracy–Efficiency Trade-off

단일 지표로 억지로 합치지 않고 Pareto 관점으로 제시한다.

- x축: latency 또는 cost
- y축: retrieval accuracy / groundedness
- 각 방법을 point로 표시

“더 정확하지만 더 비싼 방법”, “거의 동일한 정확도를 더 낮은 비용으로 제공하는 방법”을 구분하여 해석한다.

---

## 6. Ablation and Sensitivity Analysis

### 6.1 Top-K 민감도

- K = 10
- K = 20
- K = 50

### 6.2 JEV Threshold 민감도

개발 세트에서:

- τ = 0.5
- τ = 0.6
- τ = 0.7
- τ = 0.8
- τ = 0.9

중 성능–비용 trade-off를 확인하고 최종 test threshold를 고정한다.

### 6.3 Evidence Type 분석

가능한 경우:

- 법령
- 판례
- 계약 조항

별로 성능 차이를 분석한다.

### 6.4 Query Difficulty 분석

- 직접 조문 질의
- 사실관계 기반 적용 질의
- 다중 쟁점 질의

등으로 나누어 JEV가 어떤 질의에서 효과적인지 분석한다.

---

## 7. Discussion

### 7.1 RQ1 해석

- Jev가 실제 total cost를 낮췄는가?
- reranking latency 추가 비용보다 context reduction 효과가 컸는가?
- Cross-Encoder 대비 latency 이점이 있었는가?

### 7.2 RQ2 해석

- semantic similarity와 legal applicability의 차이를 Jev가 포착했는가?
- retrieval 개선이 groundedness 향상으로 이어졌는가?
- 정확한 retrieval이 항상 답변 정확도 향상으로 연결되었는가?

### 7.3 Error Analysis

실패 사례를 다음 유형으로 분류한다.

- 의미적으로 유사하지만 적용 불가능한 근거를 높은 점수로 평가
- 필요한 예외 조항 누락
- 질문의 법적 쟁점을 잘못 판별
- 판례 사실관계의 과도한 유사성에 영향
- 언어(영어/한국어)에 따른 성능 차이
- 긴 chunk에 의한 판단 오류

대표 사례를 정성적으로 제시한다.

---

## 8. Limitations and Threats to Validity

반드시 포함할 내용:

- Jev는 비교적 새로운 모델이며 API 사양과 가격이 변할 수 있음
- TypeSafe가 공개한 성능 결과는 개발사 자체 benchmark이므로 본 연구에서 독립 검증함
- LegalBench-RAG는 계약 문서 중심이므로 전체 법률 검색을 대표하지 않음
- KBL의 최종 답변 정확도가 실제 법률 상담 품질 전체를 의미하지 않음
- 한국어 retrieval gold evidence가 제한될 경우 일부 groundedness 평가는 judge 또는 표본 수작업 검증에 의존할 수 있음
- API 네트워크 latency가 모델 자체 inference latency와 혼합될 수 있음
- 법률 정보의 시점성과 관할 차이를 완전히 통제하기 어려울 수 있음

---

## 9. Ethical and Practical Considerations

- 본 연구 시스템은 법률 자문을 자동 대체하는 시스템이 아니라 RAG retrieval 실험 시스템임을 명시한다.
- 실제 사용자 의사결정에 사용되는 경우 사람의 검토가 필요함을 서술한다.
- 데이터셋별 라이선스 및 원천 데이터 사용 조건을 준수한다.
- 법률 근거의 최신성·관할·적용 시점이 중요한 실제 서비스에서는 별도 검증 계층이 필요함을 명시한다.

---

## 10. Conclusion

다음 세 문장을 중심으로 정리한다.

1. Jev 기반 legal applicability 판단이 법률 RAG의 reranking primitive로 실용적인지
2. 정확도–비용–latency trade-off가 기존 방법과 어떻게 다른지
3. retrieval 개선이 최종 grounded legal answer로 실제 연결되는지

연구 결과가 긍정적이지 않더라도 “어떤 조건에서 Jev가 유효하거나 실패하는가”를 밝히는 것을 논문의 기여로 본다.

---

# 권장 그림 및 표

## Figure 1. Overall Architecture

```text
Legal Corpus
    ↓
Retriever
    ↓
Vector Top-K
    ↓
┌───────────────┬────────────────┬────────────────┐
│ Vector Only   │ Cross-Encoder  │ JEV            │
│               │                │                │
│ Top-N         │ Re-rank Top-N  │ Score/Filter   │
└───────────────┴────────────────┴────────────────┘
                         ↓
                       LLM
                         ↓
               Answer + Evidence
```

## Figure 2. Two-stage Evaluation

```text
Phase 1
LegalBench-RAG
→ Retrieval-only validation
→ Accuracy / latency / cost

Phase 2
KBL + KBL-RAG + LRAGE
→ End-to-end Korean Legal RAG
→ Answer accuracy / groundedness / cost
```

## Figure 3. Accuracy–Efficiency Pareto Plot

- X: cost 또는 latency
- Y: retrieval F1 또는 groundedness

## Table 1. Dataset Summary

## Table 2. Experimental Conditions

## Table 3. Retrieval Results

## Table 4. Efficiency Results

## Table 5. End-to-End Answer Results

## Table 6. Ablation Results

---

# 주요 참고문헌 및 구현 자료

- Dahl, M., Magesh, V., Suzgun, M., & Ho, D. E. (2024). *Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models*. Journal of Legal Analysis. https://doi.org/10.1093/jla/laae003
- Magesh, V. et al. (2024). *Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools*. https://reglab.stanford.edu/publications/hallucination-free-assessing-the-reliability-of-leading-ai-legal-research-tools/
- Pipitone, N., & Houir Alami, G. (2024). *LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain*. https://arxiv.org/abs/2408.10343
- LegalBench-RAG Repository: https://github.com/zeroentropy-ai/legalbenchrag
- Kim, Y. et al. (2024). *Developing a Pragmatic Benchmark for Assessing Korean Legal Language Understanding in Large Language Models*. Findings of EMNLP 2024. https://arxiv.org/abs/2410.08731
- KBL Repository: https://github.com/lbox-kr/kbl
- Park, M., Oh, H., Choi, E., & Hwang, W. (2025). *LRAGE: Legal Retrieval Augmented Generation Evaluation Tool*. https://arxiv.org/abs/2504.01840
- LRAGE Repository: https://github.com/hoorangyee/LRAGE
- TypeSafe AI. (2026). *Introducing System One Models & Jev*. https://typesafe.ai/blog/introducing-system-one-models-and-jev
- TypeSafe API Docs: https://api.typesafe.ai/docs
