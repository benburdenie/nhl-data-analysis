"""Playoff odds for the season in progress, from a model trained on past seasons.

Usage:
    python -m nhl.fetch      # refreshes the current season's games
    python -m nhl.odds

Writes outputs/current_odds.md.
"""

from pathlib import Path

from nhl.analyze import completed_seasons, load
from nhl.features import latest, snapshot, team_games
from nhl.model import PREDICTORS, fit, pick_top

OUT = Path(__file__).resolve().parent.parent / "outputs"
FEATURES = PREDICTORS["Both"]


def current_odds(games, teams):
    done = completed_seasons(games, teams)
    in_progress = sorted(set(games.season) - set(done))
    if not in_progress:
        raise SystemExit("No season in progress in data/games.csv.")
    season = in_progress[-1]

    tg = team_games(games)
    now = latest(tg[tg.season == season]).merge(teams, on=["season", "team"])

    # Train at the league's typical games played so far, on the same stats
    n = int(min(max(round(now.games.median()), 1), 82))
    history = snapshot(tg[tg.season.isin(done)], n).merge(teams, on=["season", "team"])
    model = fit(history, FEATURES)

    now["playoff_prob"] = model.predict_proba(now[FEATURES])[:, 1]
    now["projected_in"] = pick_top(now, "playoff_prob")
    return season, n, now.sort_values(["conference", "playoff_prob"], ascending=[True, False])


def main():
    games, teams = load()
    season, n, table = current_odds(games, teams)
    lines = [
        f"# Playoff odds, {season[:4]}-{season[6:]}",
        "",
        f"Model: logistic regression on points % and goal differential per game, trained on "
        f"every completed season at {n} games played. Odds are per team and are not forced "
        "to add up to 16.",
        "",
    ]
    for conference, group in table.groupby("conference"):
        lines += [f"## {conference}", "",
                  "| Team | GP | Points % | GD / game | Playoff odds | Projected in |",
                  "|---|---|---|---|---|---|"]
        for r in group.itertuples():
            lines.append(f"| {r.team} | {r.games} | {r.pts_pct:.3f} | {r.gd_pg:+.2f} | "
                         f"{r.playoff_prob:.0%} | {'yes' if r.projected_in else ''} |")
        lines.append("")
    OUT.mkdir(exist_ok=True)
    (OUT / "current_odds.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
