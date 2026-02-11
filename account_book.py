import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import calendar

# 페이지 설정 (모바일 최적화)
st.set_page_config(page_title="범 & 젼 가계부", layout="centered")

# --- 스타일 설정 (보내주신 코드의 느낌을 살림) ---
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .stMetric { background-color: #F8F9FA; padding: 15px; border-radius: 10px; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: 0px 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl=0)
    except:
        return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])

st.title("📔 범 & 젼 가계부")

# --- 상단 잔액 표시 (보내주신 UI 스타일) ---
col_bum, col_jyeon = st.columns(2)

def get_balance(df):
    if df.empty: return 0
    income = df[df['구분'] == '수입']['금액'].astype(int).sum()
    expense = df[df['구분'] != '수입']['금액'].astype(int).sum()
    return income - expense

df_bum = load_data("beom")
df_jyeon = load_data("jyeon")

with col_bum:
    st.metric("Bum 잔액", f"{get_balance(df_bum):,}원")
with col_jyeon:
    st.metric("Jyeon 잔액", f"{get_balance(df_jyeon):,}원")

# --- 메인 탭 (범/젼) ---
main_tab_names = ["   범   ", "   젼   "]
tabs = st.tabs(main_tab_names)
sheet_names = ["beom", "jyeon"]

for i, tab in enumerate(tabs):
    user = sheet_names[i]
    with tab:
        # --- 1. 만년 달력 섹션 ---
        st.subheader("📅 만년 달력")
        # Streamlit의 기본 달력을 항상 펼쳐진 형태로 배치
        selected_date = st.date_input(
            "날짜 선택",
            value=datetime.now(),
            key=f"cal_{user}",
            label_visibility="collapsed"
        )

        # --- 2. 입력 섹션 (보내주신 UI처럼 하단 배치) ---
        with st.expander("➕ 내역 추가하기", expanded=True):
            with st.form(key=f"form_{user}", clear_on_submit=True):
                st.write(f"📅 선택된 날짜: **{selected_date}**")
                
                m_type = st.selectbox("구분", ["우리", "지출", "수입"], key=f"type_{user}")
                
                # 카테고리 설정
                if m_type == "수입":
                    cats = ["용돈", "기타"]
                else:
                    cats = ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"]
                
                m_cat = st.selectbox("카테고리", cats, key=f"cat_{user}")
                m_item = st.text_input("내역", key=f"item_{user}")
                m_amount = st.number_input("금액", min_value=0, step=1000, key=f"amt_{user}")
                
                if st.form_submit_button("입력하기"):
                    new_row = pd.DataFrame([{
                        "날짜": selected_date.strftime("%Y-%m-%d"),
                        "구분": m_type,
                        "카테고리": m_cat,
                        "내역": m_item,
                        "금액": m_amount
                    }])
                    
                    # '우리'인 경우 양쪽 저장
                    targets = sheet_names if m_type == "우리" else [user]
                    for t in targets:
                        existing = load_data(t)
                        updated = pd.concat([existing, new_row], ignore_index=True)
                        conn.update(worksheet=t, data=updated)
                    
                    st.success("저장되었습니다!")
                    st.rerun()

        # --- 3. 목록 섹션 ---
        st.write("---")
        st.subheader("📋 최근 목록")
        current_df = df_bum if user == "beom" else df_jyeon
        if not current_df.empty:
            # 날짜 형식 변환 및 정렬
            current_df['날짜'] = pd.to_datetime(current_df['날짜'])
            st.dataframe(
                current_df.sort_values('날짜', ascending=False).head(15), 
                use_container_width=True,
                hide_index=True
            )
