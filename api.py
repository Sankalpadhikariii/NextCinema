import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from scipy import sparse
from sklearn.metrics.pairwise import linear_kernel

# Where movies_app.csv and mat.npz live. Defaults to the folder this file is in,
# so it works no matter where uvicorn is started from.
DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent))

# Comma separated list of allowed frontend origins. Set this when you deploy.
ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

POSTER = "https://image.tmdb.org/t/p/w342"

# How much similarity vs. weighted rating counts when ranking recommendations.
# These are a starting point, tune them by trying movies you know well.
W_MATCH = 0.7
W_RATING = 0.3

app = FastAPI(title="NextCinema API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

movies = pd.read_csv(DATA_DIR / "movies_app.csv")
mat = sparse.load_npz(DATA_DIR / "mat.npz")

if mat.shape[0] != len(movies):
    raise RuntimeError(
        f"movies_app.csv has {len(movies)} rows but mat.npz has {mat.shape[0]}. "
        "Re-run the notebook cells that save both files."
    )

movies["vote_count"] = movies["vote_count"].fillna(0)
movies["wr"] = movies["wr"].fillna(0)

m = movies["vote_count"].quantile(0.60)
WR_MAX = movies["wr"].max() or 1.0

# If a title appears more than once, keep the version with the most votes.
by_votes = movies.sort_values("vote_count", ascending=False)
idx = pd.Series(by_votes.index, index=by_votes["title"])
idx = idx[~idx.index.duplicated(keep="first")]


def poster_url(r):
    p = r["poster_path"]
    return POSTER + p if isinstance(p, str) and p.startswith("/") else None


def card(i, match=None):
    r = movies.iloc[i]
    return {
        "title": r["title"],
        "year": None if pd.isna(r["year"]) else int(r["year"]),
        "rating": None if pd.isna(r["vote_average"]) else round(float(r["vote_average"]), 1),
        "genres": r["genres"] if isinstance(r["genres"], str) else "",
        "overview": r["overview"] if isinstance(r["overview"], str) else "",
        "poster": poster_url(r),
        "match": None if match is None else round(float(match), 3),
    }


@app.get("/search")
def search(q: str = Query(..., min_length=1, max_length=100)):
    hits = movies[movies["title"].str.contains(q, case=False, regex=False, na=False)]
    hits = hits.sort_values("vote_count", ascending=False).head(8)
    return [
        {
            "title": r["title"],
            "year": None if pd.isna(r["year"]) else int(r["year"]),
            "poster": poster_url(r),
        }
        for _, r in hits.iterrows()
    ]


@app.get("/popular")
def popular(n: int = Query(20, ge=1, le=50)):
    top = movies.sort_values("wr", ascending=False).head(n)
    return [card(i) for i in top.index]


@app.get("/recommend")
def recommend(title: str, n: int = Query(10, ge=1, le=30)):
    if title not in idx:
        raise HTTPException(404, "Movie not found")
    i = int(idx[title])

    sims = linear_kernel(mat[i], mat).ravel()
    sims[i] = -1.0  # never recommend the movie itself

    # Take a wide pool of the most similar movies, drop the low-vote ones,
    # then rank by a blend of similarity and weighted rating.
    pool = min(n * 5, len(sims) - 1)
    top = sims.argsort()[::-1][:pool]
    cand = movies.iloc[top].assign(match=sims[top])
    cand = cand[cand["vote_count"] >= m]
    match_n = cand["match"] / (cand["match"].max() + 1e-9)
    wr_n = (cand["wr"] - cand["wr"].min()) / (cand["wr"].max() - cand["wr"].min() + 1e-9)
    cand = cand.assign(score=W_MATCH * match_n + W_RATING * wr_n)
    cand = cand.sort_values("score", ascending=False).head(n)

    return {
        "movie": card(i),
        "recommendations": [card(ix, row["match"]) for ix, row in cand.iterrows()],
    }