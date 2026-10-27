"""local_model.py - 로컬 AI 함수 4종(API 키 불필요, CPU에서 동작).

- search_and_rerank(query, documents)     : 바이 인코더(1차 검색) + 크로스 인코더(재정렬) 순위 비교 (D2)
- transcribe_audio(audio_path)            : Whisper-tiny로 음성 → 텍스트 전사 + 언어 자동 감지 (D3)
- run_in_local_sandbox(code, timeout_sec) : 별도 프로세스 + 시간 제한으로 코드 실행(로컬 대체 샌드박스) (D4)
- try_e2b_sandbox(code)                   : E2B_API_KEY가 있을 때만 실제 E2B 클라우드 샌드박스로 실행 (D4)

모델은 처음 호출할 때 한 번만 내려받아 메모리에 올리고(lru_cache), 이후 호출에서는 그대로 재사용합니다.
(D1의 토큰화·셀프 어텐션은 아래 임베딩·리랭커·Whisper 모델 내부에서 동작합니다 - 직접 호출하는 함수는 없음)
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from functools import lru_cache

import pandas as pd

EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"   # D2: 바이 인코더, 384차원, 약 2,271만 파라미터
RERANK_MODEL_ID = "cross-encoder/ms-marco-MiniLM-L-6-v2"    # D2: 크로스 인코더(리랭커)
WHISPER_MODEL_NAME = "tiny"                                 # D3: Whisper-tiny, 약 3,718만 파라미터(최초 약 72MB 다운로드)

# D2 핵심 실험의 쇼핑몰 고객센터 FAQ 4개 문장과 질문
SAMPLE_QUERY = "환불 어떻게 하나요?"
SAMPLE_DOCUMENTS = [
    "환불은 구매 후 7일 이내에 가능합니다.",
    "배송은 결제 후 2~3일 소요됩니다.",
    "오늘 서울 날씨는 맑습니다.",
    "반품 신청은 마이페이지에서 할 수 있습니다.",
]


# ─────────────────────────────── D2: 임베딩 검색 + 리랭크 ───────────────────────────────
@lru_cache(maxsize=1)
def _load_embed_model():
    """바이 인코더(all-MiniLM-L6-v2)를 한 번만 불러와 캐싱합니다."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBED_MODEL_ID, device="cpu")


@lru_cache(maxsize=1)
def _load_rerank_model():
    """크로스 인코더(ms-marco-MiniLM-L-6-v2)를 한 번만 불러와 캐싱합니다."""
    from sentence_transformers import CrossEncoder

    return CrossEncoder(RERANK_MODEL_ID, device="cpu")


def bi_encoder_rank(query, documents):
    """질문과 문서를 '따로따로' 임베딩한 뒤 코사인 유사도로 줄 세웁니다(독립 인코딩, D2 2-1)."""
    from sentence_transformers import util

    model = _load_embed_model()
    query_emb = model.encode(query, convert_to_tensor=True)
    doc_embs = model.encode(documents, convert_to_tensor=True)
    sims = util.cos_sim(query_emb, doc_embs)[0].tolist()
    return sorted(zip(documents, sims), key=lambda x: -x[1])


def cross_encoder_rank(query, documents):
    """질문과 문서를 (query, doc) '쌍으로 묶어' 함께 채점합니다(결합 인코딩, D2 2-2)."""
    model = _load_rerank_model()
    pairs = [(query, doc) for doc in documents]
    scores = model.predict(pairs)
    return sorted(zip(documents, scores.tolist()), key=lambda x: -x[1])


def search_and_rerank(query, documents):
    """같은 질문·문서를 바이 인코더와 크로스 인코더로 각각 순위를 매겨 두 개의 표로 돌려줍니다.

    반환: (바이 인코더 DataFrame, 크로스 인코더 DataFrame)
      - 바이 인코더 점수: 코사인 유사도(보통 0~1, 1에 가까울수록 비슷)
      - 크로스 인코더 점수: 0~1로 정규화되지 않은 원점수 - 같은 질문 안에서 상대 비교용(D2 FAQ Q9)
    """
    documents = [d.strip() for d in documents if d and d.strip()]
    if not documents:
        raise ValueError("문서를 1개 이상 입력하세요.")

    def _table(ranked, score_col):
        return pd.DataFrame(
            [{"순위": i, "문서": doc, score_col: round(float(score), 4)}
             for i, (doc, score) in enumerate(ranked, start=1)]
        )

    bi = _table(bi_encoder_rank(query, documents), "코사인 유사도")
    ce = _table(cross_encoder_rank(query, documents), "리랭커 점수")
    return bi, ce


# ─────────────────────────────── D3: 음성 전사(Whisper) ───────────────────────────────
@lru_cache(maxsize=1)
def _load_whisper():
    """Whisper-tiny를 한 번만 불러와 캐싱합니다(최초 1회 약 72MB 다운로드, 이후 캐시에서 로드)."""
    import whisper

    return whisper.load_model(WHISPER_MODEL_NAME, device="cpu")


def transcribe_audio(audio_path, initial_prompt=None):
    """오디오 파일 1개를 텍스트로 전사합니다. 오디오 파일을 읽으려면 시스템에 ffmpeg가 필요합니다.

    initial_prompt: "이 오디오에 이런 단어가 나올 수 있다"는 힌트(D3 3-5-1). 기본값 None(힌트 없음)
    반환 dict: text(전사 결과), language(자동 감지된 언어 코드), seconds(전사 소요 시간)
    """
    model = _load_whisper()
    start = time.perf_counter()
    # fp16=False: CPU에서는 어차피 FP32로 계산되므로, 매번 뜨는 FP16 경고(D3 2-4 심화)를 미리 꺼 둡니다.
    result = model.transcribe(str(audio_path), fp16=False, initial_prompt=initial_prompt)
    elapsed = time.perf_counter() - start
    return {"text": result["text"].strip(), "language": result["language"], "seconds": elapsed}


# ─────────────────────────────── D4: 코드 실행 샌드박스 ───────────────────────────────
def run_in_local_sandbox(code, timeout_sec=5.0, mem_limit_mb=256):
    """사용자 코드를 '별도 프로세스'에서 '시간 제한'을 걸어 실행하는 로컬 대체 샌드박스(D4 3-2·3-5).

    - 별도 프로세스(subprocess) : 자식 프로세스가 멈춰도 이 앱(부모 프로세스)은 함께 멈추지 않음
    - timeout                   : 제한 시간을 넘기면 강제 종료(무한루프 방어의 1차 방어선)
    - 임시 폴더(cwd)            : 매 실행마다 새 빈 폴더에서 실행하고 끝나면 삭제(짧은 생명주기 흉내)
    - resource.setrlimit        : macOS·Linux에서만 메모리·CPU 상한을 추가로 시도(Windows는 없음, D4 FAQ Q3)

    ⚠️ 교육용 개념 예시입니다. 같은 컴퓨터·같은 사용자 권한으로 돌기 때문에 파일 시스템·네트워크는
       격리되지 않습니다. 신뢰할 수 없는 코드는 E2B·Docker·gVisor·Firecracker 같은 검증된 격리를 쓰세요(D4 3-1).
    반환 dict: status("완료"/"시간초과(강제종료)"/"오류"), stdout, stderr, seconds, engine
    """
    child_runner = textwrap.dedent(f"""
        try:
            import resource
            mem_bytes = {int(mem_limit_mb)} * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
            cpu_sec = int({float(timeout_sec)}) + 1
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_sec, cpu_sec))
        except Exception:
            pass   # Windows 등 resource 모듈이 없는 환경 → 시간 제한(timeout)만으로 동작

        user_code = {code!r}
        exec(compile(user_code, "<sandbox>", "exec"), {{"__name__": "__main__"}})
    """)

    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="w11_sandbox_") as workdir:
        try:
            result = subprocess.run(
                # -I: 사용자 환경변수·현재 폴더의 모듈을 읽지 않는 격리 모드 / -X utf8: Windows에서도 한글 출력이 깨지지 않게
                [sys.executable, "-I", "-X", "utf8", "-c", child_runner],
                cwd=workdir,
                timeout=timeout_sec,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            status = "완료" if result.returncode == 0 else "오류"
            stdout, stderr = result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            status, stdout, stderr = "시간초과(강제종료)", "", f"{timeout_sec}초 제한을 초과해 프로세스를 강제 종료했습니다."
    return {"status": status, "stdout": stdout, "stderr": stderr,
            "seconds": time.perf_counter() - start, "engine": "로컬 대체 샌드박스"}


def try_e2b_sandbox(code, timeout_sec=30.0):
    """E2B_API_KEY 환경변수가 있을 때만 실제 E2B 클라우드 샌드박스에서 코드를 실행합니다(D4 2-4 가드 패턴).

    - 키가 없으면 즉시 None을 반환 → app.py가 run_in_local_sandbox()로 넘어감
    - 키가 있으면 create() → run_code() → kill() (짧은 생명주기, D4 2-5)
    - 이번 작업엔 외부 접속이 필요 없으므로 allow_internet_access=False (D4 2-7·2-8)
    - 키는 코드에 적지 않고 환경변수에서만 읽습니다(D4 2-4 보안 한 줄)
    """
    api_key = os.getenv("E2B_API_KEY", "").strip()
    if not api_key:
        return None

    start = time.perf_counter()
    try:
        from e2b_code_interpreter import Sandbox

        sbx = Sandbox.create(api_key=api_key, allow_internet_access=False)
        try:
            execution = sbx.run_code(code, timeout=timeout_sec)
        finally:
            sbx.kill()   # 무슨 일이 있었든 반드시 정리(에페메럴 원칙)
    except Exception as e:
        # 키가 틀렸거나(AuthenticationException), 네트워크 오류 등. 로컬로 몰래 돌리지 않고 오류를 그대로 보여줌
        return {"status": "오류", "stdout": "", "stderr": f"E2B 호출 실패 - {type(e).__name__}: {e}",
                "seconds": time.perf_counter() - start, "engine": "E2B 클라우드 샌드박스"}

    stderr = "".join(execution.logs.stderr)
    if execution.error is not None:
        stderr += f"{execution.error.name}: {execution.error.value}\n{execution.error.traceback}"
    return {"status": "오류" if execution.error is not None else "완료",
            "stdout": "".join(execution.logs.stdout), "stderr": stderr,
            "seconds": time.perf_counter() - start, "engine": "E2B 클라우드 샌드박스"}


if __name__ == "__main__":
    # 자가 테스트: D2 핵심 실험("환불 어떻게 하나요?") 재현 + 로컬 샌드박스 3케이스
    bi, ce = search_and_rerank(SAMPLE_QUERY, SAMPLE_DOCUMENTS)
    print("[바이 인코더]\n", bi.to_string(index=False))
    print("[크로스 인코더]\n", ce.to_string(index=False))
    for label, snippet, t in [
        ("정상 코드", "total = sum(range(1, 101))\nprint('1~100 합계:', total)", 5),
        ("무한루프", "while True:\n    pass", 2),
        ("예외 발생", "print(1 / 0)", 5),
    ]:
        r = run_in_local_sandbox(snippet, timeout_sec=t)
        print(f"[샌드박스] {label}: {r['status']} ({r['seconds']:.2f}초) {r['stdout'].strip()}")
    print("[E2B] 키 없음 → None 이어야 정상:", try_e2b_sandbox("print('hi')") if not os.getenv("E2B_API_KEY") else "(키 있음)")
