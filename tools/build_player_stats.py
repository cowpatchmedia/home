
import json
from pathlib import Path

# Raw data stays outside the website repository.
RAW_DIR = Path.home() / "soccer-data" / "raw"

# Save the finished data in the website's data folder.
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_DIR / "data" / "player_stats.json"


MATCH_IDS = sorted(
    int(path.stem)
    for path in (RAW_DIR / "events").glob("*.json")
    if path.stem.isdigit()
)


# Custom proxy threshold; this is not a standardized progressive-carry definition.
PROGRESSIVE_CARRY_DISTANCE = 10


def read_json(path):
    """Read a JSON file and return its contents."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def calculate_minutes_from_events(events):
    """Calculate player minutes from starting lineups and substitutions."""
    minutes_by_player = {}
    active_players = set()
    start_times = {}

    # Determine the match's final elapsed time, excluding the shootout.
    half_end_times = [
        event.get("minute", 0) * 60 + event.get("second", 0)
        for event in events
        if event.get("type", {}).get("name") == "Half End"
        and event.get("period") in (1, 2, 3, 4)
    ]

    if not half_end_times:
        return minutes_by_player

    match_end_seconds = max(half_end_times)

    # Process lineup and substitution events in chronological order.
    for event in sorted(
        events,
        key=lambda e: (
            e.get("minute", 0),
            e.get("second", 0),
            e.get("index", 0),
        ),
    ):
        if event.get("period") == 5:
            continue

        event_type = event.get("type", {}).get("name")
        elapsed_seconds = (
            event.get("minute", 0) * 60 + event.get("second", 0)
        )

        if event_type == "Starting XI":
            lineup = event.get("tactics", {}).get("lineup", [])

            for entry in lineup:
                player_info = entry.get("player", {})
                player_id = player_info.get("id")

                if player_id is not None:
                    player_id = str(player_id)
                    minutes_by_player.setdefault(player_id, 0.0)
                    active_players.add(player_id)
                    start_times[player_id] = 0

        elif event_type == "Substitution":
            outgoing = event.get("player", {})
            substitution = event.get("substitution", {})
            incoming = substitution.get("replacement", {})

            outgoing_id = outgoing.get("id")
            incoming_id = incoming.get("id")

            if outgoing_id is not None:
                outgoing_id = str(outgoing_id)

                if outgoing_id in active_players:
                    duration = elapsed_seconds - start_times[outgoing_id]
                    minutes_by_player[outgoing_id] += max(0, duration) / 60
                    active_players.remove(outgoing_id)
                    start_times.pop(outgoing_id, None)

            if incoming_id is not None:
                incoming_id = str(incoming_id)
                minutes_by_player.setdefault(incoming_id, 0.0)
                active_players.add(incoming_id)
                start_times[incoming_id] = elapsed_seconds

        elif event_type == "Foul Committed":
            card_name = event.get("foul_committed", {}).get(
                "card", {}
            ).get("name")
            player_id = event.get("player", {}).get("id")

            if (
                card_name in ("Red Card", "Second Yellow")
                and player_id is not None
            ):
                player_id = str(player_id)

                if player_id in active_players:
                    duration = elapsed_seconds - start_times[player_id]
                    minutes_by_player[player_id] += max(0, duration) / 60
                    active_players.remove(player_id)
                    start_times.pop(player_id, None)

    # Players still on the pitch play until the final whistle.
    for player_id in active_players:
        duration = match_end_seconds - start_times[player_id]
        minutes_by_player[player_id] += max(0, duration) / 60

    return minutes_by_player



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


def accumulate_event_stats(events, players):
    """Add match event metrics to player records."""
    events_by_id = {event["id"]: event for event in events}
    key_pass_ids = set()

    for event in events:
        if event.get("period") == 5:
            continue

        if event.get("type", {}).get("name") == "Shot":
            key_pass_id = event.get("shot", {}).get("key_pass_id")
            if key_pass_id:
                key_pass_ids.add(key_pass_id)

    for event in events:
        if event.get("period") == 5:
            continue

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

            # A pass without an unsuccessful outcome is counted as completed.
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

            if assist_event and assist_event.get("player"):
                assister_id = str(assist_event["player"]["id"])

                if assister_id in players:
                    players[assister_id]["xA"] += shot_xg

                    if (
                        shot.get("outcome", {}).get("name") == "Goal"
                        and assist_event.get("pass", {}).get("goal_assist")
                    ):
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
                # This is a custom proxy using the attacking-direction x-axis.
                forward_distance = end_location[0] - start_location[0]
                if forward_distance >= PROGRESSIVE_CARRY_DISTANCE:
                    record["progressiveCarries"] += 1


players = {}

for match_id in MATCH_IDS:
    print(f"Processing match {match_id}...")

    events = read_json(RAW_DIR / "events" / f"{match_id}.json")
    lineups = read_json(RAW_DIR / "lineups" / f"{match_id}.json")

    minutes_by_player = calculate_minutes_from_events(events)

    # Register squad players, then use event timelines for playing minutes.
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
            record["minutes"] += minutes_by_player.get(key, 0)

            # Position intervals can overlap after tactical shifts; keep the
            # first recorded role instead of treating them as playing time.
            if record["position"] == "Unknown":
                positions = entry.get("positions", [])
                if positions and positions[0].get("position"):
                    record["position"] = positions[0]["position"]


    accumulate_event_stats(events, players)


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
            "Calculated from starting lineups, substitutions, dismissals, "
            "and the final whistle in StatsBomb event timelines."
        ),
        "goals": "Goal outcomes on shot events; own goals excluded.",
        "assists": "Goal shots linked to a pass marked goal_assist by StatsBomb.",
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
            "Custom proxy: carries whose x-coordinate advances at least "
            f"{PROGRESSIVE_CARRY_DISTANCE} pitch units in the attacking "
            "direction; this is not a standardized progressive-carry definition."
        ),
    },
    "players": output_players,
}

with OUTPUT_FILE.open("w", encoding="utf-8") as file:
    json.dump(output, file, ensure_ascii=False, indent=2)

print(f"\nFinished! Processed {len(MATCH_IDS)} matches.")
print(f"Players found: {len(output_players)}")
print(f"Saved results to: {OUTPUT_FILE}")
