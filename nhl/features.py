"""Turn game results into each team's season-to-date numbers after N games."""

import pandas as pd


def team_games(games):
    """One row per team per game, in the order the team played them.

    Standings points: 2 for any win, 1 for a loss in overtime or a shootout, 0 otherwise.
    """
    cols = ["season", "game_id", "date", "end"]
    home = games[cols].assign(
        team=games.home, gf=games.home_score, ga=games.away_score)
    away = games[cols].assign(
        team=games.away, gf=games.away_score, ga=games.home_score)
    tg = pd.concat([home, away], ignore_index=True)

    won = tg.gf > tg.ga
    extra_time_loss = ~won & tg.end.isin(["OT", "SO"])
    tg["points"] = 2 * won + extra_time_loss.astype(int)

    tg = tg.sort_values(["season", "team", "date", "game_id"]).reset_index(drop=True)
    by_team = tg.groupby(["season", "team"])
    tg["game_number"] = by_team.cumcount() + 1
    for col in ["points", "gf", "ga"]:
        tg[f"cum_{col}"] = by_team[col].cumsum()
    return tg


def snapshot(tg, n):
    """Each team's record after exactly its first n games.

    pts_pct: share of available standings points earned (points / 2n)
    gd_pg:   goal differential per game
    """
    at_n = tg[tg.game_number == n]
    return pd.DataFrame({
        "season": at_n.season.values,
        "team": at_n.team.values,
        "games": n,
        "pts_pct": (at_n.cum_points / (2 * n)).values,
        "gd_pg": ((at_n.cum_gf - at_n.cum_ga) / n).values,
    })


def latest(tg):
    """Each team's record after its most recent game (for an in-progress season)."""
    last = tg.loc[tg.groupby(["season", "team"]).game_number.idxmax()]
    n = last.game_number
    return pd.DataFrame({
        "season": last.season.values,
        "team": last.team.values,
        "games": n.values,
        "pts_pct": (last.cum_points / (2 * n)).values,
        "gd_pg": ((last.cum_gf - last.cum_ga) / n).values,
    })
