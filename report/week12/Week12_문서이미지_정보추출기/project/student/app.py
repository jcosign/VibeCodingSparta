"""app.py - 문서·이미지 정보 추출기 (Streamlit 3탭).

실행:  streamlit run app.py
선택:  USE_CLAUDE_CLI=1 streamlit run app.py   (PDF 탭 엔진 "cli"에서 사용, CLI가 없으면 로컬 요약 그대로)
선택:  GEMINI_API_KEY=... streamlit run app.py  (엔진 "gemini"에서 사용, 키가 없으면 로컬로 자동 대체)

탭1 🧾 이미지 추출   → extract.image_extract()            (D1·D2, 기본: Tesseract OCR + 정규식 → JSON)
탭2 📄 PDF·문서 요약 → extract.pdf_to_text() + summarize() (D3, 기본: pypdf + 규칙 기반 요약)
탭3 🌐 HTML 표 파싱  → extract.html_tables() + html_text() (D4, 항상 로컬: BeautifulSoup → DataFrame → CSV)
"""
from io import BytesIO

import pandas as pd
import streamlit as st

import extract as ex
from cli_augment import enabled_clis
from gemini_client import GEMINI_MODEL, current_mode
from sample_docs import SAMPLE_HTML, SAMPLE_PDF_PATH, make_sample_image

st.set_page_config(page_title="문서·이미지 정보 추출기", page_icon="📄", layout="wide")
st.title("📄 문서·이미지 정보 추출기")
st.caption("이미지·PDF·HTML에서 정보를 뽑아 구조화된 데이터로 정리합니다 - 기본은 전부 내 컴퓨터(로컬)에서, 키·인터넷 없이.")

tess = ex.tesseract_version()
with st.sidebar:
    st.header("엔진 상태")
    st.markdown("**로컬 OCR(Tesseract):** " + (f"🟢 {tess}" if tess else "🔴 설치 안 됨 → 이미지 탭 OCR 불가"))
    st.markdown("**AI 모드(Gemini):** " + (f"🟢 Gemini (`{GEMINI_MODEL}`)" if current_mode() == "gemini"
                                         else "🟡 키 없음 → engine=gemini를 골라도 로컬로 대체"))
    clis = enabled_clis()
    st.markdown("**CLI 다듬기:** " + (", ".join(clis) + " 켜짐" if clis else "꺼짐(로컬 모드)"))
    st.caption("PDF 파싱(pypdf)·HTML 파싱(BeautifulSoup)은 항상 로컬입니다.")


def show_meta(meta):
    """어떤 경로가 실제로 쓰였는지(mode)와, 대체됐다면 그 이유를 보여줍니다."""
    label = {"local": "🖥 로컬", "cli": "🤖 CLI", "gemini": "🟢 Gemini"}.get(meta.get("mode"), meta.get("mode"))
    st.caption(f"실제 사용 경로: {label} · 엔진: {meta.get('engine', meta.get('model', '-'))}")
    if meta.get("fallback"):
        st.info("ℹ️ " + meta["fallback"])


tab1, tab2, tab3 = st.tabs(["🧾 이미지 추출", "📄 PDF·문서 요약", "🌐 HTML 표 파싱"])

# ─────────────────────────────── 탭1: 이미지 추출 (D1·D2) ───────────────────────────────
with tab1:
    st.subheader("🧾 이미지 추출 - 영수증·표 이미지 → JSON")
    st.caption("기본(local): Tesseract OCR로 이미지 속 글자를 실제로 인식 → 정규식으로 항목·수량·금액 JSON 구조화. "
               "업로드 전, 카드번호·연락처 같은 개인정보는 가리세요(D2 4-3).")
    engine_img = st.radio("엔진", ["local", "gemini"], horizontal=True, key="img_engine")
    up = st.file_uploader("영수증·표 이미지 (없으면 샘플 영수증 사용)", type=["png", "jpg", "jpeg"], key="img_up")
    if up is not None:
        img_bytes, mime, img_key = up.getvalue(), up.type or "image/png", f"{up.name}:{up.size}"
    else:
        img_bytes, mime, img_key = make_sample_image(), "image/png", "sample"
    st.image(img_bytes, caption="업로드 이미지" if up is not None else "샘플 영수증 (sample_docs.make_sample_image)")

    if st.button("🔎 정보 추출", type="primary", key="img_btn"):
        with st.spinner("이미지에서 정보를 읽는 중..."):
            st.session_state["img_result"] = ((img_key, engine_img), ex.image_extract(img_bytes, mime=mime, engine=engine_img))

    saved = st.session_state.get("img_result")
    if saved is not None and saved[0] == (img_key, engine_img):      # 이미지·엔진을 바꾸면 이전 결과는 숨김
        text, meta = saved[1]
        show_meta(meta)
        if meta.get("error") and meta.get("mode") == "local":
            st.error(f"OCR 실패: {meta['error']}\n\nTesseract가 설치되어 있는지 확인하세요(`tesseract --version`). "
                     "INTEGRATION.md 트러블슈팅 참고.")
        if "ocr_text" in meta:
            st.markdown("**OCR 원문** (Tesseract가 실제로 읽은 글자, 언어: `" + meta.get("lang", "") + "`)")
            st.code(meta["ocr_text"].strip() or "(인식된 글자 없음)", language="text")
        st.markdown("**구조화 JSON**")
        st.code(text, language="json")

        obj = ex.safe_json(text)                                      # D2 블록 C: 깨진 JSON에도 앱이 안 죽게
        if "error" in obj and meta.get("mode") == "gemini":
            obj = ex.loose_json(text) or obj                         # D2 심화: 코드펜스·군더더기 벗기고 재시도
        if "error" in obj:
            st.warning(f"JSON 파싱 실패({obj['error']}) - 원문은 위에 그대로 보여 줍니다.")
        else:
            if isinstance(obj.get("항목"), list) and obj["항목"]:
                st.dataframe(pd.DataFrame(obj["항목"]), hide_index=True, width="stretch")
            elif meta.get("mode") == "local":
                st.warning("OCR 원문에서 'item: … qty: … price: …' 형식의 줄을 찾지 못했습니다. "
                           "_parse_receipt_lines()의 정규식을 내 영수증 형식에 맞게 넓혀 보세요(과제 '더 해보기').")
            v = ex.verify_receipt(obj)
            if v is not None:
                if v["일치"]:
                    st.success(f"✅ 검증 통과: 항목 금액 합 {v['항목합']} = 합계 {v['합계']}")
                elif v["일치"] is None:
                    st.warning(f"⚠️ 합계를 읽지 못했습니다(null). 항목 금액 합 = {v['항목합']} → 사람 확인")
                else:
                    st.warning(f"⚠️ 불일치! 항목 금액 합={v['항목합']}, 합계={v['합계']} → 사람 확인")
        st.caption("AI든 OCR이든 숫자를 잘못 읽을 수 있습니다(예: 3을 8로). 원본 이미지와 대조하세요(D2 4-2).")

# ─────────────────────────────── 탭2: PDF·문서 요약 (D3) ───────────────────────────────
with tab2:
    st.subheader("📄 PDF·문서 요약 - pypdf 텍스트 추출 → 요약")
    st.caption("기본(local): 문장마다 점수를 매겨 핵심 문장 3개를 원문 그대로 고르는 규칙 기반 요약(외부 호출 없음). "
               "요약은 참고용, 숫자의 근거는 원본입니다(D3 4-1).")
    engine_pdf = st.radio("엔진", ["local", "cli", "gemini"], horizontal=True, key="pdf_engine")
    up_pdf = st.file_uploader("PDF (없으면 sample_invoice.pdf 사용)", type=["pdf"], key="pdf_up")
    try:
        if up_pdf is not None:                                        # PdfReader는 파일 경로 대신 BytesIO도 받음
            pdf_text, pdf_key = ex.pdf_to_text(BytesIO(up_pdf.getvalue())), f"{up_pdf.name}:{up_pdf.size}"
        else:
            pdf_text, pdf_key = ex.pdf_to_text(SAMPLE_PDF_PATH), "sample"
    except Exception as e:
        pdf_text, pdf_key = None, None
        st.error(f"PDF를 열지 못했습니다: {type(e).__name__}: {e}")

    if pdf_text is not None:
        st.metric("추출 길이(글자 수)", len(pdf_text))
        if not pdf_text.strip():
            st.warning("글자가 안 뽑혀요 → 스캔본(이미지만 든 PDF)인 듯합니다. 페이지를 이미지로 저장해 "
                       "🧾 이미지 추출 탭(OCR)으로 넘기세요(D3 1-3·3-3).")
        else:
            st.text_area("추출된 텍스트", pdf_text, height=180, key="pdf_text_view")
            if st.button("📝 AI 요약", type="primary", key="pdf_btn"):
                with st.spinner("요약 중..."):
                    st.session_state["pdf_result"] = ((pdf_key, engine_pdf), ex.summarize(pdf_text, engine=engine_pdf))

            saved = st.session_state.get("pdf_result")
            if saved is not None and saved[0] == (pdf_key, engine_pdf):
                summary, meta = saved[1]
                show_meta(meta)
                st.markdown("**요약**")
                st.markdown(summary)
                if meta.get("mode") == "cli":
                    with st.expander("비교: 로컬 요약(다듬기 전)"):
                        st.markdown(meta["local_summary"])
                bad = ex.unverified_numbers(summary, pdf_text)     # D3 4-2: 요약 숫자를 원본과 자동 대조
                if bad:
                    st.warning(f"⚠️ 요약에 원본에 없는 숫자가 있습니다: {', '.join(bad)} → 원본 확인 필요")
                else:
                    st.success("✅ 요약 속 숫자가 모두 원본 텍스트에 있습니다(숫자 대조 통과).")

# ─────────────────────────────── 탭3: HTML 표 파싱 (D4) ───────────────────────────────
with tab3:
    st.subheader("🌐 HTML 표 파싱 - 웹 표 → DataFrame → CSV")
    st.caption("BeautifulSoup으로 <table>만 뽑아 표로 정리합니다(항상 로컬). "
               "실제 웹사이트를 긁을 땐 robots.txt·요청 간격·약관을 지키세요(D4 4-2).")
    html = st.text_area("HTML 입력", SAMPLE_HTML, height=260, key="html_in")

    if st.button("📊 표 파싱", type="primary", key="html_btn"):
        st.session_state["html_result"] = (html, ex.html_tables(html), ex.html_text(html))

    saved = st.session_state.get("html_result")
    if saved is not None and saved[0] == html:                        # HTML을 바꾸면 이전 결과는 숨김
        _, tables, body = saved
        if not tables:
            st.warning("표를 찾지 못했습니다.")
        for i, t in enumerate(tables, 1):
            header, rows = t[0], t[1:]
            width = len(header)
            rows = [(r + [""] * width)[:width] for r in rows]         # 칸 개수가 다른 행은 맞춰 줌(D4 4-3)
            df = pd.DataFrame(rows, columns=header)
            for col in df.columns:                                    # 문자열 숫자 → 진짜 숫자(D4 2-3)
                conv = pd.to_numeric(df[col], errors="coerce")
                if conv.notna().all():
                    df[col] = conv
            st.markdown(f"**표 {i}** ({len(df)}행 × {len(df.columns)}열)")
            cols = st.multiselect("리포트에 넣을 열(필요한 열만)", list(df.columns), default=list(df.columns),
                                  key=f"html_cols_{i}")
            report = df[cols] if cols else df
            st.dataframe(report, hide_index=True, width="stretch")
            st.download_button("⬇️ CSV 다운로드", report.to_csv(index=False).encode("utf-8-sig"),  # 엑셀 한글 깨짐 방지
                               file_name=f"table_{i}.csv", mime="text/csv", key=f"html_dl_{i}")
        st.markdown("**본문 텍스트** (`html_text`: script·style 제거)")
        st.write(body or "(본문 없음)")
