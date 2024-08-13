import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def visualize_zone_graph():
    zones_df = pd.read_csv('data/zones.csv')
    zone_graph_df = pd.read_csv('data/zone_graph.csv')

    # Create a graph
    G = nx.Graph()
    # Add nodes
    for index, row in zones_df.iterrows():
        if int(row["zone_id"]) == 9999:
            continue
        G.add_node(int(row['zone_id']), pos=(row['zone_center_lon'], row['zone_center_lat']))

    # Add edges
    for index, row in zone_graph_df.iterrows():
        G.add_edge(row['zone1_id'], row['zone2_id'])

    # positions of the nodes
    pos = nx.get_node_attributes(G, 'pos')

    # draw the nodes and the edges (all)
    plt.figure(figsize=(20, 16), dpi=300)
    nx.draw(G, pos, node_size=50, node_color='blue', with_labels=True, font_size=12)
    plt.title('Visualisierung des Zonengraphen')
    plt.savefig("figures/zone_graph.png")
