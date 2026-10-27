"""app.py - AI 업무 비서 대시보드 (3탭: 📊 대시보드 / 🤖 AI 요약 / 💬 리뷰 분류).

실행: streamlit run app.py   (또는 ./run.sh → http://localhost:8610)
키가 없으면 AI 요약은 자동으로 mock(무료)으로 동작합니다.

과제(Week10_Project.md 4단계)에서 여러분이 고칠 곳에는 [과제 N단계] 표시가 있습니다.
"""
import pandas as pd
import streamlit as st

from ai_client import ask, classify, current_mode
from data import daily_sales, orders_df, reviews_df

# set_page_config 는 st. 명령 중 가장 먼저!
st.set_page_config(page_title="AI 업무 비서 대시보드", page_icon="🧰", layout="wide")

# ── 사이드바: AI 모드 배지 ─────────────────────────────
mode = current_mode()
st.sidebar.title("🧰 설정")
if mode == "mock":
    st.sidebar.markdown("**AI 모드:** 🟡 mock (키 없이 동작)")
else:
    st.sidebar.markdown(f"**AI 모드:** 🟢 실제 API ({mode})")
st.sidebar.caption("키가 없으면 자동으로 mock으로 동작합니다.")

st.title("🧰 AI 업무 비서 대시보드")
st.caption("10주차 캡스톤 - 데이터(대시보드) · AI 요약 · 리뷰 분류를 하나의 앱으로.")

# ── 원본은 탭 밖에서 '한 번' 로딩, 각 탭은 '다른 관점'으로 본다 ──
orders = orders_df()
reviews = reviews_df()

# [과제 3단계] 기간·지역 필터를 넣으면, 아래 집계가 '필터된 orders'로 계산되게 하세요.
cat = orders.groupby("카테고리")["금액_만원"].sum().sort_values(ascending=False)
reg = orders.groupby("지역")["금액_만원"].sum().sort_values(ascending=False)

# 숫자는 Python(pandas)이 계산한다 → AI에는 이 집계 요약(digest)만 보낸다(원본 행·개인정보 X)
digest = (
    f"총매출 {int(orders['금액_만원'].sum())}만원, 총주문 {len(orders)}건. "
    f"카테고리 매출 상위: {cat.index[0]}({int(cat.iloc[0])}), {cat.index[1]}({int(cat.iloc[1])}). "
    f"지역 매출 상위: {reg.index[0]}({int(reg.iloc[0])}). "
    f"평균 별점 {reviews['별점'].mean():.2f}."
)

tab1, tab2, tab3 = st.tabs(["📊 대시보드", "🤖 AI 요약", "💬 리뷰 분류"])

# ── 📊 탭1: 대시보드 ───────────────────────────────────
with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("총매출", f"{int(orders['금액_만원'].sum()):,}만원")
    c2.metric("총주문", f"{len(orders)}건")
    c3.metric("1위 카테고리", cat.index[0])

    st.subheader("일별 매출 추이 (만원)")
    daily = daily_sales(orders)
    daily.index = pd.to_datetime(daily.index)
    st.line_chart(daily)

    left, right = st.columns(2)
    left.subheader("카테고리별 매출 (만원)")
    left.bar_chart(cat)
    right.subheader("지역별 매출 (만원)")
    right.bar_chart(reg)

    with st.expander("주문 원본 데이터 보기"):
        st.dataframe(orders)

# ── 🤖 탭2: AI 요약 ────────────────────────────────────
with tab2:
    st.write("아래 지표를 AI가 한국어 한 문단으로 정리합니다.")
    st.caption("지표 다이제스트 - AI에 보낼 재료(원본 행 대신 집계 요약만 보냅니다)")
    st.code(digest)

    # [과제 4단계] 경영진용/실무진용 톤을 고를 수 있게 system 프롬프트를 다듬어 보세요.
    system = "너는 데이터 분석 리포터야. 주어진 지표를 경영진용 한국어 한 문단으로 요약해."

    # 버튼을 눌렀을 때만 호출(rerun마다 호출하면 요금 폭탄) + max_tokens 작게
    if st.button("🤖 AI 요약 만들기", type="primary"):
        with st.spinner("AI가 요약 중..."):
            text, meta = ask(system=system, user=digest, task="summary", max_tokens=300)
        st.session_state["summary"] = (text, meta)     # 다른 버튼을 눌러 rerun돼도 결과 유지

    if "summary" in st.session_state:
        text, meta = st.session_state["summary"]
        st.success("요약 완료")
        st.write(text)
        m1, m2, m3 = st.columns(3)
        m1.metric("모드", meta["mode"])
        m2.metric("토큰(in/out)", f"{meta['input_tokens']}/{meta['output_tokens']}")
        m3.metric("비용(USD)", f"${meta['cost_usd']:.6f}")
        with st.expander("📎 근거 데이터(원본 숫자)"):
            st.code(digest)
        st.caption("AI 요약은 '참고', 숫자의 근거는 위 원본입니다. 요약 속 숫자는 반드시 대조하세요.")

# ── 💬 탭3: 리뷰 분류 ──────────────────────────────────
with tab3:
    st.caption("리뷰를 붙여넣으면 감정을 분류합니다. (규칙 기반, 키 불필요)")
    sample = "\n".join(reviews["리뷰"].head(15))
    raw = st.text_area("리뷰 입력(한 줄에 하나)", value=sample, height=240)

    if st.button("🔎 분류하기"):
        lines = [x.strip() for x in raw.splitlines() if x.strip()]
        st.session_state["classified"] = pd.DataFrame(
            {"리뷰": lines, "감정": [classify(x) for x in lines]})

    df = st.session_state.get("classified")
    if df is not None:
        if df.empty:
            st.warning("분류할 리뷰가 없습니다. 한 줄에 하나씩 붙여넣어 주세요.")
        else:
            dist = df["감정"].value_counts().reindex(["긍정", "부정", "중립"], fill_value=0)
            a, b = st.columns([2, 1])
            a.subheader("감정 분포")
            a.bar_chart(dist)
            b.metric("긍정 비율", f"{dist['긍정'] / len(df):.0%}")
            b.metric("부정 리뷰", f"{dist['부정']}건")
            st.dataframe(df)
            st.download_button("📥 CSV 내려받기", df.to_csv(index=False).encode("utf-8-sig"),
                               file_name="reviews_classified.csv", mime="text/csv")

    # [과제 5단계] 카테고리별 부정 비율을 여기에 추가하세요 (examples/example_02 참고).
