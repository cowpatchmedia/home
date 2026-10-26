
import json
from pathlib import Path

raw_dir = Path.home() / "soccer-data" / "raw"
match_id = "3869685"

lineup_path = raw_dir / "lineups" / f"{match_id}.json"
events_path = raw_dir / "events" / f"{match_id}.json"

with lineup_path.open(encoding="utf-8") as file:
    lineups = json.load(file)

with events_path.open(encoding="utf-8") as file:
    events = json.load(file)

# Print Messi's original position intervals exactly as stored.
for team in lineups:
    for player in team.get("lineup", []):
        if "Messi" in player.get("player_name", ""):
            print(f"\nPlayer: {player['player_name']}")
            print("Raw position intervals:")

            for interval in player.get("positions", []):
                print(interval)

# Print the match's Half End events.
print("\nHalf End events:")

for event in events:
    if event.get("type", {}).get("name") == "Half End":
        print({
            "period": event.get("period"),
            "minute": event.get("minute"),
            "second": event.get("second"),
            "timestamp": event.get("timestamp"),
        })
