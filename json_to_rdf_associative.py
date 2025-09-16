import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

# Namespaces
ONT = Namespace("http://example.org/ontology/association#")
DATA = Namespace("http://example.org/data/association#")

# Зареждаме JSON файла от RapidMiner
with open(r"D:\fakeStore\cluster_model\associative_rules.json", "r", encoding="utf-8") as f:
    data = json.load(f)

g = Graph()
g.bind("ont", ONT)
g.bind("data", DATA)

# Обработка на правилата
for i, rule in enumerate(data["associationRules"], start=1):
    rule_uri = DATA[f"rule{i}"]
    g.add((rule_uri, RDF.type, ONT.AssociationRule))

    # Метрики
    g.add((rule_uri, ONT.hasSupport, Literal(rule["totalSupport"], datatype=XSD.float)))
    g.add((rule_uri, ONT.hasConfidence, Literal(rule["confidence"], datatype=XSD.float)))
    if "lift" in rule:
        g.add((rule_uri, ONT.hasLift, Literal(rule["lift"], datatype=XSD.float)))

    # Premise (antecedent)
    for premise in rule.get("premise", []):
        item_name = premise["name"]
        item_uri = DATA[item_name.replace(" ", "_")]
        g.add((item_uri, RDF.type, ONT.Item))
        g.add((rule_uri, ONT.hasAntecedent, item_uri))

    # Conclusion (consequent)
    for concl in rule.get("conclusion", []):
        item_name = concl["name"]
        item_uri = DATA[item_name.replace(" ", "_")]
        g.add((item_uri, RDF.type, ONT.Item))
        g.add((rule_uri, ONT.hasConsequent, item_uri))

# Записване във файл
output_folder = r"D:\fakeStore\turtle_file"  
output_path = output_folder + r"\associative_rules.ttl"
g.serialize(output_path, format="turtle")