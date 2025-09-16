from dash import dcc, html
import dash_bootstrap_components as dbc
from rdflib import Graph, Namespace
from dataclasses import dataclass
from typing import List

@dataclass
class AssociationRule:
    antecedent: str
    consequent: str
    confidence: float
    lift: float
    support: float

class AssociationRuleParser:
    def __init__(self):
        self.data = Namespace("http://example.org/data/association#")
        self.ont = Namespace("http://example.org/ontology/association#")
        
    def parse_ttl_file(self, file_path: str) -> List[AssociationRule]:
        g = Graph()
        g.parse(file_path, format="turtle")
        rules = []
        query = """
        PREFIX data: <http://example.org/data/association#>
        PREFIX ont: <http://example.org/ontology/association#>
        SELECT ?rule ?antecedent ?consequent ?confidence ?lift ?support
        WHERE {
            ?rule a ont:AssociationRule ;
                  ont:hasAntecedent ?antecedent ;
                  ont:hasConsequent ?consequent ;
                  ont:hasConfidence ?confidence ;
                  ont:hasLift ?lift ;
                  ont:hasSupport ?support .
        }
        """
        for row in g.query(query):
            rule = AssociationRule(
                antecedent=str(row.antecedent).split("#")[-1],
                consequent=str(row.consequent).split("#")[-1],
                confidence=float(row.confidence),
                lift=float(row.lift),
                support=float(row.support)
            )
            rules.append(rule)
        return rules

def create_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col(html.H2("RDF Graph Visualizer", className="text-center mb-4"), width=12)
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Upload(
                    id='upload-data',
                    children=dbc.Button('Качи Clustering файл', color='primary', className='me-2'),
                    multiple=False,
                    className='mb-3'
                ),
                dcc.Upload(
                    id='upload-rules',
                    children=dbc.Button('Качи Association Rules файл', color='secondary', className='me-2'),
                    multiple=False,
                    className='mb-3'
                ),
            ], width=12)
        ]),

        dbc.Row([
            dbc.Col(
                dcc.Dropdown(
                    id='node-selector',
                    options=[],
                    style={'display': 'none'},
                    placeholder="Избери възел"
                ),
                width=6
            )
        ]),

        dbc.Row([
            dbc.Col(
                dcc.Tabs(
                    id='tabs',
                    value='tab-6',  # Set default tab to association rules
                    children=[
                        dcc.Tab(
                            label='Association Rules',
                            value='tab-6',
                            id='association-tab'
                        )
                    ],
                    colors={"border": "white", "primary": "#0d6efd", "background": "#f8f9fa"}
                ),
                width=12
            )
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(id='tabs-content', width=12)
        ]),

        html.Div(id='rules-store', style={'display': 'none'})
    ], fluid=True)