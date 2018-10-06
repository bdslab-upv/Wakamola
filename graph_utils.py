import networkx as nx
from dbhelper import DBHelper
import matplotlib.pyplot as plt

'''
Create the graph from the database info.
Complex network operations and visualization!
'''

def create_graph():
    # db instance
    db = DBHelper()
    # query the relationships
    rels_ = db.get_relationships()

    #void graph
    G = nx.Graph()
    # add nodes and edges
    in_ = {}
    for i, rel in enumerate(rels_):

        if rel[0] not in in_:
            in_[rel[0]] = len(in_)
        if rel[1] not in in_:
            in_[rel[1]] = len(in_)

        #bmis
        print(rel[0])
        bmi1_ = db.getBMI(rel[0])
        bmi2_ = db.getBMI(rel[1])

        G.add_node((in_[rel[0]], bmi1_))
        G.add_node((in_[rel[1]], bmi2_))
        # no loops allowed
        if rel[0] != rel[1]:
            G.add_edge((in_[rel[0]], bmi1_), (in_[rel[1]], bmi2_))

    nx.draw_networkx(G)
    plt.show()


if __name__ == '__main__':
    create_graph()
