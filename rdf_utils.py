from rdflib import Graph
import networkx as nx
from rdflib import URIRef

def parse_rdf(content):
    """Parse RDF content in Turtle format and return an RDFlib Graph."""
    g = Graph()
    try:
        g.parse(data=content, format='turtle')
        return g
    except Exception as e:
        error_msg = f"Failed to parse RDF content: {str(e)}"
        # Log the error and the content for debugging
        print(f"Error parsing RDF: {error_msg}")
        print("Content that failed to parse:")
        print(content)
        raise ValueError(error_msg)

def graph_to_networkx(rdf_graph):
    G = nx.Graph()
    for s, p, o in rdf_graph:
        s_label = strip_prefix(s)
        o_label = strip_prefix(o)
        p_label = strip_prefix(p)

        # ➤ Филтър: позволяваме само възли от интерес:
        allowed_keywords = ['member', 'cluster', 'centroid']
        if not any(key in s_label.lower() for key in allowed_keywords):
            continue
        if not any(key in o_label.lower() for key in allowed_keywords):
            continue

        G.add_node(s_label)
        G.add_node(o_label)
        G.add_edge(s_label, o_label, label=p_label)
    return G

def strip_prefix(uri):
    """
    Премахва namespace-а от URI, оставяйки само локалната част.
    """
    if isinstance(uri, URIRef):
        return uri.split('#')[-1].split('/')[-1]
    return str(uri)