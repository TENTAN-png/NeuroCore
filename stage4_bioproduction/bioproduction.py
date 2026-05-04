import streamlit as st
import networkx as nx
import plotly.graph_objects as go

def render_stage4(disease_data):
    st.header("Stage 4: Retrosynthesis & Bio-Production")
    st.write("Mapping the chemical drug candidate back to natural biosynthesis pathways.")
    
    bio_data = disease_data['biosynthesis']
    
    st.subheader(f"Recommended Host Organism: **{bio_data['organism']}**")
    
    st.markdown("### Required Engineered Enzymes:")
    for enz in bio_data['enzymes']:
        st.markdown(f"- 🧬 {enz}")
        
    st.subheader("Biosynthesis Pathway Network")
    
    # Build NetworkX graph
    G = nx.DiGraph()
    nodes = bio_data['pathway_nodes']
    
    for i in range(len(nodes) - 1):
        G.add_edge(nodes[i], nodes[i+1])
        
    pos = nx.spring_layout(G)
    
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            colorscale='YlGnBu',
            color=[],
            size=40,
            line_width=2),
        text=list(G.nodes()),
        textposition="bottom center"
    )
    
    # Color nodes
    node_colors = ['#1f77b4' if node != nodes[-1] else '#2ca02c' for node in G.nodes()]
    node_trace.marker.color = node_colors

    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title='Metabolic Pathway',
                    title_font_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002 ) ],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    import time
    
    chart_placeholder = st.empty()
    
    if st.button("▶ Simulate Bioproduction Reaction"):
        for step in range(len(nodes)):
            # Re-color nodes based on step
            current_colors = []
            sizes = []
            for i, node in enumerate(G.nodes()):
                if i < step:
                     current_colors.append('#2ca02c') # completed
                     sizes.append(40)
                elif i == step:
                     current_colors.append('#ff7f0e') # active (orange)
                     sizes.append(60) # bigger
                else:
                     current_colors.append('#1f77b4') # pending
                     sizes.append(40)
            
            node_trace.marker.color = current_colors
            node_trace.marker.size = sizes
            
            fig = go.Figure(data=[edge_trace, node_trace],
                         layout=go.Layout(
                            title=f'Reaction Step {step+1}/{len(nodes)}: Synthesizing {nodes[step]}...',
                            title_font_size=16,
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20,l=5,r=5,t=40),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )
            chart_placeholder.plotly_chart(fig, use_container_width=True)
            time.sleep(1.2) # Wait to create animation effect
            
        st.success("✅ Drug Synthesis Complete! The organism has successfully manufactured the drug.")
    else:
        # Default static view
        chart_placeholder.plotly_chart(fig, use_container_width=True)
