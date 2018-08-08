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
    objqueue = {}
    globalTime = [0]
    notaries = [Node(i,
                    objqueue,
                    globalTime,
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

    # Run simulation for nb_ticks
    for i in range(nb_ticks):
        if globalTime[0] in objqueue:
            for recipient, obj in objqueue[globalTime[0]]:
                recipient.on_receive(obj)
            del objqueue[globalTime[0]]
        globalTime[0] += 1

        for agent in notaries:
            agent.tick()

    # Print notaries information
    for n in notaries:
        print("Beacon head: %d" % n.blocks[n.beacon_chain[-1]].number)
        print("Main chain head: %d" % n.blocks[n.main_chain[-1]].number)
        #print("Shard heads: %r" % [n.blocks[x[-1]].number for x in n.shard_chains])
        print("Total beacon blocks received: %d" % (len([b for b in n.blocks.values() if isinstance(b, BeaconBlock)]) - 1))
        print("Total beacon blocks received and signed: %d" % (len([b for b in n.blocks.keys() if b in n.sigs and len(n.sigs[b]) >= n.blocks[b].notary_req]) - 1))
        print("Total main chain blocks received: %d" % (len([b for b in n.blocks.values() if isinstance(b, MainChainBlock)]) - 1))
        #print("Total shard blocks received: %r" % [len([b for b in n.blocks.values() if isinstance(b, ShardCollation) and b.shard_id == i]) - 1 for i in range(nb_shards)])

    # Plot chain from one of the notaries (the last one)
    plotNetwork(peers, "results/")
    plotChain(n, "results/")


run()

