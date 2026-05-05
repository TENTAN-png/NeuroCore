import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import json
import joblib
import xgboost as xgb
from rdkit import Chem
from rdkit.Chem import Draw, Descriptors, QED, AllChem, Lipinski, MolSurf, rdMolDescriptors
import base64
from io import BytesIO


def smiles_to_features(smiles, target_name, metadata=None, n_bits=2048):
    """Combined feature: Morgan FP (2048) + Molecular Descriptors (20) + Target One-Hot (16) = 2084 dim."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    fp_arr = np.array(fp, dtype=np.float32)
    
    try:
        desc = np.array([
            Descriptors.MolWt(mol),
            Descriptors.MolLogP(mol),
            Descriptors.NumHDonors(mol),
            Descriptors.NumHAcceptors(mol),
            Descriptors.TPSA(mol),
            Descriptors.NumRotatableBonds(mol),
            Descriptors.RingCount(mol),
            Descriptors.FractionCSP3(mol),
            Descriptors.NumAromaticRings(mol),
            Descriptors.HeavyAtomCount(mol),
            Descriptors.NumAliphaticRings(mol),
            QED.qed(mol),
            Descriptors.NumHeteroatoms(mol),
            Descriptors.NumValenceElectrons(mol),
            Lipinski.NumAromaticHeterocycles(mol),
            MolSurf.LabuteASA(mol),
            Descriptors.BalabanJ(mol) if Descriptors.BalabanJ(mol) != 0 else 0,
            rdMolDescriptors.CalcNumBridgeheadAtoms(mol),
            Descriptors.MaxPartialCharge(mol) if not math.isnan(Descriptors.MaxPartialCharge(mol)) else 0,
            Descriptors.MinPartialCharge(mol) if not math.isnan(Descriptors.MinPartialCharge(mol)) else 0,
        ], dtype=np.float32)
    except:
        return None
        
    # One-hot encode the target protein
    target_vec = np.zeros(16, dtype=np.float32)
    if metadata and 'target_to_index' in metadata:
        target_to_idx = metadata['target_to_index']
        num_targets = metadata.get('num_targets', 16)
        target_vec = np.zeros(num_targets, dtype=np.float32)
        if target_name in target_to_idx:
            target_vec[target_to_idx[target_name]] = 1.0
    
    return np.concatenate([fp_arr, desc, target_vec])


@st.cache_resource
def load_ml_models():
    """Load the GPU-trained XGBoost models."""
    models = {}
    
    # Try XGBoost GPU models first, fallback to sklearn
    xgb_pic50 = 'models/pIC50_xgb_gpu.json'
    xgb_admet = 'models/druglikeness_xgb_gpu.json'
    meta_path = 'models/training_metadata.json'
    
    if os.path.exists(xgb_pic50):
        bst = xgb.Booster()
        bst.load_model(xgb_pic50)
        models['pIC50'] = bst
        models['model_type'] = 'xgboost'
    elif os.path.exists('models/pIC50_rf_model.pkl'):
        models['pIC50'] = joblib.load('models/pIC50_rf_model.pkl')
        models['model_type'] = 'sklearn'
    
    if os.path.exists(xgb_admet):
        bst_cls = xgb.Booster()
        bst_cls.load_model(xgb_admet)
        models['druglikeness'] = bst_cls
    elif os.path.exists('models/druglikeness_gb_model.pkl'):
        models['druglikeness'] = joblib.load('models/druglikeness_gb_model.pkl')
    
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            models['metadata'] = json.load(f)
    
    return models


def predict_pIC50(models, features):
    """Predict pIC50 using loaded model (XGBoost or sklearn)."""
    if models.get('model_type') == 'xgboost':
        dmat = xgb.DMatrix(features.reshape(1, -1))
        return models['pIC50'].predict(dmat)[0]
    else:
        return models['pIC50'].predict(features.reshape(1, -1))[0]


def predict_druglikeness(models, features):
    """Predict drug-likeness using loaded model."""
    if models.get('model_type') == 'xgboost':
        dmat = xgb.DMatrix(features.reshape(1, -1))
        prob = models['druglikeness'].predict(dmat)[0]
        return int(prob > 0.5), float(max(prob, 1 - prob))
    else:
        pred = models['druglikeness'].predict(features.reshape(1, -1))[0]
        proba = models['druglikeness'].predict_proba(features.reshape(1, -1))[0]
        return int(pred), float(max(proba))


def render_stage3(disease_data):
    st.header("Stage 3: ML-Powered Drug Screening")
    st.write(f"Screening compound library against **{disease_data['mutated_gene']}** using GPU-trained XGBoost models...")
    
    models = load_ml_models()
    has_ml = 'pIC50' in models and 'druglikeness' in models
    
    if has_ml:
        meta = models.get('metadata', {})
        engine = meta.get('engine', 'Unknown')
        st.success(
            f"**ML Engine: {engine}** — Trained on **{meta.get('training_samples', 'N/A')}** ChEMBL compounds "
            f"across {meta.get('num_targets', '?')} protein targets. "
            f"pIC50 R² = **{meta.get('pIC50_r2', 'N/A')}** | "
            f"ADMET Acc = **{meta.get('druglikeness_accuracy', 'N/A')}**"
        )
    else:
        st.warning("ML models not found. Run `python train_ml_models.py` to train.")
    
    candidates = disease_data.get('drug_candidates', [])
    if not candidates:
        st.warning("No drug candidates found for this target.")
        return
    
    st.subheader(f"Top {len(candidates)} Candidates — ChEMBL Data + ML Predictions")
    
    for idx, cand in enumerate(candidates):
        smiles = cand.get('smiles', '')
        mol = Chem.MolFromSmiles(smiles) if smiles else None
        
        with st.container():
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                st.markdown(f"### {idx+1}. {cand.get('name', 'Unknown')}")
            with header_col2:
                chembl_id = cand.get('chembl_id', '')
                if chembl_id and chembl_id != 'N/A':
                    st.markdown(f"[ChEMBL →](https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/)")
            
            # Experimental Data
            st.markdown("##### 📊 Experimental Data (ChEMBL)")
            exp1, exp2 = st.columns(2)
            with exp1:
                ic50 = cand.get('ic50_nM')
                if ic50:
                    delta = "Potent" if ic50 < 1000 else "Moderate" if ic50 < 10000 else "Weak"
                    st.metric("Measured IC50", f"{ic50:.0f} nM", delta=delta)
            with exp2:
                st.metric("Source", cand.get('source', 'ChEMBL'), delta_color="off")
            
            # ML Predictions
            if has_ml and mol:
                st.markdown("##### 🤖 GPU-Trained XGBoost Predictions")
                
                feat = smiles_to_features(smiles, disease_data['mutated_gene'], meta)
                
                if feat is not None:
                    ml1, ml2, ml3, ml4 = st.columns(4)
                    
                    with ml1:
                        pred_pIC50 = predict_pIC50(models, feat)
                        pred_ic50 = 10**(-pred_pIC50) * 1e9
                        measured = cand.get('ic50_nM')
                        if measured:
                            err = abs(pred_ic50 - measured) / measured * 100
                            delta_str = f"Err: {err:.0f}%"
                        else:
                            delta_str = "Predicted"
                        st.metric("ML Predicted IC50", f"{pred_ic50:.0f} nM", delta=delta_str, delta_color="inverse")
                    
                    with ml2:
                        pred_dl, conf = predict_druglikeness(models, feat)
                        st.metric("ADMET Prediction", "PASS" if pred_dl else "FAIL", delta=f"{conf*100:.0f}% conf.")
                    
                    with ml3:
                        mw = round(Descriptors.MolWt(mol), 1)
                        st.metric("Mol Weight", f"{mw} Da", delta="Pass" if mw < 500 else "Fail")
                    
                    with ml4:
                        qed_val = round(QED.qed(mol), 3)
                        st.metric("QED", f"{qed_val}", delta="Drug-like" if qed_val > 0.5 else "Low")
            
            # Molecule image
            if mol:
                img = Draw.MolToImage(mol, size=(400, 250))
                buf = BytesIO()
                img.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode()
                st.markdown(f'<img src="data:image/png;base64,{img_b64}" width="45%">', unsafe_allow_html=True)
            
            st.text(f"SMILES: {smiles}")
            st.markdown("---")
