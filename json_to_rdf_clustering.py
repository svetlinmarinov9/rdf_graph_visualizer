import json
import os
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

# Задаване на namespace
ONT = Namespace("http://example.org/ontology/clustering#")
DATA = Namespace("http://example.org/data/clustering#")

# Определяме пътищата на файловете
input_json_path = r"D:\fakeStore\cluster_model\cluster_model.json"
current_dir = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(current_dir, "turtle_file")
output_path = os.path.join(output_folder, "cluster_model.ttl")

# Създаваме папката ако не съществува
os.makedirs(output_folder, exist_ok=True)

# Зареждане на JSON
with open(input_json_path, "r") as f:
    data = json.load(f)

g = Graph()
g.bind("ont", ONT)
g.bind("data", DATA)

# Създаване на ClusteringResult
result = DATA["result1"]
g.add((result, RDF.type, ONT.ClusteringResult))

# Добавяне на използвана метрика
g.add((DATA["squaredEuclidean"], RDF.type, ONT.DistanceFunction))
g.add((result, ONT.usedSimilarityMeasure, DATA["squaredEuclidean"]))

# Алгоритъм (ако е наличен в JSON)
if "rm_object_type" in data:
    algorithm_name = data["rm_object_type"].split(".")[-1]  # извличаме последното име
    algorithm_uri = DATA[algorithm_name]
    g.add((algorithm_uri, RDF.type, ONT.ClusteringAlgorithm))
    g.add((result, ONT.usedAlgorithm, algorithm_uri))

# Обработка на клъстери
for cluster in data["clusters"]:
    cid = f"cluster{cluster['clusterId']}"
    cluster_uri = DATA[cid]
    g.add((cluster_uri, RDF.type, ONT.Cluster))
    g.add((result, ONT.hasCluster, cluster_uri))

    # Центроид
    centroid = data["centroids"][cluster['clusterId']]["centroid"]
    centroid_uri = DATA[f"centroid{cluster['clusterId']}"]
    g.add((centroid_uri, RDF.type, ONT.FeatureVector))
    for value in centroid:
        g.add((centroid_uri, ONT.hasFeature, Literal(value, datatype=XSD.float)))
    g.add((cluster_uri, ONT.hasCentroid, centroid_uri))

# Трекинг на асигнирани членове - всеки член става само в един клъстер
assigned_members = {}

for cluster in data["clusters"]:
    cid = f"cluster{cluster['clusterId']}"
    cluster_uri = DATA[cid]

    # Членове - с проверка за дублиране
    for mid in cluster["exampleIds"]:
        # обработи като число или как текст (продукт име)
        try:
            idx = int(mid)
            member_id = f"member{idx}"
        except (ValueError, TypeError):
            # ако не е число, използвай текстът като slug
            import re
            slug = re.sub(r'[^A-Za-z0-9]+', '_', str(mid).strip())
            member_id = slug
        
        # Ако членът вече е асигниран на друг клъстер, пропусни го
        if member_id in assigned_members:
            print(f"❌ {member_id} вече е в {assigned_members[member_id]}, пропускане от {cid}")
            continue
        
        # Маркирай членът като асигниран на този клъстер
        assigned_members[member_id] = cid
        
        member_uri = DATA[member_id]
        g.add((member_uri, RDF.type, ONT.ClusterMember))
        g.add((member_uri, ONT.isMemberOf, cluster_uri))
        # Тук можеш да добавиш реален FeatureVector при наличие на данни

print(f"\n✓ Общо уникални членове: {len(assigned_members)}")
print(f"✓ Клъстери обработени: {len(data['clusters'])}")

# Записване във файл
g.serialize(output_path, format="turtle")
print(f"✓ Turtle файл записан в: {output_path}")
