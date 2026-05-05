"""
BioGenesis ML Training Pipeline v4.0 — High-Performance GPU
=============================================================
Key changes for R2 > 0.75:
  1. Target One-Hot Encoding (model knows WHICH protein target)
  2. 1000 compounds per target (doubled data)
  3. 20 molecular descriptors (up from 12)
  4. Deeper XGBoost trees + tuned hyperparameters
  5. Stratified train/test split by target
"""

import requests
import json
import os
import math
import time
import numpy as np
import joblib
from collections import Counter
from tqdm import tqdm

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, QED, Lipinski, MolSurf, rdMolDescriptors
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
import xgboost as xgb

# ============================================================
# 16 Targets — same as before
# ============================================================
TRAINING_TARGETS = {
    "CHEMBL203":  "EGFR",
    "CHEMBL4036": "ABL1",
    "CHEMBL279":  "VEGFR2",
    "CHEMBL1862": "CDK2",
    "CHEMBL2842": "JAK2",
    "CHEMBL3594": "ALK",
    "CHEMBL267":  "ERBB2",
    "CHEMBL4822": "PI3KCA",
    "CHEMBL2148": "HDAC1",
    "CHEMBL3717": "mTOR",
    "CHEMBL2035": "Aurora-A",
    "CHEMBL4005": "FGFR1",
    "CHEMBL3130": "PLK1",
    "CHEMBL4630": "BTK",
    "CHEMBL2093868": "PD-L1",
    "CHEMBL1075104": "IDH1",
}

TARGET_NAMES = list(TRAINING_TARGETS.values())
TARGET_TO_IDX = {name: i for i, name in enumerate(TARGET_NAMES)}
NUM_TARGETS = len(TARGET_NAMES)

COMPOUNDS_PER_TARGET = 1000  # Doubled from 500


def fetch_chembl_data(target_id, target_name, limit=1000):
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
                valid.append({'smiles': smiles, 'pIC50': round(pIC50, 3), 'target': target_name})
            except:
                continue
        print(f" {len(valid)} compounds")
        return valid
    except Exception as e:
        print(f" ERROR: {e}")
        return []


def smiles_to_descriptors_20(smiles):
    """20 molecular descriptors for richer feature space."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        return np.array([
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


def smiles_to_features(smiles, target_name, n_bits=2048):
    """
    Combined: Morgan FP (2048) + Descriptors (20) + Target One-Hot (16) = 2084 dim
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    fp_arr = np.array(fp, dtype=np.float32)
    
    desc = smiles_to_descriptors_20(smiles)
    if desc is None:
        return None
    
    # One-hot encode the target protein
    target_vec = np.zeros(NUM_TARGETS, dtype=np.float32)
    if target_name in TARGET_TO_IDX:
        target_vec[TARGET_TO_IDX[target_name]] = 1.0
    
    return np.concatenate([fp_arr, desc, target_vec])


def train_models():
    os.makedirs('models', exist_ok=True)
    
    print("=" * 65)
    print("  BioGenesis ML v4.0 — High-Performance GPU Training")
    print("  Target: R2 > 0.75 | Engine: XGBoost CUDA (RTX 5050)")
    print("=" * 65)
    
    # --- Collect Data ---
    print("\n[Phase 1] Scraping ChEMBL (1000 compounds x 16 targets)...")
    all_data = []
    for target_id, target_name in TRAINING_TARGETS.items():
        data = fetch_chembl_data(target_id, target_name, limit=COMPOUNDS_PER_TARGET)
        all_data.extend(data)
        time.sleep(0.5)
    
    print(f"\nTotal raw samples: {len(all_data)}")
    print("Target distribution:")
    for t, c in Counter([d['target'] for d in all_data]).most_common():
        print(f"  {t}: {c}")
    
    # --- Featurize ---
    print("\n[Phase 2] Generating features (FP + 20 desc + target encoding)...")
    X_all = []
    y_pIC50 = []
    y_druglike = []
    target_labels = []
    
    for item in tqdm(all_data, desc="Featurizing", ncols=70):
        feat = smiles_to_features(item['smiles'], item['target'])
        if feat is not None and not np.any(np.isnan(feat)):
            X_all.append(feat)
            y_pIC50.append(item['pIC50'])
            target_labels.append(item['target'])
            
            mol = Chem.MolFromSmiles(item['smiles'])
            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            hbd = Descriptors.NumHDonors(mol)
            hba = Descriptors.NumHAcceptors(mol)
            y_druglike.append(int(mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10))
    
    X_all = np.array(X_all, dtype=np.float32)
    y_pIC50 = np.array(y_pIC50, dtype=np.float32)
    y_druglike = np.array(y_druglike, dtype=np.int32)
    
    # Replace any remaining NaN/Inf
    X_all = np.nan_to_num(X_all, nan=0.0, posinf=0.0, neginf=0.0)
    
    print(f"Feature matrix: {X_all.shape[0]} x {X_all.shape[1]}")
    
    # --- Train pIC50 Regressor ---
    print("\n[Phase 3] Training pIC50 Regressor on GPU...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_pIC50, test_size=0.15, random_state=42, stratify=[TARGET_TO_IDX.get(t, 0) for t in target_labels]
    )
    
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    
    params = {
        'objective': 'reg:squarederror',
        'device': 'cuda',
        'max_depth': 12,
        'learning_rate': 0.03,
        'subsample': 0.85,
        'colsample_bytree': 0.5,
        'colsample_bylevel': 0.7,
        'min_child_weight': 5,
        'gamma': 0.2,
        'reg_alpha': 0.3,
        'reg_lambda': 2.0,
        'eval_metric': 'rmse',
    }
    
    print("  Training (up to 2000 rounds, patience=50)...")
    bst = xgb.train(
        params, dtrain,
        num_boost_round=2000,
        evals=[(dtrain, 'train'), (dtest, 'eval')],
        early_stopping_rounds=50,
        verbose_eval=100
    )
    
    y_pred = bst.predict(dtest)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    print(f"\n  >> pIC50 Results: RMSE={rmse:.3f} | R2={r2:.3f}")
    print(f"     Best iteration: {bst.best_iteration}")
    
    bst.save_model('models/pIC50_xgb_gpu.json')
    
    # --- Train ADMET Classifier ---
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
        params_cls, dtrain_d,
        num_boost_round=500,
        evals=[(dtrain_d, 'train'), (dtest_d, 'eval')],
        early_stopping_rounds=20,
        verbose_eval=100
    )
    y_pred_d = (bst_cls.predict(dtest_d) > 0.5).astype(int)
    acc = accuracy_score(y_test_d, y_pred_d)
    print(f"\n  >> ADMET Results: Accuracy={acc:.1%}")
    
    bst_cls.save_model('models/druglikeness_xgb_gpu.json')
    
    # --- Save metadata + target mapping ---
    metadata = {
        "training_samples": int(X_all.shape[0]),
        "feature_dim": int(X_all.shape[1]),
        "feature_description": "2048-bit ECFP4 + 20 molecular descriptors + 16-dim target one-hot encoding",
        "pIC50_rmse": round(rmse, 3),
        "pIC50_r2": round(r2, 3),
        "pIC50_best_iteration": int(bst.best_iteration),
        "druglikeness_accuracy": round(acc, 3),
        "targets_used": TARGET_NAMES,
        "target_to_index": TARGET_TO_IDX,
        "num_targets": NUM_TARGETS,
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
    print(f"  Data: {X_all.shape[0]} compounds | {X_all.shape[1]} features | {NUM_TARGETS} targets")
    print(f"  Engine: XGBoost GPU (NVIDIA RTX 5050)")
    print("=" * 65)


if __name__ == '__main__':
    train_models()
