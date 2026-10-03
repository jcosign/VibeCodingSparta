"""매출 데이터와 리뷰 분류기의 기본 동작을 확인합니다."""

from __future__ import annotations

import unittest

from ai_backend import ask
import data
from classifier import classify, classify_rule


class ProjectTests(unittest.TestCase):
    def test_sales_are_reproducible_and_have_expected_columns(self) -> None:
        first = data.sales_df()
        second = data.sales_df()
        self.assertTrue(first.equals(second))
        self.assertEqual(len(first), 180)
        self.assertTrue({"날짜", "카테고리", "매출"}.issubset(first.columns))
        self.assertTrue((first["매출"] > 0).all())

    def test_reviews_are_reproducible_and_include_all_example_labels(self) -> None:
        first = data.reviews_df()
        second = data.reviews_df()
        self.assertTrue(first.equals(second))
        self.assertEqual(len(first), 36)
        self.assertEqual(set(first["예시감정"]), {"긍정", "부정", "중립"})

    def test_rule_classifier_handles_each_sentiment(self) -> None:
        self.assertEqual(classify_rule("배송이 빠르고 품질도 좋아요."), "긍정")
        self.assertEqual(classify_rule("제품이 고장 나서 실망스럽습니다."), "부정")
        self.assertEqual(classify_rule("오늘 상품을 받아서 확인했습니다."), "중립")

    def test_classify_uses_requested_mode(self) -> None:
        self.assertEqual(classify("배송이 좋아요.", mode="rule"), "긍정")
        with self.assertRaises(ValueError):
            classify("리뷰", mode="unknown")

    def test_mock_ai_backend_needs_no_api_key(self) -> None:
        self.assertIn("[mock 응답]", ask("테스트 질문", mode="mock"))
        with self.assertRaises(ValueError):
            ask("테스트 질문", mode="unknown")


if __name__ == "__main__":
    unittest.main()
