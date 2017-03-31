import networkx as net
import matplotlib.pyplot as plt

from collections import defaultdict
import math

twitter_network = [ line.strip().split('\t') for line in file('twitter_network.csv') ]

orig_users = set()

o = net.DiGraph()
hfollowers = defaultdict(lambda: 0)
for (twitter_user, followed_by, followers) in twitter_network:
    o.add_edge(twitter_user, followed_by, followers=int(followers))
    hfollowers[twitter_user] = int(followers)
    orig_users.add(twitter_user)

g = o
colors = []
d = net.degree(g)
for n in g.nodes():
    if d[n] <= 2:
        g.remove_node(n)
    else:
        if n in orig_users:
            colors.append('red')
        else:
            colors.append('black')

labels = {}
for n in g.nodes():
    if n in orig_users:
        labels[n] = n

net.draw_networkx_labels(g,pos=net.spring_layout(g))
net.draw_networkx(g, node_color=colors)
plt.savefig("Graph.png", format="PNG")
plt.show()
