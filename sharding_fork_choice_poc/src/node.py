from block import BeaconBlock, MainChainBlock, ShardCollation, BlockMakingRequest, Sig
from tools import to_hex, checkpow
import random

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
    def __init__(self, _id, network, nb_shards, nb_notaries, powdiff, main_genesis, beacon_genesis, shard_geneses, sleepy=False, careless=False, base_ts_diff=1, skip_ts_diff=6):
    genesis, shard_geneses, sleepy=False, careless=False, base_ts_diff=1, skip_ts_diff=6):
        self.blocks = {
            beacon_genesis.hash: beacon_genesis,
            main_genesis.hash: main_genesis
        }
        for s in shard_geneses:
            self.blocks[s.hash] = s
        self.sigs = {}
        self.beacon_chain = [beacon_genesis.hash]
        self.main_chain = [main_genesis.hash]
        self.shard_chains = [[g.hash] for g in shard_geneses]
        self.timequeue = []
        self.parentqueue = {}
        self.children = {}
        self.ts = 0
        self.id = _id
        self.network = network
        self.used_parents = {}
        self.processed = {}
        self.sleepy = sleepy
        self.careless = careless
        self.powdiff = powdiff
        self.nb_shards = nb_shards
        self.nb_notaries = nb_notaries
        self.base_ts_diff = base_ts_diff
        self.skip_ts_diff = skip_ts_diff

    def broadcast(self, x):
        if self.sleepy and self.ts:
            return
        self.log("Broadcasting %s %s" % ("block" if isinstance(x, BeaconBlock) else "sig", to_hex(x.hash[:4])))
        self.network.broadcast(self, x)
        self.on_receive(x)

    def log(self, words, lvl=3, all=False):
        #if "Tick:" != words[:5] or self.id == 0:
        if (self.id == 0 or all) and lvl >= 2:
            print(self.id, words)

    def on_receive(self, obj, reprocess=False):
        if obj.hash in self.processed and not reprocess:
            return
        self.processed[obj.hash] = True
        self.log("Processing %s %s" % ("block" if isinstance(obj, BeaconBlock) else "sig", to_hex(obj.hash[:4])))
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
                self.log("Broadcasting block %s" % to_hex(x.hash[:4]))
                self.broadcast(x)

    def add_to_timequeue(self, obj):
        i = 0
        while i < len(self.timequeue) and self.timequeue[i].ts < obj.ts:
            i += 1
        self.timequeue.insert(i, obj)

    def add_to_multiset(self, _set, k, v):
        if k not in _set:
            _set[k] = []
        _set[k].append(v)

    def change_head(self, chain, new_head):
        chain.extend([None] * (new_head.number + 1 - len(chain)))
        i, c = new_head.number, new_head.hash
        while c != chain[i]:
            chain[i] = c
            c = self.blocks[c].parent_hash
            i -= 1
        for i in range(len(chain)):
            assert self.blocks[chain[i]].number == i

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

    def process_children(self, h):
        if h in self.parentqueue:
            for b in self.parentqueue[h]:
                self.on_receive(b, reprocess=True)
            del self.parentqueue[h]

    def on_receive_main_block(self, block):
        # Parent not yet received
        if block.parent_hash not in self.blocks:
            self.add_to_multiset(self.parentqueue, block.parent_hash, block)
            return None
        self.log("Processing main chain block %s" % to_hex(block.hash[:4]))
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
        self.network.broadcast(self, block)

    def is_descendant(self, a, b):
        a, b = self.blocks[a], self.blocks[b]
        while b.number > a.number:
            b = self.blocks[b.parent_hash]
        return a.hash == b.hash

    def change_beacon_head(self, new_head):
        self.log("Changed beacon head: %s" % new_head.number)
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
            for c in self.shard_chains[s]:
                assert self.blocks[c].shard_id == s and self.blocks[c].beacon_ref in self.beacon_chain

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
        self.log("Processing beacon block %s" % to_hex(block.hash[:4]))
        self.blocks[block.hash] = block
        # Am I a notary, and is the block building on the head? Then broadcast a signature.
        if block.parent_hash == self.beacon_chain[-1] or self.careless:
            if self.id in block.notaries:
                self.broadcast(Sig(self.id, block))
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
        self.network.broadcast(self, block)

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
                self.log("Making block request for %.1f" % target_ts)
                self.add_to_timequeue(BlockMakingRequest(block.hash, target_ts))
        # Rebroadcast
        self.network.broadcast(self, sig)

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
        self.log("Processing shard collation %s" % to_hex(block.hash[:4]))
        self.blocks[block.hash] = block
        # Set head if needed
        if block.number > self.blocks[self.shard_chains[block.shard_id][-1]].number and block.beacon_ref in self.beacon_chain:
            self.change_head(self.shard_chains[block.shard_id], block)
        # Add child record
        self.add_to_multiset(self.children, block.parent_hash, block.hash)
        # Final steps
        self.process_children(block.hash)
        self.network.broadcast(self, block)

    def tick(self):
        if self.ts == 0:
            if self.id in self.blocks[self.beacon_chain[0]].notaries:
                self.broadcast(Sig(self.id, self.blocks[self.beacon_chain[0]]))
        self.ts += 0.1
        self.log("Tick: %.1f" % self.ts, lvl=1)
        # Process time queue
        while len(self.timequeue) and self.timequeue[0].ts <= self.ts:
            self.on_receive(self.timequeue.pop(0))
        # Attempt to mine a main chain block
        pownonce = random.randrange(65537)
        mchead = self.blocks[self.main_chain[-1]]
        if checkpow(mchead.pownonce, pownonce, self.powdiff):
            self.broadcast(MainChainBlock(mchead, pownonce, self.ts, self.powdiff))
