import streamlit as st
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Draw, Descriptors, QED
import base64
from io import BytesIO

def render_stage3(disease_data):
    st.header("Stage 3: AI Drug Screening & ADMET Filter")
    st.write(f"Screening ChEMBL compound library against **{disease_data['mutated_gene']}** binding pocket...")
    
    st.info("🧬 **All compounds sourced from ChEMBL (EBI)** — Real measured IC50 binding affinities. Molecular properties computed live via RDKit.")
    
    candidates = disease_data.get('drug_candidates', [])
    
    if not candidates:
        st.warning("No drug candidates found for this target.")
        return
    
    st.subheader(f"Top {len(candidates)} Candidates from ChEMBL")
    
    for idx, cand in enumerate(candidates):
        smiles = cand.get('smiles', '')
        mol = Chem.MolFromSmiles(smiles) if smiles else None
        
        with st.container():
            # Header row with compound name + source badge
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                st.markdown(f"### {idx+1}. {cand.get('name', 'Unknown')}")
            with header_col2:
                source = cand.get('source', 'ChEMBL')
                chembl_id = cand.get('chembl_id', '')
                if chembl_id and chembl_id != 'N/A':
                    st.markdown(f"[View on ChEMBL](https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/)")
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                ic50 = cand.get('ic50_nM')
                if ic50:
                    # Color-code IC50: lower = better
                    delta_label = "Potent" if ic50 < 1000 else "Moderate" if ic50 < 10000 else "Weak"
                    st.metric("IC50 (Measured)", f"{ic50:.0f} nM", delta=delta_label)
                else:
                    affinity = cand.get('affinity', 'N/A')
                    st.metric("Binding Affinity", f"{affinity} kcal/mol", delta="Computed")
            
            with col2:
                # Compute molecular properties live via RDKit
                if mol:
                    mw = round(Descriptors.MolWt(mol), 1)
                    lipinski = "Pass" if mw < 500 else "Fail"
                    st.metric("Mol Weight", f"{mw} Da", delta=lipinski)
                else:
                    st.metric("Mol Weight", "N/A")
            
            with col3:
                if mol:
                    logp = round(Descriptors.MolLogP(mol), 2)
                    lipinski_logp = "Pass" if logp <= 5 else "Fail"
                    st.metric("LogP (Lipophilicity)", f"{logp}", delta=lipinski_logp)
                else:
                    st.metric("LogP", "N/A")
            
            with col4:
                if mol:
                    qed = round(QED.qed(mol), 3)
                    qed_label = "Drug-like" if qed > 0.5 else "Low"
                    st.metric("QED Score", f"{qed}", delta=qed_label)
                else:
                    st.metric("QED", "N/A")
            
            # Molecule image
            if mol:
                img = Draw.MolToImage(mol, size=(400, 250))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                st.markdown(f'<img src="data:image/png;base64,{img_str}" width="50%">', unsafe_allow_html=True)
            else:
                st.write("⚠️ Invalid SMILES — could not render structure")
            
            st.text(f"SMILES: {smiles}")
            st.markdown("---")
