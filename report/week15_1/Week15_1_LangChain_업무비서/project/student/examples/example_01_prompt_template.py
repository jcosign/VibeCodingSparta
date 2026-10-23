"""D1·D2: prompt | llm 체인(LCEL) - 키 없이 FakeListLLM(가짜 모델)으로."""
from langchain_core.language_models.fake import FakeListLLM  # 키 없이 쓰는 '가짜 모델'
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template("역할:{role}\n요청:{task}\n답:")
llm = FakeListLLM(responses=["[가짜LLM] 요청을 처리한 결과입니다."])

chain = prompt | llm  # ← 이 '|'가 체인(LCEL). "틀 → 모델" 파이프라인
print(chain.invoke({"role": "분석가", "task": "매출 요약"}))
