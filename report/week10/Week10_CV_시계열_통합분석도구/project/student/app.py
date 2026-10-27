"""app.py - Computer Vision·시계열 통합 분석 도구 (Streamlit 3탭).

실행:  streamlit run app.py
선택:  USE_CLAUDE_CLI=1 streamlit run app.py   (Claude CLI가 없으면 해설 박스 없이 그대로 동작)

탭1 🖼 이미지 분류  → local_model.classify_image()      (D1, ViT-Tiny)
탭2 🎨 이미지 생성  → local_model.generate_image()      (D2, segmind/tiny-sd)
탭3 📈 시계열 예측  → local_model.forecast_timeseries() (D3·D4, Holt-Winters)
"""
import pandas as pd
import streamlit as st
from PIL import Image

import local_model as lm
from cli_augment import augment, enabled_clis

st.set_page_config(page_title="CV·시계열 통합 분석 도구", page_icon="🧭", layout="wide")
st.title("🧭 Computer Vision·시계열 통합 분석 도구")
st.caption("사진을 맞히고, 그림을 그리고, 미래 숫자를 예측합니다 - 모두 내 컴퓨터(CPU)의 로컬 모델로.")

with st.sidebar:
    st.header("사용 모델 (전부 로컬)")
    st.markdown(
        f"- 이미지 분류: `{lm.VIT_MODEL_ID}`\n"
        f"- 이미지 생성: `{lm.DIFFUSION_MODEL_ID}`\n"
        "- 시계열 예측: Holt-Winters (`statsmodels`)"
    )
    clis = enabled_clis()
    st.markdown("**CLI 해설:** " + (", ".join(clis) + " 켜짐" if clis else "꺼짐(로컬 모드)"))
    st.caption("최초 1회는 모델을 내려받느라 오래 걸릴 수 있습니다(정상).")


def show_cli_notes(task, summary):
    """USE_CLAUDE_CLI / USE_CODEX_CLI 가 켜져 있고 CLI가 성공했을 때만 해설 박스를 보여줍니다."""
    notes = augment(task, summary)
    if "claude" in notes:
        st.info("🤖 Claude CLI 해설\n\n" + notes["claude"])
    if "codex" in notes:
        st.info("🤖 Codex CLI 해설\n\n" + notes["codex"])


tab1, tab2, tab3 = st.tabs(["🖼 이미지 분류", "🎨 이미지 생성", "📈 시계열 예측"])

# ─────────────────────────────── 탭1: 이미지 분류 (D1) ───────────────────────────────
with tab1:
    st.subheader("🖼 이미지 분류 - ViT-Tiny")
    st.caption("ImageNet 1,000종 사물로 학습된 모델입니다. 확신도가 낮으면 사람이 한 번 더 확인하세요.")
    source = st.radio("이미지 선택", ["샘플(scikit-image)", "직접 업로드"], horizontal=True, key="cls_src")

    image, image_key = None, None
    if source == "샘플(scikit-image)":
        from skimage import data as skdata

        samples = {"astronaut (우주비행사)": skdata.astronaut, "chelsea (고양이)": skdata.chelsea,
                   "coffee (커피잔)": skdata.coffee}
        name = st.selectbox("샘플", list(samples), key="cls_sample")
        image, image_key = Image.fromarray(samples[name]()), name
    else:
        uploaded = st.file_uploader("이미지 파일", type=["png", "jpg", "jpeg", "webp", "bmp"], key="cls_up")
        if uploaded is not None:
            image, image_key = Image.open(uploaded), f"{uploaded.name}:{uploaded.size}"

    if image is not None:
        col_img, col_res = st.columns([1, 1])
        with col_img:
            st.image(image, caption=f"입력 이미지 {image.size[0]}×{image.size[1]}", width="stretch")
        with col_res:
            if st.button("분류하기", type="primary", key="cls_btn"):
                with st.spinner("ViT-Tiny로 분류 중... (최초 1회는 모델 다운로드)"):
                    st.session_state["cls_result"] = (image_key, lm.classify_image(image, top_k=5))
            saved = st.session_state.get("cls_result")
            result = saved[1] if saved and saved[0] == image_key else None   # 이미지를 바꾸면 이전 결과는 숨김
            if result is not None:
                st.markdown("**Top-5 예측**")
                st.dataframe(result, hide_index=True, width="stretch")
                top = result.iloc[0]
                show_cli_notes("이미지 분류(ViT-Tiny, ImageNet 1,000종)",
                               "\n".join(f"{r['순위']}위 {r['라벨']} ({r['확신도(%)']}%)" for _, r in result.iterrows()))
                st.caption(f"1위: {top['라벨']} · 확신도 {top['확신도(%)']}%")

# ─────────────────────────────── 탭2: 이미지 생성 (D2) ───────────────────────────────
with tab2:
    st.subheader("🎨 이미지 생성 - 경량 Diffusion(segmind/tiny-sd)")
    st.caption("영어 프롬프트가 더 안정적입니다. 같은 프롬프트·시드·설정이면 같은 이미지가 다시 나옵니다.")
    prompt = st.text_area("프롬프트", "a small cozy bookstore cafe, warm lighting, watercolor illustration",
                          key="gen_prompt")
    c1, c2 = st.columns(2)
    steps = c1.slider("디노이징 스텝 수 (num_inference_steps)", 4, 30, 10, key="gen_steps")
    seed = c2.number_input("시드(seed)", min_value=0, value=0, step=1, key="gen_seed")

    if st.button("이미지 생성하기", type="primary", key="gen_btn"):
        if not prompt.strip():
            st.warning("프롬프트를 입력하세요.")
        else:
            with st.spinner("노이즈를 지워가며 생성 중... (최초 1회는 약 1GB 모델 다운로드로 수 분 걸릴 수 있음)"):
                img, sec = lm.generate_image(prompt, steps=steps, guidance_scale=7.0, seed=seed, size=256)
            st.session_state["gen_result"] = (img, sec, prompt, steps, seed)

    gen = st.session_state.get("gen_result")
    if gen is not None:
        img, sec, used_prompt, used_steps, used_seed = gen
        st.image(img, caption=f"256×256 · {used_steps}스텝 · seed={used_seed} · {sec:.2f}초", width=384)
        show_cli_notes("이미지 생성(segmind/tiny-sd, 256×256)",
                       f"프롬프트: {used_prompt}\n스텝: {used_steps}, guidance_scale: 7.0, 생성시간: {sec:.2f}초")

# ─────────────────────────────── 탭3: 시계열 예측 (D3·D4) ───────────────────────────────
with tab3:
    st.subheader("📈 시계열 예측 - Holt-Winters")
    st.caption("CSV는 첫 열=날짜, 둘째 열=값. 예측은 확정이 아니라 과거 패턴에 기반한 추정입니다.")
    ts_source = st.radio("데이터 선택", ["샘플(AirPassengers)", "CSV 업로드"], horizontal=True, key="ts_src")

    ts, ts_desc = None, ""
    if ts_source == "샘플(AirPassengers)":
        ts, ts_desc = lm.load_sample_airpassengers()
        st.download_button("샘플 CSV 내려받기(업로드 형식 참고용)",
                           ts.rename_axis("date").reset_index().to_csv(index=False).encode("utf-8"),
                           file_name="airpassengers.csv", mime="text/csv", key="ts_dl")
    else:
        up = st.file_uploader("CSV 파일 (날짜, 값)", type=["csv"], key="ts_up")
        if up is not None:
            try:
                ts = lm.series_from_csv(pd.read_csv(up))
                ts_desc = f"업로드 파일 {up.name}"
            except Exception as e:
                st.error(f"CSV를 읽지 못했습니다: {e}")

    if ts is not None:
        st.caption(f"{ts_desc} · {len(ts)}개 시점 · {ts.index.min().date()} ~ {ts.index.max().date()} · 빈도 {ts.index.freqstr}")
        c1, c2, c3 = st.columns(3)
        periods = c1.slider("예측할 시점 수", 1, 36, 12, key="ts_periods")
        seasonal_periods = c2.selectbox("계절 주기(seasonal_periods)", [12, 7, 52, 4], key="ts_sp",
                                        help="월별 12 · 일별(요일) 7 · 주별 52 · 분기별 4 (D4 FAQ Q6)")
        seasonal = c3.selectbox("계절성 형태", ["mul", "add"], key="ts_mode",
                                help="mul: 규모가 커질수록 계절 진폭도 커질 때 / add: 진폭이 일정할 때")

        if st.button("예측 실행", type="primary", key="ts_btn"):
            st.session_state["ts_result"] = (lm.forecast_timeseries(
                ts, periods=periods, seasonal_periods=seasonal_periods, trend="add", seasonal=seasonal), ts, ts_desc)

        saved = st.session_state.get("ts_result")
        if saved is not None and saved[2] == ts_desc:      # 데이터를 바꾸면 이전 결과는 숨김
            res, used_ts, _ = saved
            if res["note"]:
                st.warning(res["note"])
            chart = pd.concat([used_ts.rename("실제값"), res["forecast"].rename("예측값")], axis=1)
            st.line_chart(chart)

            m1, m2, m3 = st.columns(3)
            fmt = lambda v: "-" if v is None else f"{v:.4f}"
            m1.metric("alpha (수준)", fmt(res["alpha"]))
            m2.metric("beta (추세)", fmt(res["beta"]))
            m3.metric("gamma (계절성)", fmt(res["gamma"]))
            st.caption("값이 1에 가까울수록 최근 변화를 빠르게 반영, 0에 가까울수록 과거 패턴을 안정적으로 유지(D4 1-5).")

            table = res["forecast"].round(2).rename("예측값").rename_axis("날짜").reset_index()
            table["날짜"] = table["날짜"].dt.date
            st.dataframe(table, hide_index=True, width="stretch")
            show_cli_notes("시계열 예측(Holt-Winters)",
                           f"데이터: {ts_desc}, {len(used_ts)}개 시점\n"
                           f"설정: trend=add, seasonal={res['seasonal']}\n"
                           f"alpha={fmt(res['alpha'])}, beta={fmt(res['beta'])}, gamma={fmt(res['gamma'])}\n"
                           f"예측 처음 3개: {', '.join(f'{v:.1f}' for v in res['forecast'].head(3))}")
