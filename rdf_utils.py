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
        # Връзки от cluster до членове (например: cluster0 isMemberOf member1 или cluster0 hasMember productName)
        allowed_predicates = ['hasmember', 'ismemberof', 'hascluster', 'hascentroid']
        allowed_keywords = ['cluster']
        excluded_nodes = ['result1', 'centroid0', 'centroid1', 'centroid2', 'centroid3']
        
        # Поправи ексклудирани нодове
        if any(excl.lower() in s_label.lower() for excl in excluded_nodes) or \
           any(excl.lower() in o_label.lower() for excl in excluded_nodes):
            continue        
        # Включи всички ребра между cluster-и и других възли
        if not any(p.lower() in allowed_predicates for p in [p_label]):
            # Ако предиката не е за връзки между членове и клъстери, скипни
            continue
        
        # Проверяваме че поне един край е cluster
        if not (any(key in s_label.lower() for key in allowed_keywords) or 
                any(key in o_label.lower() for key in allowed_keywords)):
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