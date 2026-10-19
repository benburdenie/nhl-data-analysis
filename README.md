# NHL Data Analysis

A Python project that analyzes NHL player and team performance data across five seasons (2019-20 through 2023-24), generating visual insights using pandas and matplotlib.

---

## Features

- **Load and clean** skater, goalie, and team stats from CSV files
- **Top scorer rankings** by points, goals, assists, or points-per-game
- **Player season trends** — compare up to 3 players across seasons on one chart
- **Goalie analysis** — save %, goals-against average, shutouts, season trends
- **Team analysis** — standings, goal differential, goals for vs against
- **Scatter plot** — goal differential vs standings points (correlation analysis)
- **Full summary report** exported to `outputs/summary.txt`
- **Interactive menu** — navigate all analyses from the terminal

---

## Project Structure

```
nhl-data-analysis/
├── data/
│   ├── nhl_skaters.csv     # Skater stats (2019-20 to 2023-24)
│   ├── nhl_goalies.csv     # Goalie stats
│   └── nhl_teams.csv       # Team standings and goals data
├── src/
│   ├── main.py             # Interactive menu, program entry point
│   ├── data_loader.py      # CSV loading and data cleaning
│   ├── analysis.py         # Stats, rankings, filtering, summaries
│   └── visualization.py    # All matplotlib chart generation
├── outputs/
│   ├── top_scorers.png
│   ├── player_trends.png
│   ├── goalie_save_pct.png
│   ├── goalie_trends.png
│   ├── goal_diff_vs_points.png
│   ├── team_goals.png
│   └── summary.txt
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Dataset Source

Data is based on publicly available NHL statistics from [NHL.com](https://www.nhl.com/stats/) and [Hockey Reference](https://www.hockey-reference.com/), covering the 2019-20 through 2023-24 regular seasons.

---

## Skills Demonstrated

| Skill | Where used |
|---|---|
| Python | All source files |
| Data cleaning | `data_loader.py` — null handling, column derivation |
| Data analysis | `analysis.py` — rankings, filtering, groupby, correlation |
| Data visualization | `visualization.py` — 6 distinct chart types |
| Modular design | Separate modules for loading, analysis, and charting |
| Analytical problem solving | `generate_summary()` draws written conclusions from data |

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run from the project root directory
python src/main.py
```

**To generate all charts at once:** choose option `[6]` from the menu.

---

## Example Outputs

### Top Scorers (2022-23)
Stacked bar chart showing goals and assists for the top 10 scorers.
Connor McDavid led with 153 points — the highest single-season total in the dataset.

### Goalie Save Percentages
Linus Ullmark posted the best single-season save percentage in the dataset at .938 (2022-23), well above the league average. Save percentage is notably more consistent year-to-year than win totals, which fluctuate heavily with team quality.

### Goal Differential vs Standings (All Seasons)
Strong positive correlation (r = 0.78) — teams that outscore opponents by large margins almost always rank near the top of the standings.

---

## Key Findings

1. **Goal differential is the strongest predictor of standings** (r = 0.78). Teams like the 2022-23 Bruins (+110 GD, 135 pts) demonstrate that consistent two-way play matters more than any single stat.

2. **Save percentage is more stable than wins** year-to-year. Elite goalies (Hellebuyck, Vasilevskiy) maintain .920+ SV% even on weaker teams, while win totals swing dramatically with team performance.

3. **Power-play efficiency is a weaker predictor of standings** (r = 0.31) than goal differential. Teams can win consistently with average power plays if their 5-on-5 play is strong.

---

## Future Improvements

- GUI dashboard using Tkinter or Dash
- Pull live data directly from the NHL API
- Deadline / playoff probability tracking
- Advanced stats: Corsi, Fenwick, expected goals (xG)
- Export charts to a PDF summary report
