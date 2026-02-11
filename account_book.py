import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

st.set_page_config(page_title="가계부", layout="wide")

# --- CSS 스타일 (한글 최소화, 디자인 깔끔하게) ---
st.markdown("""
    <style>
    .cal-day { border: 1px solid #eee; height: 90px; padding: 5px; border-radius: 8px; background-color: #fdfdfd; }
    .cal-date { font-weight: bold; font-size: 1rem; margin-bottom: 2px; }
    .cal-exp { color: #ff4b4b; font-size: 0.8rem; font-weight: bold; }
    .cal-inc { color: #1f77b4; font-size: 0.8rem; font-weight: bold; }
    .today-marker { background-color: #fff9e6; border: 2px solid #ffcc00; }
    [data-testid="stExpander"] p { font-size: 0px; } /* 한글 텍스트 숨기기 */
    </style>
    """, unsafe_allow_html=True)

# 구글 시트 연결 (가장 확실한 연결 방식)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        # 시트 이름을 명시적으로 지정하여 읽기
        df = conn.read(worksheet=sheet_name, ttl=0)
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        df['금액'] = pd.to_numeric(df['금액'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])

# 연/월 상태 관리
if 'view_year' not in st.session_state: st.session_state.view_year = datetime.now().year
if 'view_month' not in st.session_state: st.session_state.view_month = datetime.now().month

def change_month(delta):
    new_month = st.session_state.view_month + delta
    if new_month > 12:
        st.session_state.view_month = 1; st.session_state.view_year += 1
    elif new_month < 1:
        st.session_state.view_month = 12; st.session_state.view_year -= 1
    else:
        st.session_state.view_month = new_month

# 메인 화면 구성
st.title("📔") # 한글 삭제

tabs = st.tabs(["Bum", "Jyeon"]) # 영어로 변경
names = ["beom", "jyeon"]

for i, tab in enumerate(tabs):
    user = names[i]
    with tab:
        df = load_data(user)
        
        # 보기 방식 선택 (그림 위주)
        view_mode = st.radio("Mode", ["📅", "📋"], horizontal=True, key=f"mode_{user}")
        
        if view_mode == "📅":
            c_prev, c_title, c_next = st.columns([1, 3, 1])
            with c_prev:
                if st.button("◀", key=f"prev_{user}"): change_month(-1); st.rerun()
            with c_title:
                st.markdown(f"### <center>{st.session_state.view_year} / {st.session_state.view_month}</center>", unsafe_allow_html=True)
            with c_next:
                if st.button("▶", key=f"next_{user}"): change_month(1); st.rerun()

            cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
            cols = st.columns(7)
            for idx, d_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]): 
                cols[idx].markdown(f"<center>{d_name}</center>", unsafe_allow_html=True)

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
                        is_today = "today-marker" if curr_date == datetime.now().date() else ""
                        
                        with cols[idx]:
                            inc_txt = f"<div class='cal-inc'>+{int(income/10000)}m</div>" if income >= 10000 else ""
                            exp_txt = f"<div class='cal-exp'>-{int(expense/10000)}m</div>" if expense >= 10000 else ""
                            st.markdown(f"<div class='cal-day {is_today}'><div class='cal-date'>{day}</div>{inc_txt}{exp_txt}</div>", unsafe_allow_html=True)
        else:
            st.dataframe(df.sort_values(by='날짜', ascending=False), use_container_width=True, hide_index=True)

        st.write("---")
        # + 옆의 한글 삭제
        with st.expander("+", expanded=True):
            with st.form(key=f"form_{user}", clear_on_submit=True):
                sel_date = st.date_input("Date", value=datetime.now(), key=f"sel_{user}")
                
                # 구분: 수입, 우리, 범지출, 젼지출
                m_type = st.selectbox("Type", ["범지출", "젼지출", "우리", "수입"], key=f"t_{user}")
                
                # 카테고리 로직 반영
                if m_type == "수입":
                    cats = ["용돈", "기타"]
                else:
                    cats = ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"]
                
                m_cat = st.selectbox("Category", cats, key=f"c_{user}")
                m_item = st.text_input("Item", key=f"i_{user}")
                m_amount = st.number_input("Amount", min_value=0, step=1000, key=f"a_{user}")
                
                # '입력'으로 버튼 이름 변경
                if st.form_submit_button("입력"):
                    new_row = pd.DataFrame([{"날짜": sel_date.strftime("%Y-%m-%d"), "구분": m_type, "카테고리": m_cat, "내역": m_item, "금액": m_amount}])
                    
                    # 저장 로직 (중요!)
                    if m_type == "우리":
                        targets = ["beom", "jyeon"]
                    elif m_type == "범지출":
                        targets = ["beom"]
                    elif m_type == "젼지출":
                        targets = ["jyeon"]
                    else: # 수입 (현재 탭 주인이 가져감)
                        targets = [user]
                    
                    for t in targets:
                        # 매번 최신 데이터를 읽어와서 합침 (연결 끊김 방지)
                        current_df = conn.read(worksheet=t, ttl=0)
                        updated_df = pd.concat([current_df, new_row], ignore_index=True)
                        conn.update(worksheet=t, data=updated_df)
                    
                    st.rerun()
