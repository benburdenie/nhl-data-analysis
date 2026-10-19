"""
data_loader.py
--------------
Responsible for reading CSV files, cleaning missing values,
and returning tidy DataFrames ready for analysis.
"""

import pandas as pd
import os


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _csv_path(filename: str) -> str:
    """Build an absolute path to a file in the data directory."""
    return os.path.join(DATA_DIR, filename)


def load_skaters() -> pd.DataFrame:
    """
    Load skater (non-goalie) statistics.
    Returns a cleaned DataFrame.
    """
    df = pd.read_csv(_csv_path("nhl_skaters.csv"))

    # Strip whitespace from string columns
    str_cols = ["player", "team", "position", "season"]
    for col in str_cols:
        df[col] = df[col].str.strip()

    # Fill missing numeric stats with 0
    numeric_cols = [
        "goals", "assists", "points", "plus_minus",
        "penalty_minutes", "powerplay_goals", "shorthanded_goals",
        "shots", "shooting_pct", "games_played"
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Derive points-per-game for convenience
    df["points_per_game"] = (
        df["points"] / df["games_played"].replace(0, 1)
    ).round(2)

    return df


def load_goalies() -> pd.DataFrame:
    """
    Load goalie statistics.
    Returns a cleaned DataFrame.
    """
    df = pd.read_csv(_csv_path("nhl_goalies.csv"))

    str_cols = ["player", "team", "season"]
    for col in str_cols:
        df[col] = df[col].str.strip()

    numeric_cols = [
        "games_played", "wins", "losses", "ot_losses",
        "goals_against_avg", "save_pct", "shutouts",
        "saves", "shots_against"
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Win percentage
    df["win_pct"] = (
        df["wins"] / df["games_played"].replace(0, 1)
    ).round(3)

    return df


def load_teams() -> pd.DataFrame:
    """
    Load team standings and stats.
    Returns a cleaned DataFrame.
    """
    df = pd.read_csv(_csv_path("nhl_teams.csv"))

    str_cols = ["team", "season"]
    for col in str_cols:
        df[col] = df[col].str.strip()

    numeric_cols = [
        "games_played", "wins", "losses", "ot_losses", "points",
        "goals_for", "goals_against", "goal_differential",
        "powerplay_pct", "penalty_kill_pct"
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Points percentage (points earned out of maximum possible)
    df["points_pct"] = (
        df["points"] / (df["games_played"] * 2)
    ).round(3)

    return df


def dataset_summary() -> None:
    """Print a quick summary of all three datasets to stdout."""
    for label, loader in [
        ("Skaters", load_skaters),
        ("Goalies", load_goalies),
        ("Teams",   load_teams),
    ]:
        df = loader()
        print(f"\n--- {label} ---")
        print(f"  Rows      : {len(df)}")
        print(f"  Columns   : {list(df.columns)}")
        print(f"  Seasons   : {sorted(df['season'].unique())}")
        missing = df.isnull().sum().sum()
        print(f"  Missing   : {missing}")
