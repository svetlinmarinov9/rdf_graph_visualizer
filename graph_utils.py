import networkx as nx
import community
import plotly.graph_objs as go
import pandas as pd

def create_adjacency_matrix(G):
    adj_matrix = nx.to_numpy_array(G)
    nodes = list(G.nodes())
    df = pd.DataFrame(adj_matrix, index=nodes, columns=nodes)
    return df

def create_adjacency_heatmap(df):
    return go.Figure(
        data=go.Heatmap(
            z=df.values,
            x=df.columns,
            y=df.index,
            colorscale='YlGnBu'
        ),
        layout=go.Layout(
            title="Матрица на съседство (Heatmap)",
            margin=dict(l=50, r=50, t=50, b=50)
        )
    )

def compute_communities(G):
    partition = community.best_partition(G)
    nx.set_node_attributes(G, partition, 'group')
    return partition

def create_network_figure(G):
    # Използваме spring_layout с повече итерации и по-голямо k за повече място
    pos = nx.spring_layout(G, k=2, iterations=100, seed=42)

    # Рисуване на ребрата
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=1, color='lightgray'),
        hoverinfo='none',
        mode='lines'
    )

    x_vals = []
    y_vals = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        x_vals.extend([x0, x1, None])
        y_vals.extend([y0, y1, None])

    edge_trace.x = x_vals
    edge_trace.y = y_vals

    # Рисуване на възлите
    node_x = []
    node_y = []
    node_text = []
    node_color = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(node).replace('_', ' '))
        node_color.append(G.nodes[node].get('group', 0))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        text=node_text,
        mode='markers+text',
        textposition='top center',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            colorscale='Viridis',
            color=node_color,
            size=15,
            line_width=2
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title="Графова визуализация",
                        title_x=0.5,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=20, r=20, t=40),
                        paper_bgcolor='#f9f9f9',
                        plot_bgcolor='#f9f9f9',
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    ))
    return fig


def create_heatmap(G):
    """Heatmap с характеристиките на центроидите (FeatureVector)"""
    try:
        import os
        from rdflib import Graph, Namespace
        
        ONT = Namespace("http://example.org/ontology/clustering#")
        DATA = Namespace("http://example.org/data/clustering#")
        
        # Зареждаме Turtle файла ако съществува
        current_dir = os.path.dirname(os.path.abspath(__file__))
        turtle_path = os.path.join(current_dir, "turtle_file", "cluster_model.ttl")
        
        if not os.path.exists(turtle_path):
            # Ако няма Turtle файл, показваме съобщение
            return go.Figure(
                layout=go.Layout(
                    title="Няма Turtle данни за характеристиките",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
            )
        
        # Зареждаме RDF графика от Turtle
        rdf_graph = Graph()
        rdf_graph.parse(turtle_path, format="turtle")
        
        # Извличаме характеристики на центроидите
        cluster_features = {}
        
        query = """
        SELECT ?cluster ?feature_idx ?value
        WHERE {
            ?cluster a <http://example.org/ontology/clustering#Cluster> ;
                    <http://example.org/ontology/clustering#hasCentroid> ?centroid .
            ?centroid <http://example.org/ontology/clustering#hasFeature> ?value .
        }
        ORDER BY ?cluster ?feature_idx
        """
        
        for row in rdf_graph.query(query):
            cluster_name = str(row.cluster).split('/')[-1]
            value = float(str(row.value))
            
            if cluster_name not in cluster_features:
                cluster_features[cluster_name] = []
            cluster_features[cluster_name].append(value)
        
        if not cluster_features:
            return go.Figure(
                layout=go.Layout(
                    title="Няма характеристици за показване",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
            )
        
        # Конвертиране в DataFrame
        import pandas as pd
        df = pd.DataFrame.from_dict(cluster_features, orient='index')
        
        # Опитваме се да вземем имена на характеристиките от JSON
        feature_names = None
        json_path = r"D:\fakeStore\cluster_model\cluster_model.json"
        import json
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    # Тьърсим имена на характеристиките
                    if "dimensionNames" in data:
                        feature_names = data["dimensionNames"]
                    elif "attribute_names" in data:
                        feature_names = data["attribute_names"]
                    elif "headerExampleSet" in data and "columns" in data["headerExampleSet"]:
                        feature_names = [col["name"] for col in data["headerExampleSet"]["columns"]]
            except Exception as e:
                print(f"Error reading feature names from JSON: {e}")
                pass
        
        # Задаваме имена на колоните
        if feature_names and len(feature_names) == len(df.columns):
            df.columns = feature_names
        else:
            df.columns = [f"Характеристика {i+1}" for i in range(len(df.columns))]
        
        # Фиксираме имена на редовете - само клъстерът
        df.index = [f"Клъстер {idx.split('cluster')[-1]}" if 'cluster' in idx.lower() else idx for idx in df.index]
        df = df.sort_index()
        
        # Попълваме NaN стойности с 0
        df = df.fillna(0)
        
        return go.Figure(
            data=go.Heatmap(
                z=df.values,
                x=df.columns,
                y=df.index,
                colorscale='Viridis',
                hovertemplate='%{y} - %{x}: %{z:.4f}<extra></extra>',
                colorbar=dict(title="Стойност")
            ),
            layout=go.Layout(
                title="Heatmap на характеристиките на центроидите",
                title_x=0.5,
                margin=dict(l=100, r=100, t=50, b=100),
                paper_bgcolor='#f9f9f9',
                width=max(800, len(df.columns) * 100),
                height=max(400, len(df) * 100)
            )
        )
        
    except Exception as e:
        print(f"Error in create_heatmap: {e}")
        import traceback
        traceback.print_exc()
        return go.Figure()


def create_table_figure(adj_df):
    # Опыт эксклюдирани нодове
    exclude_nodes = ['result1', 'centroid0', 'centroid1', 'centroid2', 'centroid3']
    adj_df = adj_df.drop(columns=[c for c in adj_df.columns if any(ex.lower() in str(c).lower() for ex in exclude_nodes)], errors='ignore')
    adj_df = adj_df.drop(index=[r for r in adj_df.index if any(ex.lower() in str(r).lower() for ex in exclude_nodes)], errors='ignore')
    
    # Изчисляване на ширина - 120px минимум за колона
    column_count = len(adj_df.columns) + 1
    width = 120 * column_count
    height = max(600, len(adj_df) * 30)
    
    # Замени _ със интервал за по-добра четимост
    formatted_columns = [str(col).replace('_', ' ') for col in adj_df.columns]
    formatted_index = [str(idx).replace('_', ' ') for idx in adj_df.index]
    
    return go.Figure(
        data=[go.Table(
            columnwidth=[120] * column_count,
            header=dict(
                values=["Продукти"] + formatted_columns,
                fill_color='paleturquoise',
                align='center',
                font=dict(color='black', size=12),
                height=30
            ),
            cells=dict(
                values=[formatted_index] + [adj_df[col].tolist() for col in adj_df.columns],
                fill_color='lavender',
                align='center',
                font=dict(color='black', size=11),
                height=25
            )
        )],
        layout=go.Layout(
            margin=dict(l=125, r=50, t=50, b=50),
            height=height,
            width=width,
            template='plotly_white',
            xaxis=dict(automargin=True)
        )
    )