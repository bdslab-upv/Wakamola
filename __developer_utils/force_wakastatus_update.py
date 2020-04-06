from ..utils import create_database_connection
from ..models import obesity_risk
import logging


if __name__ == '__main__':
    logging.getLogger("ForceWSScript")
    # 1) Acces the DB
    db = create_database_connection()
    # 2) get the list of all users
    users = db.get_users()  # generator
    # 3) Recalculate all wakastatus and cache it on the DB
    for u in users:
        # this function calculate the wakascore and caches the result
        final_wakaestado, _ = obesity_risk(u)
        logging.info(final_wakaestado)
