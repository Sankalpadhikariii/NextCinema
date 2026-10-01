from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from scipy import sparse
from sklearn.metrics.pairwise import linear_kernel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

POSTER = "https://image.tmdb.org/t/p/w342"

# movies_app.csv and mat.npz must be in the same folder as this file
movies = pd.read_csv("movies_app.csv")
mat = sparse.load_npz("mat.npz")
m = movies["vote_count"].quantile(0.60)
idx = pd.Series(movies.index, index=movies["title"]).drop_duplicates()


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
def search(q: str):
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
def popular(n: int = 20):
    top = movies.sort_values("wr", ascending=False).head(n)
    return [card(i) for i in top.index]


@app.get("/recommend")
def recommend(title: str, n: int = 10):
    if title not in idx:
        raise HTTPException(404, "Movie not found")
    i = int(idx[title])
    sims = linear_kernel(mat[i], mat).ravel()
    top = sims.argsort()[::-1][1:n * 3 + 1]
    cand = movies.iloc[top].assign(match=sims[top])
    cand = cand[cand["vote_count"] >= m].sort_values("wr", ascending=False).head(n)
    return {
        "movie": card(i),
        "recommendations": [card(ix, row["match"]) for ix, row in cand.iterrows()],
    }