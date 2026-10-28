import contextlib
import io
import unittest
from pathlib import Path

from tools.build_player_stats import build_player_stats


RAW_DIR = Path.home() / "soccer-data" / "raw"
MATCH_CASES = {
    # Candidate baselines from the builder; verify these against independent
    # match records before treating them as confirmed expected values.
    "Argentina-France final": {
        "match_id": 3869685,
        "goals_by_team": {"Argentina": 3, "France": 3},
        "players": {
            "Lionel Andrés Messi Cuccittini": {
                "minutes": 124.12,
                "goals": 2,
                "shots": 5,
                "xG": 1.455,
            },
            "Alexis Mac Allister": {
                "minutes": 115.37,
                "assists": 1,
                "shots": 3,
            },
            "Kylian Mbappé Lottin": {
                "minutes": 124.12,
                "goals": 3,
                "shots": 6,
                "xG": 1.783,
            },
            "Marcus Thuram": {
                "minutes": 83.10,
                "assists": 1,
            },
            "Ousmane Dembélé": {
                "minutes": 40.53,
                "goals": 0,
            },
        },
    },
    "Wales-Iran red-card match": {
        "match_id": 3857273,
        "goals_by_team": {"Wales": 0, "Iran": 2},
        "players": {
            "Wayne Hennessey": {
                "minutes": 83.72,
                "goals": 0,
                "passes": 34,
            },
            "Roozbeh Cheshmi": {
                "minutes": 24.73,
                "goals": 1,
                "shots": 1,
            },
            "Ramin Rezaeian": {
                "minutes": 102.13,
                "goals": 1,
                "shots": 2,
            },
            "Mehdi Taremi": {
                "minutes": 102.13,
                "assists": 1,
                "shots": 2,
            },
        },
    },
    "Denmark-Tunisia group match": {
        "match_id": 3857254,
        "goals_by_team": {"Denmark": 0, "Tunisia": 0},
        "players": {
            "Andreas Christensen": {
                "minutes": 97.60,
                "goals": 0,
                "passes": 82,
                "shots": 1,
            },
        },
    },
    "Spain-Morocco shootout match": {
        "match_id": 3869220,
        "goals_by_team": {"Spain": 0, "Morocco": 0},
        "players": {
            "Aymeric Laporte": {
                "minutes": 123.05,
                "goals": 0,
                "passes": 180,
                "shots": 1,
            },
        },
    },
}

MISSING_MATCH_FILES = [
    str(RAW_DIR / "events" / f"{case['match_id']}.json")
    for case in MATCH_CASES.values()
    if not (RAW_DIR / "events" / f"{case['match_id']}.json").is_file()
] + [
    str(RAW_DIR / "lineups" / f"{case['match_id']}.json")
    for case in MATCH_CASES.values()
    if not (RAW_DIR / "lineups" / f"{case['match_id']}.json").is_file()
]


@unittest.skipIf(
    MISSING_MATCH_FILES,
    "Local StatsBomb match files are missing: " + ", ".join(MISSING_MATCH_FILES),
)
class SelectedMatchRegressionTests(unittest.TestCase):
    def test_selected_matches_against_candidate_baselines(self):
        for label, case in MATCH_CASES.items():
            with self.subTest(match=label):
                with contextlib.redirect_stdout(io.StringIO()):
                    data = build_player_stats(
                        raw_dir=RAW_DIR,
                        match_ids=[case["match_id"]],
                    )

                self.assertEqual(data["matchesProcessed"], 1)
                players = {
                    player["name"]: player
                    for player in data["players"]
                }

                goals_by_team = {
                    team: sum(
                        player["goals"]
                        for player in players.values()
                        if player["team"] == team
                    )
                    for team in case["goals_by_team"]
                }
                self.assertEqual(goals_by_team, case["goals_by_team"])

                for player_name, expected_stats in case["players"].items():
                    with self.subTest(player=player_name):
                        self.assertIn(player_name, players)
                        actual = players[player_name]

                        for metric, expected in expected_stats.items():
                            if isinstance(expected, float):
                                self.assertAlmostEqual(
                                    actual[metric],
                                    expected,
                                    places=3 if metric == "xG" else 2,
                                    msg=f"{label}: {player_name} {metric}",
                                )
                            else:
                                self.assertEqual(
                                    actual[metric],
                                    expected,
                                    msg=f"{label}: {player_name} {metric}",
                                )


if __name__ == "__main__":
    unittest.main()
