from decimal import Decimal
import unittest

from testapp.scoring_engine import (
    ChoiceQuestion,
    ComputationalQuestion,
    ShortAnswerQuestion,
    grade_computational,
    grade_multiple_choice_exact,
    grade_multiple_choice_partial,
    grade_short_answer,
    grade_single_choice,
    total_score,
)


class ScoringEngineTests(unittest.TestCase):
    def test_single_choice_correct(self):
        q = ChoiceQuestion(points=Decimal("2"), correct_option_ids={10})
        result = grade_single_choice(q, [10])
        self.assertTrue(result.is_correct)
        self.assertEqual(result.awarded_points, Decimal("2"))

    def test_single_choice_wrong_multiple_selected(self):
        q = ChoiceQuestion(points=Decimal("2"), correct_option_ids={10})
        result = grade_single_choice(q, [10, 11])
        self.assertFalse(result.is_correct)
        self.assertEqual(result.awarded_points, Decimal("0"))

    def test_multiple_choice_exact(self):
        q = ChoiceQuestion(points=Decimal("3"), correct_option_ids={1, 2})
        good = grade_multiple_choice_exact(q, [1, 2])
        bad = grade_multiple_choice_exact(q, [1])
        self.assertEqual(good.awarded_points, Decimal("3"))
        self.assertEqual(bad.awarded_points, Decimal("0"))

    def test_multiple_choice_partial(self):
        q = ChoiceQuestion(points=Decimal("4"), correct_option_ids={1, 2, 3, 4})
        result = grade_multiple_choice_partial(q, [1, 2, 9])
        self.assertFalse(result.is_correct)
        self.assertEqual(result.awarded_points, Decimal("1.00"))

    def test_short_answer_case_insensitive(self):
        q = ShortAnswerQuestion(points=Decimal("5"), accepted_answers={"Photosynthesis", "PHOTO"}, case_sensitive=False)
        result = grade_short_answer(q, " photosynthesis ")
        self.assertTrue(result.is_correct)
        self.assertEqual(result.awarded_points, Decimal("5"))

    def test_short_answer_empty(self):
        q = ShortAnswerQuestion(points=Decimal("1"), accepted_answers={"x"})
        result = grade_short_answer(q, "")
        self.assertFalse(result.is_correct)
        self.assertEqual(result.awarded_points, Decimal("0"))

    def test_computational_with_tolerance(self):
        q = ComputationalQuestion(points=Decimal("6"), expected_answer=Decimal("3.14159"), tolerance=Decimal("0.01"))
        result = grade_computational(q, Decimal("3.14"))
        self.assertTrue(result.is_correct)
        self.assertEqual(result.awarded_points, Decimal("6"))

    def test_computational_outside_tolerance(self):
        q = ComputationalQuestion(points=Decimal("6"), expected_answer=Decimal("100"), tolerance=Decimal("0.5"))
        result = grade_computational(q, Decimal("101"))
        self.assertFalse(result.is_correct)
        self.assertEqual(result.awarded_points, Decimal("0"))

    def test_total_score(self):
        q = ChoiceQuestion(points=Decimal("2"), correct_option_ids={10})
        r1 = grade_single_choice(q, [10])
        r2 = grade_single_choice(q, [99])
        self.assertEqual(total_score([r1, r2]), Decimal("2.00"))


if __name__ == "__main__":
    unittest.main()
