import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="범 & 젼 가계부", layout="centered")

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(user_sheet):
    # 구글 시트에서 실시간으로 읽어오기 (범/젼 탭 구분)
    return conn.read(worksheet=user_sheet, ttl=0)

st.title("📔 Beom & Jyeon 24시간 가계부")

tabs = st.tabs(["   Beom   ", "   Jyeon   "])
users = ["beom", "jyeon"] 

for i, tab in enumerate(tabs):
    user = users[i]
    with tab:
        try:
            df = load_data(user)
            df['날짜'] = pd.to_datetime(df['날짜'])
            
            # 상단 잔액 요약
            now = datetime.now()
            month_df = df[df['날짜'].dt.month == now.month]
            income = month_df[month_df['구분'] == '수입']['금액'].sum()
            expense = month_df[month_df['구분'] != '수입']['금액'].sum()
            st.metric(label=f"{now.month}월 잔액", value=f"{income - expense:,.0f}원")

            # --- 입력 섹션 (년/월 이동 최적화) ---
            with st.expander("➕ 새 내역 입력하기", expanded=True):
                with st.form(key=f"form_{user}", clear_on_submit=True):
                    st.write("**날짜 선택 (년/월을 직접 클릭하세요)**")
                    c1, c2, c3 = st.columns(3)
                    with c1: y = st.selectbox("년", range(2025, 2031), index=1, key=f"y_{user}") # 2026년 기본 선택
                    with c2: m = st.selectbox("월", range(1, 13), index=now.month-1, key=f"m_{user}")
                    with c3: d = st.selectbox("일", range(1, 32), index=now.day-1, key=f"d_{user}")
                    
                    col_type, col_cat = st.columns(2)
                    with col_type:
                        new_type = st.selectbox("구분", ["우리", "지출", "수입"], key=f"t_{user}")
                    with col_cat:
                        cats = ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"] if new_type != "수입" else ["용돈", "기타"]
                        new_cat = st.selectbox("카테고리", cats, key=f"c_{user}")
                    
                    new_item = st.text_input("내역 (한글 렉 없음)", key=f"i_{user}")
                    new_amount = st.number_input("금액", min_value=0, step=1000, key=f"a_{user}")
                    
                    if st.form_submit_button("입력하기"):
                        # 구글 시트에 들어갈 데이터 정리
                        new_row = pd.DataFrame([{
                            "날짜": f"{y}-{m:02d}-{d:02d}", 
                            "구분": new_type, 
                            "카테고리": new_cat, 
                            "내역": new_item, 
                            "금액": new_amount
                        }])
                        
                        if new_type == "우리":
                            for u in users:
                                existing = load_data(u)
                                updated = pd.concat([existing, new_row], ignore_index=True)
                                conn.update(worksheet=u, data=updated)
                        else:
                            existing = load_data(user)
                            updated = pd.concat([existing, new_row], ignore_index=True)
                            conn.update(worksheet=user, data=updated)
                        
                        st.success("구글 시트에 동기화 완료!")
                        st.rerun()

            # --- 내역 리스트 ---
            st.subheader("🗓️ 전체 내역")
            if not df.empty:
                st.dataframe(
                    df.sort_values(by='날짜', ascending=False),
                    column_config={"금액": st.column_config.NumberColumn(format="%d원")},
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"구글 시트의 탭 이름이 'beom'과 'jyeon'인지 확인해주세요!")
