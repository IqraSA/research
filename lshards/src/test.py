from node import Node, BeaconBlock, MainChainBlock, ShardCollation
from tools import transform, normal_distribution, to_hex, checkpow
from plot import plotChain, plotNetwork
from mpi4py import MPI
import time, random, sys


##  This method runs the whole simulation.
#   This method first instanciates a network, a group of notaries, generates
#   the list of peers for each agent and then run the network for a number of
#   steps.  Results for each notary are printed in the end and a plot is
#   generated.
def run():
    # Define main variables
    nb_notaries = 20
    nb_shards = 20
    nb_ticks = 2000
    nb_peers = 4

    # Creat Genesis Blocks and Collations
    main_genesis = MainChainBlock(None, 59049, 0, nb_notaries*30)
    beacon_genesis = BeaconBlock(None, 1, 0, [], main_genesis, nb_notaries, nb_shards)
    shard_geneses = [ShardCollation(i, None, 0, beacon_genesis, 0) for i in range(nb_shards)]

    #print to_hex(main_genesis.hash)

    # Create list of notaries
    agent = Node(0,
                    nb_shards,
                    nb_notaries,
                    nb_notaries*30,
                    main_genesis,
                    beacon_genesis,
                    shard_geneses,
                    sleepy=0)
    #for i in range(nb_notaries)]

    # Generate peers
    #peers = {}
    #for agent in notaries:
    #    p = []
    #    while len(p) <= nb_peers // 2:
    #        peer = random.choice(notaries)
    #        if (peer.id != agent.id) and (peer not in p):
    #            p.append(peer)
    #    peers[agent.id] = peers.get(agent.id, []) + p
    #    for peer in p:
    #        if agent not in peers.get(peer.id, []):
    #            peers[peer.id] = peers.get(peer.id, []) + [agent]

    #for agent in notaries:

    agent.add_peers(nb_peers) #peers.get(agent.id, []))


    #plotNetwork(peers, "results/")
    #del peers

    # Run simulation for nb_ticks
    for i in range(nb_ticks):
        #for agent in notaries:      ### <=== PARALLEL
        agent.tick()
        agent.listen()
        agent.cleanReq()

        if (agent.id == 0) and (i % 10 == 0):
            print("Step %d done." % i)
            sys.stdout.flush()

    print("DONE!!!")

    # Print notaries information
    #for agent in notaries:              ### <=== PARALLEL
    agent.logProgress()
    plotChain(agent)

run()

