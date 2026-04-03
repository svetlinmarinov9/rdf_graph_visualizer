import json
import os
import re
# from urllib.parse import quote
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD, RDFS

# Namespaces
ONT = Namespace("http://example.org/ontology/association#")
DATA = Namespace("http://example.org/data/association#")

# Определяме пътищата на файловете
input_json_path = r"D:\fakeStore\cluster_model\associative_rules.json"
current_dir = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(current_dir, "turtle_file")
output_path = os.path.join(output_folder, "associative_rules.ttl")

# Създаваме папката ако не съществува
os.makedirs(output_folder, exist_ok=True)

# Зареждаме JSON файла от RapidMiner
with open(input_json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

g = Graph()
g.bind("ont", ONT)
g.bind("data", DATA)

# choose separator: use '-' or '_' or set to '' for no separator
SEPARATOR = '-'  # set to '_' or '' ; setting to ' ' will be percent-encoded in the URI

def slug(text, sep=SEPARATOR):
    text = (text or "").strip()
    if sep == '':
        # remove all non-alphanumeric chars
        s = re.sub(r'[^A-Za-z0-9]+', '', text)
    else:
        # replace runs of non-alphanumerics with the separator, preserve original case
        s = re.sub(r'[^A-Za-z0-9]+', sep, text)
        # collapse multiple separators
        s = re.sub(re.escape(sep) + r'{2,}', sep, s)
    return s.strip(sep)

# helper to create a safe fragment for item URIs and add a label
used_slugs = {}

def make_item_uri(name):
    base = slug(name)
    slug_val = base
    i = 1
    while slug_val in used_slugs and used_slugs[slug_val] != name:
        i += 1
        slug_val = f"{base}{sep}{i}" if SEPARATOR != '' else f"{base}{i}"
    used_slugs[slug_val] = name

    uri = DATA[slug_val]
    g.add((uri, RDF.type, ONT.Item))
    g.add((uri, RDFS.label, Literal(name)))
    return uri

# Обработка на правилата
for i, rule in enumerate(data.get("associationRules", []), start=1):
    rule_uri = DATA[f"rule{i}"]
    g.add((rule_uri, RDF.type, ONT.AssociationRule))

    # Метрики (робустно към нечислови стойности)
    try:
        g.add((rule_uri, ONT.hasSupport, Literal(float(rule["totalSupport"]), datatype=XSD.double)))
    except (KeyError, ValueError, TypeError):
        pass
    try:
        g.add((rule_uri, ONT.hasConfidence, Literal(float(rule["confidence"]), datatype=XSD.double)))
    except (KeyError, ValueError, TypeError):
        pass
    if "lift" in rule:
        try:
            g.add((rule_uri, ONT.hasLift, Literal(float(rule["lift"]), datatype=XSD.double)))
        except (ValueError, TypeError):
            pass

    # handle conviction that may be non-numeric (e.g. "Infinity")
    if "conviction" in rule:
        try:
            g.add((rule_uri, ONT.hasConviction, Literal(float(rule["conviction"]), datatype=XSD.double)))
        except (ValueError, TypeError):
            g.add((rule_uri, ONT.hasConviction, Literal(str(rule["conviction"]), datatype=XSD.string)))

    # Premise (antecedent)
    for premise in rule.get("premise", []):
        item_name = premise.get("name", "").strip()
        if not item_name:
            continue
        item_uri = make_item_uri(item_name)
        # store frequency if present
        freq = premise.get("frequency")
        if isinstance(freq, int):
            g.add((item_uri, ONT.hasFrequency, Literal(freq, datatype=XSD.integer)))
        g.add((rule_uri, ONT.hasAntecedent, item_uri))

    # Conclusion (consequent)
    for concl in rule.get("conclusion", []):
        item_name = concl.get("name", "").strip()
        if not item_name:
            continue
        item_uri = make_item_uri(item_name)
        freq = concl.get("frequency")
        if isinstance(freq, int):
            g.add((item_uri, ONT.hasFrequency, Literal(freq, datatype=XSD.integer)))
        g.add((rule_uri, ONT.hasConsequent, item_uri))

# Записване във файл
g.serialize(destination=output_path, format="turtle")
print(f"Turtle файл записан в: {output_path}")