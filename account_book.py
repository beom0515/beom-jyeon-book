import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

st.set_page_config(page_title="범 & 젼 만년 가계부", layout="wide")

# --- 달력 칸 스타일 ---
st.markdown("""
    <style>
    .cal-day { border: 1px solid #eee; height: 90px; padding: 5px; border-radius: 8px; background-color: #fdfdfd; }
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
        return df
    except:
        return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])

# --- 세션 상태로 현재 보고 있는 연/월 관리 (만년 달력의 핵심) ---
if 'view_year' not in st.session_state:
    st.session_state.view_year = datetime.now().year
if 'view_month' not in st.session_state:
    st.session_state.view_month = datetime.now().month

def change_month(delta):
    new_month = st.session_state.view_month + delta
    if new_month > 12:
        st.session_state.view_month = 1
        st.session_state.view_year += 1
    elif new_month < 1:
        st.session_state.view_month = 12
        st.session_state.view_year -= 1
    else:
        st.session_state.view_month = new_month

st.title("📔 범 & 젼 만년 달력 가계부")

tabs = st.tabs(["   범(Beom)   ", "   젼(Jyeon)   "])
names = ["beom", "jyeon"]

for i, tab in enumerate(tabs):
    user = names[i]
    with tab:
        df = load_data(user)
        
        # --- 달력 컨트롤러 (◀ 이전달 / 현재 / 다음달 ▶) ---
        c_prev, c_title, c_next = st.columns([1, 3, 1])
        with c_prev:
            if st.button("◀", key=f"prev_{user}"): change_month(-1); st.rerun()
        with c_title:
            st.markdown(f"### <center>{st.session_state.view_year}년 {st.session_state.view_month}월</center>", unsafe_allow_html=True)
        with c_next:
            if st.button("▶", key=f"next_{user}"): change_month(1); st.rerun()

        # --- 달력 판 그리기 ---
        cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
        days = ["월", "화", "수", "목", "금", "토", "일"]
        cols = st.columns(7)
        for idx, d_name in enumerate(days): cols[idx].markdown(f"<center><b>{d_name}</b></center>", unsafe_allow_html=True)

        for week in cal:
            cols = st.columns(7)
            for idx, day in enumerate(week):
                if day == 0:
                    cols[idx].write("")
                else:
                    curr_date = date(st.session_state.view_year, st.session_state.view_month, day)
                    day_data = df[df['날짜'] == curr_date]
                    
                    income = day_data[day_data['구분'] == '수입']['금액'].sum()
                    expense = day_data[day_data['구분'] != '수입']['금액'].sum()
                    
                    # 오늘 날짜 강조
                    is_today = "today-marker" if curr_date == datetime.now().date() else ""
                    
                    with cols[idx]:
                        # 0만 원일 때는 표시 안 함 (깔끔하게)
                        inc_txt = f"<div class='cal-inc'>+{int(income/10000)}만</div>" if income >= 10000 else ""
                        exp_txt = f"<div class='cal-exp'>-{int(expense/10000)}만</div>" if expense >= 10000 else ""
                        
                        st.markdown(f"""
                            <div class='cal-day {is_today}'>
                                <div class='cal-date'>{day}</div>
                                {inc_txt} {exp_txt}
                            </div>
                        """, unsafe_allow_html=True)

        # --- 입력 및 상세내역 (하단) ---
        st.write("---")
        with st.expander("➕ 내역 추가 및 상세 보기", expanded=False):
            sel_date = st.date_input("날짜 선택", value=datetime.now(), key=f"sel_{user}")
            
            # 해당 날짜 상세 내역
            day_list = df[df['날짜'] == sel_date]
            if not day_list.empty:
                st.write(f"📍 **{sel_date} 상세**")
                st.dataframe(day_list[['구분', '카테고리', '내역', '금액']], hide_index=True)
            
            st.write("**새 내역 입력**")
            with st.form(key=f"form_{user}", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1: m_type = st.selectbox("구분", ["지출", "우리", "수입"], key=f"t_{user}")
                with col2: m_cat = st.selectbox("카테고리", ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "용돈", "기타"], key=f"c_{user}")
                m_item = st.text_input("내역", key=f"i_{user}")
                m_amount = st.number_input("금액", min_value=0, step=1000, key=f"a_{user}")
                
                if st.form_submit_button("저장하기"):
                    new_row = pd.DataFrame([{"날짜": sel_date.strftime("%Y-%m-%d"), "구분": m_type, "카테고리": m_cat, "내역": m_item, "금액": m_amount}])
                    targets = names if m_type == "우리" else [user]
                    for t in targets:
                        existing = conn.read(worksheet=t, ttl=0)
                        updated = pd.concat([existing, new_row], ignore_index=True)
                        conn.update(worksheet=t, data=updated)
                    st.rerun()
