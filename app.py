import streamlit as st
import pandas as pd
import json
import joblib
import os

from stage1_genomics.genomics import render_stage1
from stage2_protein.protein_api import render_stage2
from stage3_drug.drug_screening import render_stage3
from stage4_bioproduction.bioproduction import render_stage4

st.set_page_config(page_title="BioGenesis AI", page_icon="🧬", layout="wide")

# Load pre-cached disease data
@st.cache_data
def load_data():
    with open('data/diseases.json', 'r') as f:
        return json.load(f)

diseases = load_data()

st.title("🧬 BioGenesis: End-to-End AI Drug Discovery")
st.markdown("""
Welcome to **BioGenesis**, a 4-stage AI pipeline connecting disease genomics directly to biological drug production.
This platform integrates:
1. **Genomics Profile**: Identification of mutated genes and cell types.
2. **Protein Folding (ESMFold)**: 3D prediction of the target protein.
3. **GNN Drug Screening**: Candidate generation and ADMET ranking.
4. **Bio-Production (KEGG)**: Retrosynthesis and organism recommendation for natural production.
""")

st.sidebar.subheader("AI Disease Matcher")
search_query = st.sidebar.text_input("Enter Disease Name (e.g. ALS, Cancer, Diabetes):", "ALS")

@st.cache_resource
def load_ml_models():
    if os.path.exists('models/vectorizer.pkl') and os.path.exists('models/knn_model.pkl'):
        return joblib.load('models/vectorizer.pkl'), joblib.load('models/knn_model.pkl')
    return None, None

vectorizer, knn = load_ml_models()

df = pd.read_csv('data/disease_dataset.csv')

if vectorizer and knn and search_query:
    X_query = vectorizer.transform([search_query])
    distances, indices = knn.kneighbors(X_query)
    match_index = indices[0][0]
    
    # Safety check if cached ML model is out of sync with CSV
    if match_index >= len(df):
        st.cache_resource.clear()  # Clear cache to reload models next time
        match_index = 0
        
    matched_row = df.iloc[match_index]
    
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
    
    st.sidebar.success(f"ML Match: **{selected_disease['name']}**")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Mutated Gene:** {selected_disease['mutated_gene']}")
    st.sidebar.markdown(f"**Affected Cell Type:** {selected_disease['cell_type']}")
else:
    selected_disease = diseases[0]

tabs = st.tabs(["Stage 1: Genomics", "Stage 2: 3D Protein", "Stage 3: GNN Screening", "Stage 4: BioProduction"])

with tabs[0]:
    render_stage1(selected_disease)
    
with tabs[1]:
    render_stage2(selected_disease)
    
with tabs[2]:
    render_stage3(selected_disease)
    
with tabs[3]:
    render_stage4(selected_disease)
