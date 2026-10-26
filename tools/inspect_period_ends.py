
import json
from pathlib import Path

raw_dir = Path.home() / "soccer-data" / "raw"
match_id = "3869685"

events_path = raw_dir / "events" / f"{match_id}.json"

with events_path.open(encoding="utf-8") as file:
    events = json.load(file)

for period in range(1, 6):
    period_events = [
        event for event in events
        if event.get("period") == period
    ]

    print(f"\nPERIOD {period}")

    for event in period_events:
        event_type = event.get("type", {}).get("name")

        if event_type in ("Half Start", "Half End"):
            print({
                "type": event_type,
                "minute": event.get("minute"),
                "second": event.get("second"),
                "timestamp": event.get("timestamp"),
            })

    # Show the latest timestamps for ordinary gameplay events.
    gameplay_events = [
        event for event in period_events
        if event.get("type", {}).get("name") not in (
            "Half Start", "Half End"
        )
    ]

    latest_events = sorted(
        gameplay_events,
        key=lambda event: event.get("timestamp", "")
    )[-3:]

    print("Latest non-boundary events:")

    for event in latest_events:
        print({
            "type": event.get("type", {}).get("name"),
            "minute": event.get("minute"),
            "second": event.get("second"),
            "timestamp": event.get("timestamp"),
        })
