from block import BeaconBlock, MainChainBlock, ShardCollation, BlockMakingRequest, Sig
from tools import transform, normal_distribution, to_hex, checkpow
import random

commChannel = []

##  This class represents a node in the network.
#   It will be refactored into a distributed version.
class Node():
    ##  This method is the constructor which initializes the node.
    #   It receives the genesis block from the main chain and the beacon. It
    #   also receives the number of shards and notaries in the network in
    #   addition to other few parameters.
    #   @param self             Pointer to this node.
    #   @param id               Network ID.
    #   @param nb_shards        Number of shards.
    #   @param nb_notaries      Number of notaries in the network.
    #   @param powdiff          TBD.
    #   @param main_genesis     Genesis block in the main chain.
    #   @param beacon_genesis   Genesis block in the beacon chain.
    #   @param shard_genesis    Genesis block in the shard.
    #   @param sleepy           Set to True if the node is sleepy.
    #   @param careless         Set to True if the node is careless.
    #   @param base_ts_diff     TBD.
    #   @param skip_ts_diff     TBD.
    def __init__(self, _id, nb_shards, nb_notaries, powdiff, main_genesis, beacon_genesis, shard_geneses, sleepy=False, careless=False, base_ts_diff=1, skip_ts_diff=6):
        self.blocks = {
            beacon_genesis.hash: beacon_genesis,
            main_genesis.hash: main_genesis
        }
        for s in shard_geneses:
            self.blocks[s.hash] = s
        self.sigs = {}
        self.latency_dist = transform(normal_distribution(20, (20 * 2) // 5), lambda x: max(x, 0))
        self.beacon_chain = [beacon_genesis.hash]
        self.main_chain = [main_genesis.hash]
        self.shard_chains = [[g.hash] for g in shard_geneses]
        self.timequeue = []
        self.parentqueue = {}
        self.children = {}
        self.ts = 0
        self.id = _id
        self.agents = []
        self.peers = []
        self.objqueue = {}
        self.globalTime = 0
        self.used_parents = {}
        self.processed = {}
        self.sleepy = sleepy
        self.careless = careless
        self.powdiff = powdiff
        self.nb_shards = nb_shards
        self.nb_notaries = nb_notaries
        self.base_ts_diff = base_ts_diff
        self.skip_ts_diff = skip_ts_diff
        self.reliability = 0.9



    ##  This method generates the list of peers for each peer.
    #   The peer selection is done randomly.
    #   @param self             Pointer to this node.
    #   @param num_peers        Number of peers for each peer. Set to 5 by default.
    def add_peers(self, agents, peers, num_peers=5):
        self.agents = agents
        self.peers = peers


    ##  This method sents a message to a target peer
    #   @param self Pointer to this node.
    #   @param p    Target process to receive the object.
    #   @param obj  Object to be sent.
    def send(self, p, obj):
        global commChannel
        msg = [self.id, p.id, obj]
        commChannel.append(msg)
        print "Object sent from %d to %d"  % (self.id, p.id)


    ##  This method broadcast a message to all its peers.
    #   @param self Pointer to this node.
    #   @param obj  Message to be broadcasted
    def broadcast(self, obj):
        #self.log("Broadcasting %s %s" % ("block" if isinstance(obj, BeaconBlock) else "sig", to_hex(obj.hash[:4])), lvl=3)
        for p in self.peers:
            self.send(p, obj)
        #self.on_receive(obj)


    ##  This method logs an event in the standard output
    #   @param self     Pointer to this node
    #   @param words    Message to be logged
    #   @param lvl      Verbosity level
    #   @param all      Set to True if all nodes should log this event
    def log(self, words, lvl=3, all=False):
        #if "Tick:" != words[:5] or self.id == 0:
        if (self.id == 0 or all) and lvl >= 2:
            print(self.id, words)


    ##  This method is a hub that calls the right receive function depending on
    #   which type of block is received
    #   @param self         Pointer to this node
    #   @param obj          The object that is being received
    #   @param reprocess    Set to True if the object has to be reprocessed
    def on_receive(self, obj, reprocess=False):
        if obj.hash in self.processed and not reprocess:
            return
        if random.random() > self.reliability:
            return
        self.processed[obj.hash] = True
        self.log("Processing %s %s" % ("block" if isinstance(obj, BeaconBlock) else "sig", to_hex(obj.hash[:4])), lvl=1)
        if isinstance(obj, BeaconBlock):
            return self.on_receive_beacon_block(obj)
        elif isinstance(obj, MainChainBlock):
            return self.on_receive_main_block(obj)
        elif isinstance(obj, ShardCollation):
            return self.on_receive_shard_collation(obj)
        elif isinstance(obj, Sig):
            return self.on_receive_sig(obj)
        elif isinstance(obj, BlockMakingRequest):
            if self.beacon_chain[-1] == obj.parent:
                mc_ref = self.blocks[obj.parent]
                for i in range(2):
                    if mc_ref.number == 0:
                        break
                    #mc_ref = self.blocks[mc_ref].parent_hash
                x = BeaconBlock(self.blocks[obj.parent], self.id, self.ts,
                                self.sigs[obj.parent] if obj.parent in self.sigs else [],
                                self.blocks[self.main_chain[-1]], self.nb_notaries, self.nb_shards)
                self.log("Broadcasting block %s" % to_hex(x.hash[:4]), lvl=1)
                self.broadcast(x)
                self.on_receive(x)


    ##  This method adds an object to the time queue for later processing
    #   @param self     Pointer to this node
    #   @param obj      The object to be added to the timequeue
    def add_to_timequeue(self, obj):
        i = 0
        while i < len(self.timequeue) and self.timequeue[i].ts < obj.ts:
            i += 1
        self.timequeue.insert(i, obj)


    ##  This method adds an object into a set
    #   @param self     Pointer to this node
    #   @param set      The set in which the obejct has to be added
    #   @param k        The key of the object to be stored
    #   @param v        The value of the object to be stored
    def add_to_multiset(self, _set, k, v):
        if k not in _set:
            _set[k] = []
        _set[k].append(v)


    ##  This method changes to a new head in a particular chain
    #   @param  self        Pointer to this node
    #   @param  chain       The chain that has to change head
    #   @param  new_head    The new head of the chain
    def change_head(self, chain, new_head):
        chain.extend([None] * (new_head.number + 1 - len(chain)))
        i, c = new_head.number, new_head.hash
        while c != chain[i]:
            chain[i] = c
            c = self.blocks[c].parent_hash
            i -= 1
        for i in range(len(chain)):
            assert self.blocks[chain[i]].number == i


    ##  This method recalculates the head of the chain
    #   @param  self        Pointer to this node
    #   @param  chain       The chain in which the head has to be recalculated
    #   @param  condition   The condition to recalculate the head
    def recalculate_head(self, chain, condition):
        while not condition(self.blocks[chain[-1]]):
            chain.pop()
        descendant_queue = [chain[-1]]
        new_head = chain[-1]
        while len(descendant_queue):
            first = descendant_queue.pop(0)
            if first in self.children:
                for c in self.children[first]:
                    if condition(self.blocks[c]):
                        descendant_queue.append(c)
            if self.blocks[first].number > self.blocks[new_head].number:
                new_head = first
        self.change_head(chain, self.blocks[new_head])
        for i in range(len(chain)):
            assert condition(self.blocks[chain[i]])


    ##  This method process the children
    #   @param  self    Pointer to this node
    #   @param  h       The element to be processed
    def process_children(self, h):
        if h in self.parentqueue:
            for b in self.parentqueue[h]:
                self.on_receive(b, reprocess=True)
            del self.parentqueue[h]


    ##  This method process a main chain block
    #   @param  self    Pointer to this node
    #   @param  block   The main chain block to be processed
    def on_receive_main_block(self, block):
        # Parent not yet received
        if block.parent_hash not in self.blocks:
            self.add_to_multiset(self.parentqueue, block.parent_hash, block)
            return None
        self.log("Processing main chain block %s" % to_hex(block.hash[:4]), lvl=1)
        self.blocks[block.hash] = block
        # Reorg the main chain if new head
        if block.number > self.blocks[self.main_chain[-1]].number:
            reorging = (block.parent_hash != self.main_chain[-1])
            self.change_head(self.main_chain, block)
            if reorging:
                self.recalculate_head(self.beacon_chain,
                    lambda b: isinstance(b, BeaconBlock) and b.main_chain_ref in self.main_chain)
                for i in range(self.nb_shards):
                    self.recalculate_head(self.shard_chains[i],
                        lambda b: isinstance(b, ShardCollation) and b.shard_id == i and b.beacon_ref in self.beacon_chain)
        # Add child record
        self.add_to_multiset(self.children, block.parent_hash, block.hash)
        # Final steps
        self.process_children(block.hash)
        self.broadcast(block)


    ##  This method checks the relationship between two blocks
    #   @param  self    Pointer to this node
    #   @param  a       The block to be compared
    #   @param  b       The block to be compared
    def is_descendant(self, a, b):
        a, b = self.blocks[a], self.blocks[b]
        while b.number > a.number:
            b = self.blocks[b.parent_hash]
        return a.hash == b.hash


    ##  This method changes the head of the beacon chain
    #   @param  self        Pointer to this node
    #   @param  new_head    The new head to change to
    def change_beacon_head(self, new_head):
        self.log("Changed beacon head: %s" % new_head.number, lvl=1)
        reorging = (new_head.parent_hash != self.beacon_chain[-1])
        self.change_head(self.beacon_chain, new_head)
        if reorging:
            for i in range(self.nb_shards):
                self.recalculate_head(self.shard_chains[i],
                    lambda b: isinstance(b, ShardCollation) and b.shard_id == i and b.beacon_ref in self.beacon_chain)
        # Produce shard collations?
        for s in range(self.nb_shards):
            if self.id == new_head.shard_proposers[s]:
                sc = ShardCollation(s, self.blocks[self.shard_chains[s][-1]], self.id, new_head, self.ts)
                assert sc.beacon_ref == new_head.hash
                assert self.is_descendant(self.blocks[sc.parent_hash].beacon_ref, new_head.hash)
                self.broadcast(sc)
                self.on_receive(sc)
            for c in self.shard_chains[s]:
                assert self.blocks[c].shard_id == s and self.blocks[c].beacon_ref in self.beacon_chain

    ##  This method receives a beacon block
    #   @param  self    Pointer to this node
    #   @param  block   The beacon block to be processed
    def on_receive_beacon_block(self, block):
        # Parent not yet received
        if block.parent_hash not in self.blocks:
            self.add_to_multiset(self.parentqueue, block.parent_hash, block)
            return
        # Main chain parent not yet received
        if block.main_chain_ref not in self.blocks:
            self.add_to_multiset(self.parentqueue, block.main_chain_ref, block)
            return
        # Too early
        if block.ts > self.ts:
            self.add_to_timequeue(block)
            return
        # Check consistency of cross-link reference
        assert self.is_descendant(self.blocks[block.parent_hash].main_chain_ref, block.main_chain_ref)
        # Add the block
        self.log("Processing beacon block %s" % to_hex(block.hash[:4]), lvl=1)
        self.blocks[block.hash] = block
        # Am I a notary, and is the block building on the head? Then broadcast a signature.
        if block.parent_hash == self.beacon_chain[-1] or self.careless:
            if self.id in block.notaries:
                self.broadcast(Sig(self.id, block))
                self.on_receive(Sig(self.id, block))
        # Check for sigs, add to head?, make a block?
        if len(self.sigs.get(block.hash, [])) >= block.notary_req:
            if block.number > self.blocks[self.beacon_chain[-1]].number and block.main_chain_ref in self.main_chain:
                self.change_beacon_head(block)
            if self.id in self.blocks[block.hash].child_proposers:
                my_index = self.blocks[block.hash].child_proposers.index(self.id)
                target_ts = block.ts + self.base_ts_diff + my_index * self.skip_ts_diff
                self.add_to_timequeue(BlockMakingRequest(block.hash, target_ts))
        # Add child record
        self.add_to_multiset(self.children, block.parent_hash, block.hash)
        # Final steps
        self.process_children(block.hash)
        self.broadcast(block)


    ##  This method receives a signature
    #   @param  self    Pointer to this node
    #   @param  sig     The signature to be received
    def on_receive_sig(self, sig):
        self.add_to_multiset(self.sigs, sig.target_hash, sig)
        # Add to head? Make a block?
        if sig.target_hash in self.blocks and len(self.sigs[sig.target_hash]) == self.blocks[sig.target_hash].notary_req:
            block = self.blocks[sig.target_hash]
            if block.number > self.blocks[self.beacon_chain[-1]].number and block.main_chain_ref in self.main_chain:
                self.change_beacon_head(block)
            if self.id in block.child_proposers:
                my_index = block.child_proposers.index(self.id)
                target_ts = block.ts + self.base_ts_diff + my_index * self.skip_ts_diff
                self.log("Making block request for %.1f" % target_ts, lvl=1)
                self.add_to_timequeue(BlockMakingRequest(block.hash, target_ts))
        # Rebroadcast
        self.broadcast(sig)


    ##  This method receives a shard collation
    #   @param  self    Pointer to this node
    #   @param  block   The shard collation to be received
    def on_receive_shard_collation(self, block):
        # Parent not yet received
        if block.parent_hash not in self.blocks:
            self.add_to_multiset(self.parentqueue, block.parent_hash, block)
            return None
        # Beacon ref not yet received
        if block.beacon_ref not in self.blocks:
            self.add_to_multiset(self.parentqueue, block.beacon_ref, block)
            return None
        # Check consistency of cross-link reference
        assert self.is_descendant(self.blocks[block.parent_hash].beacon_ref, block.beacon_ref)
        self.log("Processing shard collation %s" % to_hex(block.hash[:4]), lvl=1)
        self.blocks[block.hash] = block
        # Set head if needed
        if block.number > self.blocks[self.shard_chains[block.shard_id][-1]].number and block.beacon_ref in self.beacon_chain:
            self.change_head(self.shard_chains[block.shard_id], block)
        # Add child record
        self.add_to_multiset(self.children, block.parent_hash, block.hash)
        # Final steps
        self.process_children(block.hash)
        self.broadcast(block)


    ##  This method ...
    #   @param  self     Pointer to this node
    def listen(self):
        global commChannel
        for msg in commChannel:
            if msg[1] == self.id:
                obj = msg[2]
                recv_time = self.globalTime + self.latency_dist()
                print "Object sent from %d at time %d to be RECEIVED by %d at time %d" % (msg[0], self.globalTime, msg[1], recv_time)
                if recv_time not in self.objqueue:
                    self.objqueue[recv_time] = []
                self.objqueue[recv_time].append((self, obj))
                commChannel.remove(msg)


    ##  This method ticks a unit of time
    #   @param  self     Pointer to this node
    def tick(self):
        if self.globalTime in self.objqueue:
            for recipient, obj in self.objqueue[self.globalTime]:
                if recipient.id == self.id:
                    self.on_receive(obj)
            del self.objqueue[self.globalTime]

        if self.ts == 0:
            if self.id in self.blocks[self.beacon_chain[0]].notaries:
                self.broadcast(Sig(self.id, self.blocks[self.beacon_chain[0]]))
                self.on_receive(Sig(self.id, self.blocks[self.beacon_chain[0]]))
        self.ts += 0.1
        if self.ts % 10 == 0:
            self.log("Tick: %.1f" % self.ts, lvl=3)
        # Process time queue
        while len(self.timequeue) and self.timequeue[0].ts <= self.ts:
            self.on_receive(self.timequeue.pop(0))
        # Attempt to mine a main chain block
        pownonce = random.randrange(65537)
        mchead = self.blocks[self.main_chain[-1]]
        if checkpow(mchead.pownonce, pownonce, self.powdiff):
            self.broadcast(MainChainBlock(mchead, pownonce, self.ts, self.powdiff))
            self.on_receive(MainChainBlock(mchead, pownonce, self.ts, self.powdiff))
        self.globalTime = self.globalTime + 1

    ##  This method prints block progress information on a file
    #   @param  self     Pointer to this node
    def logProgress(self):
        resFile = "results/" + str(self.id) + ".txt"
        f = open(resFile, "w")
        f.write("Main chain head: %d \n" % self.blocks[self.main_chain[-1]].number)
        f.write("Total main chain blocks received: %d \n" % (len([b for b in self.blocks.values() if isinstance(b, MainChainBlock)]) - 1))
        f.write("Beacon head: %d \n" % self.blocks[self.beacon_chain[-1]].number)
        f.write("Total beacon blocks received: %d \n" % (len([b for b in self.blocks.values() if isinstance(b, BeaconBlock)]) - 1))
        f.write("Total beacon blocks received and signed: %d \n" % (len([b for b in self.blocks.keys() if b in self.sigs and len(self.sigs[b]) >= self.blocks[b].notary_req]) - 1))
        f.write("Shard heads: %r \n" % [self.blocks[x[-1]].number for x in self.shard_chains])
        #f.write("Total shard blocks received: %r \n" % [len([b for b in self.blocks.values() if isinstance(b, ShardCollation) and b.shard_id == i]) - 1 for i in range(nb_shards)])
        f.close()

