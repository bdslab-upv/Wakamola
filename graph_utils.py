'''
This file contain every method to generate the graphs
for the sake of order, everything will ne encapsulated as methods
'''

import pickle
import networkx as nx
from dbhelper import DBHelper
import collections
import community
import numpy as np
import pandas as pd
import scipy.stats as stats
from models import obesity_risk


def create_graph(store=True):
    db = DBHelper()
    # query the relationships
    relationships = db.get_relationships()

    # void graph
    G = nx.Graph()
    # add nodes and edges
    in_ = collections.OrderedDict()  # to ensure order when reading

    for i, relation in enumerate(relationships):
        if relation[0] not in in_:
            in_[relation[0]] = len(in_)
            G.add_node(in_[relation[0]])

        if relation[1] not in in_:
            in_[relation[1]] = len(in_)
            G.add_node(in_[relation[1]])

        # no loops allowed
        if relation[0] != relation[1]:
            G.add_edge(in_[relation[0]], in_[relation[1]])

    # the isolated nodes
    users_ = db.get_users()
    for user in users_:
        u = user[0]
        if u not in in_:
            in_[u] = len(in_)
            G.add_node(in_[u])

    # export to cytoscape format
    nx.write_graphml(G, 'wakamola_erg' + '.xml')
    if store:
        pickle.dump(G, open("pickled_graph.p", "wb"))
        pickle.dump(in_, open("ids_graph_ids_telegram.p", "wb"))
    # return the graph for the TODO future methods
    return G, in_


def read_wakamola_answers(in_):
    '''
    This method is adapted from the original
    df is all the answers with scores
    in_ is a modified version of the orignal in_
    including the row of the df
    '''
    db = DBHelper()
    df = db.complete_table()
    for index, row in df.iterrows():
        # completes questionnaries
        u = row["user"]
        comp = db.check_completed(u)
        _, info = obesity_risk(u, comp, network=True)
        # add the risk from the class models
        # BMI itself is more informative than score
        row["BMI"] = info["bmi"]
        row["BMI_score"] = info["bmi_score"]
        row["score_nutrition"] = info["nutrition"]
        row["score_activity"] = info["activity"]
        row["wakaestado"] = info["wakascore"]
        # TODO se pueden incluir más info
        in_[u] = (in_[u], index)
    return df, in_


def find_communities(G):
    """
    Partition of the graph using the Louvain partition algorithm
    :return: partition assigned to nodes in order in the graph object
    """
    part = community.best_partition(G)
    values = [part.get(node) for node in G.nodes()]
    return values


def kruskal_test(labels, values):
    levels = np.unique(labels)
    lv = list(zip(labels, values))
    samples = list()
    for l in levels:
        subsample = [entry[1] for entry in lv if entry[0] == l]
        samples.append(subsample)
    oddsratio, pvalue = stats.kruskal(*samples)
    return oddsratio, pvalue


def fisher_exact_test(labels, values):
    """
    Computes if the observed imbalance is statistically significant of the contingency table of label x factors is statistically significant
    :param label: class (group) of each sample
    :param factor: value that each sample takes for the factor
    :return: oddsratio, pvalue
    """
    contingency_table = pd.crosstab(labels, values)
    oddsratio, pvalue = stats.fisher_exact(contingency_table)
    return oddsratio, pvalue


if __name__ == '__main__':
    G, in_ = create_graph()
    answers, in_ = read_wakamola_answers(in_)
    communities = find_communities(G)
    # pickle the stuff
    pickle.dump(G, open("graphs/pickled_graph.p", "wb"))
    pickle.dump(in_, open("graphs/ids_graph_ids_telegram.p", "wb"))
    pickle.dump(communities, open("graphs/partitions.p", "wb"))