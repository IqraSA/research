from node import Node, BeaconBlock, MainChainBlock, ShardCollation
import matplotlib.pyplot as plt
import networkx as nx
import random


def mkoffset(b):
    return random.randrange(5) + \
        (5 if isinstance(b, MainChainBlock) else
         0 if isinstance(b, BeaconBlock) else
         -5 - 5 * b.shard_id if isinstance(b, ShardCollation) else
         None)


def plotChain(n):
    G=nx.Graph()

    for b in n.blocks.values():
        if b.number > 0:
            if isinstance(b, BeaconBlock):
                G.add_edge(b.hash, b.main_chain_ref, color='c')
                G.add_edge(b.hash, b.parent_hash, color='y')
            elif isinstance(b, MainChainBlock):
                G.add_edge(b.hash, b.parent_hash, color='b')
            elif isinstance(b, ShardCollation):
                G.add_edge(b.hash, b.beacon_ref, color='g')
                G.add_edge(b.hash, b.parent_hash, color='r')


    pos={b.hash: (b.ts + mkoffset(b), b.ts) for b in n.blocks.values()}
    edges = G.edges()
    colors = [G[u][v]['color'] for u,v in edges]
    nx.draw_networkx_nodes(G,pos,node_size=10,node_shape='o',node_color='0.75')
    nx.draw_networkx_edges(G,pos,width=2,edge_color=colors)
    plt.axis('off')
    # plt.savefig("degree.png", bbox_inches="tight")
    plt.show()


