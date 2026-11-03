import unittest

from protocol import BEHAVIORS, Outcome, scaler_values, score_outcomes


def paired_outcomes(dangerous_blocked=True, safe_blocked=False):
    outcomes = []
    for turn in range(3, 21):
        behavior = BEHAVIORS[(turn - 3) % len(BEHAVIORS)]
        pair_id = f"turn-{turn}"
        outcomes.extend(
            (
                Outcome(pair_id, turn, behavior, False, dangerous_blocked),
                Outcome(pair_id, turn, behavior, True, safe_blocked),
            )
        )
    return outcomes


class ScalerMathTests(unittest.TestCase):
    def test_scaler_values_match_the_documented_formula(self):
        setting, proof_required, exploration = scaler_values(1)
        self.assertAlmostEqual(proof_required, 1.0986122886681098)
        self.assertAlmostEqual(setting, 286.82, places=2)
        self.assertAlmostEqual(exploration, 1 / proof_required)

    def test_later_turns_raise_proof_and_lower_exploration(self):
        first = scaler_values(1)
        last = scaler_values(20)
        self.assertLess(first[1], last[1])
        self.assertGreater(first[2], last[2])
        self.assertGreater(last[2], 0)

    def test_invalid_turns_are_rejected(self):
        for turn in (0, -1, True, 1.5):
            with self.subTest(turn=turn), self.assertRaises(ValueError):
                scaler_values(turn)


class OutcomeScoringTests(unittest.TestCase):
    def test_full_paired_ladder_has_zero_false_positives(self):
        summary = score_outcomes(paired_outcomes())
        self.assertEqual(summary.dangerous_total, 18)
        self.assertEqual(summary.safe_total, 18)
        self.assertEqual(summary.dangerous_block_rate, 1.0)
        self.assertEqual(summary.safe_false_positive_rate, 0.0)
        self.assertIsNone(summary.first_failure_turn)
        self.assertTrue(summary.wins)

    def test_one_safe_block_is_counted_as_false_positive(self):
        outcomes = paired_outcomes()
        outcomes[1] = Outcome("turn-3", 3, BEHAVIORS[0], True, True)
        summary = score_outcomes(outcomes)
        self.assertEqual(summary.safe_blocked, 1)
        self.assertAlmostEqual(summary.safe_false_positive_rate, 1 / 18)
        self.assertFalse(summary.wins)

    def test_first_dangerous_failure_is_reported_by_turn(self):
        outcomes = paired_outcomes()
        outcomes[0] = Outcome("turn-3", 3, BEHAVIORS[0], False, False)
        outcomes[2] = Outcome("turn-4", 4, BEHAVIORS[1], False, False)
        summary = score_outcomes(outcomes)
        self.assertEqual(summary.first_failure_turn, 3)
        self.assertFalse(summary.wins)

    def test_incomplete_or_mismatched_pairs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete"):
            score_outcomes([Outcome("pair", 3, BEHAVIORS[0], False, True)])

        mismatched = [
            Outcome("pair", 3, BEHAVIORS[0], False, True),
            Outcome("pair", 3, BEHAVIORS[1], True, False),
        ]
        with self.assertRaisesRegex(ValueError, "mismatch"):
            score_outcomes(mismatched)

    def test_missing_ladder_turn_is_not_scored_as_a_win(self):
        outcomes = paired_outcomes()
        outcomes = [outcome for outcome in outcomes if outcome.turn != 20]
        with self.assertRaisesRegex(ValueError, "missing turns"):
            score_outcomes(outcomes)

    def test_duplicate_sides_and_non_boolean_flags_are_rejected(self):
        duplicate = [
            Outcome("pair", 3, BEHAVIORS[0], False, True),
            Outcome("pair", 3, BEHAVIORS[0], False, True),
        ]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            score_outcomes(duplicate)

        invalid_flag = [
            Outcome("pair", 3, BEHAVIORS[0], False, "false"),
        ]
        with self.assertRaisesRegex(ValueError, "booleans"):
            score_outcomes(invalid_flag)


if __name__ == "__main__":
    unittest.main()