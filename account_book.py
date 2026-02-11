import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="범 & 젼 가계부", layout="centered")

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    # 탭 이름을 직접 지정해서 읽어오기
    return conn.read(worksheet=sheet_name, ttl=0)

st.title("📔 Beom & Jyeon 24시간 가계부")

# 탭 구성 (UI용 이름)
ui_tabs = st.tabs(["   Beom   ", "   Jyeon   "])
# 실제 구글 시트의 탭 이름 (여기서 틀리면 에러나니 시트와 똑같이 맞춤)
sheet_names = ["beom", "jyeon"] 

for i, tab in enumerate(ui_tabs):
    user_sheet = sheet_names[i]
    with tab:
        try:
            # 데이터 로드
            df = load_data(user_sheet)
            
            # 상단 잔액 요약
            now = datetime.now()
            if not df.empty and '금액' in df.columns:
                df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
                month_df = df[df['날짜'].dt.month == now.month]
                income = month_df[month_df['구분'] == '수입']['금액'].sum()
                expense = month_df[month_df['구분'] != '수입']['금액'].sum()
                st.metric(label=f"{now.month}월 잔액", value=f"{income - expense:,.0f}원")

            # --- 입력 섹션 ---
            with st.expander("➕ 새 내역 입력하기", expanded=True):
                with st.form(key=f"form_{user_sheet}", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: y = st.selectbox("년", range(2025, 2031), index=1, key=f"y_{user_sheet}")
                    with c2: m = st.selectbox("월", range(1, 13), index=now.month-1, key=f"m_{user_sheet}")
                    with c3: d = st.selectbox("일", range(1, 32), index=now.day-1, key=f"d_{user_sheet}")
                    
                    col_type, col_cat = st.columns(2)
                    with col_type:
                        new_type = st.selectbox("구분", ["우리", "지출", "수입"], key=f"t_{user_sheet}")
                    with col_cat:
                        cats = ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"] if new_type != "수입" else ["용돈", "기타"]
                        new_cat = st.selectbox("카테고리", cats, key=f"c_{user_sheet}")
                    
                    new_item = st.text_input("내역", key=f"i_{user_sheet}")
                    new_amount = st.number_input("금액", min_value=0, step=1000, key=f"a_{user_sheet}")
                    
                    if st.form_submit_button("입력하기"):
                        new_row = pd.DataFrame([{
                            "날짜": f"{y}-{m:02d}-{d:02d}", 
                            "구분": new_type, 
                            "카테고리": new_cat, 
                            "내역": new_item, 
                            "금액": new_amount
                        }])
                        
                        if new_type == "우리":
                            for s in sheet_names:
                                existing = load_data(s)
                                updated = pd.concat([existing, new_row], ignore_index=True)
                                conn.update(worksheet=s, data=updated)
                        else:
                            existing = load_data(user_sheet)
                            updated = pd.concat([existing, new_row], ignore_index=True)
                            conn.update(worksheet=user_sheet, data=updated)
                        
                        st.success("기록 완료!")
                        st.rerun()

            # --- 내역 리스트 ---
            st.subheader("🗓️ 최근 내역")
            if not df.empty:
                st.dataframe(df.sort_values(by='날짜', ascending=False), use_container_width=True)
        
        except Exception as e:
            st.error(f"연결 오류! 시트의 탭 이름이 '{user_sheet}'가 맞는지, 그리고 1행에 항목명이 있는지 확인해주세요.")
            st.info("시트 첫 줄: 날짜, 구분, 카테고리, 내역, 금액")
