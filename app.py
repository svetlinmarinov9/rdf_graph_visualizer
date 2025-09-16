from dash import Dash
import layout
import callbacks
import dash_bootstrap_components as dbc

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "RDF Graph Visualizer"
app.layout = layout.create_layout()

callbacks.register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)