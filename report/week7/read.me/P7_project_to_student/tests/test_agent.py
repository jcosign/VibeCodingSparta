import unittest
from unittest.mock import patch

from agent import run_agent
from ai_backend import complete
from tools import CATEGORIES, avg_order, calc, lookup_sales, total_sales


class ToolTests(unittest.TestCase):
    def test_calc_uses_safe_arithmetic(self):
        self.assertEqual(calc("306+231")["result"], 537)
        with self.assertRaises(ValueError):
            calc("__import__('os').system('whoami')")
        with self.assertRaises(ValueError):
            calc("1000000000001")

    def test_sales_tools_are_consistent(self):
        self.assertEqual(len(CATEGORIES), 5)
        self.assertEqual(
            sum(row["revenue"] for row in (lookup_sales(name) for name in CATEGORIES)),
            total_sales()["revenue"],
        )
        item = avg_order("의류")
        self.assertEqual(item["average"], round(item["revenue"] / item["orders"], 2))


class AgentTests(unittest.TestCase):
    def test_sample_questions_choose_expected_tools(self):
        samples = {
            "의류 매출 알려줘": "lookup_sales",
            "총매출은 얼마야?": "total_sales",
            "306+231": "calc",
            "의류 객단가 알려줘": "avg_order",
        }
        for question, expected in samples.items():
            with self.subTest(question=question):
                answer, trace = run_agent(question, mode="mock")
                self.assertEqual(trace[-2]["step"], "도구 선택")
                self.assertIn(expected, trace[-2]["detail"])
                self.assertTrue(answer)

    def test_unknown_question_is_rejected_safely(self):
        answer, trace = run_agent("오늘 날씨 어때?", mode="mock")
        self.assertIn("도구가 없어요", answer)
        self.assertEqual(trace[-1]["step"], "도구 선택")

    def test_multistep_question_uses_lookup_then_calculator(self):
        answer, trace = run_agent("의류 매출과 주문당 평균을 함께 알려줘", mode="mock")
        selections = [step["detail"].split(":", 1)[0] for step in trace if step["step"] == "도구 선택"]
        executions = [step["detail"].split(":", 1)[0] for step in trace if step["step"] == "도구 실행"]

        self.assertEqual(selections, ["lookup_sales", "calc"])
        self.assertEqual(executions, ["lookup_sales", "calc"])
        self.assertIn("265만원", answer)
        self.assertIn("9.14만원", answer)

    def test_missing_llm_key_falls_back_to_mock(self):
        from unittest.mock import patch

        with patch.dict("os.environ", {}, clear=True):
            answer, trace = run_agent("의류 매출?", mode="anthropic")
        self.assertIn("만원", answer)
        self.assertTrue(any(step["step"] == "LLM 폴백" for step in trace))
        self.assertEqual(next(step["detail"] for step in trace if step["step"] == "모드"), "mock")

    def test_unknown_tool_mode_is_reported(self):
        answer, trace = run_agent("의류 매출?", mode="not-a-mode")
        self.assertIn("지원하지 않는", answer)
        self.assertEqual(trace[-1]["step"], "모드 오류")

    def test_approval_gate_blocks_tool_until_matching_approval(self):
        calls = []
        protected_tool = {
            "name": "protected_demo",
            "desc": "approval-gate test",
            "parameters": {"value": "test value"},
            "requires_approval": True,
            "function": lambda value: calls.append(value) or {"value": value},
        }

        with (
            patch("agent._decide_mock", return_value=("protected_demo", {"value": "ready"}, "test")),
            patch.dict("agent.TOOL_BY_NAME", {"protected_demo": protected_tool}),
        ):
            waiting_answer, waiting_trace = run_agent("test protected tool", mode="mock")
            self.assertIn("승인", waiting_answer)
            self.assertEqual(waiting_trace[-1]["step"], "승인 대기")
            self.assertEqual(calls, [])

            wrong_answer, wrong_trace = run_agent(
                "test protected tool",
                mode="mock",
                approved_tool="another_tool",
            )
            self.assertEqual(wrong_trace[-1]["step"], "승인 대기")
            self.assertEqual(calls, [])

            approved_answer, approved_trace = run_agent(
                "test protected tool",
                mode="mock",
                approved_tool="protected_demo",
            )

        self.assertEqual(calls, ["ready"])
        self.assertEqual(approved_trace[-2]["step"], "승인")
        self.assertIn('"value": "ready"', approved_trace[-1]["detail"])
        self.assertTrue(approved_answer)


class BackendTests(unittest.TestCase):
    def test_mock_backend_needs_no_credentials(self):
        result = complete("요약해줘", mode="mock")
        self.assertEqual(result["mode"], "mock")
        self.assertIsNone(result["fallback"])
        self.assertIn("요약해줘", result["text"])

    def test_missing_provider_key_is_reported_as_fallback(self):
        from unittest.mock import patch

        with patch.dict("os.environ", {}, clear=True):
            result = complete("요약해줘", mode="claude")
        self.assertEqual(result["mode"], "mock")
        self.assertIn("ANTHROPIC_API_KEY", result["fallback"])


if __name__ == "__main__":
    unittest.main()
