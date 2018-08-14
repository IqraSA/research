from node import Node, BeaconBlock, MainChainBlock, ShardCollation
from plot import plotChain, plotNetwork
import time
import random


##  This method runs the whole simulation.
#   This method first instanciates a network, a group of notaries, generates
#   the list of peers for each agent and then run the network for a number of
#   steps.  Results for each notary are printed in the end and a plot is
#   generated.
def run():
    # Define main variables
    nb_notaries = 40
    nb_shards = 40
    nb_ticks = 2000
    nb_peers = 5

    # Creat Genesis Blocks and Collations
    main_genesis = MainChainBlock(None, 59049, 0, nb_notaries*30)
    beacon_genesis = BeaconBlock(None, 1, 0, [], main_genesis, nb_notaries, nb_shards)
    shard_geneses = [ShardCollation(i, None, 0, beacon_genesis, 0) for i in range(nb_shards)]

    # Create list of notaries
    notaries = [Node(i,
                    nb_shards,
                    nb_notaries,
                    nb_notaries*30,
                    main_genesis,
                    beacon_genesis,
                    shard_geneses,
                    sleepy=i % 5 == 9) for i in range(nb_notaries)]

    # Generate peers
    peers = {}
    for agent in notaries:
        p = []
        while len(p) <= nb_peers // 2:
            peer = random.choice(notaries)
            if (peer.id != agent.id) and (peer not in p):
                p.append(peer)
        peers[agent.id] = peers.get(agent.id, []) + p
        for peer in p:
            if agent not in peers.get(peer.id, []):
                peers[peer.id] = peers.get(peer.id, []) + [agent]

    for agent in notaries:
        agent.add_peers(notaries, peers.get(agent.id, []))
    plotNetwork(peers, "results/")
    del peers

    # Run simulation for nb_ticks
    for i in range(nb_ticks):
        for agent in notaries:      ### <=== PARALLEL
            agent.tick()

    # Print notaries information
    for agent in notaries:              ### <=== PARALLEL
        agent.logProgress()
        plotChain(agent)

run()

