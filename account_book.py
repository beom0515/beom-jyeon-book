import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="범 & 젼 가계부", layout="centered")

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 로드 함수 (탭 이름 대신 순서나 이름으로 시도)
def load_data(sheet_name):
    try:
        # ttl=0은 실시간 데이터를 가져오기 위함입니다.
        return conn.read(worksheet=sheet_name, ttl=0)
    except:
        # 에러 발생 시 빈 데이터프레임 반환
        return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])

st.title("📔 범 & 젼 24시간 가계부")

# 탭 구성
tabs = st.tabs(["   Beom   ", "   Jyeon   "])
names = ["beom", "jyeon"]

for i, tab in enumerate(tabs):
    user = names[i]
    with tab:
        df = load_data(user)
        
        # 입력 양식
        with st.form(key=f"form_{user}", clear_on_submit=True):
            st.subheader(f"{user.upper()} 입력창")
            
            # 날짜 선택 (년/월/일 박스)
            now = datetime.now()
            c1, c2, c3 = st.columns(3)
            with c1: y = st.selectbox("년", range(2025, 2030), index=1, key=f"y_{user}")
            with c2: m = st.selectbox("월", range(1, 13), index=now.month-1, key=f"m_{user}")
            with c3: d = st.selectbox("일", range(1, 32), index=now.day-1, key=f"d_{user}")
            
            col1, col2 = st.columns(2)
            with col1:
                new_type = st.selectbox("구분", ["지출", "수입", "우리"], key=f"type_{user}")
            with col2:
                new_cat = st.selectbox("카테고리", ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"], key=f"cat_{user}")
            
            new_item = st.text_input("내역", key=f"item_{user}")
            new_amount = st.number_input("금액", min_value=0, step=100, key=f"amt_{user}")
            
            submit = st.form_submit_button("기록하기")
            
            if submit:
                new_row = pd.DataFrame([{
                    "날짜": f"{y}-{m:02d}-{d:02d}",
                    "구분": new_type,
                    "카테고리": new_cat,
                    "내역": new_item,
                    "금액": new_amount
                }])
                
                # '우리'인 경우 양쪽 다 저장, 아니면 해당 탭만 저장
                target_sheets = names if new_type == "우리" else [user]
                for s in target_sheets:
                    existing = load_data(s)
                    updated = pd.concat([existing, new_row], ignore_index=True)
                    conn.update(worksheet=s, data=updated)
                
                st.success("시트에 저장되었습니다!")
                st.rerun()

        # 최근 내역 표시
        st.write("---")
        st.subheader("최근 기록")
        st.dataframe(df.tail(10), use_container_width=True)
