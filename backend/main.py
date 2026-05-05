from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import math
import os
import json
import joblib
from rdkit import Chem
from rdkit.Chem import Descriptors, QED, AllChem
import uvicorn

app = FastAPI(title="BioGenesis ML API", version="2.0")

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

if os.path.exists('models/pIC50_rf_model.pkl'):
    pIC50_model = joblib.load('models/pIC50_rf_model.pkl')
    print("Loaded pIC50 Random Forest model")
if os.path.exists('models/druglikeness_gb_model.pkl'):
    druglike_model = joblib.load('models/druglikeness_gb_model.pkl')
    print("Loaded Drug-Likeness Gradient Boosting model")
if os.path.exists('models/training_metadata.json'):
    with open('models/training_metadata.json') as f:
        training_meta = json.load(f)


def smiles_to_fp(smiles, n_bits=2048):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    return np.array(fp)


def smiles_to_desc(smiles):
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


class DrugRequest(BaseModel):
    target_gene: str
    base_smiles: str


class PredictRequest(BaseModel):
    smiles: str


@app.get("/api/model_info")
def model_info():
    return {
        "models_loaded": {
            "pIC50_regressor": pIC50_model is not None,
            "druglikeness_classifier": druglike_model is not None
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
    
    fp = smiles_to_fp(request.smiles)
    desc = smiles_to_desc(request.smiles)
    
    if pIC50_model and fp is not None:
        pred_pIC50 = pIC50_model.predict(fp.reshape(1, -1))[0]
        pred_ic50_nM = 10**(-pred_pIC50) * 1e9
        result["ml_predicted_pIC50"] = round(pred_pIC50, 3)
        result["ml_predicted_IC50_nM"] = round(pred_ic50_nM, 1)
    
    if druglike_model and desc is not None:
        pred = druglike_model.predict(desc.reshape(1, -1))[0]
        proba = druglike_model.predict_proba(desc.reshape(1, -1))[0]
        result["ml_admet_pass"] = bool(pred == 1)
        result["ml_admet_confidence"] = round(float(max(proba)) * 100, 1)
    
    return result


@app.post("/api/generate_drugs")
def generate_drugs(request: DrugRequest):
    """Generate drug candidates with ML predictions."""
    base_smiles = request.base_smiles
    if not base_smiles or base_smiles == "N/A":
        base_smiles = "CC1=CC=C(C=C1)NC(=O)C2=CC=CC=C2"

    candidates = []
    smiles_list = [base_smiles]
    
    # Generate structural variants
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
        
        fp = smiles_to_fp(smi)
        desc = smiles_to_desc(smi)
        
        if pIC50_model and fp is not None:
            pred_pIC50 = pIC50_model.predict(fp.reshape(1, -1))[0]
            pred_ic50 = 10**(-pred_pIC50) * 1e9
            entry["ml_pIC50"] = round(pred_pIC50, 3)
            entry["ml_IC50_nM"] = round(pred_ic50, 1)
            entry["affinity"] = round(-0.000592 * 310 * math.log(pred_ic50 * 1e-9), 1)
        
        if druglike_model and desc is not None:
            pred = druglike_model.predict(desc.reshape(1, -1))[0]
            proba = druglike_model.predict_proba(desc.reshape(1, -1))[0]
            entry["ml_admet_pass"] = bool(pred == 1)
            entry["ml_admet_confidence"] = round(float(max(proba)) * 100, 1)
        
        candidates.append(entry)

    return {"candidates": candidates}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
