import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

st.set_page_config(page_title="📔 가계부", layout="wide")

# CSS: 디자인
st.markdown("""
    <style>
    .cal-day { border: 1px solid #eee; height: 100px; padding: 5px; border-radius: 8px; background-color: #fdfdfd; }
    .cal-date { font-weight: bold; font-size: 1rem; margin-bottom: 2px; }
    .cal-exp { color: #ff4b4b; font-size: 0.85rem; font-weight: bold; }
    .cal-inc { color: #1f77b4; font-size: 0.85rem; font-weight: bold; }
    .today-marker { background-color: #fff9e6; border: 2px solid #ffcc00; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        df['금액'] = pd.to_numeric(df['금액'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])

# ✅ 달력용: 0.0만 형식 함수
def format_man(amount):
    if amount == 0: return "0"
    return f"{round(amount / 10000, 1)}만"

# ✅ 목록용: 원 단위 콤마 형식 함수
def format_won(amount):
    return f"{amount:,}원"

if 'view_year' not in st.session_state: st.session_state.view_year = datetime.now().year
if 'view_month' not in st.session_state: st.session_state.view_month = datetime.now().month

def change_month(delta):
    new_month = st.session_state.view_month + delta
    if new_month > 12: st.session_state.view_year += 1; st.session_state.view_month = 1
    elif new_month < 1: st.session_state.view_year -= 1; st.session_state.view_month = 12
    else: st.session_state.view_month = new_month

st.title("📔 범 & 젼")
names = ["beom", "jyeon"]
tabs = st.tabs(["범", "젼"])

for i, tab in enumerate(tabs):
    user = names[i]
    with tab:
        df = load_data(user)
        v_mode = st.radio("보기", ["📅", "📋"], horizontal=True, key=f"v_mode_{user}", label_visibility="collapsed")
        
        if v_mode == "📅":
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1: 
                if st.button("◀", key=f"prev_{user}"): change_month(-1); st.rerun()
            with c2: st.markdown(f"### <center>{st.session_state.view_year}. {st.session_state.view_month}</center>", unsafe_allow_html=True)
            with c3: 
                if st.button("▶", key=f"next_{user}"): change_month(1); st.rerun()

            cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
            h_cols = st.columns(7)
            for idx, d_n in enumerate(["월", "화", "수", "목", "금", "토", "일"]): 
                h_cols[idx].markdown(f"<center>{d_n}</center>", unsafe_allow_html=True)

            for week in cal:
                w_cols = st.columns(7)
                for idx, day in enumerate(week):
                    if day != 0:
                        curr = date(st.session_state.view_year, st.session_state.view_month, day)
                        d_df = df[df['날짜'] == curr] if not df.empty else pd.DataFrame()
                        inc = d_df[d_df['구분'] == '수입']['금액'].sum() if not d_df.empty else 0
                        exp = d_df[d_df['구분'] != '수입']['금액'].sum() if not d_df.empty else 0
                        is_t = "today-marker" if curr == date.today() else ""
                        with w_cols[idx]:
                            # 📅 달력에만 '만' 단위 적용
                            itxt = f"<div class='cal-inc'>{format_man(inc)}</div>" if inc > 0 else ""
                            etxt = f"<div class='cal-exp'>{format_man(exp)}</div>" if exp > 0 else ""
                            st.markdown(f"<div class='cal-day {is_t}'><div class='cal-date'>{day}</div>{itxt}{etxt}</div>", unsafe_allow_html=True)
        else:
            if not df.empty:
                display_df = df.sort_values('날짜', ascending=False).reset_index()
                for idx, row in display_df.iterrows():
                    c1, c2, c3, c4, c5, c6 = st.columns([2, 1.5, 1.5, 3, 2, 1])
                    c1.write(row['날짜'])
                    c2.write(f"**{row['구분']}**")
                    c3.write(row['카테고리'])
                    c4.write(row['내역'])
                    # 📋 목록에는 정확한 '원' 단위 적용
                    c5.write(f"{format_won(row['금액'])}")
                    if c6.button("🗑️", key=f"del_{user}_{idx}"):
                        new_df = df.drop(row['index'])
                        conn.update(worksheet=user, data=new_df)
                        st.rerun()
            else: st.info("내역 없음")

        st.write("---")
        with st.expander("➕ 내역 추가", expanded=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                sel_d = st.date_input("날짜", value=date.today(), key=f"date_{user}")
                m_t = st.selectbox("구분", ["우리", "범지출", "젼지출", "수입"], key=f"type_{user}")
            with f_col2:
                c_list = ["용돈", "기타"] if m_t == "수입" else ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"]
                m_c = st.selectbox("카테고리", c_list, key=f"cat_{user}")
                m_a = st.number_input("금액(원)", min_value=0, step=1000, key=f"amt_{user}")
            m_i = st.text_input("상세 내역", key=f"item_{user}")
            if st.button("입력", key=f"save_{user}", use_container_width=True):
                new_data = pd.DataFrame([{"날짜": sel_d.strftime("%Y-%m-%d"), "구분": m_t, "카테고리": m_c, "내역": m_i, "금액": m_a}])
                targets = ["beom", "jyeon"] if m_t == "우리" else (["beom"] if m_t == "범지출" else (["jyeon"] if m_t == "젼지출" else [user]))
                for t in targets:
                    current_df = load_data(t)
                    updated_df = pd.concat([current_df, new_data], ignore_index=True)
                    conn.update(worksheet=t, data=updated_df)
                st.rerun()
