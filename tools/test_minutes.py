
import ast
import json
from pathlib import Path

project_dir = Path(__file__).resolve().parent.parent
builder_file = project_dir / "tools" / "build_player_stats.py"
events_file = Path.home() / "soccer-data" / "raw" / "events" / "3869685.json"

# Load only the saved minutes helper, without running the full builder.
source = builder_file.read_text(encoding="utf-8")
tree = ast.parse(source)

helper = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "calculate_minutes_from_events"
)

namespace = {}
exec(compile(ast.Module(body=[helper], type_ignores=[]), str(builder_file), "exec"), namespace)

with events_file.open(encoding="utf-8") as file:
    events = json.load(file)

minutes = namespace["calculate_minutes_from_events"](events)

# Build a player-ID-to-name lookup from the match events.
names = {}

for event in events:
    if event.get("type", {}).get("name") == "Starting XI":
        for entry in event.get("tactics", {}).get("lineup", []):
            player = entry.get("player", {})
            if player.get("id") is not None:
                names[str(player["id"])] = player.get("name", "Unknown")

    player = event.get("player")
    if player and player.get("id") is not None:
        names[str(player["id"])] = player.get("name", "Unknown")

    replacement = event.get("substitution", {}).get("replacement", {})
    if replacement.get("id") is not None:
        names[str(replacement["id"])] = replacement.get("name", "Unknown")

print(f"Players with recorded minutes: {len(minutes)}")
print("\nKey player results:")

for player_id, name in names.items():
    if name in ("Lionel Messi", "Kylian Mbappé", "Kylian Mbappe", "Ousmane Dembélé", "Ousmane Dembele"):
        print(f"{name}: {minutes.get(player_id, 0):.2f} minutes")

print("\nLowest and highest minute totals:")
for player_id, total in sorted(minutes.items(), key=lambda item: item[1])[:5]:
    print(f"{names.get(player_id, player_id)}: {total:.2f} minutes")

for player_id, total in sorted(minutes.items(), key=lambda item: item[1], reverse=True)[:5]:
    print(f"{names.get(player_id, player_id)}: {total:.2f} minutes")
