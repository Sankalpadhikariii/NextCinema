import streamlit as st
import pandas as pd
from scipy import sparse
from sklearn.metrics.pairwise import linear_kernel

@st.cache_resource
def load():
    movies = pd.read_csv("movies_app.csv")
    mat = sparse.load_npz("mat.npz")
    return movies, mat

movies, mat = load()
m = movies["vote_count"].quantile(0.60)
idx = pd.Series(movies.index, index=movies["title"]).drop_duplicates()

def recommend_v2(title, n=10, pool=30):
    i = idx[title]
    sims = linear_kernel(mat[i], mat).ravel()
    top = sims.argsort()[::-1][1:pool + 1]
    cand = movies.iloc[top]
    cand = cand[cand["vote_count"] >= m]
    return cand.sort_values("wr", ascending=False)["title"].head(n)

st.title("Movie Recommender")
title = st.selectbox("Pick a movie", movies["title"].sort_values())

if st.button("Recommend"):
    for t in recommend_v2(title):
        st.write("•", t)