from network import NetworkSimulator
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


def run():
    # Define main variables
    nb_notaries = 40
    nb_shards = 40
    nb_ticks = 2000

    # Creat Genesis Blocks and Collations
    main_genesis = MainChainBlock(None, 59049, 0, nb_notaries*30)
    beacon_genesis = BeaconBlock(None, 1, 0, [], main_genesis, nb_notaries, nb_shards)
    shard_geneses = [ShardCollation(i, None, 0, beacon_genesis, 0) for i in range(nb_shards)]

    # Create network simulator
    net = NetworkSimulator(latency=19)

    # Create list of notaries
    notaries = [Node(i,
                 net,
                 nb_shards,
                 nb_notaries,
                 nb_notaries*30,
                 main_genesis,
                 beacon_genesis,
                 shard_geneses,
                 sleepy=i % 5 == 9) for i in range(nb_notaries)]

    """Add notaries to the network"""
    net.agents = notaries

    # Generate peers
    net.generate_peers()

    # Run network for nb_ticks
    for i in range(nb_ticks):
        net.tick()

    # Print notaries information
    for n in notaries:
        print("Beacon head: %d" % n.blocks[n.beacon_chain[-1]].number)
        print("Main chain head: %d" % n.blocks[n.main_chain[-1]].number)
        print("Shard heads: %r" % [n.blocks[x[-1]].number for x in n.shard_chains])
        print("Total beacon blocks received: %d" % (len([b for b in n.blocks.values() if isinstance(b, BeaconBlock)]) - 1))
        print("Total beacon blocks received and signed: %d" % (len([b for b in n.blocks.keys() if b in n.sigs and len(n.sigs[b]) >= n.blocks[b].notary_req]) - 1))
        print("Total main chain blocks received: %d" % (len([b for b in n.blocks.values() if isinstance(b, MainChainBlock)]) - 1))
        print("Total shard blocks received: %r" % [len([b for b in n.blocks.values() if isinstance(b, ShardCollation) and b.shard_id == i]) - 1 for i in range(nb_shards)])

    # Plot chain
    plotChain(n)


run()

