"""Predict which teams make the playoffs from their record after N games.

Each predictor is a logistic regression on season-to-date stats. It is scored
with leave-one-season-out cross-validation: train on every other season, then
predict the held-out one, so a season never helps predict itself.

Because exactly 8 teams per conference make the playoffs, a team is predicted
"in" when its probability ranks top 8 in its conference that season.
"""

import pandas as pd
from sklearn.linear_model import LogisticRegression

from nhl.features import snapshot

PREDICTORS = {
    "Points %": ["pts_pct"],
    "Goal differential": ["gd_pg"],
    "Both": ["pts_pct", "gd_pg"],
}
PLAYOFF_SPOTS_PER_CONFERENCE = 8


def fit(train, features):
    model = LogisticRegression()
    model.fit(train[features], train.made_playoffs)
    return model


def pick_top(df, score_col, k=PLAYOFF_SPOTS_PER_CONFERENCE):
    """True for the k highest scores in each season and conference."""
    rank = df.groupby(["season", "conference"])[score_col].rank(
        ascending=False, method="first")
    return rank <= k


def evaluate(tg, teams, checkpoints, seasons):
    """Accuracy and Brier score of each predictor after N games, cross-validated by season."""
    rows = []
    for n in checkpoints:
        snap = snapshot(tg, n).merge(teams, on=["season", "team"])
        snap = snap[snap.season.isin(seasons)]
        for name, features in PREDICTORS.items():
            held_out = []
            for season in seasons:
                train, test = snap[snap.season != season], snap[snap.season == season].copy()
                test["prob"] = fit(train, features).predict_proba(test[features])[:, 1]
                held_out.append(test)
            pred = pd.concat(held_out)
            pred["predicted"] = pick_top(pred, "prob")
            rows.append({
                "games": n,
                "predictor": name,
                "accuracy": (pred.predicted == pred.made_playoffs).mean(),
                "brier": ((pred.prob - pred.made_playoffs) ** 2).mean(),
            })
    return pd.DataFrame(rows)
