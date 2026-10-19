import pandas as pd
import pytest

from nhl.analyze import completed_seasons, plot, write_findings
from nhl.features import latest, snapshot, team_games
from nhl.fetch import parse_schedule, validate
from nhl.model import evaluate, pick_top
from nhl.odds import current_odds
from tests.synthetic import make_league


# ---------------------------------------------------------------- features

def two_games():
    return pd.DataFrame([
        # A beats B in regulation, then B beats A in a shootout
        {"season": "20232024", "game_id": 1, "date": "2023-10-10", "home": "A", "away": "B",
         "home_score": 4, "away_score": 1, "end": "REG"},
        {"season": "20232024", "game_id": 2, "date": "2023-10-12", "home": "A", "away": "B",
         "home_score": 2, "away_score": 3, "end": "SO"},
    ])


def test_points_follow_nhl_rules():
    tg = team_games(two_games())
    pts = tg.set_index(["game_id", "team"]).points
    assert pts[(1, "A")] == 2 and pts[(1, "B")] == 0   # regulation win and loss
    assert pts[(2, "B")] == 2 and pts[(2, "A")] == 1   # shootout win, shootout loss


def test_snapshot_rates():
    snap = snapshot(team_games(two_games()), 2).set_index("team")
    assert snap.loc["A", "pts_pct"] == pytest.approx(3 / 4)
    assert snap.loc["A", "gd_pg"] == pytest.approx((6 - 4) / 2)
    assert snap.loc["B", "gd_pg"] == pytest.approx(-1.0)


def test_latest_uses_each_teams_own_games_played():
    games = two_games().iloc[:1]
    assert latest(team_games(games)).games.tolist() == [1, 1]


# ---------------------------------------------------------------- fetch parsing

def schedule_game(game_type, state="OFF", season=20232024, gid=1, end="REG"):
    return {"id": gid, "season": season, "gameType": game_type, "gameState": state,
            "gameDate": "2024-01-01", "gameOutcome": {"lastPeriodType": end},
            "homeTeam": {"abbrev": "BOS", "score": 3}, "awayTeam": {"abbrev": "TOR", "score": 2}}


def test_parse_schedule_keeps_only_completed_regular_season_games():
    schedule = {"games": [
        schedule_game(1, gid=1),                    # preseason
        schedule_game(2, gid=2),                    # completed regular season
        schedule_game(2, state="FUT", gid=3),       # not played yet
        schedule_game(2, season=20222023, gid=4),   # wrong season
    ]}
    games, made_playoffs = parse_schedule(schedule, "20232024")
    assert [g["game_id"] for g in games] == [2]
    assert made_playoffs is False


def test_parse_schedule_detects_playoffs():
    _, made_playoffs = parse_schedule({"games": [schedule_game(3)]}, "20232024")
    assert made_playoffs is True


def test_validate_rejects_short_seasons():
    games, teams = make_league(seasons=("20222023",), games_per_team=40)
    with pytest.raises(SystemExit):
        validate(games, teams, current_season="")


def test_validate_accepts_a_full_league():
    games, teams = make_league(seasons=("20222023",))
    validate(games, teams, current_season="")


# ---------------------------------------------------------------- model

def test_pick_top_takes_eight_per_conference():
    games, teams = make_league(seasons=("20222023",))
    df = teams.assign(score=range(len(teams)))
    picked = df[pick_top(df, "score")]
    assert picked.groupby("conference").size().tolist() == [8, 8]


def test_end_to_end_on_synthetic_league(tmp_path):
    games, teams = make_league()
    seasons = completed_seasons(games, teams)
    assert len(seasons) == 4

    results = evaluate(team_games(games), teams, [10, 41, 82], seasons)
    acc = results.pivot(index="games", columns="predictor", values="accuracy")
    # Final points decide the playoffs in this league, so 82-game points % is perfect
    assert acc.loc[82, "Points %"] == pytest.approx(1.0)
    # More games played should never make points % a worse guide
    assert acc.loc[10, "Points %"] <= acc.loc[41, "Points %"] <= acc.loc[82, "Points %"]
    assert (results.accuracy > 0.5).all()
    # Final points % decides the playoffs here, so at 82 games its probabilities
    # should beat goal differential's. Without feature scaling, regularization
    # blunted them and points % scored worse (Brier ~0.11 vs ~0.06).
    brier = results.pivot(index="games", columns="predictor", values="brier")
    assert brier.loc[82, "Points %"] < brier.loc[82, "Goal differential"]
    assert brier.loc[82, "Points %"] < 0.08

    plot(results, len(seasons), tmp_path / "chart.png")
    write_findings(results, seasons, 128, tmp_path / "findings.md")
    assert (tmp_path / "chart.png").stat().st_size > 10_000
    assert "| 41 |" in (tmp_path / "findings.md").read_text()


def test_current_odds_for_a_season_in_progress():
    games, teams = make_league(
        seasons=("20212022", "20222023", "20232024", "20242025"), partial=("20242025", 12))
    season, n, table = current_odds(games, teams)
    assert season == "20242025" and n == 12
    assert len(table) == 32
    assert table.playoff_prob.between(0, 1).all()
    assert table.groupby("conference").projected_in.sum().tolist() == [8, 8]
