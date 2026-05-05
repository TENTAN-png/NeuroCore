import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import joblib
from rdkit import Chem
from rdkit.Chem import Draw, Descriptors, QED, AllChem
import base64
from io import BytesIO


def smiles_to_fingerprint(smiles, n_bits=2048):
    """Converts SMILES to Morgan Fingerprint (ECFP4)."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    return np.array(fp)


def smiles_to_descriptors(smiles):
    """Computes molecular descriptors for ADMET prediction."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return np.array([
        Descriptors.MolWt(mol),
        Descriptors.MolLogP(mol),
        Descriptors.NumHDonors(mol),
        Descriptors.NumHAcceptors(mol),
        Descriptors.TPSA(mol),
        Descriptors.NumRotatableBonds(mol),
        Descriptors.RingCount(mol),
        QED.qed(mol)
    ])


@st.cache_resource
def load_ml_models():
    """Load the trained ML models."""
    models = {}
    
    pic50_path = 'models/pIC50_rf_model.pkl'
    druglike_path = 'models/druglikeness_gb_model.pkl'
    metadata_path = 'models/training_metadata.json'
    
    if os.path.exists(pic50_path):
        models['pIC50'] = joblib.load(pic50_path)
    if os.path.exists(druglike_path):
        models['druglikeness'] = joblib.load(druglike_path)
    if os.path.exists(metadata_path):
        import json
        with open(metadata_path) as f:
            models['metadata'] = json.load(f)
    
    return models


def render_stage3(disease_data):
    st.header("Stage 3: ML-Powered Drug Screening")
    st.write(f"Screening compound library against **{disease_data['mutated_gene']}** using trained ML models...")
    
    # Load ML models
    models = load_ml_models()
    has_ml = 'pIC50' in models and 'druglikeness' in models
    
    if has_ml:
        meta = models.get('metadata', {})
        st.success(
            f"**ML Models Loaded** — Trained on **{meta.get('training_samples', 'N/A')}** real ChEMBL compounds "
            f"from {len(meta.get('targets_used', []))} protein targets. "
            f"pIC50 Regressor R²={meta.get('pIC50_r2', 'N/A')}, "
            f"ADMET Classifier Accuracy={meta.get('druglikeness_accuracy', 'N/A')}"
        )
    else:
        st.warning("ML models not found. Run `python train_ml_models.py` to train on ChEMBL data.")
    
    candidates = disease_data.get('drug_candidates', [])
    
    if not candidates:
        st.warning("No drug candidates found for this target.")
        return
    
    st.subheader(f"Top {len(candidates)} Candidates — ChEMBL + ML Predictions")
    
    for idx, cand in enumerate(candidates):
        smiles = cand.get('smiles', '')
        mol = Chem.MolFromSmiles(smiles) if smiles else None
        
        with st.container():
            # Header
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                st.markdown(f"### {idx+1}. {cand.get('name', 'Unknown')}")
            with header_col2:
                chembl_id = cand.get('chembl_id', '')
                if chembl_id and chembl_id != 'N/A':
                    st.markdown(f"[View on ChEMBL →](https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/)")
            
            # ---- EXPERIMENTAL DATA (from ChEMBL) ----
            st.markdown("##### 📊 Experimental Data (ChEMBL)")
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                ic50 = cand.get('ic50_nM')
                if ic50:
                    delta_label = "Potent" if ic50 < 1000 else "Moderate" if ic50 < 10000 else "Weak"
                    st.metric("Measured IC50", f"{ic50:.0f} nM", delta=delta_label)
            with exp_col2:
                source = cand.get('source', 'ChEMBL')
                st.metric("Data Source", source, delta_color="off")
            
            # ---- ML PREDICTIONS ----
            if has_ml and mol:
                st.markdown("##### 🤖 ML Model Predictions")
                
                fp = smiles_to_fingerprint(smiles)
                desc = smiles_to_descriptors(smiles)
                
                ml_col1, ml_col2, ml_col3, ml_col4 = st.columns(4)
                
                with ml_col1:
                    if fp is not None:
                        pred_pIC50 = models['pIC50'].predict(fp.reshape(1, -1))[0]
                        pred_ic50_nM = 10**(-pred_pIC50) * 1e9
                        
                        measured_ic50 = cand.get('ic50_nM', None)
                        if measured_ic50:
                            error_pct = abs(pred_ic50_nM - measured_ic50) / measured_ic50 * 100
                            delta_str = f"Error: {error_pct:.0f}%"
                        else:
                            delta_str = "Predicted"
                        
                        st.metric("ML Predicted IC50", f"{pred_ic50_nM:.0f} nM", delta=delta_str, delta_color="inverse")
                
                with ml_col2:
                    if desc is not None:
                        pred_druglike = models['druglikeness'].predict(desc.reshape(1, -1))[0]
                        pred_proba = models['druglikeness'].predict_proba(desc.reshape(1, -1))[0]
                        confidence = max(pred_proba) * 100
                        label = "PASS" if pred_druglike == 1 else "FAIL"
                        st.metric("ADMET Prediction", label, delta=f"{confidence:.0f}% conf.")
                
                with ml_col3:
                    if mol:
                        mw = round(Descriptors.MolWt(mol), 1)
                        lipinski = "Pass" if mw < 500 else "Fail"
                        st.metric("Mol Weight", f"{mw} Da", delta=lipinski)
                
                with ml_col4:
                    if mol:
                        qed_val = round(QED.qed(mol), 3)
                        qed_label = "Drug-like" if qed_val > 0.5 else "Low"
                        st.metric("QED Score", f"{qed_val}", delta=qed_label)
            
            # Molecule image
            if mol:
                img = Draw.MolToImage(mol, size=(400, 250))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                st.markdown(f'<img src="data:image/png;base64,{img_str}" width="45%">', unsafe_allow_html=True)
            
            st.text(f"SMILES: {smiles}")
            st.markdown("---")
