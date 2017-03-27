import networkx as nx
import matplotlib.pyplot as plt

from collections import defaultdict
import math

twitter_network = [ line.strip().split('\t') for line in file('twitter_network.csv') ]

o = nx.Graph()
hfollowers = defaultdict(lambda: 0)
for (twitter_user, followed_by, followers) in twitter_network:
    o.add_edge(twitter_user, followed_by, followers=int(followers))

nx.draw(o)
plt.show()
