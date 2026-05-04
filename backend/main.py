from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from rdkit import Chem
from rdkit.Chem import Descriptors, QED
import uvicorn

app = FastAPI()

# Allow React to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DrugRequest(BaseModel):
    target_gene: str
    base_smiles: str

@app.post("/api/generate_drugs")
def generate_drugs(request: DrugRequest):
    base_smiles = request.base_smiles
    if not base_smiles or base_smiles == "N/A":
        # Fallback to a generic scaffold if none provided
        base_smiles = "CC1=CC=C(C=C1)NC(=O)C2=CC=CC=C2"

    candidates = []
    
    # 1. Lead Compound (Original)
    mol = Chem.MolFromSmiles(base_smiles)
    if mol:
        candidates.append({
            "name": f"{request.target_gene}-Lead Compound",
            "smiles": base_smiles,
            "mw": round(Descriptors.MolWt(mol), 2),
            "logp": round(Descriptors.MolLogP(mol), 2),
            "qed_score": round(QED.qed(mol), 3),
            "affinity": round(random.uniform(-11.5, -9.0), 1) # Still simulated as docking requires AutoDock Vina
        })

    # 2. Dynamically mutate the SMILES to create derivatives
    # In chemistry, adding halogens (F, Cl) or methyl groups (C) often improves binding
    mutations = [
        ("C", "Derivative Alpha (Methylated)"),
        ("F", "Derivative Beta (Fluorinated)"),
        ("Cl", "Derivative Gamma (Chlorinated)")
    ]
    
    for element, name in mutations:
        try:
            # Simple heuristic mutation: append functional group to the SMILES
            # (In a production GNN, this would be a generative model output)
            mutated_smiles = base_smiles + element
            mut_mol = Chem.MolFromSmiles(mutated_smiles)
            if mut_mol:
                candidates.append({
                    "name": f"{request.target_gene}-{name}",
                    "smiles": mutated_smiles,
                    "mw": round(Descriptors.MolWt(mut_mol), 2),
                    "logp": round(Descriptors.MolLogP(mut_mol), 2),
                    "qed_score": round(QED.qed(mut_mol), 3),
                    "affinity": round(random.uniform(-12.0, -8.0), 1)
                })
        except:
            pass

    return {"candidates": candidates}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
