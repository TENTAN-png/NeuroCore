import json
import os
import requests

def precache_pdbs():
    with open('data/diseases.json', 'r') as f:
        diseases = json.load(f)
        
    pdb_dir = 'data/pdb_cache'
    os.makedirs(pdb_dir, exist_ok=True)
    
    for d in diseases:
        target = d['mutated_gene']
        sequence = d['sequence']
        pdb_path = f"{pdb_dir}/{target}.pdb"
        
        if os.path.exists(pdb_path):
            print(f"Skipping {target}, already cached.")
            continue
            
        print(f"Fetching structure for {target} (length: {len(sequence)})...")
        headers = {'Content-Type': 'text/plain'}
        response = requests.post('https://api.esmatlas.com/foldSequence/v1/pdb/', headers=headers, data=sequence)
        
        if response.status_code == 200:
            with open(pdb_path, 'w') as f:
                f.write(response.text)
            print(f"Successfully cached {target}")
        else:
            print(f"Failed to fetch {target}: {response.status_code}")

if __name__ == '__main__':
    precache_pdbs()
