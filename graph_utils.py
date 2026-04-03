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
    adj_df = create_adjacency_matrix(G)
    # Филтрираме редове и колони както в таблицата
    clusters_to_show = ['cluster0', 'cluster1', 'cluster2', 'cluster3']
    exclude_keywords = ['cluster0', 'cluster1', 'cluster2', 'cluster3', 'clustermember', 'cluster', 'centroidclustermodel', 'clusteringalgorithm', 'result1', 'centroid0', 'centroid1', 'centroid2', 'centroid3']
    rows_to_show = [c for c in clusters_to_show if c in adj_df.index]
    cols_to_show = sorted([c for c in adj_df.columns if not any(ex.lower() in str(c).lower() for ex in exclude_keywords)])
    
    if rows_to_show and cols_to_show:
        adj_df_filtered = adj_df.loc[rows_to_show, cols_to_show]
    else:
        adj_df_filtered = adj_df
    
    # Замени _ със интервал за по-добра четимост
    formatted_columns = [str(col).replace('_', ' ') for col in adj_df_filtered.columns]
    formatted_index = [str(idx).replace('_', ' ') for idx in adj_df_filtered.index]
    
    return go.Figure(
        data=go.Heatmap(
            z=adj_df_filtered.values,
            x=formatted_columns,
            y=formatted_index,
            colorscale='YlOrRd',
            xgap=2,  # Разстояние между колоните
            ygap=2,  # Разстояние между редовете
            hovertemplate='%{y} - %{x}: %{z}<extra></extra>'
        ),
        layout=go.Layout(
            title="Heatmap на съседството",
            title_x=0.5,
            margin=dict(l=100, r=50, t=50, b=100),
            paper_bgcolor='#f9f9f9',
            width=max(600, len(adj_df_filtered.columns) * 80),
            height=max(500, len(adj_df_filtered) * 80)
        )
    )


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