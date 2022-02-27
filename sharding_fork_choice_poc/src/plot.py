from node import Node, BeaconBlock, MainChainBlock, ShardCollation
import matplotlib.pyplot as plt
import networkx as nx
import random, time


##  This methods creates an offset for plotting blocks of the main chain,
#   the beacon chain and all the shards
#   @param b    Block to be plotted
def mkoffset(b):
    return random.randrange(5) + \
        (0 if isinstance(b, MainChainBlock) else
         5 if isinstance(b, BeaconBlock) else
         5 + 5 * b.shard_id if isinstance(b, ShardCollation) else
         None)


##  This method plots the blockchain as seen from one of the notaries
#   @param n    The notarie to plot its view of the chain
def plotChain(n):
    G=nx.Graph()
    fileName = f"results/chain-{str(n.id)}.png"
    for b in n.blocks.values():
        if b.number > 0:
            if isinstance(b, BeaconBlock):
                G.add_edge(b.hash, b.main_chain_ref, color='c')
                G.add_edge(b.hash, b.parent_hash, color='g')
            elif isinstance(b, MainChainBlock):
                G.add_edge(b.hash, b.parent_hash, color='b')
            elif isinstance(b, ShardCollation):
                G.add_edge(b.hash, b.beacon_ref, color='r')
                G.add_edge(b.hash, b.parent_hash, color='y')
    plt.clf()
    fig = plt.figure(figsize=(18,9))
    pos={b.hash: (b.ts + mkoffset(b), b.ts) for b in n.blocks.values()}
    edges = G.edges()
    colors = [G[u][v]['color'] for u,v in edges]
    nx.draw_networkx_nodes(G, pos, node_size=10, node_shape='o', node_color='0.75')
    nx.draw_networkx_edges(G, pos, width=2, edge_color=colors)
    plt.ylabel("Time (ticks)")
    plt.savefig(fileName, bbox_inches="tight")
    plt.close()


##  This method plots the peer to peer network of the blockchain being
#   simulated
#   @param peers    The peer to peer network to plot
#   @param dir      The directory where the figure should be saved
def plotNetwork(peers, dir):
    plt.clf()
    G=nx.Graph()
    fig = plt.figure(figsize=(18,9))
    for peer in peers:
        G.add_node(str(peer))
        for p in peers.get(peer):
            G.add_edge(str(peer), str(p.id))
    nx.draw(G, with_labels=True)
    plt.axis("off")
    plt.savefig(f'{dir}/network.png', bbox_inches="tight")


