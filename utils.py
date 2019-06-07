import networkx as nx
from dbhelper import DBHelper
import matplotlib.pyplot as plt
import hashlib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
import pickle


logging.basicConfig(level=logging.INFO)

'''
Refactored to be a general utils class
MD5 was moved here in order to be more general
'''


def md5(id_user):
    '''
    Hashes id_user usign MD5. Ensures anonimity.
    '''
    return hashlib.md5(str(id_user).encode('utf-8')).hexdigest()


def send_mail(sender, receivers, subject, body, smtp_server, smtp_port, password):
    # Create the container (outer) email message.
    msg = MIMEMultipart()
    msg['Subject'] = subject
    # me == the sender's email address
    # family = the list of all recipients' email addresses
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    body = MIMEText(body) # convert the body to a MIME compatible string
    msg.attach(body)

    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(smtp_server,smtp_port)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.ehlo() # Can be omitted
        server.login(sender, password)
        server.sendmail(sender, receivers, msg.as_string())
        server.quit()
    except Exception as e:
        logging.error(e)
        logging.error('Error sending mail')


def create_graph(name):
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

        bmi1_ = round(db.getBMI(rel[0]), 1)
        bmi2_ = round(db.getBMI(rel[1]), 1)

        G.add_node((in_[rel[0]], bmi1_))
        G.add_node((in_[rel[1]], bmi2_))
        # no loops allowed
        if rel[0] != rel[1]:
            G.add_edge((in_[rel[0]], bmi1_), (in_[rel[1]], bmi2_))

        # the isolated nodes
        users_ = db.get_users()
        for us in users_:
            if us not in in_:
                bmi_ = round(db.getBMI(us[0]), 1)
                in_[us] = len(in_)
                G.add_node((in_[us], bmi_))

    # export to cytoscape format
    nx.write_graphml(G, 'graphs/'+name+'.xml')
    # save to pickle
    pickle.dump(G, open("pickled_graph.p", "wb"))
    pickle.dump(in_, open("ids_graph_ids_telegram.p", "wb"))

    # very basic visualization, just for error checking
    #nx.draw_networkx(G)
    #plt.show()
    # return the graph for the TODO future methods
    return G


if __name__ == '__main__':
    create_graph(name='cytoscape_graph')
