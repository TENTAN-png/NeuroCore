"""
BioGenesis ML Training Pipeline v2.0
=====================================
Trains REAL machine learning models on PUBLIC ChEMBL bioactivity data.

Models Trained:
  1. pIC50 Regressor — Predicts binding potency from molecular structure
     (Random Forest on 2048-bit Morgan Fingerprints)
  2. Drug-Likeness Classifier — Predicts if a compound passes ADMET filters
     (Gradient Boosting on molecular descriptors)

Data Source: ChEMBL (European Bioinformatics Institute)
"""

import requests
import json
import os
import math
import numpy as np
import joblib
from tqdm import tqdm

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, QED
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score

# ============================================================
# STEP 1: Scrape Training Data from ChEMBL
# ============================================================

# These are well-studied drug targets with thousands of bioactivity records
TRAINING_TARGETS = {
    "CHEMBL203":  "EGFR",      # Epidermal Growth Factor Receptor
    "CHEMBL4036": "ABL1",      # Abelson Tyrosine Kinase (Imatinib target)
    "CHEMBL279":  "VEGFR2",    # Vascular Endothelial Growth Factor Receptor
    "CHEMBL1862": "CDK2",      # Cyclin-Dependent Kinase 2
    "CHEMBL2842": "JAK2",      # Janus Kinase 2
    "CHEMBL3594": "ALK",       # Anaplastic Lymphoma Kinase
    "CHEMBL267":  "ERBB2",     # HER2
    "CHEMBL4822": "PI3KCA",    # PI3K alpha
}


def fetch_chembl_training_data(target_id, target_name, limit=200):
    """Fetches IC50 bioactivity data from ChEMBL REST API."""
    print(f"  Scraping {target_name} ({target_id})...")
    url = (
        f"https://www.ebi.ac.uk/chembl/api/data/activity.json"
        f"?target_chembl_id={target_id}"
        f"&standard_type=IC50"
        f"&standard_units=nM"
        f"&limit={limit}"
        f"&format=json"
    )
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return []
        
        data = response.json()
        activities = data.get('activities', [])
        
        valid = []
        seen = set()
        for act in activities:
            smiles = act.get('canonical_smiles', '')
            ic50_val = act.get('standard_value')
            mol_id = act.get('molecule_chembl_id', '')
            
            if not smiles or not ic50_val or mol_id in seen:
                continue
            
            try:
                ic50 = float(ic50_val)
                if ic50 <= 0:
                    continue
                # Convert IC50 (nM) to pIC50 = -log10(IC50 in Molar)
                pIC50 = -math.log10(ic50 * 1e-9)
                
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    continue
                
                seen.add(mol_id)
                valid.append({
                    'smiles': smiles,
                    'pIC50': round(pIC50, 3),
                    'target': target_name
                })
            except:
                continue
        
        print(f"    Got {len(valid)} valid datapoints")
        return valid
        
    except Exception as e:
        print(f"    ERROR: {e}")
        return []


def smiles_to_fingerprint(smiles, n_bits=2048):
    """Converts SMILES to Morgan Fingerprint (ECFP4) — the industry standard."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    return np.array(fp)


def smiles_to_descriptors(smiles):
    """Computes 8 key molecular descriptors for ADMET prediction."""
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


# ============================================================
# STEP 2: Train Models
# ============================================================

def train_models():
    os.makedirs('models', exist_ok=True)
    
    print("=" * 60)
    print("BioGenesis ML Training Pipeline v2.0")
    print("Training on REAL ChEMBL bioactivity data")
    print("=" * 60)
    
    # --- Collect Training Data ---
    all_data = []
    for target_id, target_name in TRAINING_TARGETS.items():
        data = fetch_chembl_training_data(target_id, target_name, limit=200)
        all_data.extend(data)
        import time
        time.sleep(1)
    
    print(f"\nTotal training samples collected: {len(all_data)}")
    
    if len(all_data) < 50:
        print("ERROR: Not enough data collected. Check internet connection.")
        return
    
    # --- Generate Features ---
    print("\nGenerating molecular fingerprints (ECFP4, 2048-bit)...")
    X_fp = []
    X_desc = []
    y_pIC50 = []
    y_druglike = []
    valid_smiles = []
    
    for item in tqdm(all_data, desc="Featurizing"):
        fp = smiles_to_fingerprint(item['smiles'])
        desc = smiles_to_descriptors(item['smiles'])
        
        if fp is not None and desc is not None:
            X_fp.append(fp)
            X_desc.append(desc)
            y_pIC50.append(item['pIC50'])
            
            # Drug-likeness label: Lipinski Rule of 5
            mol = Chem.MolFromSmiles(item['smiles'])
            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            hbd = Descriptors.NumHDonors(mol)
            hba = Descriptors.NumHAcceptors(mol)
            lipinski_pass = int(mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10)
            y_druglike.append(lipinski_pass)
            valid_smiles.append(item['smiles'])
    
    X_fp = np.array(X_fp)
    X_desc = np.array(X_desc)
    y_pIC50 = np.array(y_pIC50)
    y_druglike = np.array(y_druglike)
    
    print(f"Feature matrix shape: {X_fp.shape}")
    print(f"Drug-like ratio: {y_druglike.mean():.2%}")
    
    # --- Train Model 1: pIC50 Regressor ---
    print("\n--- Training pIC50 Regressor (Random Forest) ---")
    X_train, X_test, y_train, y_test = train_test_split(
        X_fp, y_pIC50, test_size=0.2, random_state=42
    )
    
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    
    y_pred = rf_model.predict(X_test)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    print(f"  RMSE: {rmse:.3f}")
    print(f"  R2 Score: {r2:.3f}")
    
    joblib.dump(rf_model, 'models/pIC50_rf_model.pkl')
    print("  Saved: models/pIC50_rf_model.pkl")
    
    # --- Train Model 2: Drug-Likeness Classifier ---
    print("\n--- Training Drug-Likeness Classifier (Gradient Boosting) ---")
    X_train_d, X_test_d, y_train_d, y_test_d = train_test_split(
        X_desc, y_druglike, test_size=0.2, random_state=42
    )
    
    gb_model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
    gb_model.fit(X_train_d, y_train_d)
    
    y_pred_d = gb_model.predict(X_test_d)
    acc = accuracy_score(y_test_d, y_pred_d)
    print(f"  Accuracy: {acc:.3f}")
    
    joblib.dump(gb_model, 'models/druglikeness_gb_model.pkl')
    print("  Saved: models/druglikeness_gb_model.pkl")
    
    # --- Save training metadata ---
    metadata = {
        "training_samples": len(all_data),
        "feature_dim_fingerprint": int(X_fp.shape[1]),
        "feature_dim_descriptors": int(X_desc.shape[1]),
        "pIC50_rmse": round(rmse, 3),
        "pIC50_r2": round(r2, 3),
        "druglikeness_accuracy": round(acc, 3),
        "targets_used": list(TRAINING_TARGETS.values()),
        "data_source": "ChEMBL (ebi.ac.uk/chembl)"
    }
    with open('models/training_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print(f"  pIC50 Regressor:        RMSE={rmse:.3f}, R2={r2:.3f}")
    print(f"  Drug-Likeness Classifier: Accuracy={acc:.1%}")
    print(f"  Data: {len(all_data)} compounds from {len(TRAINING_TARGETS)} ChEMBL targets")
    print("=" * 60)


if __name__ == '__main__':
    train_models()
