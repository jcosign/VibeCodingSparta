"""규칙 기반 리뷰 감정 분류기와 선택형 Hugging Face 분류기."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from importlib import import_module
from typing import Any


logger = logging.getLogger(__name__)
LABELS = ("긍정", "부정", "중립")
_POSITIVE_WORDS = (
    "좋",
    "만족",
    "추천",
    "빠르",
    "훌륭",
    "편리",
    "예쁘",
    "잘 샀",
    "꼼꼼",
    "감사",
    "최고",
)
_NEGATIVE_WORDS = (
    "나쁘",
    "별로",
    "실망",
    "불량",
    "고장",
    "늦",
    "엉망",
    "불편",
    "환불",
    "싫",
    "않",
    "최악",
)


def classify_rule(text: str) -> str:
    """긍정·부정 단어 수를 비교해 리뷰 하나를 분류합니다."""
    if not isinstance(text, str):
        raise TypeError("리뷰는 문자열이어야 합니다.")

    normalized = text.strip().casefold()
    positive_count = sum(word in normalized for word in _POSITIVE_WORDS)
    negative_count = sum(word in normalized for word in _NEGATIVE_WORDS)
    if positive_count > negative_count:
        return "긍정"
    if negative_count > positive_count:
        return "부정"
    return "중립"


@lru_cache(maxsize=1)
def _hf_pipeline() -> Any:
    """Hugging Face 파이프라인은 처음 필요한 순간에만 준비합니다."""
    pipeline = import_module("transformers").pipeline
    model_name = os.getenv(
        "HF_MODEL",
        "cardiffnlp/twitter-xlm-roberta-base-sentiment",
    )
    return pipeline("sentiment-analysis", model=model_name)


def classify_hf(text: str) -> str:
    """선택형 다국어 감정 모델로 리뷰를 분류합니다."""
    if not isinstance(text, str):
        raise TypeError("리뷰는 문자열이어야 합니다.")
    if not text.strip():
        return "중립"

    sentiment_pipeline = _hf_pipeline()
    result = sentiment_pipeline(text[:512])[0]
    label = str(result["label"]).casefold()
    if label.startswith("label_"):
        try:
            label_id = int(label.removeprefix("label_"))
        except ValueError:
            label_id = -1
        config = getattr(getattr(sentiment_pipeline, "model", None), "config", None)
        label_names = getattr(config, "id2label", {})
        label = str(label_names.get(label_id, label)).casefold()

    if "positive" in label or "긍정" in label:
        return "긍정"
    if "negative" in label or "부정" in label:
        return "부정"
    if "neutral" in label or "중립" in label:
        return "중립"
    raise ValueError(f"Hugging Face 모델이 알 수 없는 감정 라벨을 반환했습니다: {result['label']}")


def classify(text: str, mode: str | None = None) -> str:
    """CLF_MODE=rule(기본) 또는 hf로 리뷰 하나를 분류합니다."""
    selected_mode = (mode or os.getenv("CLF_MODE", "rule")).strip().casefold()
    if selected_mode == "rule":
        return classify_rule(text)
    if selected_mode == "hf":
        try:
            return classify_hf(text)
        except Exception as error:
            logger.warning(
                "Hugging Face 분류에 실패해 규칙 기반 분류기로 대체합니다: %s",
                error,
                exc_info=True,
            )
            return classify_rule(text)
    raise ValueError(f"지원하지 않는 CLF_MODE입니다: {selected_mode!r} (rule 또는 hf)")


if __name__ == "__main__":
    for sample in (
        "배송이 빠르고 품질도 좋아요!",
        "제품이 고장 나서 정말 실망스럽습니다.",
        "오늘 상품을 받아서 사용해 보고 있어요.",
    ):
        print(f"{classify(sample)}: {sample}")
