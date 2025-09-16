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
    pos = nx.kamada_kawai_layout(G)

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
        node_text.append(str(node))
        node_color.append(G.nodes[node].get('group', 0))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        text=node_text,
        mode='markers+text',
        textposition='top center',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='Viridis',
            color=node_color,
            size=15,
            colorbar=dict(title='Общност'),
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
    return go.Figure(
        data=go.Heatmap(
            z=adj_df.values,
            x=adj_df.columns,
            y=adj_df.index,
            colorscale='YlOrRd'
        ),
        layout=go.Layout(
            title="Heatmap на съседството",
            title_x=0.5,
            margin=dict(t=40, b=40),
            paper_bgcolor='#f9f9f9',
        )
    )

def create_table_figure(adj_df):
    return go.Figure(
        data=[go.Table(
            header=dict(
                values=["Върхове"] + list(adj_df.columns),
                fill_color='paleturquoise',
                align='left',
                font=dict(color='black', size=12)
            ),
            cells=dict(
                values=[adj_df.index] + [adj_df[col].tolist() for col in adj_df.columns],
                fill_color='lavender',
                align='left',
                font=dict(color='black', size=11)
            )
        )]
    )