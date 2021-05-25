'''
This file contain every method to generate the graphs
for the sake of order, everything will ne encapsulated as methods
'''

import pickle
import networkx as nx
from utils import create_database_connection
from debug import timeit
import collections
import community
import numpy as np
import pandas as pd
import scipy.stats as stats
from models import obesity_risk
import logging
from os import environ
from singleton import NetworkCache
from sys import getsizeof

logger = logging.getLogger(__name__)
if environ["MODE"] == 'test':
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.WARNING)

@timeit
def create_graph(store=False):
    logger = logging.getLogger("create_graph_function")
    db = create_database_connection()
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

    logger.info("Number of nodes " + str(len(in_.keys())))
    # export to cytoscape format
    nx.write_graphml(G, 'wakamola_erg' + '.xml')
    if store:
        pickle.dump(G, open("pickled_graph.p", "wb"))
        pickle.dump(in_, open("ids_graph_ids_telegram.p", "wb"))
    return G, in_

@timeit
def read_wakamola_answers(in_, date_filt=None):
    '''
    This method is adapted from the original
    df is all the answers with scores
    in_ is the dictionary hashes_id -> graph_id correspondence
    including the row of the df.
    IMPORTANT: the responses taken are filtered by date
    '''
    # new cache
    net_cache = NetworkCache()
    db = create_database_connection()
    # now df should have a 'date' column
    df = db.complete_table(date_filt=date_filt)
    new_df = []
    index = 0
    for row in df.itertuples():
        # need to this to edit the rows
        aux_ = row._asdict()
        u = aux_["user"]
        cache_value: tuple = net_cache.get_cached_value(u)
        if not cache_value[0]:
            comp = db.check_completed(u)
            _, info = obesity_risk(u, comp, network=True)
            # cache this thing
            net_cache.cache_value(hashed_id=u, to_cache_value=info)
        else:
            info = cache_value[1]

        # add the risk from the class models
        # BMI itself is more informative than score
        aux_["BMI"] = info["bmi"]
        aux_["BMI_score"] = info["bmi_score"]
        aux_["score_nutrition"] = info["nutrition"]
        aux_["score_activity"] = info["activity"]
        aux_["wakaestado"] = info["wakascore"]
        aux_["social"] = info["network"]
        new_df.append(aux_)
        in_[u] = (in_[u], index)
        index += 1
    logger.info(index)
    logger.info(f"Cache size: {getsizeof(net_cache.get_cache())} bytes")
    return pd.DataFrame(new_df), in_


@timeit
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
    :param labels: class (group) of each sample
    :param values: value that each sample takes for the factor
    :return: oddsratio, pvalue
    """
    contingency_table = pd.crosstab(labels, values)
    oddsratio, pvalue = stats.fisher_exact(contingency_table)
    return oddsratio, pvalue


def filtered_desglose(date_filt, path_graphs='ficheros_p/'):
    # interaction with 'in_' is veeeery cheap
    _, in_ = create_graph()
    desglose, _ = read_wakamola_answers(in_)
    path_to_desglose = path_graphs + "desglose"+"_"+str(date_filt)+".csv"
    desglose.to_csv(path_to_desglose, sep=";")
    return path_to_desglose


def update_graph_files(path_graphs='ficheros_p/'):
    """
    :param path_graphs: path to dump the files
    :param date_filt: date in format yyyymmdd to filter these results
    :return:
    """
    G, in_ = create_graph()
    desglose, in_ = read_wakamola_answers(in_)
    communities = find_communities(G)
    # pickle the stuff
    pickle.dump(G, open(path_graphs+"pickled_graph.p", "wb"))
    pickle.dump(in_, open(path_graphs+"ids_graph_ids_telegram.p", "wb"))
    pickle.dump(communities, open(path_graphs+"partitions.p", "wb"))
    desglose.to_csv(path_graphs+"desglose.csv", sep=";", index=False)
    return G, in_



    