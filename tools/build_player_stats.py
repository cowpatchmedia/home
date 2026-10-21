
import json
from pathlib import Path

# The raw files stay outside the website repository.
RAW_DIR = Path.home() / "soccer-data" / "raw"

# Save the finished data in the website's data folder.
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_DIR / "data" / "player_stats.json"

MATCH_IDS = [3857276, 3857271, 3857296, 3857274]


def read_json(path):
    """Read a JSON file and return its contents."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def parse_clock(clock):
    """Convert a time such as '64:10' into seconds."""
    if not clock:
        return None

    minutes, seconds = clock.split(":")
    return int(minutes) * 60 + int(seconds)


def make_player(player_id, name, team_id, team_name):
    """Create one player's statistics record."""
    return {
        "id": str(player_id),
        "name": name,
        "teamId": team_id,
        "team": team_name,
        "position": "Unknown",
        "minutes": 0,
        "goals": 0,
        "assists": 0,
        "shots": 0,
        "passes": 0,
        "keyPasses": 0,
        "tackles": 0,
        "interceptions": 0,
    }


players = {}

for match_id in MATCH_IDS:
    print(f"Processing match {match_id}...")

    events = read_json(RAW_DIR / "events" / f"{match_id}.json")
    lineups = read_json(RAW_DIR / "lineups" / f"{match_id}.json")
    # Estimate the match's final elapsed time from Half End events.
    half_end_times = [
        event.get("minute", 0) * 60 + event.get("second", 0)
        for event in events
        if event.get("type", {}).get("name") == "Half End"
    ]

    match_end_seconds = max(half_end_times) if half_end_times else None

    # Register players and estimate their minutes from lineup intervals.
    for team in lineups:
        for entry in team["lineup"]:
            player_id = entry["player_id"]
            key = str(player_id)

            if key not in players:
                players[key] = make_player(
                    player_id,
                    entry["player_name"],
                    team["team_id"],
                    team["team_name"],
                )

            record = players[key]
            intervals = entry.get("positions", [])
            longest_position = None
            longest_duration = -1

            for interval in intervals:
                start = parse_clock(interval.get("from"))
                end = parse_clock(interval.get("to"))

                # A missing end time means the player remained on the
                # field until the match ended.
                if end is None:
                    end = match_end_seconds

                if start is not None and end is not None and end >= start:
                    duration = end - start
                    record["minutes"] += duration / 60

                    if duration > longest_duration:
                        longest_duration = duration
                        longest_position = interval.get("position")

            if longest_position:
                record["position"] = longest_position

    # Link shots to the passes that created them.
    events_by_id = {event["id"]: event for event in events}
    key_pass_ids = set()

    for event in events:
        if event.get("type", {}).get("name") == "Shot":
            key_pass_id = event.get("shot", {}).get("key_pass_id")
            if key_pass_id:
                key_pass_ids.add(key_pass_id)

    # Count player actions.
    for event in events:
        player_info = event.get("player")
        if not player_info:
            continue

        player_id = str(player_info["id"])

        # Usually these players are already registered from the lineups.
        if player_id not in players:
            team_info = event.get("team", {})
            players[player_id] = make_player(
                player_id,
                player_info["name"],
                team_info.get("id"),
                team_info.get("name", "Unknown"),
            )

        record = players[player_id]
        event_type = event.get("type", {}).get("name")

        if event_type == "Pass":
            record["passes"] += 1

            if event["id"] in key_pass_ids:
                record["keyPasses"] += 1

        elif event_type == "Shot":
            record["shots"] += 1
            shot = event.get("shot", {})

            if shot.get("outcome", {}).get("name") == "Goal":
                record["goals"] += 1

                # Credit an assist when the goal references a key pass.
                key_pass_id = shot.get("key_pass_id")
                assist_event = events_by_id.get(key_pass_id)

                if assist_event and assist_event.get("player"):
                    assister_id = str(assist_event["player"]["id"])
                    if assister_id in players:
                        players[assister_id]["assists"] += 1

        elif event_type == "Duel":
            duel_type = event.get("duel", {}).get("type", {}).get("name")
            if duel_type == "Tackle":
                record["tackles"] += 1

        elif event_type == "Interception":
            record["interceptions"] += 1


# Prepare the compact output for the website.
output_players = []

for player in players.values():
    minutes = player["minutes"]

    # Convert accumulated seconds to minutes and round for display.
    player["minutes"] = round(minutes, 2)

    # Calculate per-90 rates only when minutes are available.
    for metric in [
        "goals", "assists", "shots", "passes",
        "keyPasses", "tackles", "interceptions"
    ]:
        rate_name = metric + "Per90"
        player[rate_name] = (
            round(player[metric] * 90 / minutes, 3)
            if minutes > 0 else 0
        )

    output_players.append(player)

output_players.sort(key=lambda player: player["name"].lower())

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

output = {
    "source": "StatsBomb Open Data",
    "competition": "FIFA World Cup",
    "season": "2022",
    "matchesProcessed": len(MATCH_IDS),
    "metricNotes": {
        "minutes": "Summed lineup position intervals; validate before analysis.",
        "goals": "Goal outcomes on shot events; own goals excluded.",
        "assists": "Goal shots with a linked key pass.",
        "keyPasses": "Passes linked to a shot event.",
        "tackles": "Tackle-type duel events, including attempts.",
        "interceptions": "Interception events."
    },
    "players": output_players
}

with OUTPUT_FILE.open("w", encoding="utf-8") as file:
    json.dump(output, file, ensure_ascii=False, indent=2)

print(f"\nFinished! Processed {len(MATCH_IDS)} matches.")
print(f"Players found: {len(output_players)}")
print(f"Saved results to: {OUTPUT_FILE}")
