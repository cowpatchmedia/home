import contextlib
import html
import io
from pathlib import Path

if __package__:
    from tools.build_player_stats import RAW_DIR, build_player_stats
else:
    from build_player_stats import RAW_DIR, build_player_stats


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_DIR / "tools" / "player_stats_comparison.html"
MATCHES = [
    (3869685, "Argentina vs France", "Final · extra time · penalty shootout"),
    (3857273, "Wales vs Iran", "Group stage · red card"),
    (3857254, "Denmark vs Tunisia", "Group stage · regulation time"),
    (3869220, "Spain vs Morocco", "Round of 16 · extra time · penalty shootout"),
]
METRICS = [
    ("minutes", "Minutes", 2),
    ("goals", "Goals", 0),
    ("assists", "Assists", 0),
    ("shots", "Shots", 0),
    ("xG", "xG", 3),
    ("passes", "Pass attempts", 0),
    ("completedPasses", "Completed passes", 0),
    ("passCompletionPct", "Pass completion %", 1),
]
METRIC_NOTES = {
    "minutes": "Playing time estimated from lineup, substitution, dismissal, and final-whistle events.",
    "goals": "StatsBomb goal outcomes on shot events; own goals are excluded.",
    "assists": "Goal shots linked to a pass marked goal_assist by StatsBomb.",
    "shots": "StatsBomb Shot events; penalty-shootout period is excluded.",
    "xG": "Sum of StatsBomb shot-level expected-goals values.",
    "passes": "All StatsBomb Pass events, including unsuccessful attempts and set-piece pass types.",
    "completedPasses": "Pass events without a recorded unsuccessful outcome.",
    "passCompletionPct": "Completed passes divided by pass attempts, multiplied by 100.",
}


def escape(value):
    return html.escape(str(value), quote=True)


def format_value(value, decimals):
    if decimals == 0:
        return str(int(value))
    return f"{value:.{decimals}f}"


def render_player(player, match_id):
    name = escape(player["name"])
    player_id = escape(player["id"])
    rows = []

    for metric, label, decimals in METRICS:
        value = format_value(player[metric], decimals)
        input_step = "1" if decimals == 0 else "any"
        key = f"{match_id}-{player_id}-{metric}"
        rows.append(
            "<tr>"
            f"<th scope=\"row\">{escape(label)}</th>"
            f"<td class=\"number\">{escape(value)}</td>"
            "<td>"
            f"<input type=\"number\" step=\"{input_step}\" "
            f"aria-label=\"Independent {escape(label)} for {name}\" "
            f"data-reference data-key=\"{escape(key)}\" "
            f"data-calculated=\"{escape(value)}\" "
            f"data-decimals=\"{decimals}\">"
            "</td>"
            f"<td class=\"number\"><output data-difference "
            f"data-key=\"{escape(key)}\">—</output></td>"
            f"<td class=\"definition\">{escape(METRIC_NOTES[metric])}</td>"
            "</tr>"
        )

    details_id = f"player-{match_id}-{player_id}"
    return (
        "<tr class=\"player-row\">"
        f"<th scope=\"row\"><details><summary>{name}</summary>"
        f"<span class=\"player-id\">StatsBomb ID: {player_id}</span>"
        "</details></th>"
        f"<td>{escape(player['position'])}</td>"
        f"<td class=\"number\">{format_value(player['minutes'], 2)}</td>"
        f"<td class=\"number\">{player['goals']}</td>"
        f"<td class=\"number\">{player['assists']}</td>"
        f"<td class=\"number\">{player['shots']}</td>"
        f"<td class=\"number\">{format_value(player['xG'], 3)}</td>"
        f"<td class=\"number\">{player['passes']}</td>"
        f"<td class=\"number\">{player['completedPasses']}</td>"
        f"<td class=\"number\">{format_value(player['passCompletionPct'], 1)}%</td>"
        "<td>"
        f"<details class=\"compare-details\" id=\"{escape(details_id)}\">"
        "<summary>Enter reference values</summary>"
        "<div class=\"comparison-wrap\"><table class=\"comparison-table\">"
        "<thead><tr><th>Metric</th><th>Calculated</th>"
        "<th>Independent</th><th>Difference<br><small>reference − calculated</small></th>"
        "<th>Calculation definition</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
        "</details>"
        "</td>"
        "</tr>"
    )


def render_match(match_id, title, context, data):
    players = [player for player in data["players"] if player["minutes"] > 0]
    teams = sorted({player["team"] for player in players})
    goals_by_team = {
        team: sum(
            player["goals"] for player in players if player["team"] == team
        )
        for team in teams
    }
    score = " – ".join(str(goals_by_team[team]) for team in teams)
    player_rows = "".join(render_player(player, match_id) for player in players)
    match_title = escape(title)

    return f"""
    <section class="match-card" id="match-{match_id}">
      <header class="match-heading">
        <div>
          <p class="eyebrow">Match {match_id} · {escape(context)}</p>
          <h2>{match_title}</h2>
        </div>
        <p class="score" aria-label="Score">{escape(score)}</p>
      </header>
      <p class="teams">{escape(" vs ".join(teams))} · {len(players)} players with recorded minutes</p>
      <label class="source-field">
        Independent source URL
        <input type="url" data-source data-match="{match_id}"
          placeholder="Paste the source URL used for this match">
      </label>
      <label class="source-field">
        Source notes / definition differences
        <textarea data-source-notes data-match="{match_id}" rows="2"
          placeholder="For example: passes are completed passes; minutes rounded to whole minutes"></textarea>
      </label>
      <div class="table-wrap">
        <table class="player-table">
          <thead><tr>
            <th scope="col">Player</th><th scope="col">Listed position</th>
            <th scope="col">Minutes</th><th scope="col">Goals</th>
            <th scope="col">Assists</th><th scope="col">Shots</th>
            <th scope="col">xG</th><th scope="col">Pass attempts</th>
            <th scope="col">Completed</th><th scope="col">Pass %</th>
            <th scope="col">Compare</th>
          </tr></thead>
          <tbody>{player_rows}</tbody>
        </table>
      </div>
    </section>
    """


def build_report():
    sections = []
    for match_id, title, context in MATCHES:
        with contextlib.redirect_stdout(io.StringIO()):
            data = build_player_stats(raw_dir=RAW_DIR, match_ids=[match_id])
        sections.append(render_match(match_id, title, context, data))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2022 World Cup player stats comparison</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #17212b;
      background: #f3f6f8;
      font-synthesis: none;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; }}
    main {{ max-width: 1500px; margin: auto; padding: 2rem clamp(1rem, 3vw, 3rem); }}
    h1 {{ margin: 0 0 .4rem; font-size: clamp(1.7rem, 4vw, 2.5rem); }}
    h2 {{ margin: .2rem 0; font-size: 1.4rem; }}
    h3 {{ margin: 0; font-size: 1.1rem; }}
    .intro {{ max-width: 850px; color: #465564; line-height: 1.55; }}
    .notice {{ border-left: 4px solid #d59a2a; background: #fff8e8; padding: .8rem 1rem; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: .75rem; align-items: center; margin: 1rem 0 1.5rem; }}
    button {{ border: 0; border-radius: .4rem; background: #174f65; color: white; padding: .65rem 1rem; font: inherit; cursor: pointer; }}
    button:hover {{ background: #0e3949; }}
    .status {{ color: #275b3a; min-height: 1.5em; }}
    .match-card {{ background: #fff; border: 1px solid #d5dee4; border-radius: .7rem; margin: 1.4rem 0; padding: clamp(1rem, 2vw, 1.5rem); box-shadow: 0 2px 8px #132a3810; }}
    .match-heading {{ display: flex; justify-content: space-between; align-items: center; gap: 1rem; }}
    .eyebrow {{ color: #526576; font-size: .82rem; letter-spacing: .03em; margin: 0; }}
    .score {{ font-size: 1.7rem; font-weight: 750; margin: 0; white-space: nowrap; }}
    .teams {{ color: #526576; margin: .2rem 0 1rem; }}
    .source-field {{ display: block; max-width: 850px; font-size: .9rem; font-weight: 650; margin: .7rem 0; }}
    input, textarea {{ display: block; width: 100%; margin-top: .3rem; padding: .55rem .65rem; border: 1px solid #aebdc7; border-radius: .35rem; font: inherit; background: #fff; }}
    input:focus, textarea:focus {{ outline: 3px solid #83c4db; outline-offset: 1px; }}
    .table-wrap, .comparison-wrap {{ overflow-x: auto; }}
    table {{ border-collapse: collapse; width: 100%; }}
    .player-table {{ min-width: 1120px; margin-top: 1rem; font-size: .9rem; }}
    th, td {{ border-bottom: 1px solid #e0e6ea; padding: .55rem .6rem; text-align: left; vertical-align: top; }}
    thead th {{ background: #edf3f6; position: sticky; top: 0; z-index: 1; white-space: nowrap; }}
    .player-row:nth-child(even) {{ background: #fafcfd; }}
    .number {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
    .player-row > th {{ min-width: 190px; }}
    summary {{ cursor: pointer; color: #174f65; font-weight: 650; }}
    .player-id {{ display: block; margin-top: .25rem; color: #667784; font-size: .75rem; font-weight: 400; }}
    .compare-details {{ min-width: 190px; }}
    .comparison-wrap {{ max-width: 1120px; margin: .7rem 0; }}
    .comparison-table {{ min-width: 780px; font-size: .83rem; background: white; }}
    .comparison-table th {{ background: #f2f6f8; }}
    .comparison-table input {{ min-width: 105px; width: 115px; }}
    .comparison-table .definition {{ min-width: 280px; color: #465564; }}
    output[data-difference] {{ font-variant-numeric: tabular-nums; }}
    footer {{ color: #526576; font-size: .85rem; margin: 2rem 0; }}
    @media print {{
      body {{ background: white; }}
      main {{ max-width: none; padding: 0; }}
      .toolbar, .source-field, .compare-details, .notice + p {{ display: none; }}
      .match-card {{ box-shadow: none; break-inside: avoid; }}
      .table-wrap {{ overflow: visible; }}
      .player-table {{ min-width: 0; font-size: 8pt; }}
      th, td {{ padding: .25rem; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>2022 FIFA World Cup · player-stat comparison</h1>
  <p class="intro">A focused worksheet for checking StatsBomb-derived values against independent match records.
    It is generated from the local StatsBomb Open Data files and the current calculation code.</p>
  <p class="notice"><strong>These are calculated values, not independently verified facts.</strong>
    Reference fields are blank by design. Confirm each source’s definitions—especially minutes,
    pass attempts versus completed passes, and xG—before interpreting differences.</p>
  <p class="intro">Choose <strong>Enter reference values</strong> on a player row to reveal the metric-by-metric
    comparison. The difference is independent value minus calculated value.</p>
  <div class="toolbar">
    <button type="button" id="export-button">Download entered comparisons (JSON)</button>
    <button type="button" onclick="window.print()">Print / save as PDF</button>
    <span class="status" id="status" role="status" aria-live="polite"></span>
  </div>
  {''.join(sections)}
  <footer>
    The match score shown is the sum of included StatsBomb goal-shot events; shootout kicks are excluded.
    Minutes are estimates reconstructed from match events. xA is an approximation based on linked shot xG.
    Carries are not included in this comparison worksheet because the current 10-unit carry measure is a custom proxy.
  </footer>
</main>
<script>
  const numberInputs = document.querySelectorAll("[data-reference]");

  numberInputs.forEach((input) => {{
    input.addEventListener("input", () => {{
      const difference = document.querySelector(
        `[data-difference][data-key="${{input.dataset.key}}"]`
      );
      if (input.value === "") {{
        difference.textContent = "—";
        return;
      }}

      const delta = Number(input.value) - Number(input.dataset.calculated);
      const decimals = Number(input.dataset.decimals);
      difference.textContent = `${{delta > 0 ? "+" : ""}}${{delta.toFixed(decimals)}}`;
    }});
  }});

  document.getElementById("export-button").addEventListener("click", () => {{
    const comparisons = [...document.querySelectorAll("[data-source]")]
      .map((sourceInput) => {{
        const matchId = sourceInput.dataset.match;
        const section = document.getElementById(`match-${{matchId}}`);
        const sourceNotes = section.querySelector("[data-source-notes]").value;
        const players = [...section.querySelectorAll("[data-reference]")]
          .filter((input) => input.value !== "")
          .map((input) => ({{
            key: input.dataset.key,
            metric: input.getAttribute("aria-label"),
            calculated: Number(input.dataset.calculated),
            independent: Number(input.value),
            difference: Number(input.value) - Number(input.dataset.calculated),
          }}));
        return {{
          matchId,
          match: section.querySelector("h2").textContent,
          sourceUrl: sourceInput.value,
          sourceNotes,
          players,
        }};
      }});
    const blob = new Blob([JSON.stringify(comparisons, null, 2)], {{
      type: "application/json",
    }});
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "player-stat-comparisons.json";
    link.click();
    URL.revokeObjectURL(link.href);
    document.getElementById("status").textContent =
      "Downloaded the entered comparison values.";
  }});
</script>
</body>
</html>
"""


def main():
    OUTPUT_FILE.write_text(build_report(), encoding="utf-8")
    print(f"Saved comparison report to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
