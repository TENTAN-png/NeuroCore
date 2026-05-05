"""
BioGenesis ML Training Pipeline v3.0 — GPU-Accelerated
========================================================
Trains on ChEMBL bioactivity data using:
  1. XGBoost GPU-accelerated pIC50 Regressor (ECFP4 + molecular descriptors)
  2. XGBoost GPU-accelerated ADMET Classifier
  3. 3x more training data (500 compounds per target, 16 targets)

Hardware: NVIDIA RTX 5050 (CUDA)
Data Source: ChEMBL (European Bioinformatics Institute)
"""

import requests
import json
import os
import math
import time
import numpy as np
import joblib
from tqdm import tqdm

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, QED
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
import xgboost as xgb

# ============================================================
# EXPANDED TARGET LIST — 16 well-studied drug targets
# ============================================================
TRAINING_TARGETS = {
    # Kinases (huge bioactivity databases)
    "CHEMBL203":  "EGFR",
    "CHEMBL4036": "ABL1",
    "CHEMBL279":  "VEGFR2",
    "CHEMBL1862": "CDK2",
    "CHEMBL2842": "JAK2",
    "CHEMBL3594": "ALK",
    "CHEMBL267":  "ERBB2",
    "CHEMBL4822": "PI3KCA",
    # Additional high-value targets
    "CHEMBL2148": "HDAC1",     # Histone Deacetylase
    "CHEMBL3717": "mTOR",      # Mammalian Target of Rapamycin
    "CHEMBL2035": "Aurora-A",  # Aurora Kinase A
    "CHEMBL4005": "FGFR1",    # Fibroblast Growth Factor Receptor
    "CHEMBL3130": "PLK1",      # Polo-Like Kinase
    "CHEMBL4630": "BTK",       # Bruton's Tyrosine Kinase
    "CHEMBL2093868": "PD-L1",  # Programmed Death-Ligand 1
    "CHEMBL1075104": "IDH1",   # Isocitrate Dehydrogenase 1
}

COMPOUNDS_PER_TARGET = 500  # 3x more than before


def fetch_chembl_data(target_id, target_name, limit=500):
    """Fetches IC50 bioactivity data from ChEMBL REST API."""
    print(f"  [{target_name}] Scraping {target_id}...", end="", flush=True)
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
            print(f" FAILED ({response.status_code})")
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
        
        print(f" {len(valid)} compounds")
        return valid
        
    except Exception as e:
        print(f" ERROR: {e}")
        return []


def smiles_to_features(smiles, n_bits=2048):
    """
    Combined feature vector: Morgan Fingerprint (2048) + Molecular Descriptors (12)
    Total: 2060 features per molecule
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    # Morgan Fingerprint (ECFP4)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    fp_arr = np.array(fp, dtype=np.float32)
    
    # Molecular Descriptors (12 features)
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
        QED.qed(mol)
    ], dtype=np.float32)
    
    # Concatenate: [2048-bit fingerprint | 12 descriptors] = 2060 features
    return np.concatenate([fp_arr, desc])


def train_models():
    os.makedirs('models', exist_ok=True)
    
    print("=" * 65)
    print("  BioGenesis ML Training Pipeline v3.0 — GPU-Accelerated")
    print("  Hardware: NVIDIA RTX 5050 | Engine: XGBoost CUDA")
    print("=" * 65)
    
    # --- Collect Training Data ---
    print("\n[Phase 1] Scraping ChEMBL bioactivity data...")
    all_data = []
    for target_id, target_name in TRAINING_TARGETS.items():
        data = fetch_chembl_data(target_id, target_name, limit=COMPOUNDS_PER_TARGET)
        all_data.extend(data)
        time.sleep(0.8)
    
    print(f"\nTotal raw samples: {len(all_data)}")
    
    if len(all_data) < 100:
        print("ERROR: Not enough data. Check internet.")
        return
    
    # --- Generate Features ---
    print("\n[Phase 2] Generating combined features (ECFP4 + 12 descriptors)...")
    X_all = []
    y_pIC50 = []
    y_druglike = []
    
    for item in tqdm(all_data, desc="Featurizing", ncols=70):
        feat = smiles_to_features(item['smiles'])
        if feat is not None:
            X_all.append(feat)
            y_pIC50.append(item['pIC50'])
            
            mol = Chem.MolFromSmiles(item['smiles'])
            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            hbd = Descriptors.NumHDonors(mol)
            hba = Descriptors.NumHAcceptors(mol)
            lipinski = int(mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10)
            y_druglike.append(lipinski)
    
    X_all = np.array(X_all, dtype=np.float32)
    y_pIC50 = np.array(y_pIC50, dtype=np.float32)
    y_druglike = np.array(y_druglike, dtype=np.int32)
    
    print(f"Feature matrix: {X_all.shape[0]} samples x {X_all.shape[1]} features")
    print(f"Drug-like ratio: {y_druglike.mean():.1%}")
    
    # --- Train pIC50 Regressor on GPU ---
    print("\n[Phase 3] Training pIC50 Regressor on GPU...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_pIC50, test_size=0.15, random_state=42
    )
    
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    
    params = {
        'objective': 'reg:squarederror',
        'device': 'cuda',
        'max_depth': 10,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.6,
        'min_child_weight': 3,
        'gamma': 0.1,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'eval_metric': 'rmse',
    }
    
    evals = [(dtrain, 'train'), (dtest, 'eval')]
    
    print("  Training with early stopping (patience=30)...")
    bst = xgb.train(
        params,
        dtrain,
        num_boost_round=1000,
        evals=evals,
        early_stopping_rounds=30,
        verbose_eval=50
    )
    
    y_pred = bst.predict(dtest)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    print(f"\n  >> pIC50 Regressor Results:")
    print(f"     RMSE: {rmse:.3f}")
    print(f"     R2 Score: {r2:.3f}")
    print(f"     Best iteration: {bst.best_iteration}")
    
    bst.save_model('models/pIC50_xgb_gpu.json')
    print("  Saved: models/pIC50_xgb_gpu.json")
    
    # --- Train ADMET Classifier on GPU ---
    print("\n[Phase 4] Training ADMET Classifier on GPU...")
    X_train_d, X_test_d, y_train_d, y_test_d = train_test_split(
        X_all, y_druglike, test_size=0.15, random_state=42
    )
    
    dtrain_d = xgb.DMatrix(X_train_d, label=y_train_d)
    dtest_d = xgb.DMatrix(X_test_d, label=y_test_d)
    
    params_cls = {
        'objective': 'binary:logistic',
        'device': 'cuda',
        'max_depth': 8,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.6,
        'eval_metric': 'error',
    }
    
    bst_cls = xgb.train(
        params_cls,
        dtrain_d,
        num_boost_round=500,
        evals=[(dtrain_d, 'train'), (dtest_d, 'eval')],
        early_stopping_rounds=20,
        verbose_eval=50
    )
    
    y_pred_d = (bst_cls.predict(dtest_d) > 0.5).astype(int)
    acc = accuracy_score(y_test_d, y_pred_d)
    print(f"\n  >> ADMET Classifier Results:")
    print(f"     Accuracy: {acc:.1%}")
    
    bst_cls.save_model('models/druglikeness_xgb_gpu.json')
    print("  Saved: models/druglikeness_xgb_gpu.json")
    
    # --- Save metadata ---
    metadata = {
        "training_samples": int(X_all.shape[0]),
        "feature_dim": int(X_all.shape[1]),
        "feature_description": "2048-bit ECFP4 Morgan Fingerprint + 12 molecular descriptors",
        "pIC50_rmse": round(rmse, 3),
        "pIC50_r2": round(r2, 3),
        "pIC50_best_iteration": int(bst.best_iteration),
        "druglikeness_accuracy": round(acc, 3),
        "targets_used": list(TRAINING_TARGETS.values()),
        "num_targets": len(TRAINING_TARGETS),
        "data_source": "ChEMBL (ebi.ac.uk/chembl)",
        "engine": "XGBoost 3.2.0 + CUDA (RTX 5050)",
        "model_type": "xgboost_gpu"
    }
    with open('models/training_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 65)
    print("  TRAINING COMPLETE")
    print(f"  pIC50 Regressor:   R2 = {r2:.3f}  |  RMSE = {rmse:.3f}")
    print(f"  ADMET Classifier:  Accuracy = {acc:.1%}")
    print(f"  Data: {X_all.shape[0]} compounds from {len(TRAINING_TARGETS)} targets")
    print(f"  Engine: XGBoost GPU (NVIDIA RTX 5050)")
    print("=" * 65)


if __name__ == '__main__':
    train_models()
