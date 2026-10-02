# 🎬 NextCinema — Movie Recommendation System

A full-stack movie recommender. Pick a movie you like and get similar ones, ranked by both how closely they match and how well they were received. It combines a **content-based** recommender (TF-IDF on plot, genres, keywords, cast and director), a **collaborative filtering** model built with TensorFlow/Keras, and a **React** frontend served by a **FastAPI** backend.

<img width="1104" height="774" alt="Screenshot 2026-10-01 210825" src="https://github.com/user-attachments/assets/72b79792-6ceb-4637-85f3-3fb7427aea56" />
<img width="1818" height="937" alt="Screenshot 2026-10-01 215708" src="https://github.com/user-attachments/assets/33af26c8-abe0-4bd3-80b5-7ada9570029e" />


## Features

- **Content-based recommendations:** movies are matched on overview, genres, keywords, top 3 cast members and director (the director is weighted higher), using TF-IDF vectors and cosine similarity.
- **Quality-aware ranking:** similar movies are filtered by vote count and ranked by a blend of similarity and the IMDB weighted rating, so obscure low-vote films don't beat well-loved ones.
- **Collaborative filtering:** a matrix factorization model (user and movie embeddings plus biases) trained on user ratings with TensorFlow/Keras, with early stopping to prevent overfitting.
- **Hybrid approach (notebook):** content similarity picks the candidates and the user model orders them by predicted rating for a given user.
- **Model evaluation:** RMSE, MAE, accuracy, precision, recall, F1, ROC AUC, confusion matrix, and precision@10 / recall@10, all plotted in the notebook.
- **Web app:** search with autocomplete and poster thumbnails, a top-rated home page, movie detail view, and recommendation cards with rating and match badges.
- **Tested API:** endpoint tests with pytest.

## Tech stack

| Layer | Tools |
|---|---|
| Data and ML | Python, pandas, NumPy, scikit-learn, TensorFlow / Keras, SciPy |
| Visualization | Matplotlib, Seaborn |
| Backend | FastAPI, Uvicorn, pytest |
| Frontend | React, Vite, CSS |

## Dataset

[The Movies Dataset](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset) from Kaggle (`movies_metadata`, `credits`, `keywords`, `links_small`, `ratings_small`). The project uses the ~9,000 movies in `links_small`, which keeps the similarity computation light on memory.

The raw Kaggle files are **not** in this repository because of their size. You only need them if you want to re-run the notebook. The processed files the app needs (`movies_app.csv` and `mat.npz`) are included, so you can run the app without downloading anything.

## How it works

1. **Preprocessing:** merge metadata, credits and keywords on the TMDB id, clean malformed ids, parse the stringified JSON columns, and build a text "soup" per movie.
2. **Content model:** vectorize the soup with TF-IDF and compute cosine similarity between movies.
3. **Collaborative model:** encode users and movies as integer ids, learn 32-dimensional embeddings, and predict `rating = user · movie + user bias + movie bias`. On held-out ratings the model reached a validation RMSE of about 0.88.
4. **Evaluation:** ratings of 4 or above count as "liked", which turns the regression into a classification problem so precision, recall and F1 can be reported.
5. **Serving:** the TF-IDF matrix and a cleaned movie table are loaded by the FastAPI backend, which exposes `/search`, `/popular` and `/recommend`. The React app calls these endpoints.

## Project structure

```
NextCinema/
├── api.py                  # FastAPI backend
├── recommender.ipynb       # data cleaning, models, evaluation graphs
├── movies_app.csv          # processed movie table used by the API
├── mat.npz                 # TF-IDF matrix used by the API
├── requirements.txt        # runtime dependencies
├── requirements-dev.txt    # test dependencies
├── pytest.ini
├── tests/
│   └── test_api.py
└── movie-ui/               # React + Vite frontend
    └── src/
        ├── App.jsx
        └── App.css
```

## Getting started

**1. Clone the repository.**

```bash
git clone https://github.com/Sankalpadhikariii/NextCinema.git
cd NextCinema
```

**2. Start the backend.**

```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

API docs are available at `http://localhost:8000/docs`.

**3. Start the frontend** (requires Node.js), in a second terminal.

```bash
cd movie-ui
npm install
npm run dev
```

Open `http://localhost:5173`.

**4. Run the tests** (optional).

```bash
pip install -r requirements-dev.txt
pytest
```

### Configuration

The backend reads two optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATA_DIR` | folder containing `api.py` | where `movies_app.csv` and `mat.npz` are loaded from |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | comma-separated list of allowed frontend origins |

## API

| Endpoint | Description |
|---|---|
| `GET /search?q=...` | Autocomplete: up to 8 matching titles with year and poster |
| `GET /popular?n=20` | Top movies by weighted rating |
| `GET /recommend?title=...&n=10` | Selected movie plus `n` recommendations with match scores |

## Roadmap

- [ ] User accounts and sessions (sign up, log in, JWT)
- [ ] Let users rate movies and keep a watchlist
- [ ] Serve the personalized hybrid model in the app (currently the web app uses the content-based recommender; the hybrid model lives in the notebook)
- [ ] Handle new users (cold start) from their first few ratings
- [ ] Subscription tiers

## Acknowledgements

Data from [The Movies Dataset](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset) on Kaggle. Posters are loaded from TMDB's image server. This product uses TMDB data but is not endorsed or certified by TMDB.
