"""
analysis.py
-----------
All statistical computations, rankings, and filters.
No I/O here — just functions that take DataFrames and return DataFrames.
"""

import pandas as pd


# ─────────────────────────────────────────────────────────────
#  Skater analysis
# ─────────────────────────────────────────────────────────────

def top_scorers(df: pd.DataFrame, season: str = None,
                top_n: int = 10, metric: str = "points") -> pd.DataFrame:
    """
    Return the top N skaters ranked by the chosen metric.

    Parameters
    ----------
    df      : skater DataFrame from data_loader.load_skaters()
    season  : e.g. '2022-23'; None = all seasons combined (max value per player)
    top_n   : number of players to return
    metric  : column to rank by ('points', 'goals', 'assists', 'points_per_game')
    """
    if season:
        df = df[df["season"] == season].copy()
    else:
        # Aggregate across seasons: use max season value per player for ranking
        df = df.sort_values("season").groupby("player", as_index=False).last()

    return (
        df.nlargest(top_n, metric)
          [["player", "team", "season", "games_played",
            "goals", "assists", "points", "points_per_game"]]
          .reset_index(drop=True)
    )


def player_season_trend(df: pd.DataFrame, player: str) -> pd.DataFrame:
    """Return season-by-season stats for a single player."""
    result = df[df["player"].str.lower() == player.lower()].copy()
    result = result.sort_values("season")
    return result[["season", "team", "games_played",
                   "goals", "assists", "points", "points_per_game"]]


def filter_by_position(df: pd.DataFrame, position: str) -> pd.DataFrame:
    """Filter skaters to a specific position (C, LW, RW, D)."""
    return df[df["position"].str.upper() == position.upper()].copy()


def scoring_by_season(df: pd.DataFrame) -> pd.DataFrame:
    """Average goals, assists, and points per player grouped by season."""
    return (
        df.groupby("season")[["goals", "assists", "points"]]
          .mean()
          .round(1)
          .reset_index()
          .sort_values("season")
    )


# ─────────────────────────────────────────────────────────────
#  Goalie analysis
# ─────────────────────────────────────────────────────────────

def top_goalies(df: pd.DataFrame, season: str = None,
                top_n: int = 8, metric: str = "save_pct") -> pd.DataFrame:
    """
    Return the top N goalies ranked by the chosen metric.
    Minimum 20 games played to qualify.
    """
    qualified = df[df["games_played"] >= 20].copy()
    if season:
        qualified = qualified[qualified["season"] == season]

    sort_asc = metric in ("goals_against_avg",)
    return (
        qualified.sort_values(metric, ascending=sort_asc)
                 .head(top_n)
                 [["player", "team", "season", "games_played",
                   "wins", "goals_against_avg", "save_pct", "shutouts"]]
                 .reset_index(drop=True)
    )


def goalie_trend(df: pd.DataFrame, player: str) -> pd.DataFrame:
    """Season-by-season stats for a single goalie."""
    result = df[df["player"].str.lower() == player.lower()].copy()
    return result.sort_values("season")[
        ["season", "team", "games_played", "wins",
         "goals_against_avg", "save_pct", "shutouts"]
    ]


def save_pct_by_season(df: pd.DataFrame) -> pd.DataFrame:
    """League-average save percentage by season (min 20 GP)."""
    qualified = df[df["games_played"] >= 20]
    return (
        qualified.groupby("season")["save_pct"]
                 .mean()
                 .round(4)
                 .reset_index()
                 .sort_values("season")
    )


# ─────────────────────────────────────────────────────────────
#  Team analysis
# ─────────────────────────────────────────────────────────────

def top_teams(df: pd.DataFrame, season: str = None,
              top_n: int = 8, metric: str = "points") -> pd.DataFrame:
    """Return top N teams by chosen metric for a season (or all-time best)."""
    if season:
        df = df[df["season"] == season].copy()
    return (
        df.nlargest(top_n, metric)
          [["team", "season", "wins", "losses", "ot_losses",
            "points", "goals_for", "goals_against",
            "goal_differential", "powerplay_pct"]]
          .reset_index(drop=True)
    )


def goal_differential_ranking(df: pd.DataFrame, season: str) -> pd.DataFrame:
    """Rank teams by goal differential for a given season."""
    return (
        df[df["season"] == season]
          .sort_values("goal_differential", ascending=False)
          [["team", "points", "goals_for", "goals_against", "goal_differential"]]
          .reset_index(drop=True)
    )


def pp_vs_standings(df: pd.DataFrame, season: str = None) -> pd.DataFrame:
    """Return power-play % alongside standings points for correlation analysis."""
    if season:
        df = df[df["season"] == season]
    return df[["team", "season", "points", "powerplay_pct",
               "penalty_kill_pct", "goal_differential"]].copy()


def teams_over_time(df: pd.DataFrame, teams: list) -> pd.DataFrame:
    """Filter to specific teams and return their stats across all seasons."""
    return (
        df[df["team"].isin(teams)]
          .sort_values(["team", "season"])
          [["team", "season", "wins", "points",
            "goals_for", "goals_against", "goal_differential"]]
    )


# ─────────────────────────────────────────────────────────────
#  Summary text
# ─────────────────────────────────────────────────────────────

def generate_summary(skaters, goalies, teams) -> str:
    """
    Produce a human-readable text summary of key findings
    across all three datasets.
    """
    lines = []
    lines.append("=" * 55)
    lines.append("  NHL DATA ANALYSIS  --  KEY FINDINGS")
    lines.append("=" * 55)

    # Top scorer all time
    best = top_scorers(skaters, top_n=1).iloc[0]
    lines.append(f"\nSCORING")
    lines.append(f"  All-time single-season leader in dataset:")
    lines.append(f"  {best['player']} ({best['team']}, {best['season']})"
                 f" -- {best['points']} pts in {best['games_played']} GP")

    # Scoring trend
    trend = scoring_by_season(skaters)
    best_avg_season = trend.loc[trend["points"].idxmax(), "season"]
    lines.append(f"  Highest-scoring season (avg pts/player): {best_avg_season}")

    # Goalie
    lines.append(f"\nGOALTENDING")
    best_sv = top_goalies(goalies, top_n=1, metric="save_pct").iloc[0]
    lines.append(f"  Best single-season save pct:")
    lines.append(f"  {best_sv['player']} ({best_sv['team']}, {best_sv['season']})"
                 f"  SV%: {best_sv['save_pct']:.3f}")

    avg_sv = save_pct_by_season(goalies)
    sv_low  = avg_sv.loc[avg_sv["save_pct"].idxmin()]
    sv_high = avg_sv.loc[avg_sv["save_pct"].idxmax()]
    lines.append(f"  League avg SV% ranged from {sv_low['save_pct']:.3f}"
                 f" ({sv_low['season']}) to {sv_high['save_pct']:.3f}"
                 f" ({sv_high['season']})")
    lines.append(f"  Save percentage is more stable year-to-year than wins,")
    lines.append(f"  reflecting how team defence influences goalie win totals.")

    # Teams
    lines.append(f"\nTEAMS")
    best_team = top_teams(teams, top_n=1).iloc[0]
    lines.append(f"  Best single-season points total:")
    lines.append(f"  {best_team['team']} ({best_team['season']})"
                 f"  -- {best_team['points']} pts, +{best_team['goal_differential']} GD")

    corr = teams["goal_differential"].corr(teams["points"])
    lines.append(f"  Goal differential vs standings points correlation: r = {corr:.2f}")
    lines.append(f"  Teams with stronger goal differential consistently")
    lines.append(f"  finish higher in standings (r = {corr:.2f}).")

    pp_corr = teams["powerplay_pct"].corr(teams["points"])
    lines.append(f"  Power-play % vs standings points correlation: r = {pp_corr:.2f}")
    if pp_corr > 0.4:
        lines.append(f"  Power-play efficiency is a meaningful predictor of standings.")
    else:
        lines.append(f"  Power-play % alone is a weak predictor of final standings.")

    lines.append("\n" + "=" * 55)
    return "\n".join(lines)
