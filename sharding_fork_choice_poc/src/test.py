from network import NetworkSimulator
from node import Node, BeaconBlock, MainChainBlock, ShardCollation
from plot import plotChain


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

