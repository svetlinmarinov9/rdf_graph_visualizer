import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

# Задаване на namespace
ONT = Namespace("http://example.org/ontology/clustering#")
DATA = Namespace("http://example.org/data/clustering#")

# Зареждане на JSON
with open(r"D:\fakeStore\cluster_model\cluster_model.json", "r") as f:
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

# Алгоритъм (не е в JSON, затова го отбелязваме като unknown)
g.add((DATA["unknownAlgorithm"], RDF.type, ONT.ClusteringAlgorithm))
g.add((result, ONT.usedAlgorithm, DATA["unknownAlgorithm"]))

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

    # Членове
    for mid in cluster["exampleIds"]:
        member_uri = DATA[f"member{int(mid)}"]
        g.add((member_uri, RDF.type, ONT.ClusterMember))
        g.add((member_uri, ONT.isMemberOf, cluster_uri))
        # Тук можеш да добавиш реален FeatureVector при наличие на данни

# Записване във файл
output_folder = r"D:\fakeStore\turtle_file"  
output_path = output_folder + r"\cluster_model.ttl"
g.serialize(output_path, format="turtle")