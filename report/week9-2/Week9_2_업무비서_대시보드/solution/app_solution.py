"""app_solution.py - 과제 4단계 3~5번 예시 답안 (강사·채점용).

project/app.py 에 다음을 더한 버전입니다.
  3단계: 대시보드 탭에 기간(날짜) 슬라이더 + 지역 선택 상자 → 지표·차트·digest 모두 재계산
  4단계: AI 요약 톤 선택(경영진용/실무진용) → system 프롬프트 교체
  5단계: 리뷰 분류 탭에 카테고리별 부정 비율(표·차트·30% 경보)

실행(Week9_2_업무비서_대시보드 폴더에서): streamlit run solution/app_solution.py --server.port 8611
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "project"))   # project/의 data.py·ai_client.py 사용

import pandas as pd
import streamlit as st

from ai_client import ask, classify, current_mode
from data import REGIONS, daily_sales, orders_df, reviews_df

st.set_page_config(page_title="AI 업무 비서 대시보드", page_icon="🧰", layout="wide")

mode = current_mode()
st.sidebar.title("🧰 설정")
if mode == "mock":
    st.sidebar.markdown("**AI 모드:** 🟡 mock (키 없이 동작)")
else:
    st.sidebar.markdown(f"**AI 모드:** 🟢 실제 API ({mode})")
st.sidebar.caption("키가 없으면 자동으로 mock으로 동작합니다.")

st.title("🧰 AI 업무 비서 대시보드")
st.caption("10주차 캡스톤 - 데이터(대시보드) · AI 요약 · 리뷰 분류를 하나의 앱으로.")

orders = orders_df()
reviews = reviews_df()

# 4단계: 톤별 system 프롬프트 (숫자는 digest 안에서만 쓰게 범위를 좁힌다)
SYSTEM_PROMPTS = {
    "경영진용": ("너는 데이터 분석 리포터야. 주어진 지표를 경영진용 한국어 한 문단으로 요약해. "
              "결론과 의사결정 포인트를 먼저 말해. 주어진 숫자만 쓰고 새로운 숫자를 만들지 마."),
    "실무진용": ("너는 데이터 분석 리포터야. 주어진 지표를 실무진용 한국어 한 문단으로 요약해. "
              "카테고리·지역별로 바로 점검할 항목을 짚어. 주어진 숫자만 쓰고 새로운 숫자를 만들지 마."),
}


def make_digest(view, reviews, label):
    cat = view.groupby("카테고리")["금액_만원"].sum().sort_values(ascending=False)
    reg = view.groupby("지역")["금액_만원"].sum().sort_values(ascending=False)
    top_cat = ", ".join(f"{k}({int(v)})" for k, v in cat.head(2).items())
    top_reg = ", ".join(f"{k}({int(v)})" for k, v in reg.head(1).items())
    return (f"[{label}] 총매출 {int(view['금액_만원'].sum())}만원, 총주문 {len(view)}건. "
            f"카테고리 매출 상위: {top_cat}. 지역 매출 상위: {top_reg}. "
            f"평균 별점 {reviews['별점'].mean():.2f}.")


tab1, tab2, tab3 = st.tabs(["📊 대시보드", "🤖 AI 요약", "💬 리뷰 분류"])

# ── 📊 탭1: 대시보드 + 3단계 필터 ───────────────────────
with tab1:
    f1, f2 = st.columns([3, 1])
    dmin, dmax = orders["날짜"].min(), orders["날짜"].max()
    start, end = f1.slider("기간", min_value=dmin, max_value=dmax, value=(dmin, dmax), format="YYYY-MM-DD")
    region = f2.selectbox("지역", ["전체"] + REGIONS)

    view = orders[(orders["날짜"] >= start) & (orders["날짜"] <= end)]
    if region != "전체":
        view = view[view["지역"] == region]
    label = f"{start}~{end} · {region}"

    if view.empty:
        st.warning("선택한 기간·지역에 주문이 없습니다. 범위를 넓혀 보세요.")
    else:
        cat = view.groupby("카테고리")["금액_만원"].sum().sort_values(ascending=False)
        reg = view.groupby("지역")["금액_만원"].sum().sort_values(ascending=False)
        c1, c2, c3 = st.columns(3)
        c1.metric("총매출", f"{int(view['금액_만원'].sum()):,}만원")
        c2.metric("총주문", f"{len(view)}건")
        c3.metric("1위 카테고리", cat.index[0])
        # 숫자 상식 대조: 필터를 걸면 전체보다 작거나 같아야 한다
        st.caption(f"선택 범위 매출 {int(view['금액_만원'].sum()):,}만원 / 전체 {int(orders['금액_만원'].sum()):,}만원")

        st.subheader("일별 매출 추이 (만원)")
        daily = daily_sales(view)
        daily.index = pd.to_datetime(daily.index)
        st.line_chart(daily)

        left, right = st.columns(2)
        left.subheader("카테고리별 매출 (만원)")
        left.bar_chart(cat)
        right.subheader("지역별 매출 (만원)")
        right.bar_chart(reg)

        with st.expander("필터된 주문 데이터 보기"):
            st.dataframe(view)

digest = None if view.empty else make_digest(view, reviews, label)

# ── 🤖 탭2: AI 요약 + 4단계 톤 선택 ─────────────────────
with tab2:
    if digest is None:
        st.info("대시보드 탭의 필터 결과가 비어 있어 요약할 지표가 없습니다.")
    else:
        st.write("아래 지표(대시보드 필터 반영)를 AI가 한국어 한 문단으로 정리합니다.")
        st.code(digest)
        tone = st.radio("요약 대상", list(SYSTEM_PROMPTS), horizontal=True)
        st.caption(f"system 프롬프트: {SYSTEM_PROMPTS[tone]}")

        if st.button("🤖 AI 요약 만들기", type="primary"):
            with st.spinner("AI가 요약 중..."):
                text, meta = ask(system=SYSTEM_PROMPTS[tone], user=digest, task="summary", max_tokens=300)
            st.session_state["summary"] = (text, meta, digest, tone)

        if "summary" in st.session_state:
            text, meta, used_digest, used_tone = st.session_state["summary"]
            if used_digest != digest or used_tone != tone:
                st.warning("필터나 톤이 바뀌었습니다. 아래는 이전 요약입니다 - 다시 눌러 갱신하세요.")
            st.success(f"요약 완료 ({used_tone})")
            st.write(text)
            m1, m2, m3 = st.columns(3)
            m1.metric("모드", meta["mode"])
            m2.metric("토큰(in/out)", f"{meta['input_tokens']}/{meta['output_tokens']}")
            m3.metric("비용(USD)", f"${meta['cost_usd']:.6f}")
            with st.expander("📎 근거 데이터(원본 숫자)"):
                st.code(used_digest)

# ── 💬 탭3: 리뷰 분류 + 5단계 카테고리별 부정 비율 ───────
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

    st.divider()
    st.subheader("카테고리별 부정 비율 (data.py 리뷰 120건 기준)")
    rv = reviews.assign(감정=reviews["리뷰"].map(classify))
    neg = (rv.groupby("카테고리")["감정"].apply(lambda s: (s == "부정").mean())
             .sort_values(ascending=False))
    table = pd.DataFrame({"리뷰 수": rv.groupby("카테고리").size(), "부정 비율": neg}).loc[neg.index]
    l, r = st.columns([1, 1])
    l.dataframe(table.style.format({"부정 비율": "{:.0%}"}))
    r.bar_chart(neg)
    high = [k for k, v in neg.items() if v > 0.30]
    if high:
        st.warning(f"부정 비율 30% 초과: {', '.join(high)} → CS/품질 점검 우선 대상")
