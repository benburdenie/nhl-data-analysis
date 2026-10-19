"""Download NHL game results from the public NHL web API and save them as CSVs.

Usage:
    python -m nhl.fetch                 # all default seasons plus the current one
    python -m nhl.fetch --seasons 20232024 20242025

Raw JSON responses are cached under data/raw/ so re-running only downloads what
is missing. Outputs:
    data/games.csv  one row per completed regular-season game
    data/teams.csv  one row per team-season: conference and whether it made the playoffs
"""

import argparse
import json
import time
from pathlib import Path

import pandas as pd
import requests

API = "https://api-web.nhle.com/v1"
DATA = Path(__file__).resolve().parent.parent / "data"
RAW = DATA / "raw"

# Full 82-game seasons under today's points rules (2 for a win, 1 for an OT or
# shootout loss). 2012-13 (lockout, 48 games), 2019-20 (stopped at ~70 games)
# and 2020-21 (56 games, realigned divisions) are left out so every season is
# comparable game for game.
HISTORICAL_SEASONS = [
    "20102011", "20112012", "20132014", "20142015", "20152016", "20162017",
    "20172018", "20182019", "20212022", "20222023", "20232024", "20242025",
    "20252026",
]

REGULAR, PLAYOFF = 2, 3
COMPLETED = {"OFF", "FINAL"}


def get_json(url, cache_path, refresh=False, pause=0.25):
    """GET a URL, caching the JSON on disk. Set refresh=True for data that changes."""
    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text())
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(resp.text)
    time.sleep(pause)  # be polite to a free public API
    return resp.json()


def season_end_dates(refresh=False):
    """Map season id (e.g. '20232024') to the last day of its standings."""
    data = get_json(f"{API}/standings-season", RAW / "standings-season.json", refresh)
    return {str(s["id"]): s["standingsEnd"] for s in data["seasons"]}


def season_teams(season, end_date, current=False):
    """Teams in a season with their conference, from the final (or today's) standings."""
    date = "now" if current else end_date
    data = get_json(f"{API}/standings/{date}", RAW / season / "standings.json", refresh=current)
    return [
        {"team": row["teamAbbrev"]["default"], "conference": row["conferenceName"]}
        for row in data["standings"]
    ]


def parse_schedule(schedule, season):
    """Pull completed regular-season games and playoff appearance from one club schedule."""
    games, made_playoffs = [], False
    for g in schedule.get("games", []):
        if str(g.get("season")) != season:
            continue
        if g.get("gameType") == PLAYOFF:
            made_playoffs = True
        if g.get("gameType") != REGULAR or g.get("gameState") not in COMPLETED:
            continue
        games.append({
            "season": season,
            "game_id": g["id"],
            "date": g["gameDate"],
            "home": g["homeTeam"]["abbrev"],
            "away": g["awayTeam"]["abbrev"],
            "home_score": g["homeTeam"]["score"],
            "away_score": g["awayTeam"]["score"],
            "end": g.get("gameOutcome", {}).get("lastPeriodType", "REG"),
        })
    return games, made_playoffs


def fetch_season(season, end_date, current=False):
    """Download one season. The current season is always re-downloaded."""
    teams = season_teams(season, end_date, current=current)
    games, team_rows = [], []
    for t in teams:
        url = f"{API}/club-schedule-season/{t['team']}/{season}"
        schedule = get_json(url, RAW / season / f"{t['team']}.json", refresh=current)
        team_games, made = parse_schedule(schedule, season)
        games.extend(team_games)
        team_rows.append({"season": season, **t, "made_playoffs": made})
    # Each game shows up in both teams' schedules
    games = list({g["game_id"]: g for g in games}.values())
    return games, team_rows


def validate(games, teams, current_season):
    """Fail loudly if a finished season doesn't look like a real NHL season."""
    problems = []
    for season, group in teams.groupby("season"):
        if season == current_season:
            continue
        season_games = games[games.season == season]
        counts = pd.concat([season_games.home, season_games.away]).value_counts()
        if not (counts == 82).all():
            problems.append(f"{season}: teams without 82 games: {counts[counts != 82].to_dict()}")
        n_playoff = int(group.made_playoffs.sum())
        if n_playoff != 16:
            problems.append(f"{season}: {n_playoff} playoff teams, expected 16")
    if problems:
        raise SystemExit("Data check failed:\n  " + "\n  ".join(problems))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seasons", nargs="+", default=HISTORICAL_SEASONS)
    parser.add_argument("--current", default="20262027",
                        help="in-progress season to include for live odds ('' to skip)")
    args = parser.parse_args()

    end_dates = season_end_dates(refresh=bool(args.current))
    seasons = list(args.seasons) + ([args.current] if args.current else [])

    all_games, all_teams = [], []
    for season in seasons:
        if season not in end_dates:
            print(f"skipping {season}: not in the API's season list")
            continue
        print(f"fetching {season}...")
        g, t = fetch_season(season, end_dates[season], current=season == args.current)
        all_games.extend(g)
        all_teams.extend(t)

    games = pd.DataFrame(all_games).sort_values(["season", "date", "game_id"])
    teams = pd.DataFrame(all_teams).sort_values(["season", "team"])
    validate(games, teams, args.current)

    DATA.mkdir(exist_ok=True)
    games.to_csv(DATA / "games.csv", index=False)
    teams.to_csv(DATA / "teams.csv", index=False)
    print(f"saved {len(games)} games and {len(teams)} team-seasons to {DATA}")


if __name__ == "__main__":
    main()
