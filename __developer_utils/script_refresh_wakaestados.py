"""
Script para refrescar el ultimo wakaestados
de todos los miembros de la base de datos
dado que la informacion del bot esta altamente cacheada
este script ejecuta una vez la actualizacion si ocurren cambios
la manera de calcular el wakaestado
"""
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from models import obesity_risk
from dbhelper import DBHelper



if __name__ == '__main__':
    db = DBHelper()
    all_users = db.get_users()
    for us in all_users:
        # this function also update the last wakaestado
        final, _ = obesity_risk(us[0], completed = None)
        if final < 0 or final > 100:
            print(final)