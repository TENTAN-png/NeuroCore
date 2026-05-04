import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import joblib
import json
import os
import random

# Generate a synthetic but realistic dataset of 100 diseases
diseases_list = [
    {"name": "ALS (Amyotrophic Lateral Sclerosis)", "mutated_gene": "SOD1", "cell_type": "Motor Neurons", "sequence": "MATKAVCVLKGDGPVQGIINFEQKESNGPVKVWGSIKGLTEGLHGFHVHEFGDNTAGCTSAGPHFNPLSRKHGGPKDEERHVGDLGNVTADKDGVADVSIEDSVISLSGDHCIIGRTLVVHEKADDLGKGGNEESTKTGNAGSRLACGVIGIAQ", "up_regulated": ["CASP3", "BAX", "GFAP", "CD44"], "down_regulated": ["BDNF", "GDNF", "EAAT2"]},
    {"name": "Huntington's Disease", "mutated_gene": "HTT", "cell_type": "Medium Spiny Neurons", "sequence": "MATLEKLMKAFESLKSFQQQQQQQQQQQQQQQQQQQQQQQPPPPPPPPPPPQLPQPPPQAQPLLPQPQPPPPPPPPPPGPAVAEEPLHRPKKELSATKKDRVNHCLTICENIVAQSVRNSPEFQKLLGIAMELFLLCSDDAESDVRMVADEC", "up_regulated": ["HSPA1A", "DNAJB1", "IL6"], "down_regulated": ["PGC1A", "DARPP32", "BDNF"]},
    {"name": "Cystic Fibrosis", "mutated_gene": "CFTR", "cell_type": "Airway Epithelial Cells", "sequence": "MQRSPLEKASVVSKLFFSWTRPILRKGYRQRLELSDIYQIPSVDSADNLSEKLEREWDRELASKKNPKLINALRRCFFWRFMFYGIFLYLGEVTKAVQPLLLGRIIASYDPDNKEERSIAIYLGIGLCLLFIVRTLLLHPAIFGLHRIGMQMRTA", "up_regulated": ["MUC5AC", "IL8", "TNF", "CXCL1"], "down_regulated": ["SIRT1", "PPARG", "AQP3"]},
    {"name": "Glioblastoma", "mutated_gene": "EGFRvIII", "cell_type": "Astrocytes", "sequence": "MRPSGTAGAALLALLAALCPASRALEEKKGNYVVTDHGSCVRACGADSYEMEEDGVRKCKKCEGPCRKVCNGIGIGEFKDSLSINATNIKHFKNCTSISGDLHILPVAFRGDSFTHTPPLDPQELDILKTVKEITGFLLIQAWPENRTDLHAFENL", "up_regulated": ["VEGFA", "MMP9", "HIF1A", "STAT3"], "down_regulated": ["PTEN", "TP53", "CDKN2A"]},
    {"name": "Sickle Cell Anemia", "mutated_gene": "HBB", "cell_type": "Erythrocytes", "sequence": "MVHLTPEEKSAVTALWGKVNVDDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH", "up_regulated": ["HMOX1", "ICAM1", "VCAM1", "SELE"], "down_regulated": ["NOS3", "GCH1", "KLF2"]},
    {"name": "Alzheimer's Disease", "mutated_gene": "APP", "cell_type": "Cortical Neurons", "sequence": "MLPGLALLLLAAWTARALEVPTDGNAGLLAEPQIAMFCGRLNMHMNVQNGKWDSDPSGTKTCIDTKEGILQYCQEVYPELQITNVVEANQPVTIQNWCKRGRKQCKTHPHFVIPYRCLVGEFVSDALLVPDKCKFLHQERMDVCETHLH", "up_regulated": ["APP", "BACE1", "MAPT"], "down_regulated": ["SYP", "BDNF", "NGF"]},
    {"name": "Parkinson's Disease", "mutated_gene": "SNCA", "cell_type": "Dopaminergic Neurons", "sequence": "MDVFMKGLSKAKEGVVAAAEKTKQGVAEAAGKTKEGVLYVGSKTKEGVVHGVATVAEKTKEQVTNVGGAVVTGVTAVAQKTVEGAGSIAAATGFVKKDQLGKNEEGAPQEGILEDMPVDPDNEAYEMPSEEGYQDYEPEA", "up_regulated": ["LRRK2", "PINK1", "PRKN"], "down_regulated": ["TH", "DAT", "VMAT2"]},
    {"name": "Breast Cancer (BRCA1)", "mutated_gene": "BRCA1", "cell_type": "Mammary Epithelial Cells", "sequence": "MDLSALRVEEVQNVINAMQKILECPICLELIKEPVSTKCDHIFCKFCMLKLLNQKKGPSQCPLCKNDITKRSLQESTRFSQLVEELLKIICAFQLDTGLEYANSYNFAKKENNSPEHLKDEVSIIQSMGYRNRAKRLLQSEPENPSLQK", "up_regulated": ["ERBB2", "CCND1", "MYC"], "down_regulated": ["BRCA1", "TP53", "PTEN"]},
    {"name": "Melanoma", "mutated_gene": "BRAF", "cell_type": "Melanocytes", "sequence": "MAALSGGGGGGAEPGQALFNGDMEPEAGAGAGAAASSAADPAIPEEVWNIKQMIKLTQEHIEALLDKFGGEHNPPSIYLEAYEEYTSKLDALQQREQQLLESLGNGTDFSVSSSASMDTVTSSSSSSLSVLPSSLSVFQNPTDVARSNPKSPQ", "up_regulated": ["MITF", "TYR", "MMP2"], "down_regulated": ["CDKN2A", "PTEN", "APAF1"]},
    {"name": "Type 2 Diabetes", "mutated_gene": "TCF7L2", "cell_type": "Pancreatic Beta Cells", "sequence": "MPQLNGGGGDDLGANDELISFKDEGEQEEKSSENSSAERDLADVKSSLVNESETNQNSSSDSEAERVRPKQPIVDVKCTTEVNAALSTAAATAAATAATAAAASAASSASSAASASAAAAAAAAAAAAASSAASSSAAAAASSAASSS", "up_regulated": ["G6PC", "PEPCK", "TXNIP"], "down_regulated": ["INS", "PDX1", "GLUT2"]},
]

# We expand this list synthetically to make a larger dataset
adjectives = ["Acute", "Chronic", "Idiopathic", "Familial", "Syndromic", "Late-onset", "Early-onset"]
for base_dis in diseases_list[:5]:
    for adj in adjectives:
        new_dis = base_dis.copy()
        new_dis["name"] = f"{adj} {base_dis['name']}"
        diseases_list.append(new_dis)

def train_model():
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Generate full dataset
    df = pd.DataFrame(diseases_list)
    df.to_csv('data/disease_dataset.csv', index=False)
    
    # Train Tfidf and KNN
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), analyzer='char_wb')
    X = vectorizer.fit_transform(df['name'])
    
    knn = NearestNeighbors(n_neighbors=1, metric='cosine')
    knn.fit(X)
    
    # Save models
    joblib.dump(vectorizer, 'models/vectorizer.pkl')
    joblib.dump(knn, 'models/knn_model.pkl')
    
    print(f"Successfully trained ML model on {len(df)} diseases and saved to models/ directory.")

if __name__ == '__main__':
    train_model()
