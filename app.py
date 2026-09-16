"""데모 화면 (streamlit).

실행: streamlit run app.py

최종 답변만 보여주지 않고 분류 결과·호출한 근거 문서·검증 결과까지 화면에 노출한다
(관찰가능성 — N039 10장. 판단 과정을 보여줘야 "왜 이렇게 답했는지"에 답할 수 있다).
"""

import streamlit as st

import agent
import context

st.set_page_config(page_title="AI Easy 레슨 챗봇 (라우팅 에이전트 데모)", page_icon="🤖")
st.title("AI Easy 레슨 챗봇 데모")
st.caption("N039 라우팅 에이전트 프로젝트 — 분류·근거·검증 과정을 그대로 보여줍니다.")

question = st.text_input("궁금한 것을 물어보세요", placeholder="예: 챗봇 질문은 하루에 몇 번까지 무료인가요?")

if st.button("질문하기") and question.strip():
    with st.spinner("생각 중..."):
        result = agent.run(question)

    st.subheader("답변")
    st.write(result["answer"])

    st.subheader("분류 결과")
    st.code(result["category"])

    st.subheader("호출한 근거 문서")
    docs = context.CATEGORY_DOCS.get(result["category"], [])
    if docs:
        for d in docs:
            st.write(f"- `docs/{d}`")
    else:
        st.write("(근거 문서 없음 — 범위 밖으로 판정되어 넘김)")

    st.subheader("검증 결과")
    validation = result.get("validation", {})
    if validation.get("passed"):
        st.success("✓ 근거 내 답변 (통과)")
    else:
        st.error("✗ 근거 밖 내용 감지")
        for claim in validation.get("unsupported_claims", []):
            st.write(f"- {claim}")
