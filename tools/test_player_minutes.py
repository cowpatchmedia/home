import unittest

from tools.build_player_stats import calculate_minutes_from_events


def event(event_type, minute, second=0, period=1, **fields):
    return {
        "type": {"name": event_type},
        "minute": minute,
        "second": second,
        "period": period,
        **fields,
    }


class CalculateMinutesTests(unittest.TestCase):
    def test_substitutions_and_extra_time_use_match_elapsed_clock(self):
        events = [
            event(
                "Starting XI",
                0,
                tactics={
                    "lineup": [
                        {"player": {"id": 1}},
                        {"player": {"id": 2}},
                    ]
                },
            ),
            event(
                "Substitution",
                30,
                15,
                player={"id": 1},
                substitution={"replacement": {"id": 3}},
            ),
            event("Half End", 47, period=1),
            event("Half End", 124, 7, period=4),
            event(
                "Substitution",
                125,
                0,
                period=5,
                player={"id": 2},
                substitution={"replacement": {"id": 4}},
            ),
        ]

        minutes = calculate_minutes_from_events(events)

        self.assertAlmostEqual(minutes["1"], 30.25)
        self.assertAlmostEqual(minutes["2"], 124 + 7 / 60)
        self.assertAlmostEqual(minutes["3"], 124 + 7 / 60 - 30.25)
        self.assertNotIn("4", minutes)

    def test_red_cards_stop_counting_playing_time(self):
        for card_name in ("Red Card", "Second Yellow"):
            with self.subTest(card_name=card_name):
                events = [
                    event(
                        "Starting XI",
                        0,
                        tactics={"lineup": [{"player": {"id": 1}}]},
                    ),
                    event(
                        "Foul Committed",
                        60,
                        30,
                        period=2,
                        player={"id": 1},
                        foul_committed={"card": {"name": card_name}},
                    ),
                    event("Half End", 98, period=2),
                ]

                minutes = calculate_minutes_from_events(events)

                self.assertAlmostEqual(minutes["1"], 60.5)

    def test_returns_no_minutes_when_match_end_is_missing(self):
        events = [
            event(
                "Starting XI",
                0,
                tactics={"lineup": [{"player": {"id": 1}}]},
            )
        ]

        self.assertEqual(calculate_minutes_from_events(events), {})


if __name__ == "__main__":
    unittest.main()
