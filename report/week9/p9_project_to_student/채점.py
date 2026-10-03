"""과제의 6개 기본 지표를 간단히 정적 검사합니다."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def _functions(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _check(root: Path) -> list[tuple[str, bool, str]]:
    data_functions = _functions(root / "data.py")
    classifier_functions = _functions(root / "classifier.py")
    data_source = _source(root / "data.py")
    classifier_source = _source(root / "classifier.py")
    app_source = _source(root / "app.py")
    backend_source = _source(root / "ai_backend.py")
    submitted = any(root.glob("*.py"))

    return [
        ("① 제출", submitted, "파이썬 파일 제출됨"),
        (
            "② 데이터(data.py)",
            {"sales_df", "reviews_df"}.issubset(data_functions) and "numpy" in data_source,
            "data.py에 sales_df·reviews_df와 합성 데이터 생성 코드가 있음",
        ),
        (
            "③ 분류기(classifier)",
            {"classify", "classify_rule", "classify_hf"}.issubset(classifier_functions)
            and "CLF_MODE" in classifier_source,
            "classify()에 rule 기본·hf 선택 경로가 있음",
        ),
        (
            "④ 대시보드 탭",
            all(marker in app_source for marker in ("st.tabs", ".metric(", "st.line_chart", "st.bar_chart")),
            "탭·매출 지표·일별/카테고리 그래프가 있음",
        ),
        (
            "⑤ 분류 탭(표·CSV)",
            all(marker in app_source for marker in ("classify(", "st.dataframe(", "st.download_button(")),
            "리뷰 분류·결과 표·CSV 다운로드가 있음",
        ),
        (
            "⑥ 멀티 백엔드/HF",
            "def ask(" in backend_source or "classify_hf" in classifier_functions,
            "ai_backend.py의 ask() 또는 Hugging Face 연동이 있음",
        ),
    ]


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    results = _check(root)
    earned = sum(10 for _, passed, _ in results if passed)
    required = sum(passed for _, passed, _ in results[1:])
    grade = "미제출" if not results[0][1] else "상" if required >= 4 else "중" if required == 3 else "하"

    for title, passed, detail in results:
        status = "O" if passed else "X"
        print(f"{title:<22} [{status}] {10 if passed else 0:>2}점  · {detail}")
    print("-" * 60)
    print(f"총점: {earned} / 60  |  나머지(②~⑥) 충족: {required}개  →  등급: {grade}")


if __name__ == "__main__":
    main()
