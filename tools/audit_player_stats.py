
import json
import math
from pathlib import Path

DATA_FILE = Path("data/player_stats.json")

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
players = data["players"]

# Each item maps a displayed metric to its rate and raw-count fields.
metrics = [
    ("goalsPer90", "goals", "Goals / 90"),
    ("xGPer90", "xG", "xG / 90"),
    ("xAPer90", "xA", "xA / 90"),
    ("tacklesPer90", "tackles", "Tackles / 90"),
    ("interceptionsPer90", "interceptions", "Interceptions / 90"),
    ("ballRecoveriesPer90", "ballRecoveries", "Ball recoveries / 90"),
    ("passesPer90", "passes", "Passes / 90"),
    (
        "progressiveCarriesPer90",
        "progressiveCarries",
        "Carries advancing 10+ units / 90",
    ),
]

def is_goalkeeper(player):
    position = str(player.get("position") or "").lower()
    return "goalkeeper" in position

outfield_players = [
    player for player in players
    if not is_goalkeeper(player)
]

print(f"Matches processed: {data.get('matchesProcessed')}")
print(f"All player records: {len(players)}")
print(f"Outfield records by current position field: {len(outfield_players)}")
print(
    "Outfield players with minutes:",
    sum(p.get("minutes", 0) > 0 for p in outfield_players)
)

# Inspect the highest rates, retaining raw counts and minutes.
for rate_key, count_key, label in metrics:
    eligible = [
        p for p in outfield_players
        if p.get("minutes", 0) > 0
        and p.get(rate_key) is not None
        and math.isfinite(float(p[rate_key]))
    ]

    eligible.sort(
        key=lambda p: float(p[rate_key]),
        reverse=True
    )

    print(f"\n{'=' * 78}")
    print(label)
    print(f"{'=' * 78}")
    print(f"{'Player':26} {'Position':22} {'Minutes':>8} {'Count':>8} {'Per 90':>9}")

    for player in eligible[:15]:
        print(
            f"{player.get('name', 'Unknown')[:26]:26} "
            f"{str(player.get('position') or 'Unknown')[:22]:22} "
            f"{player.get('minutes', 0):8.1f} "
            f"{float(player.get(count_key, 0)):8.2f} "
            f"{float(player[rate_key]):9.2f}"
        )

# Flag records where short playing time may make rates volatile.
print(f"\n{'=' * 78}")
print("Players with less than 90 minutes and unusually high rates")
print(f"{'=' * 78}")

for rate_key, count_key, label in metrics:
    candidates = [
        p for p in outfield_players
        if 0 < p.get("minutes", 0) < 90
        and p.get(rate_key) is not None
        and math.isfinite(float(p[rate_key]))
    ]
    candidates.sort(
        key=lambda p: float(p[rate_key]),
        reverse=True
    )

    if candidates:
        print(f"\n{label}:")
        for p in candidates[:5]:
            print(
                f"  {p.get('name', 'Unknown')}: "
                f"{p.get('minutes', 0):.1f} min, "
                f"{count_key}={p.get(count_key, 0)}, "
                f"rate={float(p[rate_key]):.2f}"
            )
