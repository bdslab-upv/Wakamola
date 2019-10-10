#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, json, shutil, string
import networkx as nx
import csv
import logging

logger = logging.getLogger("networker")
logger.setLevel(logging.INFO)

graph_data = { 'nodes': [], 'links': [] }

# ---------------------------------------------------------------
# -------------VALORES DE ENTRADA--------------------------------
# ---------------------------------------------------------------

# Nodos y arcos
nodos_y_arcos = nx.read_gpickle("ficheros_p/pickled_graph.p")
logger.info(nodos_y_arcos)
# Identificadores
identificadores = nx.read_gpickle("ficheros_p/ids_graph_ids_telegram.p")
# Agrupaciones
agrupaciones = nx.read_gpickle("ficheros_p/partitions.p")

# ---------------------------------------------------------------
# -------------VALORES DE ENTRADA (csv)--------------------------
# ---------------------------------------------------------------
csv_BMI = []
csv_score_activity = []
csv_score_nutrition = []
csv_id_telegram = []
csv_wakaestado = []
csv_score_social = []


with open('ficheros_p/desglose.csv', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=';')

    # csv_reader = csv.reader(csv_file, delimiter=';')
    line_count = 0
    for row in csv_reader:
        if line_count > 0:
            csv_BMI.append(row["BMI"])
            csv_score_activity.append(row["score_activity"])
            csv_score_nutrition.append(row["score_nutrition"])
            csv_id_telegram.append(row["user"])
            csv_wakaestado.append(row["wakaestado"])
            csv_score_social.append(row["social"])
        line_count += 1


# ---------------------------------------------------------------
# ------------- CARACTERIZACIÓN DE LOS NODOS---------------------

# ---------------------------------------------------------------

ids = []
for node in identificadores.items():
    ids.append(node[::-1])


contador = 1
listado_nodos = []
nodos_validos = []
for node in nodos_y_arcos.nodes():

    # Cruce de idnodo con tabla CSV
    value_index = 0
    if str(ids[node][1]) in csv_id_telegram:
        value_index = csv_id_telegram.index(str(ids[node][1]))

    txtstr = "ID_Node: " + str(node) + " / "
    txtstr = txtstr + "ID_Telegram: " +   str(ids[node][1])+ " / "
    txtstr = txtstr + "ID_Variable: " +   str(ids[node][0][1])+ " / "
    txtstr = txtstr + "Partition: " +   str(agrupaciones[node])+ " / "
    logger.info(csv_BMI[value_index])
    print(value_index)
    txtstr = txtstr + "BMI: " +  str(round(float(csv_BMI[value_index].replace(",",".")),2))+ " / "
    txtstr = txtstr + "Activity Score: " +  str(round(float(csv_score_activity[value_index].replace(",",".")),2))+ " / "
    txtstr = txtstr + "Nutrition Score: " +  str(round(float(csv_score_nutrition[value_index].replace(",",".")),2))+ " / "
    txtstr = txtstr + "Social Score: " +  str(round(float(csv_score_social[value_index].replace(",",".")),2))+ " / "
    txtstr = txtstr + "Wakastatus Score: " +  str(round(float(csv_wakaestado[value_index].replace(",","."))))

    listado_nodos.append(-1)
    if round(float(csv_BMI[value_index].replace(",","."))) > 0 :
        if round(float(csv_score_activity[value_index].replace(",","."))) > 0 :
            if round(float(csv_wakaestado[value_index].replace(",","."))) > 0 :
                if round(float(csv_score_nutrition[value_index].replace(",","."))) > 0 :
                    nodos_validos.append(node)
                    graph_data['nodes'].append({
                        "id": node,
                        "name": str(round(float(csv_wakaestado[value_index].replace(",",".")))),
                        "color": str(round(float(csv_BMI[value_index].replace(",",".")),2)),
                        "grupo" : str(agrupaciones[node]),
                        "p_ID": str(node),
                        "p_ID_Telegram":  str(ids[node][1]),
                        "p_ID_Variable":  str(ids[node][0][1]),
                        "p_Particion":  str(agrupaciones[node]),
                        "csv_id_telegram": str(csv_id_telegram[value_index]),
                        "csv_BMI": str(round(float(csv_BMI[value_index].replace(",",".")),2)),
                        "csv_score_activity": str(round(float(csv_score_activity[value_index].replace(",",".")),2)),
                        "csv_score_nutrition": str(round(float(csv_score_nutrition[value_index].replace(",",".")),2)),
                        "csv_score_social": str(round(float(csv_score_social[value_index].replace(",",".")),2)),
                        "csv_wakaestado": str(round(float(csv_wakaestado[value_index].replace(",",".")))),
                        "texto": txtstr,
                    })
                    listado_nodos[node] = contador
                    contador = contador + 1

# print(listado_nodos)
# print(nodos_validos)


# ---------------------------------------------------------------
# ------------- CARACTERIZACIÓN DE LOS ARCOS---------------------
# ---------------------------------------------------------------

j = 0
for edge in nodos_y_arcos.edges():
    source = edge[0]
    target = edge[1]

    if source in nodos_validos and target in nodos_validos :
        agrupacion = 1
        if agrupaciones[source] == agrupaciones[target]:
            agrupacion = 2

        graph_data['links'].append({
                "source" : listado_nodos[source],
                "target" : listado_nodos[target],
                "value": agrupacion,
            })
        j += 1


# ---------------------------------------------------------------
# ------------- GUARDADO ----------------------------------------
# ---------------------------------------------------------------
with open('html/template.html', 'r') as file:
    template_data = file.readlines()

k = 0
for line in template_data:
    template_data[k] = line.replace('line_count', str(line_count-1)).replace('template_json', json.dumps(graph_data))
    k += 1

with open(sys.argv[1]+'.html', 'w') as file:
    file.writelines( template_data )
