import streamlit as st
import pandas as pd
import json

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

disease_names = [d['name'] for d in diseases]
selected_disease_name = st.sidebar.selectbox("Select Target Disease", disease_names)
selected_disease = next(d for d in diseases if d['name'] == selected_disease_name)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Mutated Gene:** {selected_disease['mutated_gene']}")
st.sidebar.markdown(f"**Affected Cell Type:** {selected_disease['cell_type']}")

tabs = st.tabs(["Stage 1: Genomics", "Stage 2: 3D Protein", "Stage 3: GNN Screening", "Stage 4: BioProduction"])

with tabs[0]:
    render_stage1(selected_disease)
    
with tabs[1]:
    render_stage2(selected_disease)
    
with tabs[2]:
    render_stage3(selected_disease)
    
with tabs[3]:
    render_stage4(selected_disease)
