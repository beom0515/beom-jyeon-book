import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

st.set_page_config(page_title="범 & 젼", layout="wide")

# CSS 스타일
st.markdown("""
    <style>
    .block-container { padding: 0.5rem !important; max-width: 100% !important; }
    .summary-box {
        background-color: #ffffff; border: 1px solid #eee; border-radius: 8px;
        padding: 8px; margin-bottom: 10px; display: flex; justify-content: space-between;
        font-size: 0.9rem;
    }
    .summary-item { text-align: center; flex: 1; }
    .val-inc { color: #1f77b4; font-weight: bold; }
    .val-exp { color: #ff4b4b; font-weight: bold; }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        font-size: 1.1rem !important; font-weight: 700 !important; text-align: center !important;
    }
    div[data-testid="stSelectbox"] { max-width: 140px !important; margin: 5px auto !important; }

    .calendar-grid {
        display: grid; grid-template-columns: repeat(7, 1fr);
        gap: 1px; width: 100%; border: 1px solid #eee;
    }
    .day-header { font-size: 0.8rem; font-weight: bold; text-align: center; padding: 5px; background: #f8f9fa; border-bottom: 1px solid #eee; }
    .sun-holiday { color: #ff4b4b !important; } 
    .sat { color: #1f77b4 !important; } 
    
    .cal-day { 
        min-height: 65px; background: #fff; display: flex; flex-direction: column; 
        align-items: center; padding: 2px; border: 0.5px solid #f9f9f9;
    }
    .date-row { display: flex; align-items: baseline; gap: 3px; justify-content: center; width: 100%; }
    .cal-date { font-weight: bold; font-size: 0.85rem; }
    .holiday-name { font-size: 0.5rem; font-weight: normal; white-space: nowrap; }
    
    .cal-exp { color: #ff4b4b; font-size: 0.65rem; font-weight: bold; margin-top: 1px; }
    .cal-inc { color: #1f77b4; font-size: 0.65rem; font-weight: bold; }
    .today-marker { background-color: #fff9e6; border: 1.5px solid #ffcc00; }
    
    /* 목록 카드 스타일 */
    .record-card { 
        background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #eee; 
        margin-bottom: 6px; border-left: 5px solid #007bff; position: relative;
    }
    div[data-testid="stSelectbox"] label { display: none; }
    </style>
    """, unsafe_allow_html=True)

# 2026-2028 공휴일 데이터
def get_holiday_info(y, m, d):
    h = {
        2026: {(1,1):"신정", (2,16):"설날", (2,17):"설날", (2,18):"설날", (3,1):"삼일절", (3,2):"대체", (5,5):"어린이날", (5,24):"석탄일", (5,25):"대체", (6,6):"현충일", (8,15):"광복절", (8,17):"대체", (9,24):"추석", (9,25):"추석", (9,26):"추석", (10,3):"개천절", (10,5):"대체", (10,9):"한글날", (12,25):"성탄절"},
        2027: {(1,1):"신정", (2,6):"설날", (2,7):"설날", (2,8):"설날", (2,9):"대체", (3,1):"삼일절", (5,5):"어린이날", (5,13):"석탄일", (6,6):"현충일", (8,15):"광복절", (8,16):"대체", (9,14):"추석", (9,15):"추석", (9,16):"추석", (10,3):"개천절", (10,4):"대체", (10,9):"한글날", (10,11):"대체", (12,25):"성탄절"},
        2028: {(1,1):"신정", (1,26):"설날", (1,27):"설날", (1,28):"설날", (3,1):"삼일절", (5,2):"석탄일", (5,5):"어린이날", (6,6):"현충일", (8,15):"광복절", (10,2):"추석", (10,3):"개천절/추석", (10,4):"추석", (10,5):"대체", (10,9):"한글날", (12,25):"성탄절"}
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

if 'view_year' not in st.session_state: st.session_state.view_year = 2026
if 'view_month' not in st.session_state: st.session_state.view_month = 2

st.title("📔 범 & 젼")
user_tabs = st.tabs(["범", "젼"])
calendar.setfirstweekday(calendar.SUNDAY)

for i, user in enumerate(["beom", "jyeon"]):
    with user_tabs[i]:
        df = load_data(user)
        v_mode = st.radio("모드", ["📅", "📋"], horizontal=True, key=f"v_{user}", label_visibility="collapsed")
        
        # 상단 연/월 선택
        c1, c2 = st.columns(2)
        with c1: 
            y_list = [f"{y}년" for y in range(2024, 2029)]
            sel_y = st.selectbox("Y", y_list, index=y_list.index(f"{st.session_state.view_year}년"), key=f"y_{user}")
            st.session_state.view_year = int(sel_y.replace("년", ""))
        with c2:
            sel_m = st.selectbox("M", [f"{m}월" for m in range(1, 13)], index=st.session_state.view_month-1, key=f"m_{user}")
            st.session_state.view_month = int(sel_m.replace("월", ""))

        df_view = df[(df['날짜'].apply(lambda x: x.year) == st.session_state.view_year) & (df['날짜'].apply(lambda x: x.month) == st.session_state.view_month)] if not df.empty else pd.DataFrame()
        t_inc, t_exp = df_view[df_view['구분'] == '수입']['금액'].sum(), df_view[df_view['구분'] != '수입']['금액'].sum()

        st.markdown(f'<div class="summary-box"><div class="summary-item">수입 <span class="val-inc">+{t_inc:,}</span></div><div class="summary-item">지출 <span class="val-exp">-{t_exp:,}</span></div><div class="summary-item">잔액 <b>{t_inc-t_exp:,}</b></div></div>', unsafe_allow_html=True)

        if v_mode == "📅":
            # 달력 모드
            cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
            grid = '<div class="calendar-grid">'
            for idx, h in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
                grid += f'<div class="day-header {"sun-holiday" if idx==0 else ("sat" if idx==6 else "")}">{h}</div>'
            for week in cal:
                for idx, day in enumerate(week):
                    if day != 0:
                        h_name = get_holiday_info(st.session_state.view_year, st.session_state.view_month, day)
                        d_cls = "sun-holiday" if (idx == 0 or h_name) else ("sat" if idx == 6 else "")
                        curr_d = date(st.session_state.view_year, st.session_state.view_month, day)
                        d_df = df_view[df_view['날짜'] == curr_d] if not df_view.empty else pd.DataFrame()
                        inc, exp = d_df[d_df['구분'] == '수입']['금액'].sum(), d_df[d_df['구분'] != '수입']['금액'].sum()
                        grid += f'<div class="cal-day {"today-marker" if curr_d==date.today() else ""}">'
                        grid += f'<div class="date-row"><div class="cal-date {d_cls}">{day}</div>'
                        if h_name: grid += f'<div class="holiday-name {d_cls}">{h_name}</div>'
                        grid += f'</div>'
                        if inc > 0: grid += f'<div class="cal-inc">{format_man(inc)}</div>'
                        if exp > 0: grid += f'<div class="cal-exp">{format_man(exp)}</div>'
                        grid += '</div>'
                    else: grid += '<div class="cal-day" style="background:none; border:none;"></div>'
            st.markdown(grid + '</div>', unsafe_allow_html=True)
            
        else:
            # 📋 목록 모드 (삭제 버튼 포함)
            if not df_view.empty:
                df_sorted = df_view.sort_values(by="날짜", ascending=True)
                for idx, row in df_sorted.iterrows():
                    col_text, col_del = st.columns([0.85, 0.15])
                    with col_text:
                        st.markdown(f"""
                            <div class="record-card">
                                <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#666;">
                                    <span><b>{row['날짜'].strftime('%m/%d')}</b> ({row['구분']})</span>
                                    <span>{row['카테고리']}</span>
                                </div>
                                <div style="font-size:1rem; font-weight:bold; margin-top:2px;">{row['금액']:,}원</div>
                                <div style="font-size:0.75rem; color:#444;">📝 {row['내역']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    with col_del:
                        st.write("") # 간격 맞추기
                        if st.button("🗑️", key=f"del_{user}_{idx}"):
                            full_df = load_data(user)
                            # 날짜, 구분, 금액, 내역이 모두 일치하는 행 삭제
                            full_df = full_df.drop(full_df[(full_df['날짜'] == row['날짜']) & 
                                                          (full_df['구분'] == row['구분']) & 
                                                          (full_df['금액'] == row['금액']) & 
                                                          (full_df['내역'] == row['내역'])].index)
                            conn.update(worksheet=user, data=full_df)
                            st.rerun()
            else:
                st.info(f"{st.session_state.view_month}월 내역이 없습니다.")

        st.write("---")
        with st.expander("+ 내역 추가", expanded=True):
            col1, col2 = st.columns(2)
            with col1: sd = st.date_input("날짜", value=date.today(), key=f"d_{user}")
            with col2: mt = st.selectbox("구분", ["우리", "범지출", "젼지출", "수입"], key=f"t_{user}")
            clist = ["용돈", "기타"] if mt == "수입" else ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"]
            mc = st.selectbox("카테고리", clist, key=f"c_{user}")
            ma = st.number_input("금액", min_value=0, step=1000, key=f"a_{user}")
            mi = st.text_input("상세내역", key=f"i_{user}")
            if st.button("저장", key=f"s_{user}", use_container_width=True):
                info = mi if mi.strip() != "" else mc
                if mt == "우리":
                    split = int(ma // 2)
                    new_row = pd.DataFrame([{"날짜": sd, "구분": "우리", "카테고리": mc, "내역": info, "금액": split}])
                    for t in ["beom", "jyeon"]:
                        upd = pd.concat([load_data(t), new_row], ignore_index=True)
                        conn.update(worksheet=t, data=upd)
                else:
                    new_row = pd.DataFrame([{"날짜": sd, "구분": mt, "카테고리": mc, "내역": info, "금액": ma}])
                    upd = pd.concat([load_data(user), new_row], ignore_index=True)
                    conn.update(worksheet=user, data=upd)
                st.rerun()
