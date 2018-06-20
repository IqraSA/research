from tools import transform, normal_distribution
import random

##  This class represents a peer to peer network.
#   It will be refactored to run in a distributed system.
class NetworkSimulator():
    ##  This method is the constructor which initializes the network.
    #   It receives the simulated latency of the network.
    #   @param self             Pointer to this network.
    #   @param latency          Network latency, set to 50 by default.
    def __init__(self, latency=50):
        self.agents = []
        self.latency_distribution_sample = transform(normal_distribution(latency, (latency * 2) // 5), lambda x: max(x, 0))
        self.time = 0
        self.objqueue = {}
        self.peers = {}
        self.reliability = 0.9

    ##  This method generates the list of peers for each peer.
    #   The peer selection is done randomly.
    #   @param self             Pointer to this network.
    #   @param num_peers        Number of peers for each peer. Set to 5 by default.
    def generate_peers(self, num_peers=5):
        self.peers = {}
        for a in self.agents:
            p = []
            while len(p) <= num_peers // 2:
                p.append(random.choice(self.agents))
                if p[-1] == a:
                    p.pop()
            self.peers[a.id] = self.peers.get(a.id, []) + p
            for peer in p:
                self.peers[peer.id] = self.peers.get(peer.id, []) + [a]

#    ##  This method simulates a time tick in the network.
#    #   @param self             Pointer to this network.
#    def tick(self):
#        for a in self.agents:
#            a.tick()
#
#    ##  This method broadcast an object to the network.
#    #   @param self             Pointer to this network.
#    #   @param sender           Pointer to the sender.
#    #   @param obj              Pointer to the object to be broadcasted.
#    def broadcast(self, sender, obj):
#        for p in self.peers[sender.id]:
#            recv_time = self.time + self.latency_distribution_sample()
#            if recv_time not in self.objqueue:
#                self.objqueue[recv_time] = []
#            self.objqueue[recv_time].append((p, obj))
#
#    ##  This method runs the simulattion in the network.
#    #   @param self             Pointer to this network.
#    def run(self, steps):
#        for i in range(steps):
#            self.tick()
#
#    ##  This method sends an object directly to another peer in the network.
#    #   @param self             Pointer to this network.
#    #   @param sender           Pointer to the sender.
#    #   @param to_id            ID of the target.
#    #   @param obj              Pointer to the object to be broadcasted.
#    def direct_send(self, to_id, obj):
#        for a in self.agents:
#            if a.id == to_id:
#                recv_time = self.time + self.latency_distribution_sample()
#                if recv_time not in self.objqueue:
#                    self.objqueue[recv_time] = []
#                self.objqueue[recv_time].append((a, obj))
#
#    ##  This method knocks offline several nodes in the network.
#    #   @param self             Pointer to this network.
#    #   @param n                Number of nodes to be knocked offline.
#    def knock_offline_random(self, n):
#        ko = {}
#        while len(ko) < n:
#            c = random.choice(self.agents)
#            ko[c.id] = c
#        for c in ko.values():
#            self.peers[c.id] = []
#        for a in self.agents:
#            self.peers[a.id] = [x for x in self.peers[a.id] if x.id not in ko]
#
#    ##  This method creates a partition in the network.
#    #   @param self             Pointer to this network.
#    def partition(self):
#        a = {}
#        while len(a) < len(self.agents) / 2:
#            c = random.choice(self.agents)
#            a[c.id] = c
#        for c in self.agents:
#            if c.id in a:
#                self.peers[c.id] = [x for x in self.peers[c.id] if x.id in a]
#            else:
#                self.peers[c.id] = [x for x in self.peers[c.id] if x.id not in a]

