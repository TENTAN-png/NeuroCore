import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import joblib
import json
import os

def train_model():
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Load base diseases from json
    with open('data/diseases.json', 'r') as f:
        base_diseases = json.load(f)
        
    # We expand this list synthetically to make a larger dataset
    diseases_list = []
    adjectives = ["", "Acute", "Chronic", "Idiopathic", "Familial", "Syndromic", "Late-onset", "Early-onset"]
    
    for base_dis in base_diseases:
        for adj in adjectives:
            new_dis = base_dis.copy()
            if adj:
                new_dis["name"] = f"{adj} {base_dis['name']}"
            diseases_list.append(new_dis)
    
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
