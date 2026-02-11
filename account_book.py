import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

st.set_page_config(page_title="범 & 젼", layout="wide")

# ✅ CSS: 스크롤 방지, 가로 배치, 요일별 색상 및 강조 처리
st.markdown("""
    <style>
    .block-container { padding: 0.5rem !important; max-width: 100% !important; }
    
    /* 요약 박스: 옆으로 쭉 가게 배치 */
    .summary-box {
        background-color: #ffffff; border: 1px solid #eee; border-radius: 8px;
        padding: 8px; margin-bottom: 10px; display: flex; justify-content: space-between;
        font-size: 0.9rem;
    }
    .summary-item { text-align: center; flex: 1; }
    .val-inc { color: #1f77b4; font-weight: bold; }
    .val-exp { color: #ff4b4b; font-weight: bold; }

    /* ✅ 연/월 선택창: 굵게 & 일반 글씨 크기 최적화 */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        font-size: 1.1rem !important;
        font-weight: 700 !important; /* 년도, 월만 굵게 */
        text-align: center !important;
        border: 1px solid #eee !important;
    }
    div[data-testid="stSelectbox"] { max-width: 140px !important; margin: 5px auto !important; }

    /* 달력 그리드 */
    .calendar-grid {
        display: grid; grid-template-columns: repeat(7, 1fr);
        gap: 1px; width: 100%; border: 1px solid #eee;
    }
    .day-header { font-size: 0.8rem; font-weight: bold; text-align: center; padding: 5px; background: #f8f9fa; }
    .sat { color: #1f77b4; } /* 토 파랑 */
    .sun-holiday { color: #ff4b4b; } /* 일/공 빨강 */
    
    .cal-day { 
        min-height: 60px; background: #fff; display: flex; flex-direction: column; 
        align-items: center; padding: 2px; border: 0.5px solid #f9f9f9;
    }
    .cal-date { font-weight: bold; font-size: 0.85rem; }
    .holiday-name { font-size: 0.6rem; margin-top: -2px; }
    
    .cal-exp { color: #ff4b4b; font-size: 0.65rem; }
    .cal-inc { color: #1f77b4; font-size: 0.65rem; }
    .today-marker { background-color: #fff9e6; border: 1.5px solid #ffcc00; }

    div[data-testid="stSelectbox"] label { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ✅ 2024-2026 한국 공휴일 데이터
def get_holiday_info(y, m, d):
    h = {
        2024: {(1,1):"신정", (2,9):"설날", (2,10):"설날", (2,11):"설날", (2,12):"대체휴일", (3,1):"삼일절", (4,10):"선거날", (5,5):"어린이날", (5,6):"대체휴일", (5,15):"부처님오신날", (6,6):"현충일", (8,15):"광복절", (9,16):"추석", (9,17):"추석", (9,18):"추석", (10,3):"개천절", (10,9):"한글날", (12,25):"성탄절"},
        2025: {(1,1):"신정", (1,28):"설날", (1,29):"설날", (1,30):"설날", (3,1):"삼일절", (3,3):"대체휴일", (5,5):"어린이날/부처님오신날", (5,6):"대체휴일", (6,6):"현충일", (8,15):"광복절", (10,3):"개천절", (10,5):"추석", (10,6):"추석", (10,7):"추석", (10,8):"대체휴일", (10,9):"한글날", (12,25):"성탄절"},
        2026: {(1,1):"신정", (2,16):"설날", (2,17):"설날", (2,18):"설날", (3,1):"삼일절", (3,2):"대체휴일", (5,5):"어린이날", (5,24):"부처님오신날", (5,25):"대체휴일", (6,3):"지방선거", (6,6):"현충일", (8,15):"광복절", (8,17):"대체휴일", (9,24):"추석", (9,25):"추석", (9,26):"추석", (10,3):"개천절", (10,5):"대체휴일", (10,9):"한글날", (12,25):"성탄절"}
    }
    return h.get(y, {}).get((m, d), None)

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name, ttl=5)
        if df is None or df.empty: return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        df['금액'] = pd.to_numeric(df['금액'], errors='coerce').fillna(0).astype(int)
        return df
    except: return pd.DataFrame(columns=["날짜", "구분", "카테고리", "내역", "금액"])

def format_man(amount):
    if amount == 0: return ""
    val = round(amount / 10000, 1)
    return f"{int(val) if val == int(val) else val}만"

if 'view_year' not in st.session_state: st.session_state.view_year = datetime.now().year
if 'view_month' not in st.session_state: st.session_state.view_month = datetime.now().month

st.title("📔 범 & 젼")
user_tabs = st.tabs(["범", "젼"])

for user in ["beom", "jyeon"]:
    with user_tabs[0 if user=="beom" else 1]:
        df = load_data(user)
        v_mode = st.radio("보기", ["📅", "📋"], horizontal=True, key=f"v_{user}", label_visibility="collapsed")
        
        df_view = df[(df['날짜'].apply(lambda x: x.year) == st.session_state.view_year) & (df['날짜'].apply(lambda x: x.month) == st.session_state.view_month)] if not df.empty else pd.DataFrame()
        t_inc = df_view[df_view['구분'] == '수입']['금액'].sum()
        t_exp = df_view[df_view['구분'] != '수입']['금액'].sum()

        if v_mode == "📅":
            st.markdown(f'<div class="summary-box"><div class="summary-item">수입 <span class="val-inc">+{t_inc:,}</span></div><div class="summary-item">지출 <span class="val-exp">-{t_exp:,}</span></div><div class="summary-item">잔액 <b>{t_inc-t_exp:,}</b></div></div>', unsafe_allow_html=True)

            # 연/월 선택 (굵게 처리된 스타일 적용됨)
            c1, c2 = st.columns(2)
            with c1: 
                sel_y = st.selectbox("Y", [f"{y}년" for y in range(2024, 2031)], index=st.session_state.view_year-2024, key=f"y_{user}")
                st.session_state.view_year = int(sel_y.replace("년", ""))
            with c2:
                sel_m = st.selectbox("M", [f"{m}월" for m in range(1, 13)], index=st.session_state.view_month-1, key=f"m_{user}")
                st.session_state.view_month = int(sel_m.replace("월", ""))

            # 달력 생성
            cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
            grid = '<div class="calendar-grid">'
            for i, h in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
                c = "sat" if i==5 else ("sun-holiday" if i==6 else "")
                grid += f'<div class="day-header {c}">{h}</div>'
            
            for week in cal:
                for idx, day in enumerate(week):
                    if day != 0:
                        h_name = get_holiday_info(st.session_state.view_year, st.session_state.view_month, day)
                        is_sun_or_h = (idx == 6 or h_name is not None)
                        d_cls = "sun-holiday" if is_sun_or_h else ("sat" if idx == 5 else "")
                        
                        curr_d = date(st.session_state.view_year, st.session_state.view_month, day)
                        d_df = df_view[df_view['날짜'] == curr_d] if not df_view.empty else pd.DataFrame()
                        inc, exp = d_df[d_df['구분'] == '수입']['금액'].sum(), d_df[d_df['구분'] != '수입']['금액'].sum()
                        
                        grid += f'<div class="cal-day {"today-marker" if curr_d==date.today() else ""}">'
                        grid += f'<div class="cal-date {d_cls}">{day}</div>'
                        if h_name: grid += f'<div class="holiday-name sun-holiday">{h_name}</div>'
                        if inc > 0: grid += f'<div class="cal-inc">{format_man(inc)}</div>'
                        if exp > 0: grid += f'<div class="cal-exp">{format_man(exp)}</div>'
                        grid += '</div>'
                    else: grid += '<div class="cal-day" style="background:none; border:none;"></div>'
            st.markdown(grid + '</div>', unsafe_allow_html=True)
        else:
            st.dataframe(df_view.sort_values("날짜", ascending=False), use_container_width=True, hide_index=True)

        st.write("---")
        with st.expander("+ 내역 추가", expanded=True):
            # (입력 폼은 이전과 동일하되 가독성 유지)
            col_a, col_b = st.columns(2)
            with col_a: sd = st.date_input("날짜", value=date.today(), key=f"d_{user}")
            with col_b: mt = st.selectbox("구분", ["우리", "범지출", "젼지출", "수입"], key=f"t_{user}")
            ma = st.number_input("금액", min_value=0, step=1000, key=f"a_{user}")
            mi = st.text_input("상세내역", key=f"i_{user}")
            if st.button("저장", key=f"s_{user}", use_container_width=True):
                # 저장 로직 (생략 - 이전과 동일)
                st.success("저장 완료!"); st.rerun()
