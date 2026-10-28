import unittest

from tools.build_player_stats import accumulate_event_stats, make_player


def event(event_id, event_type, player=None, period=1, **fields):
    if "pass_data" in fields:
        fields["pass"] = fields.pop("pass_data")

    return {
        "id": event_id,
        "type": {"name": event_type},
        "player": player,
        "period": period,
        **fields,
    }


class AccumulateEventStatsTests(unittest.TestCase):
    def test_event_metrics_and_shootout_exclusion(self):
        events = [
            event(
                "pass-goal",
                "Pass",
                {"id": 1, "name": "Passer"},
                pass_data={"outcome": None, "goal_assist": True},
            ),
            event(
                "pass-shot",
                "Pass",
                {"id": 1, "name": "Passer"},
                pass_data={"outcome": {"name": "Incomplete"}},
            ),
            event(
                "goal",
                "Shot",
                {"id": 2, "name": "Shooter"},
                shot={
                    "key_pass_id": "pass-goal",
                    "statsbomb_xg": 0.4,
                    "outcome": {"name": "Goal"},
                },
            ),
            event(
                "saved",
                "Shot",
                {"id": 2, "name": "Shooter"},
                shot={
                    "key_pass_id": "pass-shot",
                    "statsbomb_xg": 0.1,
                    "outcome": {"name": "Saved"},
                },
            ),
            event(
                "tackle",
                "Duel",
                {"id": 1, "name": "Passer"},
                duel={"type": {"name": "Tackle"}},
            ),
            event("interception", "Interception", {"id": 1, "name": "Passer"}),
            event(
                "recovery",
                "Ball Recovery",
                {"id": 1, "name": "Passer"},
                ball_recovery={"recovery_failure": False},
            ),
            event(
                "failed-recovery",
                "Ball Recovery",
                {"id": 1, "name": "Passer"},
                ball_recovery={"recovery_failure": True},
            ),
            event(
                "progressive-carry",
                "Carry",
                {"id": 1, "name": "Passer"},
                location=[10, 20],
                carry={"end_location": [20, 25]},
            ),
            event(
                "short-carry",
                "Carry",
                {"id": 1, "name": "Passer"},
                location=[10, 20],
                carry={"end_location": [19, 25]},
            ),
            event(
                "backward-carry",
                "Carry",
                {"id": 1, "name": "Passer"},
                location=[20, 20],
                carry={"end_location": [10, 25]},
            ),
            event(
                "shootout-goal",
                "Shot",
                {"id": 2, "name": "Shooter"},
                period=5,
                shot={
                    "key_pass_id": "pass-goal",
                    "statsbomb_xg": 1.0,
                    "outcome": {"name": "Goal"},
                },
            ),
            event("no-player", "Interception"),
        ]
        players = {
            "1": make_player(1, "Passer", 10, "Team"),
            "2": make_player(2, "Shooter", 10, "Team"),
        }

        accumulate_event_stats(events, players)

        passer = players["1"]
        self.assertEqual(passer["passes"], 2)
        self.assertEqual(passer["completedPasses"], 1)
        self.assertEqual(passer["keyPasses"], 2)
        self.assertEqual(passer["assists"], 1)
        self.assertAlmostEqual(passer["xA"], 0.5)
        self.assertEqual(passer["tackles"], 1)
        self.assertEqual(passer["interceptions"], 1)
        self.assertEqual(passer["ballRecoveries"], 1)
        self.assertEqual(passer["progressiveCarries"], 1)

        shooter = players["2"]
        self.assertEqual(shooter["shots"], 2)
        self.assertEqual(shooter["goals"], 1)
        self.assertAlmostEqual(shooter["xG"], 0.5)


if __name__ == "__main__":
    unittest.main()
