import osmnx as ox
G = ox.graph_from_place('Colombo, Sri Lanka', network_type='drive')
stats = ox.stats.basic_stats(G)
print('keys:', list(stats.keys()))
for k,v in stats.items():
    print(k, type(v))
print('\nfull stats:')
print(stats)
