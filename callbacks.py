from dash import Input, Output, State, html, dcc
from dash.exceptions import PreventUpdate
import base64
import networkx as nx
import dash
import rdf_utils
import graph_utils
import tempfile
import os
import dash_bootstrap_components as dbc
from layout import AssociationRuleParser

def register_callbacks(app):
    @app.callback(
        Output('tabs', 'children'),
        [Input('upload-data', 'contents'),
         Input('upload-rules', 'contents')]
    )
    def update_tabs(cluster_contents, rules_contents):
        tabs = []
        
        # Add clustering tabs if cluster file is uploaded
        if cluster_contents:
            tabs.extend([
                dcc.Tab(label='Граф', value='tab-1'),
                dcc.Tab(label='Матрица', value='tab-2'),
                dcc.Tab(label='Heatmap', value='tab-3'),
                dcc.Tab(label='Инфо за възел', value='tab-4'),
                dcc.Tab(label='Анализ', value='tab-5')
            ])
            return tabs  # Return immediately if cluster file is present
        
        # Only show rules tabs if no cluster file but rules file exists
        if rules_contents:
            tabs.extend([
                dcc.Tab(label='Таблица с правила', value='tab-6'),
                dcc.Tab(label='Статистика', value='tab-7'),
                dcc.Tab(label='Топ правила', value='tab-8'),
                dcc.Tab(label='Визуализация', value='tab-9')
            ])
        else:
            tabs.append(dcc.Tab(label='Моля, качете файл', value='tab-6'))
        
        return tabs

    # Callback for updating node-selector
    @app.callback(
        Output('node-selector', 'options'),
        Output('node-selector', 'style'),
        Input('upload-data', 'contents'),
        prevent_initial_call=True
    )
    def update_node_selector(file_contents):
        if not file_contents:
            raise PreventUpdate

        content_type, content_string = file_contents.split(',')
        decoded = base64.b64decode(content_string).decode('utf-8')

        try:
            rdf_graph = rdf_utils.parse_rdf(decoded)
            nx_graph = rdf_utils.graph_to_networkx(rdf_graph)
        except ValueError as e:
            return html.Div(f"Грешка: {str(e)}", style={'color': 'red'}), no_update, no_update

        # Filter only nodes of type member, cluster, centroid
        allowed_nodes = []
        for node in nx_graph.nodes():
            node_str = str(node).lower()
            if any(key in node_str for key in ['member', 'cluster', 'centroid']):
                allowed_nodes.append({'label': node, 'value': node})

        allowed_nodes.sort(key=lambda x: x['label'].lower())
        style = {'display': 'block', 'width': '50%', 'margin': '10px 0'}
        return allowed_nodes, style

    @app.callback(
        [Output('rules-store', 'children'),
         Output('tabs-content', 'children')],
        [Input('tabs', 'value'),
         Input('upload-data', 'contents'),
         Input('upload-rules', 'contents')],
        [State('node-selector', 'value')],
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def update_content(tab, file_contents, rules_contents, selected_node):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # Handle cluster visualization first
        if file_contents:
            # Handle clustering visualization
            content_type, content_string = file_contents.split(',')
            decoded = base64.b64decode(content_string).decode('utf-8')

            rdf_graph = rdf_utils.parse_rdf(decoded)
            nx_graph = rdf_utils.graph_to_networkx(rdf_graph)
            graph_utils.compute_communities(nx_graph)

            # Return appropriate content based on selected tab
            if tab == 'tab-1':
                return None, dcc.Graph(figure=graph_utils.create_network_figure(nx_graph))

            if tab == 'tab-2':
                adj_df = graph_utils.create_adjacency_matrix(nx_graph)
                return None, html.Div([
                    html.H4("Матрица на съседство"),
                    dcc.Graph(figure=graph_utils.create_table_figure(adj_df))
                ])

            if tab == 'tab-3':
                return None, dcc.Graph(figure=graph_utils.create_heatmap(nx_graph))

            if tab == 'tab-4':
                if not selected_node:
                    return None, html.Div("Избери възел от падащото меню горе.")

                neighbors = list(nx_graph.neighbors(selected_node))
                group = nx_graph.nodes[selected_node].get('group', 'N/A')
                degree = nx_graph.degree(selected_node)

                return None, html.Div([
                    html.H4(f"Информация за възел: {selected_node}"),
                    html.Ul([
                        html.Li(f"Възел: {selected_node}"),
                        html.Li(f"Група: {group}"),
                        html.Li(f"Степен: {degree}"),
                        html.Li(f"Свързани възли: {', '.join(neighbors)}")
                    ])
                ])

            if tab == 'tab-5':
                num_nodes = nx_graph.number_of_nodes()
                num_edges = nx_graph.number_of_edges()
                avg_degree = sum(dict(nx_graph.degree()).values()) / num_nodes
                density = nx.density(nx_graph)

                partition = graph_utils.compute_communities(nx_graph)
                communities = {}
                for node, group in partition.items():
                    communities.setdefault(group, []).append(node)

                largest_community = max(communities.items(), key=lambda x: len(x[1]))

                return None, html.Div([
                    html.H4("Анализ на графа"),
                    html.Ul([
                        html.Li(f"Брой върхове: {num_nodes}"),
                        html.Li(f"Брой ребра: {num_edges}"),
                        html.Li(f"Средна степен: {avg_degree:.2f}"),
                        html.Li(f"Плътност на графа: {density:.4f}"),
                        html.Li(f"Най-голяма общност: {largest_community[0]} с {len(largest_community[1])} върха")
                    ])
                ])

        # Only handle rules tabs if there's no cluster file
        if not file_contents and tab in ['tab-6', 'tab-7', 'tab-8', 'tab-9']:
            if not rules_contents:
                return None, html.Div([
                    html.H4("Няма заредени асоциативни правила"),
                    html.P("Моля, качете TTL файл с асоциативни правила.")
                ])

            try:
                # Parse rules if not already parsed
                if trigger_id == 'upload-rules' or trigger_id == 'tabs':
                    content_type, content_string = rules_contents.split(',')
                    decoded = base64.b64decode(content_string)

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.ttl') as tmp:
                        tmp.write(decoded)
                        tmp_path = tmp.name

                    parser = AssociationRuleParser()
                    rules = parser.parse_ttl_file(tmp_path)
                    os.unlink(tmp_path)

                    # Return content based on selected tab
                    if tab == 'tab-6':  # Rules Table
                        table = html.Div([
                            html.H4("Асоциативни правила"),
                            dbc.Table([
                                html.Thead(
                                    html.Tr([
                                        html.Th("Антецедент"),
                                        html.Th("Консеквент"),
                                        html.Th("Достоверност"),
                                        html.Th("Повдигане"),
                                        html.Th("Поддръжка")
                                    ])
                                ),
                                html.Tbody([
                                    html.Tr([
                                        html.Td(rule.antecedent),
                                        html.Td(rule.consequent),
                                        html.Td(f"{rule.confidence:.3f}"),
                                        html.Td(f"{rule.lift:.3f}"),
                                        html.Td(f"{rule.support:.3f}")
                                    ]) for rule in rules
                                ])
                            ], bordered=True, hover=True, striped=True, className="mt-3")
                        ])
                        return "Rules loaded", table

                    elif tab == 'tab-7':  # Rules Statistics
                        avg_confidence = sum(rule.confidence for rule in rules) / len(rules)
                        avg_lift = sum(rule.lift for rule in rules) / len(rules)
                        avg_support = sum(rule.support for rule in rules) / len(rules)
                        
                        return "Rules loaded", html.Div([
                            html.H4("Статистика на правилата"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardHeader("Обща статистика"),
                                        dbc.CardBody([
                                            html.H5(f"Общ брой правила: {len(rules)}", className="mb-3"),
                                            dbc.ListGroup([
                                                dbc.ListGroupItem([
                                                    html.Strong("Достоверност:"),
                                                    html.Div([
                                                        html.Div(f"Средна: {avg_confidence:.3f}"),
                                                        html.Div(f"Мин: {min(rule.confidence for rule in rules):.3f}"),
                                                        html.Div(f"Макс: {max(rule.confidence for rule in rules):.3f}")
                                                    ])
                                                ]),
                                                dbc.ListGroupItem([
                                                    html.Strong("Повдигане:"),
                                                    html.Div([
                                                        html.Div(f"Средно: {avg_lift:.3f}"),
                                                        html.Div(f"Мин: {min(rule.lift for rule in rules):.3f}"),
                                                        html.Div(f"Макс: {max(rule.lift for rule in rules):.3f}")
                                                    ])
                                                ]),
                                                dbc.ListGroupItem([
                                                    html.Strong("Поддръжка:"),
                                                    html.Div([
                                                        html.Div(f"Средна: {avg_support:.3f}"),
                                                        html.Div(f"Мин: {min(rule.support for rule in rules):.3f}"),
                                                        html.Div(f"Макс: {max(rule.support for rule in rules):.3f}")
                                                    ])
                                                ])
                                            ])
                                        ])
                                    ], className="mb-4")
                                ], width=12)
                            ])
                        ])

                    elif tab == 'tab-8':  # Top Rules
                        sorted_by_confidence = sorted(rules, key=lambda x: x.confidence, reverse=True)[:5]
                        sorted_by_lift = sorted(rules, key=lambda x: x.lift, reverse=True)[:5]
                        
                        return "Rules loaded", html.Div([
                            html.H4("Топ правила"),
                            html.Div([
                                html.H5("Топ 5 по достоверност", className="mt-4"),
                                dbc.Table([
                                    html.Thead(html.Tr([
                                        html.Th("Правило"),
                                        html.Th("Достоверност")
                                    ])),
                                    html.Tbody([
                                        html.Tr([
                                            html.Td(f"{rule.antecedent} → {rule.consequent}"),
                                            html.Td(f"{rule.confidence:.3f}")
                                        ]) for rule in sorted_by_confidence
                                    ])
                                ], bordered=True, hover=True, striped=True),
                                
                                html.H5("Топ 5 по повдигане", className="mt-4"),
                                dbc.Table([
                                    html.Thead(html.Tr([
                                        html.Th("Правило"),
                                        html.Th("Повдигане")
                                    ])),
                                    html.Tbody([
                                        html.Tr([
                                            html.Td(f"{rule.antecedent} → {rule.consequent}"),
                                            html.Td(f"{rule.lift:.3f}")
                                        ]) for rule in sorted_by_lift
                                    ])
                                ], bordered=True, hover=True, striped=True)
                            ])
                        ])

                    elif tab == 'tab-9':  # Rules Visualization
                        return "Rules loaded", html.Div([
                            html.H4("Разпределение на правилата"),
                            dbc.Row([
                                dbc.Col([
                                    dcc.Graph(
                                        figure={
                                            'data': [
                                                {
                                                    'x': [rule.confidence for rule in rules],
                                                    'y': [rule.support for rule in rules],
                                                    'mode': 'markers',
                                                    'marker': {
                                                        'size': 12,
                                                        'color': [rule.lift for rule in rules],
                                                        'colorscale': 'Viridis',
                                                        'showscale': True,
                                                        'colorbar': {'title': 'Повдигане'}
                                                    },
                                                    'text': [f"{rule.antecedent} → {rule.consequent}<br>Lift: {rule.lift:.3f}" for rule in rules],
                                                    'hoverinfo': 'text',
                                                    'type': 'scatter',
                                                    'name': 'Правила'
                                                }
                                            ],
                                            'layout': {
                                                'title': 'Достоверност спрямо Поддръжка',
                                                'xaxis': {'title': 'Достоверност', 'range': [0, 1]},
                                                'yaxis': {'title': 'Поддръжка', 'range': [0, 1]},
                                                'hovermode': 'closest',
                                                'template': 'plotly_white'
                                            }
                                        },
                                        className="mb-4"
                                    )
                                ], width=12),
                                dbc.Col([
                                    dcc.Graph(
                                        figure={
                                            'data': [
                                                {
                                                    'x': [rule.lift for rule in rules],
                                                    'type': 'histogram',
                                                    'name': 'Разпределение',
                                                    'nbinsx': 20,
                                                    'marker': {'color': '#636EFA'}
                                                }
                                            ],
                                            'layout': {
                                                'title': 'Разпределение на повдигането',
                                                'xaxis': {'title': 'Повдигане'},
                                                'yaxis': {'title': 'Брой правила'},
                                                'template': 'plotly_white'
                                            }
                                        }
                                    )
                                ], width=12)
                            ])
                        ])

            except Exception as e:
                return None, html.Div(f"Грешка при обработката на файла: {str(e)}")

        # Handle tab changes
        if trigger_id == 'tabs':
            # Remove the explicit check for tab-6 since we don't want to show rules message when cluster file is present
            if file_contents:
                if tab == 'tab-1':
                    return dash.no_update, dcc.Graph(figure=graph_utils.create_network_figure(nx_graph))

                if tab == 'tab-2':
                    adj_df = graph_utils.create_adjacency_matrix(nx_graph)
                    return dash.no_update, html.Div([
                        html.H4("Матрица на съседство"),
                        dcc.Graph(figure=graph_utils.create_table_figure(adj_df))
                    ])

                if tab == 'tab-3':
                    return dash.no_update, dcc.Graph(figure=graph_utils.create_heatmap(nx_graph))

                if tab == 'tab-4':
                    if not selected_node:
                        return dash.no_update, html.Div("Избери възел от падащото меню горе.")

                    neighbors = list(nx_graph.neighbors(selected_node))
                    group = nx_graph.nodes[selected_node].get('group', 'N/A')
                    degree = nx_graph.degree(selected_node)

                    return dash.no_update, html.Div([
                        html.H4(f"Информация за възел: {selected_node}"),
                        html.Ul([
                            html.Li(f"Възел: {selected_node}"),
                            html.Li(f"Група: {group}"),
                            html.Li(f"Степен: {degree}"),
                            html.Li(f"Свързани възли: {', '.join(neighbors)}")
                        ])
                    ])

                if tab == 'tab-5':
                    num_nodes = nx_graph.number_of_nodes()
                    num_edges = nx_graph.number_of_edges()
                    avg_degree = sum(dict(nx_graph.degree()).values()) / num_nodes
                    density = nx.density(nx_graph)

                    partition = graph_utils.compute_communities(nx_graph)
                    communities = {}
                    for node, group in partition.items():
                        communities.setdefault(group, []).append(node)

                    largest_community = max(communities.items(), key=lambda x: len(x[1]))

                    return dash.no_update, html.Div([
                        html.H4("Анализ на графа"),
                        html.Ul([
                            html.Li(f"Брой върхове: {num_nodes}"),
                            html.Li(f"Брой ребра: {num_edges}"),
                            html.Li(f"Средна степен: {avg_degree:.2f}"),
                            html.Li(f"Плътност на графа: {density:.4f}"),
                            html.Li(f"Най-голяма общност: {largest_community[0]} с {len(largest_community[1])} върха")
                        ])
                    ])

            # Only show rules-related messages if no cluster file is present
            if not file_contents and tab in ['tab-6', 'tab-7', 'tab-8', 'tab-9']:
                if not rules_contents:
                    return None, html.Div([
                        html.H4("Няма заредени асоциативни правила"),
                        html.P("Моля, качете TTL файл с асоциативни правила.")
                    ])

        return dash.no_update, html.Div("Избери таб.")