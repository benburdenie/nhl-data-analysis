"""A fake 32-team league with the same CSV shape as the real data, for tests."""

import numpy as np
import pandas as pd

CONFERENCES = ["Eastern", "Western"]


def make_league(seasons=("20202021", "20212022", "20222023", "20232024"),
                games_per_team=82, partial=None, seed=0):
    """Return (games, teams) DataFrames. Pass partial=(season, n) to stop a season early."""
    rng = np.random.default_rng(seed)
    teams = [f"T{i:02d}" for i in range(32)]
    conference = {t: CONFERENCES[i % 2] for i, t in enumerate(teams)}
    game_rows, team_rows = [], []
    game_id = 0
    for season in seasons:
        strength = dict(zip(teams, rng.normal(0, 0.6, len(teams))))
        rounds = games_per_team
        if partial and partial[0] == season:
            rounds = partial[1]
        for r in range(rounds):
            order = rng.permutation(teams)
            for home, away in zip(order[::2], order[1::2]):
                game_id += 1
                hs = rng.poisson(np.exp(1.1 + 0.25 * (strength[home] - strength[away])))
                as_ = rng.poisson(np.exp(1.1 + 0.25 * (strength[away] - strength[home])))
                end = "REG"
                if hs == as_:  # decide ties in OT or a shootout
                    end = "OT" if rng.random() < 0.6 else "SO"
                    if rng.random() < 0.5:
                        hs += 1
                    else:
                        as_ += 1
                game_rows.append({
                    "season": season, "game_id": game_id,
                    "date": f"{season[:4]}-10-01+{r:03d}",
                    "home": home, "away": away,
                    "home_score": hs, "away_score": as_, "end": end,
                })
        team_rows += [{"season": season, "team": t, "conference": conference[t]} for t in teams]

    games = pd.DataFrame(game_rows)
    teams_df = pd.DataFrame(team_rows)

    # Playoffs: top 8 by points in each conference (only for finished seasons)
    from nhl.features import team_games
    tg = team_games(games)
    final = tg.groupby(["season", "team"]).points.sum().rename("pts").reset_index()
    final = final.merge(teams_df, on=["season", "team"])
    final["rank"] = final.groupby(["season", "conference"]).pts.rank(
        ascending=False, method="first")
    final["made_playoffs"] = final["rank"] <= 8
    if partial:
        final.loc[final.season == partial[0], "made_playoffs"] = False
    teams_df = teams_df.merge(final[["season", "team", "made_playoffs"]], on=["season", "team"])
    return games, teams_df
