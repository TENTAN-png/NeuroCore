import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

def render_stage1(disease_data):
    st.header(f"Stage 1: Genomics Profile - {disease_data['name']}")
    st.write(f"Analyzing dysregulated genes in **{disease_data['cell_type']}** affected by **{disease_data['mutated_gene']}** mutation.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upregulated Genes")
        for gene in disease_data['up_regulated']:
            st.markdown(f"- 🔴 **{gene}**")
            
    with col2:
        st.subheader("Downregulated Genes")
        for gene in disease_data['down_regulated']:
            st.markdown(f"- 🔵 **{gene}**")
            
    st.subheader("Gene Expression Heatmap")
    
    # Generate mock heatmap data for demonstration
    genes = disease_data['up_regulated'] + disease_data['down_regulated']
    patients = [f"Patient_{i}" for i in range(1, 11)]
    
    data = []
    for gene in genes:
        if gene in disease_data['up_regulated']:
            expr = np.random.normal(loc=2.0, scale=0.5, size=len(patients))
        else:
            expr = np.random.normal(loc=-2.0, scale=0.5, size=len(patients))
        data.append(expr)
        
    df = pd.DataFrame(data, index=genes, columns=patients)
    
    fig = px.imshow(df, 
                    labels=dict(x="Patients", y="Genes", color="Expression Level"),
                    x=patients,
                    y=genes,
                    color_continuous_scale="RdBu_r",
                    aspect="auto")
    
    st.plotly_chart(fig, use_container_width=True)
