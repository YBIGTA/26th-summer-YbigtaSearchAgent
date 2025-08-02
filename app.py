# app.py

import streamlit as st
import requests
import json

# --- Streamlit UI 구성 ---

st.title("🤖 YBIGTA AI Agent")
st.write("YBIGTA의 모든 것을 물어보세요!")

# 사용자 질문 입력
user_question = st.text_input("질문을 입력하세요:", "")

if st.button("답변 생성하기"):
    if user_question:
        with st.spinner('답변을 생성하는 중입니다...'):
            try:
                # 백엔드 API에 요청 보내기
                response = requests.post(
                    "http://127.0.0.1:8000/ask",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps({"query": user_question})
                )

                if response.status_code == 200:
                    # 답변 표시
                    answer = response.json().get("answer")
                    st.success("답변이 도착했습니다!")
                    st.write(answer)
                else:
                    st.error(f"오류가 발생했습니다. (상태 코드: {response.status_code})")
                    st.json(response.json())

            except requests.exceptions.RequestException as e:
                st.error(f"API 서버에 연결할 수 없습니다: {e}")
    else:
        st.warning("질문을 입력해주세요.")