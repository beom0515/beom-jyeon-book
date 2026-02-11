import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

# 페이지 설정: 제목만 깔끔하게
st.set_page_config(page_title="범 & 젼", layout="wide")

# CSS: 모바일에서 카드 형태로 보이게 하고 폰트 크기 조절
st.markdown("""
    <style>
    /* 전체 폰트 및 배경 */
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    .main { padding: 1rem; }
    
    /* 달력 디자인 */
    .cal-day { border: 1px solid #eee; height: 85px; padding: 3px; border-radius: 8px; background-color: #fdfdfd; }
    .cal-date { font-weight: bold; font-size: 0.9rem; margin-bottom: 2px; }
    .cal-exp { color: #ff4b4b; font-size: 0.75rem; font-weight: bold; }
    .cal-inc { color: #1f77b4; font-size: 0.75rem; font-weight: bold; }
    .today-marker { background-color: #fff9e6; border: 2px solid #ffcc00; }
    
    /* 모바일 리스트 카드 디자인 */
    .record-card {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #007bff;
    }
    .record-row { margin-bottom: 4px; font-size: 0.95rem; }
    .record-label { color: #666; font-size: 0.8rem; margin-right: 8px; }
    .record-amount { font-weight: bold; color: #333; font-size: 1.1rem; }
    
    /* 버튼 및 입력창 모바일 최적화 */
    .stButton>button { width: 100%; border-radius: 8px; }
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

def format_man(amount):
    if amount == 0: return "0"
    return f"{round(amount / 10000, 1)}만"

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
            cols = st.columns(7)
            days = ["월", "화", "수", "목", "금", "토", "일"]
            for j in range(7): cols[j].markdown(f"<center><small>{days[j]}</small></center>", unsafe_allow_html=True)

            for week in cal:
                w_cols = st.columns(7)
                for idx, day in enumerate(week):
                    if day != 0:
                        curr = date(st.session_state.view_year, st.session_state.view_month, day)
                        d_df = df[df['날짜'] == curr] if not df.empty else pd.DataFrame()
                        inc = d_df[d_df['구분'] == '수입']['금액'].sum()
                        exp = d_df[d_df['구분'] != '수입']['금액'].sum()
                        is_t = "today-marker" if curr == date.today() else ""
                        with w_cols[idx]:
                            itxt = f"<div class='cal-inc'>{format_man(inc)}</div>" if inc > 0 else ""
                            etxt = f"<div class='cal-exp'>{format_man(exp)}</div>" if exp > 0 else ""
                            st.markdown(f"<div class='cal-day {is_t}'><div class='cal-date'>{day}</div>{itxt}{etxt}</div>", unsafe_allow_html=True)
        else:
            if not df.empty:
                display_df = df.sort_values('날짜', ascending=False).reset_index()
                for idx, row in display_df.iterrows():
                    # 📱 모바일용 카드 레이아웃
                    with st.container():
                        st.markdown(f"""
                        <div class="record-card">
                            <div class="record-row"><span class="record-label">날짜</span><b>{row['날짜']}</b></div>
                            <div class="record-row"><span class="record-label">구분</span>{row['구분']}</div>
                            <div class="record-row"><span class="record-label">카테고리</span>{row['카테고리']}</div>
                            <div class="record-row"><span class="record-label">금액</span><span class="record-amount">{format_won(row['금액'])}</span></div>
                            <div class="record-row"><span class="record-label">상세</span>{row['내역']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("🗑️ 삭제", key=f"del_{user}_{idx}"):
                            new_df = df.drop(row['index'])
                            conn.update(worksheet=user, data=new_df)
                            st.rerun()
            else: st.info("내역 없음")

        st.write("---")
        # ✅ '+ 내역 추가' 대신 '+'만 사용
        with st.expander("+", expanded=True):
            sel_d = st.date_input("날짜", value=date.today(), key=f"date_{user}")
            m_t = st.selectbox("구분", ["우리", "범지출", "젼지출", "수입"], key=f"type_{user}")
            c_list = ["용돈", "기타"] if m_t == "수입" else ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"]
            m_c = st.selectbox("카테고리", c_list, key=f"cat_{user}")
            m_a = st.number_input("금액(원)", min_value=0, step=1000, key=f"amt_{user}")
            m_i = st.text_input("상세 내역", key=f"item_{user}")
            if st.button("입력", key=f"save_{user}"):
                new_data = pd.DataFrame([{"날짜": sel_d.strftime("%Y-%m-%d"), "구분": m_t, "카테고리": m_c, "내역": m_i, "금액": m_a}])
                targets = ["beom", "jyeon"] if m_t == "우리" else (["beom"] if m_t == "범지출" else (["jyeon"] if m_t == "젼지출" else [user]))
                for t in targets:
                    current_df = load_data(t)
                    updated_df = pd.concat([current_df, new_data], ignore_index=True)
                    conn.update(worksheet=t, data=updated_df)
                st.rerun()
# 데이터가 있거나 '구분' 컬럼이 존재할 때만 계산
                        if not d_df.empty and '구분' in d_df.columns:
                            inc = d_df[d_df['구분'] == '수입']['금액'].sum()
                            exp = d_df[d_df['구분'] != '수입']['금액'].sum()
                        else:
                            inc = 0
                            exp = 0
