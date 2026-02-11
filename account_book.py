import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

st.set_page_config(page_title="📔", layout="wide")

# --- CSS (디자인 깔끔하게) ---
st.markdown("""
    <style>
    .cal-day { border: 1px solid #eee; height: 95px; padding: 5px; border-radius: 8px; background-color: #fdfdfd; }
    .cal-date { font-weight: bold; font-size: 1rem; margin-bottom: 2px; }
    .cal-exp { color: #ff4b4b; font-size: 0.8rem; font-weight: bold; }
    .cal-inc { color: #1f77b4; font-size: 0.8rem; font-weight: bold; }
    .today-marker { background-color: #fff9e6; border: 2px solid #ffcc00; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        df['금액'] = pd.to_numeric(df['금액'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])

if 'view_year' not in st.session_state: st.session_state.view_year = datetime.now().year
if 'view_month' not in st.session_state: st.session_state.view_month = datetime.now().month

def change_month(delta):
    new_month = st.session_state.view_month + delta
    if new_month > 12: st.session_state.view_year += 1; st.session_state.view_month = 1
    elif new_month < 1: st.session_state.view_year -= 1; st.session_state.view_month = 12
    else: st.session_state.view_month = new_month

st.title("📔")

# 탭 이름을 사용자님 요청대로 소문자로 설정
names = ["beom", "jyeon"]
tabs = st.tabs(names)

for i, tab in enumerate(tabs):
    user = names[i]
    with tab:
        df = load_data(user)
        v_mode = st.radio("Mode", ["📅", "📋"], horizontal=True, key=f"m_{user}")
        
        if v_mode == "📅":
            c1, c2, c3 = st.columns([1, 3, 1])
            with c1: 
                if st.button("◀", key=f"p_{user}"): change_month(-1); st.rerun()
            with c2: st.markdown(f"### <center>{st.session_state.view_year} / {st.session_state.view_month}</center>", unsafe_allow_html=True)
            with c3: 
                if st.button("▶", key=f"n_{user}"): change_month(1); st.rerun()

            cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
            days_h = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            h_cols = st.columns(7)
            for idx, d_name in enumerate(days_h): h_cols[idx].markdown(f"<center>{d_name}</center>", unsafe_allow_html=True)

            for week in cal:
                w_cols = st.columns(7)
                for idx, day in enumerate(week):
                    if day != 0:
                        curr = date(st.session_state.view_year, st.session_state.view_month, day)
                        d_df = df[df['날짜'] == curr]
                        inc = d_df[d_df['구분'] == '수입']['금액'].sum()
                        exp = d_df[d_df['구분'] != '수입']['금액'].sum()
                        is_t = "today-marker" if curr == date.today() else ""
                        with w_cols[idx]:
                            itxt = f"<div class='cal-inc'>+{int(inc/10000)}m</div>" if inc >= 10000 else ""
                            etxt = f"<div class='cal-exp'>-{int(exp/10000)}m</div>" if exp >= 10000 else ""
                            st.markdown(f"<div class='cal-day {is_t}'><div class='cal-date'>{day}</div>{itxt}{etxt}</div>", unsafe_allow_html=True)
        else:
            st.dataframe(df.sort_values('날짜', ascending=False), use_container_width=True, hide_index=True)

        st.write("---")
        with st.expander("+", expanded=True):
            sel_d = st.date_input("Date", value=date.today(), key=f"sd_{user}")
            m_t = st.selectbox("Type", ["범지출", "젼지출", "우리", "수입"], key=f"mt_{user}")
            
            # 수입일 때 카테고리 즉시 변경
            c_list = ["용돈", "기타"] if m_t == "수입" else ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"]
            
            m_c = st.selectbox("Category", c_list, key=f"mc_{user}")
            m_i = st.text_input("Item", key=f"mi_{user}")
            m_a = st.number_input("Amount", min_value=0, step=1000, key=f"ma_{user}")
            
            if st.button("입력", key=f"btn_{user}"):
                new = pd.DataFrame([{"날짜": sel_d.strftime("%Y-%m-%d"), "구분": m_t, "카테고리": m_c, "내역": m_i, "금액": m_a}])
                
                # 저장 로직
                if m_t == "우리": tgs = ["beom", "jyeon"]
                elif m_t == "범지출": tgs = ["beom"]
                elif m_t == "젼지출": tgs = ["jyeon"]
                else: tgs = [user]
                
                for t in tgs:
                    current_df = conn.read(worksheet=t, ttl=0)
                    up_df = pd.concat([current_df, new], ignore_index=True)
                    conn.update(worksheet=t, data=up_df)
                st.success("OK")
                st.rerun()
