import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import calendar

st.set_page_config(page_title="범 & 젼 달력 가계부", layout="wide")

# --- 달력 디자인용 CSS ---
st.markdown("""
    <style>
    .cal-day { border: 1px solid #eee; height: 80px; padding: 5px; border-radius: 5px; font-size: 0.8rem; }
    .cal-date { font-weight: bold; margin-bottom: 2px; }
    .cal-exp { color: #ff4b4b; font-size: 0.75rem; }
    .cal-inc { color: #31333f; font-size: 0.75rem; font-weight: bold; }
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

st.title("📅 범 & 젼 만년달력 대시보드")

tabs = st.tabs(["   범(Beom)   ", "   젼(Jyeon)   "])
names = ["beom", "jyeon"]

for i, tab in enumerate(tabs):
    user = names[i]
    with tab:
        df = load_data(user)
        now = datetime.now()
        
        # --- [중요] 큼직한 한달 달력 판 그리기 ---
        st.subheader(f"🗓️ {now.year}년 {now.month}월 지출 현황")
        
        cal = calendar.monthcalendar(now.year, now.month)
        cols = st.columns(7)
        days = ["월", "화", "수", "목", "금", "토", "일"]
        
        for idx, day_name in enumerate(days):
            cols[idx].write(f"**{day_name}**")

        for week in cal:
            cols = st.columns(7)
            for idx, day in enumerate(week):
                if day == 0:
                    cols[idx].write("")
                else:
                    target_date = datetime(now.year, now.month, day).date()
                    day_data = df[df['날짜'] == target_date]
                    
                    income = day_data[day_data['구분'] == '수입']['금액'].sum()
                    expense = day_data[day_data['구분'] != '수입']['금액'].sum()
                    
                    # 달력 한 칸 구성
                    with cols[idx]:
                        st.markdown(f"""
                            <div class='cal-day'>
                                <div class='cal-date'>{day}</div>
                                {'<div class="cal-inc">+' + str(int(income/10000)) + '만</div>' if income > 0 else ''}
                                {'<div class="cal-exp">-' + str(int(expense/10000)) + '만</div>' if expense > 0 else ''}
                            </div>
                        """, unsafe_allow_html=True)

        # --- 입력창 (팝업 느낌으로 하단 배치) ---
        st.write("---")
        with st.expander("➕ 내역 추가 (날짜 선택)", expanded=False):
            with st.form(key=f"form_{user}", clear_on_submit=True):
                sel_date = st.date_input("날짜", value=now, key=f"d_{user}")
                col1, col2 = st.columns(2)
                with col1: m_type = st.selectbox("구분", ["지출", "우리", "수입"], key=f"t_{user}")
                with col2: m_cat = st.selectbox("카테고리", ["식비", "교통", "여가", "생필품", "주식", "열매", "통신", "기타"], key=f"c_{user}")
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

        # 상세 내역 표
        if st.checkbox("이번 달 전체 내역 보기", key=f"list_{user}"):
            st.dataframe(df.sort_values('날짜', ascending=False), use_container_width=True)
