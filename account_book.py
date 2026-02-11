import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import calendar

st.set_page_config(page_title="범 & 젼 달력 가계부", layout="centered")

# --- 스타일 설정 (달력 가독성 높이기) ---
st.markdown("""
    <style>
    .stDateInput { width: 100%; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    .css-1r6slb0 { padding: 10px; border-radius: 10px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        return df
    except:
        return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])

st.title("📅 범 & 젼 캘린더 가계부")

# 탭 구성 (범/젼)
tabs = st.tabs(["   범(Beom)   ", "   젼(Jyeon)   "])
names = ["beom", "jyeon"]

for i, tab in enumerate(tabs):
    user = names[i]
    with tab:
        df = load_data(user)
        
        # --- 1. 이번 달 요약 ---
        today = datetime.now().date()
        this_month_df = df[pd.to_datetime(df['날짜']).dt.month == today.month]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            total_in = this_month_df[this_month_df['구분'] == '수입']['금액'].sum()
            st.metric("이번달 수입", f"{total_in:,.0f}원")
        with col2:
            total_out = this_month_df[this_month_df['구분'] != '수입']['금액'].sum()
            st.metric("이번달 지출", f"{total_out:,.0f}원")
        with col3:
            st.metric("잔액", f"{(total_in - total_out):,.0f}원")

        # --- 2. 메인 만년 달력 섹션 ---
        st.write("---")
        st.subheader("🗓️ 날짜별 내역 확인")
        
        # 달력 위젯 (이걸로 날짜를 선택하면 해당 날짜 내역이 아래에 뜸)
        selected_date = st.date_input("날짜를 선택하세요", value=today, key=f"cal_{user}")
        
        # 선택한 날짜의 내역 보여주기 (범님이 가장 중요하게 생각하신 부분)
        day_df = df[df['날짜'] == selected_date]
        
        if not day_df.empty:
            st.info(f"📍 {selected_date} 내역")
            for _, row in day_df.iterrows():
                color = "🔵" if row['구분'] == "수입" else "🔴"
                st.write(f"{color} [{row['카테고리']}] {row['내역']}: **{row['금액']:,}원**")
        else:
            st.write(f"⚪ {selected_date}에 기록된 내역이 없습니다.")

        # --- 3. 입력 섹션 (보내주신 코드의 입력창 기능) ---
        with st.expander("➕ 이 날짜에 기록하기", expanded=False):
            with st.form(key=f"form_{user}", clear_on_submit=True):
                m_type = st.selectbox("구분", ["지출", "수입", "우리"], key=f"t_{user}")
                m_cat = st.selectbox("카테고리", ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "용돈", "기타"], key=f"c_{user}")
                m_item = st.text_input("내역", key=f"i_{user}")
                m_amount = st.number_input("금액", min_value=0, step=1000, key=f"a_{user}")
                
                if st.form_submit_button("저장하기"):
                    new_row = pd.DataFrame([{
                        "날짜": selected_date.strftime("%Y-%m-%d"),
                        "구분": m_type,
                        "카테고리": m_cat,
                        "내역": m_item,
                        "금액": m_amount
                    }])
                    
                    targets = names if m_type == "우리" else [user]
                    for t in targets:
                        existing = conn.read(worksheet=t, ttl=0)
                        updated = pd.concat([existing, new_row], ignore_index=True)
                        conn.update(worksheet=t, data=updated)
                    
                    st.success(f"{selected_date} 저장 완료!")
                    st.rerun()

        # --- 4. 전체 리스트 (하단) ---
        st.write("---")
        if st.checkbox("이번 달 전체 내역 보기", key=f"check_{user}"):
            st.dataframe(this_month_df.sort_values('날짜', ascending=False), use_container_width=True)
