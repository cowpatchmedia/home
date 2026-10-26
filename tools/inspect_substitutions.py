
import json
from pathlib import Path

raw_dir = Path.home() / "soccer-data" / "raw"
match_id = "3869685"

events_path = raw_dir / "events" / f"{match_id}.json"

with events_path.open(encoding="utf-8") as file:
    events = json.load(file)

    lineups_path = raw_dir / "lineups" / f"{match_id}.json"

with lineups_path.open(encoding="utf-8") as file:
    lineups = json.load(file)

print("STARTING XI EVENTS")

for event in events:
    if event.get("type", {}).get("name") != "Starting XI":
        continue

    players = [
        item.get("player", {}).get("name")
        for item in event.get("tactics", {}).get("lineup", [])
    ]

    print({
        "team": event.get("team", {}).get("name"),
        "players": players,
    })

print("\nSUBSTITUTIONS")

for event in events:
    if event.get("type", {}).get("name") != "Substitution":
        continue

    replacement = event.get("substitution", {}).get("replacement", {})

    print({
        "period": event.get("period"),
        "timestamp": event.get("timestamp"),
        "player_off": event.get("player", {}).get("name"),
        "player_on": replacement.get("name"),
    })

print("\nPERIOD ENDINGS")

seen = set()

for event in events:
    if event.get("type", {}).get("name") != "Half End":
        continue

    key = (
        event.get("period"),
        event.get("timestamp"),
    )

    if key in seen:
        continue

    seen.add(key)

    print({
        "period": event.get("period"),
        "timestamp": event.get("timestamp"),
    })

print("\nDEMBÉLÉ POSITION INTERVALS")

for team in lineups:
    for player in team.get("lineup", []):
        if player.get("player_name") == "Ousmane Dembélé":
            print(player.get("positions", []))

print("\nMESSI POSITION INTERVALS")

for team in lineups:
    for player in team.get("lineup", []):
        if player.get("player_name") == "Lionel Andrés Messi Cuccittini":
            print(player.get("positions", []))