"""app.py - LLM 검색·Audio·에이전트 실행환경 통합 도구 (Streamlit 3탭).

실행:  streamlit run app.py
선택:  USE_CLAUDE_CLI=1 streamlit run app.py   (Claude CLI가 없으면 해설 박스 없이 그대로 동작)

탭1 🔎 검색+리랭크   → local_model.search_and_rerank()                       (D2, 바이 인코더 + 크로스 인코더)
탭2 🎙 음성 전사     → local_model.transcribe_audio()                        (D3, Whisper-tiny)
탭3 🤖 코드 샌드박스 → local_model.try_e2b_sandbox() / run_in_local_sandbox() (D4)
"""
import os
import tempfile
from pathlib import Path

import streamlit as st

import local_model as lm
from cli_augment import augment, enabled_clis

st.set_page_config(page_title="LLM 검색·Audio·샌드박스 통합 도구", page_icon="🧭", layout="wide")
st.title("🧭 LLM 검색·Audio·에이전트 실행환경 통합 도구")
st.caption("관련 문서를 찾고, 음성을 글자로 받아 적고, AI가 만든 코드를 격리된 공간에서 실행합니다 - 모두 내 컴퓨터(CPU)에서.")

with st.sidebar:
    st.header("사용 모델 (전부 로컬)")
    st.markdown(
        f"- 바이 인코더: `{lm.EMBED_MODEL_ID}`\n"
        f"- 크로스 인코더: `{lm.RERANK_MODEL_ID}`\n"
        f"- 음성 전사: Whisper `{lm.WHISPER_MODEL_NAME}`\n"
        "- 코드 실행: 로컬 대체 샌드박스 (`E2B_API_KEY`가 있으면 E2B)"
    )
    st.markdown("**E2B:** " + ("`E2B_API_KEY` 있음 → 클라우드 샌드박스 시도" if os.getenv("E2B_API_KEY")
                               else "키 없음 → 로컬 대체 샌드박스"))
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


tab1, tab2, tab3 = st.tabs(["🔎 검색+리랭크", "🎙 음성 전사", "🤖 코드 샌드박스"])

# ─────────────────────────────── 탭1: 검색+리랭크 (D2) ───────────────────────────────
with tab1:
    st.subheader("🔎 검색+리랭크 - 바이 인코더 vs 크로스 인코더")
    st.caption("같은 질문·같은 문서를 두 방식으로 줄 세워 나란히 비교합니다. 실무에서는 바이 인코더로 넓게 찾고, "
               "크로스 인코더로 다시 줄 세웁니다(검색-후-재정렬).")
    query = st.text_input("질문", lm.SAMPLE_QUERY, key="sr_query")
    docs_text = st.text_area("문서 목록 (한 줄에 문서 1개)", "\n".join(lm.SAMPLE_DOCUMENTS), height=150, key="sr_docs")

    if st.button("검색 실행", type="primary", key="sr_btn"):
        documents = [line for line in docs_text.splitlines() if line.strip()]
        if not query.strip() or not documents:
            st.warning("질문과 문서를 1개 이상 입력하세요.")
        else:
            with st.spinner("임베딩·리랭커 모델로 채점 중... (최초 1회는 모델 다운로드)"):
                st.session_state["sr_result"] = ((query, docs_text), lm.search_and_rerank(query, documents))

    saved = st.session_state.get("sr_result")
    if saved is not None and saved[0] == (query, docs_text):     # 질문·문서를 바꾸면 이전 결과는 숨김
        bi, ce = saved[1]
        col_bi, col_ce = st.columns(2)
        with col_bi:
            st.markdown("**① 바이 인코더 순위** (코사인 유사도, 빠름)")
            st.dataframe(bi, hide_index=True, width="stretch")
        with col_ce:
            st.markdown("**② 크로스 인코더 순위** (리랭커 점수, 정확)")
            st.dataframe(ce, hide_index=True, width="stretch")
        if bi.iloc[0]["문서"] != ce.iloc[0]["문서"]:
            st.warning("두 방식의 1위가 다릅니다. 바이 인코더 1위가 항상 정답은 아니므로 리랭커로 재확인하는 이유입니다(D2 3-1-보충).")
        st.caption("리랭커 점수는 0~1 사이가 아닌 원점수라 같은 질문 안에서 순서 비교용으로만 보세요(D2 FAQ Q9). "
                   "리랭커도 틀릴 수 있습니다(D2 2-5 사례 A).")
        show_cli_notes(
            "검색+리랭크(바이 인코더 all-MiniLM-L6-v2 vs 크로스 인코더 ms-marco-MiniLM-L-6-v2)",
            f"질문: {query}\n"
            + "바이 인코더: " + " / ".join(f"{r['순위']}위 {r['문서']}({r['코사인 유사도']})" for _, r in bi.iterrows())
            + "\n크로스 인코더: " + " / ".join(f"{r['순위']}위 {r['문서']}({r['리랭커 점수']})" for _, r in ce.iterrows()),
        )

# ─────────────────────────────── 탭2: 음성 전사 (D3) ───────────────────────────────
with tab2:
    st.subheader("🎙 음성 전사 - Whisper-tiny (ASR/STT)")
    st.caption("소리 → 글자. 전문용어·소음·억양에서는 틀릴 수 있으니 결과는 사람이 확인하세요(D3 3-5). "
               "오디오 파일을 읽으려면 컴퓨터에 ffmpeg가 설치되어 있어야 합니다.")
    uploaded = st.file_uploader("오디오 파일", type=["wav", "mp3", "m4a", "aiff"], key="asr_up")
    if uploaded is not None:
        st.audio(uploaded)
        audio_key = f"{uploaded.name}:{uploaded.size}"
        if st.button("전사 실행", type="primary", key="asr_btn"):
            # Whisper는 파일 경로를 받으므로 업로드 내용을 임시 파일로 저장 → 전사 → 바로 삭제
            suffix = Path(uploaded.name).suffix or ".wav"
            with tempfile.TemporaryDirectory(prefix="w11_audio_") as tmpdir:
                tmp_path = Path(tmpdir) / f"upload{suffix}"
                tmp_path.write_bytes(uploaded.getvalue())
                with st.spinner("Whisper-tiny로 전사 중... (최초 1회는 약 72MB 모델 다운로드)"):
                    try:
                        st.session_state["asr_result"] = (audio_key, lm.transcribe_audio(tmp_path))
                    except Exception as e:   # ffmpeg 미설치 시 whisper가 오디오를 읽지 못함
                        st.session_state.pop("asr_result", None)
                        st.error(f"전사에 실패했습니다: {type(e).__name__}: {e}\n\n"
                                 "ffmpeg가 설치되어 있는지 확인하세요(`ffmpeg -version`).")

        saved = st.session_state.get("asr_result")
        if saved is not None and saved[0] == audio_key:           # 파일을 바꾸면 이전 결과는 숨김
            res = saved[1]
            st.text_area("전사 결과", res["text"], height=120, key="asr_text")
            m1, m2 = st.columns(2)
            m1.metric("감지된 언어", res["language"])
            m2.metric("전사 소요 시간", f"{res['seconds']:.2f}초")
            show_cli_notes("음성 전사(Whisper-tiny)",
                           f"감지된 언어: {res['language']}\n전사 결과: {res['text']}")

# ─────────────────────────────── 탭3: 코드 샌드박스 (D4) ───────────────────────────────
with tab3:
    st.subheader("🤖 코드 샌드박스 - 에이전트가 만든 코드를 격리해 실행")
    st.caption("`E2B_API_KEY`가 있으면 E2B 클라우드 샌드박스, 없으면 로컬 대체 샌드박스(별도 프로세스 + 시간 제한)로 실행합니다. "
               "로컬 대체 샌드박스는 교육용이며 완전한 보안 경계가 아닙니다(D4 3-1).")
    code = st.text_area("실행할 파이썬 코드", "total = sum(range(1, 101))\nprint('1~100 합계:', total)",
                        height=180, key="sb_code")
    timeout_sec = st.slider("시간 제한(초)", 1, 30, 5, key="sb_timeout")

    if st.button("코드 실행", type="primary", key="sb_btn"):
        with st.spinner("격리된 공간에서 실행 중..."):
            result = lm.try_e2b_sandbox(code)            # 키가 없으면 None
            used_local = result is None
            if used_local:
                result = lm.run_in_local_sandbox(code, timeout_sec=float(timeout_sec))
        st.session_state["sb_result"] = (code, used_local, result)

    saved = st.session_state.get("sb_result")
    if saved is not None and saved[0] == code:                    # 코드를 바꾸면 이전 결과는 숨김
        _, used_local, res = saved
        if used_local:
            st.info("ℹ️ E2B_API_KEY가 없어 로컬 대체 샌드박스를 사용했습니다.")
        status_view = {"완료": st.success, "시간초과(강제종료)": st.warning}.get(res["status"], st.error)
        status_view(f"상태: {res['status']} · 실행 환경: {res['engine']} · {res['seconds']:.2f}초")
        st.markdown("**stdout (표준 출력)**")
        st.code(res["stdout"] or "(출력 없음)", language="text")
        st.markdown("**stderr (오류 출력)**")
        st.code(res["stderr"] or "(출력 없음)", language="text")
        st.caption("안전하게 실행됐다는 것이 결과가 정확하다는 뜻은 아닙니다. 계산 결과는 사람이 검증하세요(D4 4-2).")
        show_cli_notes("코드 샌드박스 실행",
                       f"실행 환경: {res['engine']}\n상태: {res['status']}\n"
                       f"stdout: {res['stdout'][:500]}\nstderr: {res['stderr'][:500]}")
