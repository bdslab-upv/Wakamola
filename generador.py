#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Code created by Manuel Portoles
# Edited and optimized (still on it!) by Vicent Blanes

import json
import networkx as nx
import pandas as pd
import logging


logging.basicConfig(level=logging.INFO)


def create_html(filename='netweb'):
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    logger.error(f"Funcion create_html")
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
    csv_data = pd.read_csv('ficheros_p/desglose.csv', sep=';')


    logger.error(f"desglose line count: {csv_data.shape}")
    logger.error(csv_data.columns.values)
    line_count = csv_data.shape[0]
    csv_id_telegram = list(csv_data.user)
    csv_BMI = list(csv_data.BMI)
    csv_score_activity = list(csv_data.score_activity)
    csv_score_nutrition = list(csv_data.score_nutrition)
    csv_score_social = list(csv_data.social)
    csv_wakaestado = list(csv_data.wakaestado)

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
        

        if str(ids[node][1]) in csv_id_telegram:
            value_index = csv_id_telegram.index(str(ids[node][1]))

        logger.error(f"value_index: {value_index}")
        
        # English version (This could be parametrized and merged!!)
        txtstr_en = f"ID_Node: {node} / "
        txtstr_en = txtstr_en + f"ID_Variable: {ids[node][0][1]} / "
        txtstr_en = txtstr_en + f"Comunity: {agrupaciones[node]} / "
        txtstr_en = txtstr_en + f"BMI: {round(csv_BMI[value_index], 2)} / "
        txtstr_en = txtstr_en + f"Activity Score: {round(csv_score_activity[value_index], 2)} /"
        txtstr_en = txtstr_en + f"Diet Score: {round(csv_score_nutrition[value_index], 2)} / "
        txtstr_en = txtstr_en + f"Social Score: {round(csv_score_social[value_index], 2)} / "
        txtstr_en = txtstr_en + f"Wakastatus Score: {round(csv_wakaestado[value_index])}"
        
        # Spanish version
        txtstr_es = f"ID_Node: {node} / "
        txtstr_es = txtstr_es + f"ID_Variable: {ids[node][0][1]} / "
        txtstr_es = txtstr_es + f"Comunidad: {agrupaciones[node]} / "
        txtstr_es = txtstr_es + f"IMC: {round(csv_BMI[value_index], 2)} /"
        txtstr_es = txtstr_es + f"Puntuación de actividad: {round(csv_score_activity[value_index], 2)} / "
        txtstr_es = txtstr_es + f"Puntuación nutritional: {round(csv_score_nutrition[value_index], 2)} / "
        txtstr_es = txtstr_es + f"Puntuación red social: {round(csv_score_social[value_index], 2)} / "
        txtstr_es = txtstr_es + f"Puntuación Wakaestado: {round(csv_wakaestado[value_index])}"


        listado_nodos.append(-1)
        if round(csv_BMI[value_index]) > 0:
            if round(csv_score_activity[value_index]) > 0:
                if round(csv_wakaestado[value_index]) > 0:
                    if round(csv_score_nutrition[value_index]) > 0:
                        nodos_validos.append(node)
                        graph_data['nodes'].append({
                            "id": node,
                            "name": str(round(csv_wakaestado[value_index], 2)),
                            "color": str(round(csv_BMI[value_index], 2)),
                            "grupo": str(agrupaciones[node]),
                            "p_ID": str(node),
                            "p_ID_Telegram": str(ids[node][1]),
                            "p_ID_Variable": str(ids[node][0][1]),
                            "p_Particion": str(agrupaciones[node]),
                            "csv_id_telegram": str(csv_id_telegram[value_index]),
                            "csv_BMI": str(round(csv_BMI[value_index], 2)),
                            "csv_score_activity": str(round(csv_score_activity[value_index], 2)),
                            "csv_score_nutrition": str(round(csv_score_nutrition[value_index], 2)),
                            "csv_score_social": str(round(csv_score_social[value_index], 2)),
                            "csv_wakaestado": str(round(csv_wakaestado[value_index])),
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
        template_data[k] = line.replace('_ts', str(line_count)).replace('_ty', str(nodos_count)).replace('_tc', str(
            len(agrupaciones_count))).replace('_tr', str(len(graph_data['links']))).replace('template_json',
                                                                                            json.dumps(graph_data))
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
        template_data[k] = line.replace('_ts', str(line_count)).replace('_ty', str(nodos_count)).replace('_tc', str(
            len(agrupaciones_count))).replace('_tr', str(len(graph_data['links']))).replace('template_json',
                                                                                            json.dumps(graph_data))
        k += 1

    with open(filename + '_en.html', 'w') as file:
        file.writelines(template_data)

