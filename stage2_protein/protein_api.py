import streamlit as st
import requests
import py3Dmol
from stmol import showmol
import time
import os

def render_stage2(disease_data):
    st.header(f"Stage 2: 3D Protein Structure Prediction")
    st.write(f"Target: **{disease_data['mutated_gene']}**")
    
    sequence = disease_data['sequence']
    st.text_area("Protein Sequence (FASTA)", sequence, height=100)
    
    pdb_dir = 'data/pdb_cache'
    os.makedirs(pdb_dir, exist_ok=True)
    pdb_path = f"{pdb_dir}/{disease_data['mutated_gene']}.pdb"
    
    if st.button("Predict 3D Structure with ESMFold"):
        pdb_string = None
        if os.path.exists(pdb_path):
            st.info("Loaded pre-cached structure for rapid demo.")
            with open(pdb_path, 'r') as f:
                pdb_string = f.read()
        else:
            with st.spinner("Calling ESMFold API... This may take a minute."):
                headers = {
                    'Content-Type': 'text/plain',
                }
                try:
                    response = requests.post('https://api.esmatlas.com/foldSequence/v1/pdb/', headers=headers, data=sequence)
                    if response.status_code == 200:
                        pdb_string = response.text
                        with open(pdb_path, 'w') as f:
                            f.write(pdb_string)
                        st.success("Successfully folded protein!")
                    else:
                        st.error(f"ESMFold API error: {response.status_code}")
                        st.write(response.text)
                except Exception as e:
                    st.error(f"Failed to connect to ESMFold: {e}")
                    
        if pdb_string:
            st.subheader("Interactive 3D Viewer")
            view = py3Dmol.view(width=800, height=500)
            view.addModel(pdb_string, 'pdb')
            view.setStyle({'cartoon': {'color': 'spectrum'}})
            view.setBackgroundColor('#111111')
            view.zoomTo()
            showmol(view, height=500, width=800)
