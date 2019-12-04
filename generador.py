#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Code created by Manuel Portoles

import sys
import json
import networkx as nx
import pandas as pd
import numpy as np


def create_html(filename='netweb'):
    graph_data = {'nodes': [], 'links': []}

    # ---------------------------------------------------------------
    # -------------VALORES DE ENTRADA--------------------------------
    # ---------------------------------------------------------------

    # Nodos y arcos
    nodos_y_arcos = nx.read_gpickle("ficheros_p/pickled_graph.p")
    # Identificadores
    identificadores = nx.read_gpickle("ficheros_p/ids_graph_ids_telegram.p")
    # Agrupaciones
    agrupaciones = nx.read_gpickle("ficheros_p/partitions.p")
    # print(agrupaciones)

    # ---------------------------------------------------------------
    # -------------VALORES DE ENTRADA (csv)--------------------------
    # ---------------------------------------------------------------

    desglose_ = pd.read_csv('ficheros_p/desglose.csv', delimiter=';')
    print(desglose_['BMI'])
    line_count = desglose_.shape[0]
    main_headers = ['BMI', 'score_activity', 'score_nutrition', 'wakaestado', 'social']

    # ---------------------------------------------------------------
    # ------------- CARACTERIZACIÓN DE LOS NODOS---------------------
    # ---------------------------------------------------------------

    ids = []
    for node in identificadores.items():
        ids.append(node[::-1])

    contador = 0
    listado_nodos = []
    nodos_validos = []
    for node in nodos_y_arcos.nodes():

        # Cruce de idnodo con tabla CSV
        value_index = 0
        actual_id_ = str(ids[node][1])
        selected_row = None
        if actual_id_ in np.array(desglose_['user']):
            # pick the row of that id
            selected_row = desglose_[desglose_['user'] == actual_id_]
        else:
            continue

        txtstr_en = ["ID_Node: " + str(node), "ID_Telegram: " + actual_id_, "ID_Variable: " + str(ids[node][0][1])]
        # TODO this can be in a multilanguage file!!!
        headers_ = ["Comunity", "BMI", "Activity Score", "Diet Score", "Social Score", "Wakastatus Score"]
        for h in headers_:
            for mh in main_headers:
                txtstr_en.append(h + ": " + str(round(float(selected_row[mh].replace(",", ".")), 2)))
        txtstr_en = ' / '.join(txtstr_en)

        # TODO, same for spanish, this can be comprehended in only one loop
        txtstr_es = ["ID_Node: " + str(node), "ID_Telegram: " + actual_id_, "ID_Variable: " + str(ids[node][0][1])]
        headers_ = ["Comunidad", "IMC", "Puntuación de actividad", "Puntuación nutritional", "Puntuación red social",
                    "Puntuación Wakaestado"]
        for h in headers_:
            for mh in main_headers:
                txtstr_es.append(h + ": " + str(round(float(selected_row[mh].replace(",", ".")), 2)))
        txtstr_es = ' / '.join(txtstr_es)

        listado_nodos.append(-1)
        if float(selected_row['BMI']) > 0 and float(selected_row['score_activity']) > 0 \
                and float(selected_row['wakaestado']) > 0 and float(selected_row['score_nutrition']) > 0:
            nodos_validos.append(node)
            graph_data['nodes'].append({
                "id": node,
                "name": str(selected_row['wakaestado']),
                "color": str(selected_row['BMI']),
                "grupo": str(agrupaciones[node]),
                "p_ID": str(node),
                "p_ID_Telegram": str(ids[node][1]),
                "p_ID_Variable": str(ids[node][0][1]),
                "p_Particion": str(agrupaciones[node]),
                "csv_id_telegram": str(selected_row['user']),
                "csv_BMI": str(round(float(selected_row['BMI']), 2)),
                "csv_score_activity": str(round(float(selected_row['score_activity']), 2)),
                "csv_score_nutrition": str(round(float(selected_row['score_nutrition']), 2)),
                "csv_score_social": str(round(float(selected_row['social']), 2)),
                "csv_wakaestado": str(round(float(selected_row['wakaestado']))),
                "texto_en": txtstr_en,
                "texto_es": txtstr_es,
            })
            listado_nodos[node] = contador
            contador = contador + 1

    agrupaciones_count = []
    nodos_count = line_count
    puntero = 0
    # print(agrupaciones)
    for i in listado_nodos:
        if listado_nodos[puntero] != -1:
            if agrupaciones[puntero] not in agrupaciones_count:
                agrupaciones_count.append(agrupaciones[puntero])
        else:
            nodos_count = nodos_count - 1
        # print(puntero,listado_nodos[puntero],agrupaciones[puntero],agrupaciones_count)
        puntero = puntero + 1

    # ---------------------------------------------------------------
    # ------------- CARACTERIZACIÓN DE LOS ARCOS---------------------
    # ---------------------------------------------------------------

    j = 0
    for edge in nodos_y_arcos.edges():
        source = edge[0]
        target = edge[1]

        if source in nodos_validos and target in nodos_validos:
            agrupacion = 1
            if agrupaciones[source] == agrupaciones[target]:
                agrupacion = 2

            graph_data['links'].append({
                "source": listado_nodos[source],
                "target": listado_nodos[target],
                "value": agrupacion,
            })
            j += 1

    # ---------------------------------------------------------------
    # ------------- GUARDADO ----------------------------------------
    # ---------------------------------------------------------------
    with open('html/template_es.html', 'r') as file:
        template_data = file.readlines()

    k = 0
    for line in template_data:
        template_data[k] = line.replace('_ts', str(line_count)) \
            .replace('_ty', str(nodos_count)) \
            .replace('_tc', str(len(agrupaciones_count))) \
            .replace('_tr', str(len(graph_data['links']))) \
            .replace('template_json', json.dumps(graph_data))
        k += 1

    with open(filename + '_es.html', 'w') as file:
        file.writelines(template_data)

    # ---------------------------------------------------------------
    # ------------- GUARDADO ----------------------------------------
    # ---------------------------------------------------------------
    with open('html/template_en.html', 'r') as file:
        template_data = file.readlines()

    k = 0
    for line in template_data:
        template_data[k] = line.replace('_ts', str(line_count)) \
            .replace('_ty', str(nodos_count)) \
            .replace('_tc', str(len(agrupaciones_count))) \
            .replace('_tr', str(len(graph_data['links']))) \
            .replace('template_json', json.dumps(graph_data))
        k += 1

    with open(filename + '_en.html', 'w') as file:
        file.writelines(template_data)
