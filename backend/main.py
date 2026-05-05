from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import math
import os
import json
import joblib
import xgboost as xgb
from rdkit import Chem
from rdkit.Chem import Descriptors, QED, AllChem, Lipinski, MolSurf, rdMolDescriptors
import uvicorn

app = FastAPI(title="BioGenesis ML API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load ML models at startup
pIC50_model = None
druglike_model = None
training_meta = None
model_type = None

if os.path.exists('models/pIC50_xgb_gpu.json'):
    pIC50_model = xgb.Booster()
    pIC50_model.load_model('models/pIC50_xgb_gpu.json')
    model_type = 'xgboost'
    print("Loaded pIC50 XGBoost model")
elif os.path.exists('models/pIC50_rf_model.pkl'):
    pIC50_model = joblib.load('models/pIC50_rf_model.pkl')
    model_type = 'sklearn'
    print("Loaded pIC50 Random Forest model")

if os.path.exists('models/druglikeness_xgb_gpu.json'):
    druglike_model = xgb.Booster()
    druglike_model.load_model('models/druglikeness_xgb_gpu.json')
    print("Loaded Drug-Likeness XGBoost model")
elif os.path.exists('models/druglikeness_gb_model.pkl'):
    druglike_model = joblib.load('models/druglikeness_gb_model.pkl')
    print("Loaded Drug-Likeness Gradient Boosting model")

if os.path.exists('models/training_metadata.json'):
    with open('models/training_metadata.json') as f:
        training_meta = json.load(f)

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

class DrugRequest(BaseModel):
    target_gene: str
    base_smiles: str

class PredictRequest(BaseModel):
    smiles: str
    target_gene: str

@app.get("/api/model_info")
def model_info():
    return {
        "models_loaded": {
            "pIC50_regressor": pIC50_model is not None,
            "druglikeness_classifier": druglike_model is not None,
            "model_type": model_type
        },
        "training_metadata": training_meta
    }

@app.post("/api/predict")
def predict_single(request: PredictRequest):
    """Run ML prediction on a single SMILES string."""
    mol = Chem.MolFromSmiles(request.smiles)
    if mol is None:
        return {"error": "Invalid SMILES"}
    
    result = {
        "smiles": request.smiles,
        "mw": round(Descriptors.MolWt(mol), 2),
        "logp": round(Descriptors.MolLogP(mol), 2),
        "qed": round(QED.qed(mol), 3),
    }
    
    feat = smiles_to_features(request.smiles, request.target_gene, training_meta)
    
    if pIC50_model and feat is not None:
        if model_type == 'xgboost':
            dmat = xgb.DMatrix(feat.reshape(1, -1))
            pred_pIC50 = pIC50_model.predict(dmat)[0]
        else:
            pred_pIC50 = pIC50_model.predict(feat.reshape(1, -1))[0]
        
        pred_ic50_nM = 10**(-pred_pIC50) * 1e9
        result["ml_predicted_pIC50"] = round(float(pred_pIC50), 3)
        result["ml_predicted_IC50_nM"] = round(float(pred_ic50_nM), 1)
    
    if druglike_model and feat is not None:
        if model_type == 'xgboost':
            dmat = xgb.DMatrix(feat.reshape(1, -1))
            prob = druglike_model.predict(dmat)[0]
            pred = 1 if prob > 0.5 else 0
            confidence = float(max(prob, 1 - prob)) * 100
        else:
            pred = druglike_model.predict(feat.reshape(1, -1))[0]
            proba = druglike_model.predict_proba(feat.reshape(1, -1))[0]
            confidence = float(max(proba)) * 100
            
        result["ml_admet_pass"] = bool(pred == 1)
        result["ml_admet_confidence"] = round(float(confidence), 1)
    
    return result

@app.post("/api/generate_drugs")
def generate_drugs(request: DrugRequest):
    """Generate drug candidates with ML predictions."""
    base_smiles = request.base_smiles
    if not base_smiles or base_smiles == "N/A":
        base_smiles = "CC1=CC=C(C=C1)NC(=O)C2=CC=CC=C2"

    candidates = []
    smiles_list = [base_smiles]
    
    mutations = [("C", "Methylated"), ("F", "Fluorinated"), ("Cl", "Chlorinated")]
    for element, _ in mutations:
        mut = base_smiles + element
        if Chem.MolFromSmiles(mut):
            smiles_list.append(mut)
    
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        
        entry = {
            "name": f"{request.target_gene}-{'Lead' if i == 0 else mutations[i-1][1]}",
            "smiles": smi,
            "mw": round(Descriptors.MolWt(mol), 2),
            "logp": round(Descriptors.MolLogP(mol), 2),
            "qed_score": round(QED.qed(mol), 3),
        }
        
        feat = smiles_to_features(smi, request.target_gene, training_meta)
        
        if pIC50_model and feat is not None:
            if model_type == 'xgboost':
                dmat = xgb.DMatrix(feat.reshape(1, -1))
                pred_pIC50 = pIC50_model.predict(dmat)[0]
            else:
                pred_pIC50 = pIC50_model.predict(feat.reshape(1, -1))[0]
                
            pred_ic50 = 10**(-pred_pIC50) * 1e9
            entry["ml_pIC50"] = round(float(pred_pIC50), 3)
            entry["ml_IC50_nM"] = round(float(pred_ic50), 1)
            entry["affinity"] = round(-0.000592 * 310 * math.log(pred_ic50 * 1e-9), 1)
        
        if druglike_model and feat is not None:
            if model_type == 'xgboost':
                dmat = xgb.DMatrix(feat.reshape(1, -1))
                prob = druglike_model.predict(dmat)[0]
                pred = 1 if prob > 0.5 else 0
                confidence = float(max(prob, 1 - prob)) * 100
            else:
                pred = druglike_model.predict(feat.reshape(1, -1))[0]
                proba = druglike_model.predict_proba(feat.reshape(1, -1))[0]
                confidence = float(max(proba)) * 100
                
            entry["ml_admet_pass"] = bool(pred == 1)
            entry["ml_admet_confidence"] = round(float(confidence), 1)
        
        candidates.append(entry)

    return {"candidates": candidates}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
