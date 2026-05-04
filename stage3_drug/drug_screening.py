import streamlit as st
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Draw
import base64
from io import BytesIO

def render_stage3(disease_data):
    st.header("Stage 3: GNN Drug Screening & ADMET Filter")
    st.write(f"Screening library against **{disease_data['mutated_gene']}** binding pocket...")
    
    candidates = disease_data['drug_candidates']
    
    st.subheader("Top Candidates Generated")
    
    for idx, cand in enumerate(candidates):
        with st.container():
            st.markdown(f"### {idx+1}. {cand['name']}")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                st.metric("Binding Affinity", f"{cand['affinity']} kcal/mol", delta="High")
            with col2:
                st.metric("ADMET Safety Score", f"{cand['admet_score']:.2f}", delta="Safe")
                
            with col3:
                # Generate molecule image
                mol = Chem.MolFromSmiles(cand['smiles'])
                if mol:
                    img = Draw.MolToImage(mol, size=(300, 200))
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    st.markdown(f'<img src="data:image/png;base64,{img_str}" width="100%">', unsafe_allow_html=True)
                else:
                    st.write("Invalid SMILES string")
            
            st.text(f"SMILES: {cand['smiles']}")
            st.markdown("---")
