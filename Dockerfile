FROM python:3.7

RUN apt-get update -y
RUN apt install apache2 -y

RUN pip install --upgrade pip
RUN pip install requests
RUN pip install emoji
RUN pip install pandas
RUN pip install mysql.connector
RUN pip install networkx
RUN pip install matplotlib
RUN pip install python-louvain
RUN pip install scipy

ADD alphahealth /opt/wakamola
ADD alphahealth/html/ /var/www/html/html
WORKDIR /opt/wakamola


EXPOSE 80

# RUN apachectl start
RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf
CMD sh __developer_utils/run.sh
