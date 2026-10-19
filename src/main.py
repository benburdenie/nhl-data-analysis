"""
main.py
-------
Program entry point. Displays an interactive menu and
calls the appropriate analysis + visualization functions.
Run from the project root:
    python src/main.py
"""

import os
import sys

# Make sure sibling modules are importable when running as a script
sys.path.insert(0, os.path.dirname(__file__))

import data_loader as dl
import analysis    as an
import visualization as vz


SEASONS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]
DEFAULT_SEASON = "2022-23"


# ─────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────

def _divider(char="-", width=52):
    print(char * width)

def _header(title: str):
    _divider("=")
    print(f"  {title}")
    _divider("=")

def _pick_season() -> str:
    print("\n  Available seasons:")
    for i, s in enumerate(SEASONS, 1):
        print(f"    [{i}] {s}")
    choice = input("  Choose season (or press Enter for 2022-23): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(SEASONS):
        return SEASONS[int(choice) - 1]
    return DEFAULT_SEASON


# ─────────────────────────────────────────────────────────────
#  Menu sections
# ─────────────────────────────────────────────────────────────

def menu_top_scorers(skaters):
    _header("Top Scorers")
    season = _pick_season()

    print("\n  Rank by: [1] Points  [2] Goals  [3] Assists  [4] Pts/Game")
    opt = input("  Choice (Enter = Points): ").strip()
    metrics = {"1": "points", "2": "goals", "3": "assists", "4": "points_per_game"}
    metric = metrics.get(opt, "points")

    df = an.top_scorers(skaters, season=season, top_n=10, metric=metric)
    print(f"\n  Top 10 by {metric}  --  {season}\n")
    print(df.to_string(index=False))

    print("\n  Generating chart...")
    vz.plot_top_scorers(df, season, metric)
    print("  Done!")


def menu_player_trend(skaters):
    _header("Player Season Trend")
    print("\n  Enter up to 3 player names (comma-separated):")
    print("  Example: Connor McDavid, Auston Matthews")
    raw = input("  > ").strip()
    names = [n.strip() for n in raw.split(",")][:3]

    trends = {name: an.player_season_trend(skaters, name) for name in names}
    for name, df in trends.items():
        if df.empty:
            print(f"  [!] No data found for '{name}'")
        else:
            print(f"\n  {name}:\n{df.to_string(index=False)}")

    if any(not v.empty for v in trends.values()):
        print("\n  Generating chart...")
        vz.plot_player_trends(trends)
        print("  Done!")


def menu_goalie_analysis(goalies):
    _header("Goalie Analysis")
    season = _pick_season()

    print("\n  [1] Save percentage ranking")
    print("  [2] Goals against average ranking")
    print("  [3] Season trend for a goalie")
    opt = input("  Choice: ").strip()

    if opt == "3":
        print("\n  Enter up to 2 goalie names (comma-separated):")
        print("  Example: Connor Hellebuyck, Andrei Vasilevskiy")
        raw = input("  > ").strip()
        names = [n.strip() for n in raw.split(",")][:2]
        trends = {name: an.goalie_trend(goalies, name) for name in names}
        for name, df in trends.items():
            if df.empty:
                print(f"  [!] No data found for '{name}'")
            else:
                print(f"\n  {name}:\n{df.to_string(index=False)}")
        if any(not v.empty for v in trends.values()):
            vz.plot_goalie_trend(trends)
            print("  Chart saved!")
    else:
        metric = "save_pct" if opt != "2" else "goals_against_avg"
        df = an.top_goalies(goalies, season=season, top_n=8, metric=metric)
        print(f"\n  Top goalies ({metric})  --  {season}\n")
        print(df.to_string(index=False))
        vz.plot_goalie_save_pct(df, season)
        print("  Chart saved!")


def menu_team_analysis(teams):
    _header("Team Analysis")

    print("\n  [1] Standings / top teams for a season")
    print("  [2] Goal differential vs standings (scatter, all seasons)")
    print("  [3] Goals for vs against comparison")
    opt = input("  Choice: ").strip()

    if opt == "2":
        print("\n  Generating scatter plot...")
        vz.plot_goal_differential_vs_points(teams)
        print("  Chart saved!")
        corr = teams["goal_differential"].corr(teams["points"])
        print(f"\n  Correlation (goal diff vs points): r = {corr:.2f}")
        print("  Teams with stronger goal differential consistently")
        print("  finish higher in standings.")
    elif opt == "3":
        season = _pick_season()
        df = an.top_teams(teams, season=season, top_n=10)
        print(f"\n  Top teams  --  {season}\n")
        print(df.to_string(index=False))
        vz.plot_team_goals(teams, season)
        print("  Chart saved!")
    else:
        season = _pick_season()
        df = an.top_teams(teams, season=season)
        print(f"\n  Top teams  --  {season}\n")
        print(df.to_string(index=False))

        gd_df = an.goal_differential_ranking(teams, season)
        print(f"\n  Goal differential ranking  --  {season}\n")
        print(gd_df.to_string(index=False))


def menu_summary(skaters, goalies, teams):
    _header("Full Summary Report")
    summary = an.generate_summary(skaters, goalies, teams)
    print(summary)

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "outputs", "summary.txt"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(summary + "\n")
    print(f"\n  Summary saved to: {out_path}")


def menu_generate_all(skaters, goalies, teams):
    """Generate every chart and the summary in one shot."""
    _header("Generate All Outputs")
    season = DEFAULT_SEASON
    print(f"  Using season: {season}\n")

    print("  [1/6] Top scorers chart...")
    df = an.top_scorers(skaters, season=season, top_n=10)
    vz.plot_top_scorers(df, season)

    print("  [2/6] Player trends chart (McDavid, Matthews, MacKinnon)...")
    names = ["Connor McDavid", "Auston Matthews", "Nathan MacKinnon"]
    trends = {n: an.player_season_trend(skaters, n) for n in names}
    vz.plot_player_trends(trends)

    print("  [3/6] Goalie save % chart...")
    gdf = an.top_goalies(goalies, season=season, top_n=8)
    vz.plot_goalie_save_pct(gdf, season)

    print("  [4/6] Goalie trend chart (Hellebuyck, Vasilevskiy)...")
    goalie_names = ["Connor Hellebuyck", "Andrei Vasilevskiy"]
    goalie_trends = {n: an.goalie_trend(goalies, n) for n in goalie_names}
    vz.plot_goalie_trend(goalie_trends)

    print("  [5/6] Goal differential vs standings scatter...")
    vz.plot_goal_differential_vs_points(teams)

    print("  [6/6] Team goals for/against chart...")
    vz.plot_team_goals(teams, season)

    print("\n  All charts generated.")
    menu_summary(skaters, goalies, teams)


# ─────────────────────────────────────────────────────────────
#  Main loop
# ─────────────────────────────────────────────────────────────

def main():
    print("\n  Loading data...")
    skaters = dl.load_skaters()
    goalies = dl.load_goalies()
    teams   = dl.load_teams()
    print("  Data loaded successfully.\n")

    while True:
        _divider("=")
        print("       NHL DATA ANALYSIS")
        _divider("=")
        print("  [1]  Top Scorers")
        print("  [2]  Player Season Trend")
        print("  [3]  Goalie Analysis")
        print("  [4]  Team Analysis")
        print("  [5]  Full Summary Report")
        print("  [6]  Generate All Charts + Summary")
        print("  [0]  Exit")
        _divider()

        choice = input("  Choice: ").strip()

        if   choice == "1": menu_top_scorers(skaters)
        elif choice == "2": menu_player_trend(skaters)
        elif choice == "3": menu_goalie_analysis(goalies)
        elif choice == "4": menu_team_analysis(teams)
        elif choice == "5": menu_summary(skaters, goalies, teams)
        elif choice == "6": menu_generate_all(skaters, goalies, teams)
        elif choice == "0":
            print("\n  Goodbye!\n")
            break
        else:
            print("  Invalid option. Please enter 0-6.")


if __name__ == "__main__":
    main()
