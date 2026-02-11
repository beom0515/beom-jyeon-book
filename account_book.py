import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

st.set_page_config(page_title="범 & 젼", layout="wide")

# ✅ CSS: 잔액 요약 및 모바일 최적화
st.markdown("""
    <style>
    .block-container { padding: 0.5rem !important; max-width: 100% !important; }
    
    /* 잔액 요약 스타일 */
    .summary-box {
        background-color: #ffffff;
        border: 1px solid #eee;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-around;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .summary-item { display: flex; flex-direction: column; }
    .summary-label { font-size: 0.7rem; color: #888; margin-bottom: 2px; }
    .summary-value { font-size: 1rem; font-weight: bold; }
    .val-inc { color: #1f77b4; }
    .val-exp { color: #ff4b4b; }
    .val-total { color: #333; }

    /* 달력 본체 */
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

    div[data-testid="stSelectbox"] label { display: none; }
    div[data-testid="stHorizontalBlock"] { gap: 5px !important; }
    .record-card { background:#f8f9fa; padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid #007bff; }
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
        if '내역' not in df.columns: df['내역'] = ""
        return df[cols]
    except Exception: return pd.DataFrame(columns=cols)

def format_man(amount):
    if amount == 0: return ""
    val = round(amount / 10000, 1)
    return f"{int(val) if val == int(val) else val}만"

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
        
        # 데이터 필터링 (선택된 연/월)
        if not df.empty:
            df_view = df[(df['날짜'].apply(lambda x: x.year) == st.session_state.view_year) & 
                        (df['날짜'].apply(lambda x: x.month) == st.session_state.view_month)]
            total_inc = df_view[df_view['구분'] == '수입']['금액'].sum()
            total_exp = df_view[df_view['구분'] != '수입']['금액'].sum()
            balance = total_inc - total_exp
        else:
            total_inc, total_exp, balance = 0, 0, 0

        if v_mode == "📅":
            # ✅ 1. 잔액 요약란 추가
            st.markdown(f"""
                <div class="summary-box">
                    <div class="summary-item"><span class="summary-label">수입</span><span class="summary-value val-inc">+{total_inc:,}</span></div>
                    <div class="summary-item"><span class="summary-label">지출</span><span class="summary-value val-exp">-{total_exp:,}</span></div>
                    <div class="summary-item"><span class="summary-label">잔액</span><span class="summary-value val-total">{balance:,}</span></div>
                </div>
            """, unsafe_allow_html=True)

            # 2. 연/월 선택
            sel_col1, sel_col2 = st.columns(2)
            with sel_col1:
                year_list = list(range(2024, 2031))
                st.session_state.view_year = st.selectbox("Y", year_list, index=year_list.index(st.session_state.view_year), key=f"sel_y_{user}")
            with sel_col2:
                month_list = list(range(1, 13))
                st.session_state.view_month = st.selectbox("M", month_list, index=month_list.index(st.session_state.view_month), key=f"sel_m_{user}")

            # 3. 달력
            cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
            grid_html = '<div class="calendar-grid">'
            for d in ["월", "화", "수", "목", "금", "토", "일"]:
                grid_html += f'<div class="day-header">{d}</div>'
            for week in cal:
                for day in week:
                    if day != 0:
                        curr = date(st.session_state.view_year, st.session_state.view_month, day)
                        d_df = df_view[df_view['날짜'] == curr] if not df_view.empty else pd.DataFrame()
                        inc = d_df[d_df['구분'] == '수입']['금액'].sum()
                        exp = d_df[d_df['구분'] != '수입']['금액'].sum()
                        is_t = "today-marker" if curr == date.today() else ""
                        grid_html += f'<div class="cal-day {is_t}"><div class="cal-date">{day}</div>'
                        grid_html += f'<div class="cal-inc">{format_man(inc)}</div>' if inc > 0 else ""
                        grid_html += f'<div class="cal-exp">{format_man(exp)}</div>' if exp > 0 else ""
                        grid_html += '</div>'
                    else: grid_html += '<div class="cal-day" style="border:none; background:none;"></div>'
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)
            
        else:
            # 목록 보기
            if not df_view.empty:
                display_df = df_view.sort_values('날짜', ascending=False)
                for idx, row in display_df.iterrows():
                    st.markdown(f"""<div class="record-card">
                        <div style="font-size:0.85rem;"><b>{row['날짜']}</b> | {row['구분']}</div>
                        <div style="font-size:1rem; font-weight:bold;">{row['금액']:,}원 ({row['카테고리']})</div>
                        <div style="font-size:0.8rem; color:#666;">📝 {row['내역']}</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{user}_{idx}"):
                        full_df = load_data(user)
                        # 원본 데이터에서 해당 행 찾아서 삭제 (날짜, 구분, 내역, 금액 일치 확인)
                        drop_idx = full_df[(full_df['날짜']==row['날짜']) & (full_df['금액']==row['금액']) & (full_df['내역']==row['내역'])].index
                        if not drop_idx.empty:
                            new_df = full_df.drop(drop_idx[0])
                            conn.update(worksheet=user, data=new_df)
                            st.rerun()
            else: st.info("내역 없음")

        st.write("---")
        with st.expander("+ 내역 추가", expanded=True):
            sel_d = st.date_input("날짜", value=date.today(), key=f"date_{user}")
            m_t = st.selectbox("구분", ["우리", "범지출", "젼지출", "수입"], key=f"type_{user}")
            c_list = ["용돈", "기타"] if m_t == "수입" else ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"]
            m_c = st.selectbox("카테고리", c_list, key=f"cat_{user}")
            m_a = st.number_input("금액(원)", min_value=0, step=1000, key=f"amt_{user}")
            m_i = st.text_input("상세내역", key=f"info_{user}")
            
            if st.button("저장", key=f"save_{user}", use_container_width=True):
                final_info = m_i if m_i.strip() != "" else m_c
                if m_t == "우리":
                    split_amt = int(m_a // 2)
                    new_row = pd.DataFrame([{"날짜": sel_d.strftime("%Y-%m-%d"), "구분": "우리", "카테고리": m_c, "내역": final_info, "금액": split_amt}])
                    targets = ["beom", "jyeon"]
                else:
                    new_row = pd.DataFrame([{"날짜": sel_d.strftime("%Y-%m-%d"), "구분": m_t, "카테고리": m_c, "내역": final_info, "금액": m_a}])
                    targets = [user]

                for t in targets:
                    curr_df = load_data(t)
                    upd_df = pd.concat([curr_df, new_row], ignore_index=True)
                    conn.update(worksheet=t, data=upd_df)
                st.rerun()
