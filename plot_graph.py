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

SEED = 'CNN'
g = net.DiGraph(net.ego_graph(o, SEED , radius=3))

def trim_degrees_ted(g, degree=1, ted_degree=1):
    g2 = g.copy()
    d = net.degree(g2)
    for n in g2.nodes():
        if n == SEED: continue # don't prune the SEED node
        if n not in orig_users:
            g2.remove_node(n)
    return g2


def trim_edges_ted(g, weight=1, ted_weight=10):
    g2 = net.DiGraph()
    for f, to, edata in g.edges_iter(data=True):
        if f == SEED or to == SEED: # keep edges that link to the SEED node
            g2.add_edge(f, to, edata)
        elif f in orig_users or to in orig_users:
            if edata['followers'] >= ted_weight:
                g2.add_edge(f, to, edata)
        elif edata['followers'] >= weight:
            g2.add_edge(f, to, edata)
    return g2

core = trim_degrees_ted(g, degree=300, ted_degree=1)

core = trim_edges_ted(core, weight=250000, ted_weight=35000)

nodeset_types = { 'Orig': lambda s: s in orig_users, 'Not Orig': lambda s: s not in orig_users }

nodesets = defaultdict(list)

for nodeset_typename, nodeset_test in nodeset_types.iteritems():
    nodesets[nodeset_typename] = [ n for n in core.nodes_iter() if nodeset_test(n) ]

pos = net.spring_layout(core) # compute layout

colours = ['red','green']
colourmap = {}

plt.figure(figsize=(18,18))
plt.axis('off')

# draw nodes
i = 0
alphas = {'Orig': 0.6, 'Not Orig': 0.4}
for k in nodesets.keys():
    ns = [ math.log10(hfollowers[n]+1) * 80 for n in nodesets[k] ]
    print k, len(ns)
    net.draw_networkx_nodes(core, pos, nodelist=nodesets[k], node_size=ns, node_color=colours[i], alpha=alphas[k])
    colourmap[k] = colours[i]
    i += 1
print 'colourmap: ', colourmap

net.draw_networkx_edges(core, pos, width=0.2, alpha=0.2)

# draw labels
alphas = { 'Orig': 1.0, 'Not Orig': 0.5}
for k in nodesets.keys():
    for n in nodesets[k]:
        x, y = pos[n]
        plt.text(x, y+0.02, s=n, alpha=alphas[k], horizontalalignment='center', fontsize=9)

plt.savefig("Graph.png", format="PNG")
plt.show()
