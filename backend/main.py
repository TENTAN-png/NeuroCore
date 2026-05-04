from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import joblib
import os

app = FastAPI(title="BioGenesis API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data
df = pd.read_csv('../data/disease_dataset.csv')
with open('../data/diseases.json', 'r') as f:
    diseases_raw = json.load(f)

# Load Models
vectorizer = joblib.load('../models/vectorizer.pkl')
knn = joblib.load('../models/knn_model.pkl')

@app.get("/diseases")
def list_diseases():
    return {"diseases": df['name'].tolist()}

@app.get("/search")
def search_disease(query: str):
    query_lower = query.lower()
    exact_matches = df[df['name'].str.lower().str.contains(query_lower)]
    
    if not exact_matches.empty:
        match_index = exact_matches.index[0]
    else:
        X_query = vectorizer.transform([query])
        distances, indices = knn.kneighbors(X_query)
        match_index = indices[0][0]
        
    if match_index >= len(df):
        match_index = 0
        
    matched_row = df.iloc[match_index]
    
    # Send full structured json
    selected_disease = {
        "name": matched_row["name"],
        "mutated_gene": matched_row["mutated_gene"],
        "cell_type": matched_row["cell_type"],
        "sequence": matched_row["sequence"],
        "up_regulated": eval(matched_row["up_regulated"]),
        "down_regulated": eval(matched_row["down_regulated"]),
        "drug_candidates": eval(str(matched_row["drug_candidates"])),
        "biosynthesis": eval(str(matched_row["biosynthesis"]))
    }
    
    return selected_disease
