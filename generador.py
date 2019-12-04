#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Code created by Manuel Portoles

import sys, os, json
import networkx as nx
import csv
import logging


def create_html(filename='netweb'):
    
    graph_data = { 'nodes': [], 'links': [] }

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
    csv_BMI = []
    csv_score_activity = []
    csv_score_nutrition = []
    csv_id_telegram = []
    csv_wakaestado = []
    csv_score_social = []


    with open('ficheros_p/desglose.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
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


    contador = 0
    listado_nodos = []
    nodos_validos = []
    for node in nodos_y_arcos.nodes():

        # Cruce de idnodo con tabla CSV
        value_index = 0
        if str(ids[node][1]) in csv_id_telegram:
            value_index = csv_id_telegram.index(str(ids[node][1]))

        txtstr_en = "ID_Node: " + str(node) + " / "
        txtstr_en = txtstr_en + "ID_Telegram: " +   str(ids[node][1])+ " / "
        txtstr_en = txtstr_en + "ID_Variable: " +   str(ids[node][0][1])+ " / "
        txtstr_en = txtstr_en + "Comunity: " +   str(agrupaciones[node])+ " / "
        txtstr_en = txtstr_en + "BMI: " +  str(round(float(csv_BMI[value_index].replace(",",".")),2))+ " / "
        txtstr_en = txtstr_en + "Activity Score: " +  str(round(float(csv_score_activity[value_index].replace(",",".")),2))+ " / "
        txtstr_en = txtstr_en + "Diet Score: " +  str(round(float(csv_score_nutrition[value_index].replace(",",".")),2))+ " / "
        txtstr_en = txtstr_en + "Social Score: " +  str(round(float(csv_score_social[value_index].replace(",",".")),2))+ " / "
        txtstr_en = txtstr_en + "Wakastatus Score: " +  str(round(float(csv_wakaestado[value_index].replace(",","."))))

        txtstr_es = "ID_Node: " + str(node) + " / "
        txtstr_es = txtstr_es + "ID_Telegram: " +   str(ids[node][1])+ " / "
        txtstr_es = txtstr_es + "ID_Variable: " +   str(ids[node][0][1])+ " / "
        txtstr_es = txtstr_es + "Comunidad: " +   str(agrupaciones[node])+ " / "
        txtstr_es = txtstr_es + "IMC: " +  str(round(float(csv_BMI[value_index].replace(",",".")),2))+ " / "
        txtstr_es = txtstr_es + "Puntuación de actividad: " +  str(round(float(csv_score_activity[value_index].replace(",",".")),2))+ " / "
        txtstr_es = txtstr_es + "Puntuación nutritional : " +  str(round(float(csv_score_nutrition[value_index].replace(",",".")),2))+ " / "
        txtstr_es = txtstr_es + "Puntuación red social: " +  str(round(float(csv_score_social[value_index].replace(",",".")),2))+ " / "
        txtstr_es = txtstr_es + "Puntuación Wakaestado : " +  str(round(float(csv_wakaestado[value_index].replace(",","."))))

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
    with open('html/template_es.html', 'r') as file:
        template_data = file.readlines()

    k = 0
    for line in template_data:
        template_data[k] = line.replace('_ts', str(line_count)).replace('_ty', str(nodos_count)).replace('_tc', str(len(agrupaciones_count))).replace('_tr', str(len(graph_data['links']))).replace('template_json', json.dumps(graph_data))
        k += 1

    with open(filename+'_es.html', 'w') as file:
        file.writelines(template_data)

    # ---------------------------------------------------------------
    # ------------- GUARDADO ----------------------------------------
    # ---------------------------------------------------------------
    with open('html/template_en.html', 'r') as file:
        template_data = file.readlines()

    k = 0
    for line in template_data:
        template_data[k] = line.replace('_ts', str(line_count)).replace('_ty', str(nodos_count)).replace('_tc', str(len(agrupaciones_count))).replace('_tr', str(len(graph_data['links']))).replace('template_json', json.dumps(graph_data))
        k += 1

    with open(filename+'_en.html', 'w') as file:
        file.writelines(template_data)
