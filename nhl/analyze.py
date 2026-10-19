"""Run the playoff-prediction study on data/games.csv and data/teams.csv.

Usage:
    python -m nhl.analyze

Writes outputs/results.csv, outputs/accuracy_by_games.png and outputs/findings.md.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from nhl.features import team_games  # noqa: E402
from nhl.model import PREDICTORS, evaluate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "outputs"
CHECKPOINTS = [5, 10, 15, 20, 25, 30, 41, 50, 60, 70, 82]
REPORT_AT = [10, 20, 41]

# Validated categorical palette (blue, orange, aqua) on a near-white surface
COLORS = {"Points %": "#2a78d6", "Goal differential": "#eb6834", "Both": "#1baf7a"}
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"


def load():
    games = pd.read_csv(DATA / "games.csv", dtype={"season": str})
    teams = pd.read_csv(DATA / "teams.csv", dtype={"season": str})
    return games, teams


def completed_seasons(games, teams):
    """Seasons where every team has played 82 games (so playoff outcomes are known)."""
    tg_counts = pd.concat([games[["season", "home"]].rename(columns={"home": "team"}),
                           games[["season", "away"]].rename(columns={"away": "team"})])
    per_team = tg_counts.groupby(["season", "team"]).size()
    done = per_team.groupby("season").min() >= 82
    return sorted(done[done].index)


def plot(results, n_seasons, path):
    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ends = {}
    for name in PREDICTORS:
        r = results[results.predictor == name]
        ax.plot(r.games, r.accuracy * 100, color=COLORS[name], linewidth=2,
                marker="o", markersize=4)
        ends[name] = (r.games.iloc[-1], r.accuracy.iloc[-1] * 100)
    # Direct labels at the line ends, nudged apart so they never overlap
    placed = []
    for name, (x, y) in sorted(ends.items(), key=lambda kv: -kv[1][1]):
        label_y = min([y] + [p - 3.2 for p in placed])
        placed.append(label_y)
        ax.plot([x + 0.8, x + 2.5], [y, label_y], color=COLORS[name], linewidth=1)
        ax.text(x + 3, label_y, name, va="center", color=INK, fontsize=9)
    ax.axhline(50, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(83, 51, "random guess", color=MUTED, fontsize=8, ha="left")
    ax.set_xlim(0, 100)
    ax.set_ylim(45, 100)
    ax.set_xticks([0, 10, 20, 30, 41, 50, 60, 70, 82])
    ax.set_xlabel("Games played", color=MUTED)
    ax.set_ylabel("Teams classified correctly (%)", color=MUTED)
    ax.set_title(f"How well each stat picks the 16 playoff teams ({n_seasons} seasons)",
                 color=INK, fontsize=11, loc="left", pad=12)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def write_findings(results, seasons, n_team_seasons, path):
    table = results.pivot(index="games", columns="predictor", values="accuracy")
    table = table[list(PREDICTORS)]
    lines = [
        "# Findings",
        "",
        f"Seasons: {', '.join(s[:4] + '-' + s[6:] for s in seasons)} "
        f"({len(seasons)} seasons, {n_team_seasons} team-seasons). "
        "Leave-one-season-out cross-validation; top 8 per conference predicted in.",
        "",
        "## Share of teams classified correctly",
        "",
        "| Games played | " + " | ".join(PREDICTORS) + " |",
        "|---|" + "---|" * len(PREDICTORS),
    ]
    for n, row in table.iterrows():
        lines.append(f"| {n} | " + " | ".join(f"{v:.1%}" for v in row) + " |")
    lines += ["", "## At a glance", ""]
    for n in [n for n in REPORT_AT if n in table.index]:
        row = table.loc[n]
        best = row.idxmax()
        lines.append(
            f"- After {n} games: points % gets {row['Points %']:.1%} right, goal "
            f"differential {row['Goal differential']:.1%}, both together "
            f"{row['Both']:.1%} (best: {best}).")
    brier = results.pivot(index="games", columns="predictor", values="brier")
    lines += ["", "## Brier score (lower is better; measures probability quality)", "",
              "| Games played | " + " | ".join(PREDICTORS) + " |",
              "|---|" + "---|" * len(PREDICTORS)]
    for n, row in brier[list(PREDICTORS)].iterrows():
        lines.append(f"| {n} | " + " | ".join(f"{v:.3f}" for v in row) + " |")
    path.write_text("\n".join(lines) + "\n")


def main():
    games, teams = load()
    seasons = completed_seasons(games, teams)
    if len(seasons) < 2:
        raise SystemExit("Need at least two completed seasons. Run `python -m nhl.fetch` first.")
    tg = team_games(games)
    results = evaluate(tg, teams, CHECKPOINTS, seasons)

    OUT.mkdir(exist_ok=True)
    results.to_csv(OUT / "results.csv", index=False)
    plot(results, len(seasons), OUT / "accuracy_by_games.png")
    n_team_seasons = int(teams.season.isin(seasons).sum())
    write_findings(results, seasons, n_team_seasons, OUT / "findings.md")
    print((OUT / "findings.md").read_text())


if __name__ == "__main__":
    main()
