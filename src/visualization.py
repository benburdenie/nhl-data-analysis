"""
visualization.py
----------------
All chart creation using matplotlib.
Each function saves a PNG to the outputs/ directory
and returns the file path.
"""

import os
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for saving files
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

OUTPUTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "outputs"
)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Consistent colour palette
COLOURS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf"
]
DARK_BG   = "#1a1a2e"
PANEL_BG  = "#16213e"
TEXT_COL  = "#e0e0e0"
ACCENT    = "#0f3460"
GRID_COL  = "#2a2a4a"


def _apply_dark_style(fig, ax):
    """Apply a consistent dark hockey-rink-inspired style to any axis."""
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)
    ax.tick_params(colors=TEXT_COL, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COL)
    ax.yaxis.label.set_color(TEXT_COL)
    ax.title.set_color(TEXT_COL)
    ax.spines["bottom"].set_color(GRID_COL)
    ax.spines["left"].set_color(GRID_COL)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=GRID_COL, linewidth=0.6, linestyle="--")
    ax.set_axisbelow(True)


def _save(fig, filename: str) -> str:
    path = os.path.join(OUTPUTS_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


# ─────────────────────────────────────────────────────────────
#  Chart 1: Top Scorers Bar Chart
# ─────────────────────────────────────────────────────────────

def plot_top_scorers(df: pd.DataFrame, season: str,
                     metric: str = "points") -> str:
    """
    Horizontal bar chart of top scorers for a given season,
    stacked into goals and assists if metric == 'points'.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_dark_style(fig, ax)

    labels = df["player"] + "\n(" + df["team"] + ")"

    if metric == "points":
        ax.barh(labels, df["assists"], color=COLOURS[0],
                label="Assists", height=0.55)
        ax.barh(labels, df["goals"], left=df["assists"],
                color=COLOURS[1], label="Goals", height=0.55)
        ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COL,
                  labelcolor=TEXT_COL, fontsize=9)
        xlabel = "Points (Goals + Assists)"
    else:
        ax.barh(labels, df[metric], color=COLOURS[2], height=0.55)
        xlabel = metric.replace("_", " ").title()

    # Value labels
    for i, row in df.iterrows():
        val = row[metric]
        ax.text(val + 0.5, i, str(int(val)),
                va="center", ha="left", color=TEXT_COL, fontsize=8)

    ax.invert_yaxis()
    ax.set_xlabel(xlabel, color=TEXT_COL, fontsize=10)
    ax.set_title(f"Top Scorers  —  {season}", color=TEXT_COL,
                 fontsize=13, fontweight="bold", pad=12)

    return _save(fig, "top_scorers.png")


# ─────────────────────────────────────────────────────────────
#  Chart 2: Player point trend over seasons
# ─────────────────────────────────────────────────────────────

def plot_player_trends(trends: dict) -> str:
    """
    Line chart comparing point totals across seasons for
    multiple players.

    Parameters
    ----------
    trends : {player_name: DataFrame} from analysis.player_season_trend()
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_dark_style(fig, ax)

    for i, (name, df) in enumerate(trends.items()):
        if df.empty:
            continue
        ax.plot(df["season"], df["points"], marker="o",
                color=COLOURS[i % len(COLOURS)],
                linewidth=2, markersize=6, label=name)
        # Annotate last point
        last = df.iloc[-1]
        ax.annotate(f"{int(last['points'])}",
                    xy=(last["season"], last["points"]),
                    xytext=(4, 4), textcoords="offset points",
                    color=COLOURS[i % len(COLOURS)], fontsize=8)

    ax.set_xlabel("Season", color=TEXT_COL, fontsize=10)
    ax.set_ylabel("Points", color=TEXT_COL, fontsize=10)
    ax.set_title("Player Point Trends by Season",
                 color=TEXT_COL, fontsize=13, fontweight="bold", pad=12)
    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COL,
              labelcolor=TEXT_COL, fontsize=9)
    ax.tick_params(axis="x", rotation=15)

    return _save(fig, "player_trends.png")


# ─────────────────────────────────────────────────────────────
#  Chart 3: Goalie save-percentage comparison
# ─────────────────────────────────────────────────────────────

def plot_goalie_save_pct(df: pd.DataFrame, season: str) -> str:
    """
    Horizontal bar chart of top goalies' save percentages,
    with a league-average reference line.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_dark_style(fig, ax)

    avg = df["save_pct"].mean()
    colours = [COLOURS[2] if v >= avg else COLOURS[3]
               for v in df["save_pct"]]

    labels = df["player"] + "\n(" + df["team"] + ")"
    bars = ax.barh(labels, df["save_pct"], color=colours, height=0.55)

    # League average line
    ax.axvline(avg, color=TEXT_COL, linestyle="--", linewidth=1.2,
               label=f"Avg: {avg:.3f}")

    # Value labels
    for bar, val in zip(bars, df["save_pct"]):
        ax.text(bar.get_width() + 0.0003, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", color=TEXT_COL, fontsize=8)

    ax.invert_yaxis()
    ax.set_xlabel("Save Percentage", color=TEXT_COL, fontsize=10)
    ax.set_title(f"Goalie Save Percentages  —  {season}",
                 color=TEXT_COL, fontsize=13, fontweight="bold", pad=12)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f"))
    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COL,
              labelcolor=TEXT_COL, fontsize=9)

    return _save(fig, "goalie_save_pct.png")


# ─────────────────────────────────────────────────────────────
#  Chart 4: Goalie season trend (line)
# ─────────────────────────────────────────────────────────────

def plot_goalie_trend(trends: dict) -> str:
    """
    Line chart of GAA and save % over seasons for one or more goalies.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    for ax in (ax1, ax2):
        _apply_dark_style(fig, ax)

    for i, (name, df) in enumerate(trends.items()):
        if df.empty:
            continue
        c = COLOURS[i % len(COLOURS)]
        ax1.plot(df["season"], df["goals_against_avg"], marker="o",
                 color=c, linewidth=2, markersize=6, label=name)
        ax2.plot(df["season"], df["save_pct"], marker="s",
                 color=c, linewidth=2, markersize=6, label=name)

    for ax, title, ylabel in [
        (ax1, "Goals Against Average", "GAA"),
        (ax2, "Save Percentage", "SV%"),
    ]:
        ax.set_title(title, color=TEXT_COL, fontsize=11, fontweight="bold")
        ax.set_ylabel(ylabel, color=TEXT_COL, fontsize=10)
        ax.set_xlabel("Season", color=TEXT_COL, fontsize=10)
        ax.tick_params(axis="x", rotation=15)
        ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COL,
                  labelcolor=TEXT_COL, fontsize=8)

    ax1.invert_yaxis()  # Lower GAA = better, show at top
    fig.suptitle("Goalie Performance Over Time",
                 color=TEXT_COL, fontsize=14, fontweight="bold", y=1.02)

    return _save(fig, "goalie_trends.png")


# ─────────────────────────────────────────────────────────────
#  Chart 5: Goal differential vs standings points scatter
# ─────────────────────────────────────────────────────────────

def plot_goal_differential_vs_points(df: pd.DataFrame, season: str = None) -> str:
    """
    Scatter plot: goal differential (x) vs standings points (y).
    Each dot = one team-season.
    """
    title_suffix = season if season else "All Seasons"
    fig, ax = plt.subplots(figsize=(9, 6))
    _apply_dark_style(fig, ax)

    # Colour by season for multi-season view
    seasons = sorted(df["season"].unique())
    season_colours = {s: COLOURS[i % len(COLOURS)] for i, s in enumerate(seasons)}

    for s in seasons:
        sub = df[df["season"] == s]
        ax.scatter(sub["goal_differential"], sub["points"],
                   color=season_colours[s], s=70, alpha=0.85, label=s,
                   edgecolors="none")

    # Trend line
    import numpy as np
    m, b = np.polyfit(df["goal_differential"], df["points"], 1)
    x_line = [df["goal_differential"].min(), df["goal_differential"].max()]
    y_line = [m * x + b for x in x_line]
    ax.plot(x_line, y_line, color="white", linewidth=1.2,
            linestyle="--", alpha=0.6, label="Trend")

    # Annotate a few standout teams
    for _, row in df.nlargest(3, "points").iterrows():
        ax.annotate(f"{row['team']} '{row['season'][-2:]}",
                    xy=(row["goal_differential"], row["points"]),
                    xytext=(5, 3), textcoords="offset points",
                    color=TEXT_COL, fontsize=7)

    ax.set_xlabel("Goal Differential", color=TEXT_COL, fontsize=10)
    ax.set_ylabel("Standings Points", color=TEXT_COL, fontsize=10)
    ax.set_title(f"Goal Differential vs Standings Points  —  {title_suffix}",
                 color=TEXT_COL, fontsize=12, fontweight="bold", pad=12)
    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COL,
              labelcolor=TEXT_COL, fontsize=7, ncol=2)

    return _save(fig, "goal_diff_vs_points.png")


# ─────────────────────────────────────────────────────────────
#  Chart 6: Team goals for/against comparison
# ─────────────────────────────────────────────────────────────

def plot_team_goals(df: pd.DataFrame, season: str) -> str:
    """
    Grouped bar chart: goals for vs goals against for top teams in a season.
    """
    data = (
        df[df["season"] == season]
          .sort_values("points", ascending=False)
          .head(10)
          .reset_index(drop=True)
    )

    fig, ax = plt.subplots(figsize=(11, 5))
    _apply_dark_style(fig, ax)

    x = range(len(data))
    width = 0.38
    ax.bar([i - width / 2 for i in x], data["goals_for"],
           width=width, color=COLOURS[0], label="Goals For")
    ax.bar([i + width / 2 for i in x], data["goals_against"],
           width=width, color=COLOURS[3], label="Goals Against")

    ax.set_xticks(list(x))
    ax.set_xticklabels(data["team"], color=TEXT_COL, fontsize=9)
    ax.set_ylabel("Goals", color=TEXT_COL, fontsize=10)
    ax.set_title(f"Goals For vs Goals Against  —  Top 10 Teams {season}",
                 color=TEXT_COL, fontsize=12, fontweight="bold", pad=12)
    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COL,
              labelcolor=TEXT_COL, fontsize=9)

    return _save(fig, "team_goals.png")
