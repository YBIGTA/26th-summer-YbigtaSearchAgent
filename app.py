# app.py (피드백 기능 추가 버전)

import streamlit as st
import requests
import json

st.title("🤖 YBIGTA AI Agent (피드백 기능)")
st.write("AI의 답변이 마음에 드시나요? 피드백을 남겨주세요!")

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
# 답변과 피드백을 매칭하기 위해 마지막 질문을 저장할 변수
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

# --- (대화 기록 표시는 기존과 동일) ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 사용자 입력 처리 ---
if user_question := st.chat_input("질문을 입력하세요..."):
    st.chat_message("user").markdown(user_question)
    st.session_state.last_query = user_question # 마지막 질문 저장
    st.session_state.chat_history.append({"role": "user", "content": user_question})

    with st.spinner('답변을 생성하는 중입니다...'):
        try:
            # --- (API 요청 부분은 기존과 동일) ---
            response = requests.post(
                "http://backend:8000/conversation",
                headers={"Content-Type": "application/json"},
                data=json.dumps({
                    "query": user_question,
                    "chat_history": [(msg["content"], st.session_state.chat_history[i+1]["content"]) for i, msg in enumerate(st.session_state.chat_history[:-1]) if msg["role"] == "user"]
                })
            )

            if response.status_code == 200:
                ai_answer = response.json().get("answer")

                # --- 👇 AI 답변과 함께 피드백 버튼 표시 👇 ---
                with st.chat_message("assistant"):
                    st.markdown(ai_answer)

                    # 두 개의 컬럼을 만들어 버튼을 나란히 배치
                    col1, col2, _ = st.columns([1, 1, 8])

                    with col1:
                        if st.button("👍", key=f"good_{len(st.session_state.chat_history)}"):
                            requests.post(
                                "http://backend:8000/feedback",
                                json={"query": user_question, "answer": ai_answer, "feedback": "good"}
                            )
                            st.toast("피드백 감사합니다! 😊")

                    with col2:
                        if st.button("👎", key=f"bad_{len(st.session_state.chat_history)}"):
                            requests.post(
                                "http://backend:8000/feedback",
                                json={"query": user_question, "answer": ai_answer, "feedback": "bad"}
                            )
                            st.toast("개선에 참고하겠습니다! 🙇")

                st.session_state.chat_history.append({"role": "assistant", "content": ai_answer})
            else:
                st.error(f"오류가 발생했습니다: {response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"API 서버에 연결할 수 없습니다: {e}")