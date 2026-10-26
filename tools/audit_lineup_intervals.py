
import json
from pathlib import Path

RAW_DIR = Path.home() / "soccer-data" / "raw"
EVENTS_DIR = RAW_DIR / "events"
LINEUPS_DIR = RAW_DIR / "lineups"


def parse_clock(clock):
    """Convert a clock such as '64:10' into seconds."""
    if not clock:
        return None

    minutes, seconds = clock.split(":")
    return int(minutes) * 60 + int(seconds)


def load_json(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


matches_checked = 0
players_checked = 0
overlap_count = 0
invalid_count = 0
out_of_bounds_count = 0
missing_match_end_count = 0
longest_player_match = None

for lineup_path in sorted(LINEUPS_DIR.glob("*.json")):
    if not lineup_path.stem.isdigit():
        continue

    match_id = lineup_path.stem
    events_path = EVENTS_DIR / f"{match_id}.json"

    if not events_path.exists():
        print(f"Missing events file for match {match_id}")
        continue

    lineups = load_json(lineup_path)
    events = load_json(events_path)

    half_end_times = [
        event.get("minute", 0) * 60 + event.get("second", 0)
        for event in events
        if event.get("type", {}).get("name") == "Half End"
    ]

    match_end = max(half_end_times) if half_end_times else None

    if match_end is None:
        missing_match_end_count += 1
        print(f"WARNING: Match {match_id} has no Half End event")

    matches_checked += 1

    for team in lineups:
        for player in team.get("lineup", []):
            intervals = []

            for position in player.get("positions", []):
                start = parse_clock(position.get("from"))
                end = parse_clock(position.get("to"))

                # Open-ended intervals use the recorded match end.
                if end is None:
                    end = match_end

                if start is None or end is None:
                    continue

                if end < start:
                    invalid_count += 1
                    print(
                        f"INVALID interval | Match {match_id} | "
                        f"{player['player_name']} | {start} to {end}"
                    )
                    continue

                if match_end is not None and (
                    start > match_end or end > match_end
                ):
                    out_of_bounds_count += 1
                    print(
                        f"OUT OF BOUNDS | Match {match_id} | "
                        f"{player['player_name']} | "
                        f"{start} to {end} | Match end: {match_end}"
                    )

                intervals.append((start, end))

            if not intervals:
                continue

            players_checked += 1
            intervals.sort()

            total_seconds = sum(
                end - start for start, end in intervals
            )

            if (
                longest_player_match is None
                or total_seconds > longest_player_match[0]
            ):
                longest_player_match = (
                    total_seconds,
                    match_id,
                    player["player_name"],
                )

            latest_end = intervals[0][1]

            for start, end in intervals[1:]:
                if start < latest_end:
                    overlap_count += 1
                    print(
                        f"POSSIBLE OVERLAP | Match {match_id} | "
                        f"{player['player_name']} | "
                        f"Next interval starts at {start}, "
                        f"previous interval ends at {latest_end}"
                    )

                latest_end = max(latest_end, end)


print("\n--- AUDIT SUMMARY ---")
print(f"Matches checked: {matches_checked}")
print(f"Players with valid intervals: {players_checked}")
print(f"Possible interval overlaps: {overlap_count}")
print(f"Invalid intervals: {invalid_count}")
print(f"Intervals beyond match end: {out_of_bounds_count}")
print(f"Matches missing Half End events: {missing_match_end_count}")

if longest_player_match:
    seconds, match_id, player_name = longest_player_match
    print(
        f"Longest summed player time in one match: "
        f"{seconds / 60:.2f} minutes — {player_name} "
        f"(match {match_id})"
    )
