
import json
from pathlib import Path

# Raw data stays outside the website repository.
RAW_DIR = Path.home() / "soccer-data" / "raw"

# Save the finished data in the website's data folder.
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_DIR / "data" / "player_stats.json"

MATCH_IDS = [3857276, 3857271, 3857296, 3857274]

# Provisional progressive-carry threshold in StatsBomb pitch units.
# We will validate the coordinate direction before relying on this metric.
PROGRESSIVE_CARRY_DISTANCE = 10


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
        "xG": 0.0,
        "xA": 0.0,
        "passes": 0,
        "completedPasses": 0,
        "keyPasses": 0,
        "tackles": 0,
        "interceptions": 0,
        "ballRecoveries": 0,
        "progressiveCarries": 0,
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
            longest_position = None
            longest_duration = -1

            for interval in entry.get("positions", []):
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

    # Index events so shots can be linked to the passes that created them.
    events_by_id = {event["id"]: event for event in events}

    key_pass_ids = set()

    for event in events:
        if event.get("type", {}).get("name") == "Shot":
            key_pass_id = event.get("shot", {}).get("key_pass_id")
            if key_pass_id:
                key_pass_ids.add(key_pass_id)

    # Count actions and derive attacking, defending, and progression metrics.
    for event in events:
        player_info = event.get("player")
        if not player_info:
            continue

        player_id = str(player_info["id"])

        if player_id not in players:
            team_info = event.get("team", {})
            players[player_id] = make_player(
                player_info["id"],
                player_info["name"],
                team_info.get("id"),
                team_info.get("name", "Unknown"),
            )

        record = players[player_id]
        event_type = event.get("type", {}).get("name")

        if event_type == "Pass":
            record["passes"] += 1

            # In StatsBomb data, a pass without an outcome is normally
            # completed; an outcome records an unsuccessful result.
            pass_data = event.get("pass", {})

            if pass_data.get("outcome") is None:
                record["completedPasses"] += 1

            if event["id"] in key_pass_ids:
                record["keyPasses"] += 1

        elif event_type == "Shot":
            shot = event.get("shot", {})
            shot_xg = float(shot.get("statsbomb_xg") or 0)

            record["shots"] += 1
            record["xG"] += shot_xg

            key_pass_id = shot.get("key_pass_id")
            assist_event = events_by_id.get(key_pass_id)

            # Approximate xA by crediting the linked passer with the
            # xG value of the shot their pass created.
            if assist_event and assist_event.get("player"):
                assister_id = str(assist_event["player"]["id"])

                if assister_id in players:
                    players[assister_id]["xA"] += shot_xg

                    if shot.get("outcome", {}).get("name") == "Goal":
                        players[assister_id]["assists"] += 1

            if shot.get("outcome", {}).get("name") == "Goal":
                record["goals"] += 1

        elif event_type == "Duel":
            duel_type = event.get("duel", {}).get("type", {}).get("name")

            if duel_type == "Tackle":
                record["tackles"] += 1

        elif event_type == "Interception":
            record["interceptions"] += 1

        elif event_type == "Ball Recovery":
            recovery = event.get("ball_recovery", {})

            # Exclude explicitly failed recovery attempts.
            if not recovery.get("recovery_failure", False):
                record["ballRecoveries"] += 1

        elif event_type == "Carry":
            start_location = event.get("location")
            end_location = event.get("carry", {}).get("end_location")

            if (
                start_location
                and end_location
                and len(start_location) >= 2
                and len(end_location) >= 2
            ):
                # PROVISIONAL: count carries whose end x-coordinate
                # advances at least the chosen threshold.
                # Confirm the coordinate direction before relying on this.
                forward_distance = end_location[0] - start_location[0]

                if forward_distance >= PROGRESSIVE_CARRY_DISTANCE:
                    record["progressiveCarries"] += 1


# Prepare the compact output for the website.
output_players = []

for player in players.values():
    minutes = player["minutes"]

    # Calculate rates using full-precision minutes before rounding display.
    count_metrics = [
        "goals",
        "assists",
        "shots",
        "passes",
        "completedPasses",
        "keyPasses",
        "tackles",
        "interceptions",
        "ballRecoveries",
        "progressiveCarries",
    ]

    for metric in count_metrics:
        rate_name = metric + "Per90"
        player[rate_name] = (
            round(player[metric] * 90 / minutes, 3)
            if minutes > 0 else 0
        )

    player["xGPer90"] = (
        round(player["xG"] * 90 / minutes, 3)
        if minutes > 0 else 0
    )

    player["xAPer90"] = (
        round(player["xA"] * 90 / minutes, 3)
        if minutes > 0 else 0
    )

    # Completion percentage is a percentage, not a per-90 rate.
    player["passCompletionPct"] = (
        round(player["completedPasses"] / player["passes"] * 100, 1)
        if player["passes"] > 0 else 0
    )

    # Round display values only after calculating the rates.
    player["minutes"] = round(minutes, 2)
    player["xG"] = round(player["xG"], 3)
    player["xA"] = round(player["xA"], 3)

    output_players.append(player)

output_players.sort(key=lambda player: player["name"].lower())

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

output = {
    "source": "StatsBomb Open Data",
    "competition": "FIFA World Cup",
    "season": "2022",
    "matchesProcessed": len(MATCH_IDS),
    "metricNotes": {
        "minutes": (
            "Summed lineup position intervals; estimates based on "
            "StatsBomb event timelines."
        ),
        "goals": "Goal outcomes on shot events; own goals excluded.",
        "assists": "Goal shots with a linked key pass.",
        "xG": "Sum of StatsBomb shot-level expected goals.",
        "xA": (
            "Approximation: sum of linked shot xG credited to the "
            "player making the key pass."
        ),
        "passes": "All pass events, including unsuccessful attempts.",
        "completedPasses": (
            "Pass events without a recorded unsuccessful outcome."
        ),
        "passCompletionPct": (
            "Completed passes divided by all pass attempts, multiplied by 100."
        ),
        "keyPasses": "Passes linked to a shot event.",
        "tackles": "Tackle-type duel events, including attempts.",
        "interceptions": "Interception events.",
        "ballRecoveries": (
            "Ball Recovery events excluding explicitly marked failures."
        ),
        "progressiveCarries": (
            "Provisional: carries whose end x-coordinate advances at least "
            f"{PROGRESSIVE_CARRY_DISTANCE} pitch units. Validate attacking "
            "direction before analysis."
        ),
    },
    "players": output_players,
}

with OUTPUT_FILE.open("w", encoding="utf-8") as file:
    json.dump(output, file, ensure_ascii=False, indent=2)

print(f"\nFinished! Processed {len(MATCH_IDS)} matches.")
print(f"Players found: {len(output_players)}")
print(f"Saved results to: {OUTPUT_FILE}")
