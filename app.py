import streamlit as st
import pandas as pd
import json
import joblib
import os

from style import load_css
from stage1_genomics.genomics import render_stage1
from stage2_protein.protein_api import render_stage2
from stage3_drug.drug_screening import render_stage3
from stage4_bioproduction.bioproduction import render_stage4

st.set_page_config(page_title="BioGenesis Platform", page_icon="🧬", layout="wide")

# Inject Custom CSS
st.markdown(load_css(), unsafe_allow_html=True)

# 1. Custom Top Bar Header
st.markdown("""
<div class="top-bar">
    <h1>🧬 BioGenesis Platform</h1>
    <div class="top-bar-status">SYSTEM ONLINE • v1.2.0</div>
</div>
""", unsafe_allow_html=True)

# Load pre-cached disease data
@st.cache_data
def load_data(cache_buster=1):
    with open('data/diseases.json', 'r') as f:
        return json.load(f)

diseases = load_data()
df = pd.read_csv('data/disease_dataset.csv')

# --- LEFT SIDEBAR (Clinical Styling) ---
st.sidebar.markdown('<div class="sidebar-section-label">Target Selection</div>', unsafe_allow_html=True)
search_query = st.sidebar.selectbox("Disease Target", df['name'].tolist(), index=0)

@st.cache_resource
def load_ml_models(cache_buster=1):
    if os.path.exists('models/vectorizer.pkl') and os.path.exists('models/knn_model.pkl'):
        return joblib.load('models/vectorizer.pkl'), joblib.load('models/knn_model.pkl')
    return None, None

vectorizer, knn = load_ml_models()

if vectorizer and knn and search_query:
    query_lower = search_query.lower()
    exact_matches = df[df['name'].str.lower().str.contains(query_lower)]
    
    if not exact_matches.empty:
        match_index = exact_matches.index[0]
    else:
        X_query = vectorizer.transform([search_query])
        distances, indices = knn.kneighbors(X_query)
        match_index = indices[0][0]
        
        if match_index >= len(df):
            st.cache_resource.clear()
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
    
    st.sidebar.markdown('<div class="sidebar-section-label">Model Output</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div style="font-size: 14px; color: #f8fafc; font-weight: 500; margin-bottom: 16px;">Target Matched:<br/><span style="color: #60a5fa; font-size: 16px;">{selected_disease["name"]}</span></div>', unsafe_allow_html=True)
    
    st.sidebar.markdown('<div class="sidebar-section-label">Key Metadata</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="metadata-badge accent">Target Gene: {selected_disease["mutated_gene"]}</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="metadata-badge">Tissue/Cell: {selected_disease["cell_type"]}</div>', unsafe_allow_html=True)
else:
    selected_disease = diseases[0]

# --- MAIN CONTENT AREA ---
# The CSS injected above overrides standard tabs to look like a horizontal step indicator.
tabs = st.tabs([
    "Step 1: Genomics Profiling", 
    "Step 2: 3D Protein Structural Analysis", 
    "Step 3: GNN Drug Generation", 
    "Step 4: Bioproduction Pathway"
])

with tabs[0]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    render_stage1(selected_disease)
    st.markdown('</div>', unsafe_allow_html=True)
    
with tabs[1]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    render_stage2(selected_disease)
    st.markdown('</div>', unsafe_allow_html=True)
    
with tabs[2]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    render_stage3(selected_disease)
    st.markdown('</div>', unsafe_allow_html=True)
    
with tabs[3]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    render_stage4(selected_disease)
    st.markdown('</div>', unsafe_allow_html=True)
