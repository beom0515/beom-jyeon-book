import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

st.set_page_config(page_title="범 & 젼", layout="wide")

# ✅ CSS: 모바일 사파리 맞춤형 레이아웃
st.markdown("""
    <style>
    .block-container { padding: 0.5rem !important; max-width: 100% !important; }
    
    /* 달력 본체 7열 고정 */
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 2px;
        width: 100%;
        margin-top: 10px;
    }
    .day-header { font-size: 0.75rem; font-weight: bold; text-align: center; color: #888; }
    .cal-day { 
        border: 1px solid #eee; height: 60px; border-radius: 4px; 
        background-color: #fdfdfd; display: flex; flex-direction: column; 
        align-items: center; justify-content: flex-start; padding: 2px;
    }
    .cal-date { font-weight: bold; font-size: 0.85rem; }
    .cal-exp { color: #ff4b4b; font-size: 0.65rem; font-weight: bold; }
    .cal-inc { color: #1f77b4; font-size: 0.65rem; font-weight: bold; }
    .today-marker { background-color: #fff9e6; border: 1.5px solid #ffcc00; }

    /* 선택 상자 라벨 숨기기 및 간격 조정 */
    div[data-testid="stSelectbox"] label { display: none; }
    div[data-testid="stHorizontalBlock"] { gap: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    cols = ["날짜", "구분", "카테고리", "내역", "금액"]
    try:
        df = conn.read(worksheet=sheet_name, ttl=5)
        if df is None or df.empty: return pd.DataFrame(columns=cols)
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        df['금액'] = pd.to_numeric(df['금액'], errors='coerce').fillna(0).astype(int)
        return df[cols]
    except Exception: return pd.DataFrame(columns=cols)

def format_man(amount):
    if amount == 0: return ""
    val = round(amount / 10000, 1)
    return f"{int(val) if val == int(val) else val}만"

# 현재 날짜 기준 초기화
if 'view_year' not in st.session_state: st.session_state.view_year = datetime.now().year
if 'view_month' not in st.session_state: st.session_state.view_month = datetime.now().month

st.title("📔 범 & 젼")
user_tabs = st.tabs(["범", "젼"])
names = ["beom", "jyeon"]

for i, tab in enumerate(user_tabs):
    user = names[i]
    with tab:
        df = load_data(user)
        v_mode = st.radio("보기", ["📅", "📋"], horizontal=True, key=f"v_mode_{user}", label_visibility="collapsed")
        
        if v_mode == "📅":
            # ✅ [연도/월 선택] 5:5로 배치 - 사파리에서도 이 정도는 안 깨집니다!
            sel_col1, sel_col2 = st.columns(2)
            with sel_col1:
                year_list = list(range(datetime.now().year - 1, datetime.now().year + 3))
                st.session_state.view_year = st.selectbox("연도", year_list, index=year_list.index(st.session_state.view_year), key=f"sel_y_{user}")
            with sel_col2:
                month_list = list(range(1, 13))
                st.session_state.view_month = st.selectbox("월", month_list, index=month_list.index(st.session_state.view_month), key=f"sel_m_{user}")

            # 달력 본체
            cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
            grid_html = '<div class="calendar-grid">'
            for d in ["월", "화", "수", "목", "금", "토", "일"]:
                grid_html += f'<div class="day-header">{d}</div>'
            for week in cal:
                for day in week:
                    if day != 0:
                        curr = date(st.session_state.view_year, st.session_state.view_month, day)
                        d_df = df[df['날짜'] == curr] if not df.empty else pd.DataFrame()
                        inc = d_df[d_df['구분'] == '수입']['금액'].sum() if not d_df.empty else 0
                        exp = d_df[d_df['구분'] != '수입']['금액'].sum() if not d_df.empty else 0
                        is_t = "today-marker" if curr == date.today() else ""
                        grid_html += f'<div class="cal-day {is_t}"><div class="cal-date">{day}</div>'
                        grid_html += f'<div class="cal-inc">{format_man(inc)}</div>' if inc > 0 else ""
                        grid_html += f'<div class="cal-exp">{format_man(exp)}</div>' if exp > 0 else ""
                        grid_html += '</div>'
                    else: grid_html += '<div class="cal-day" style="border:none; background:none;"></div>'
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)
            
        else:
            # 목록 보기 (생략 없이 유지)
            if not df.empty:
                display_df = df.sort_values('날짜', ascending=False).reset_index()
                for idx, row in display_df.iterrows():
                    st.markdown(f"""<div style="background:#f8f9fa; padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid #007bff;">
                        <div style="font-size:0.85rem;"><b>{row['날짜']}</b> | {row['구분']}</div>
                        <div style="font-size:1rem; font-weight:bold;">{row['금액']:,}원 ({row['카테고리']})</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{user}_{idx}"):
                        new_df = df.drop(row['index']); conn.update(worksheet=user, data=new_df); st.rerun()
            else: st.info("내역 없음")

        st.write("---")
        with st.expander("+ 추가"):
            sel_d = st.date_input("날짜", value=date.today(), key=f"date_{user}")
            m_t = st.selectbox("구분", ["우리", "범지출", "젼지출", "수입"], key=f"type_{user}")
            m_a = st.number_input("금액", min_value=0, step=1000, key=f"amt_{user}")
            if st.button("입력", key=f"save_{user}", use_container_width=True):
                new_row = pd.DataFrame([{"날짜": sel_d.strftime("%Y-%m-%d"), "구분": m_t, "카테고리": "기타", "내역": "기타", "금액": m_a}])
                targets = ["beom", "jyeon"] if m_t == "우리" else ([user])
                for t in targets:
                    curr_df = load_data(t); upd_df = pd.concat([curr_df, new_row], ignore_index=True); conn.update(worksheet=t, data=upd_df)
                st.rerun()
