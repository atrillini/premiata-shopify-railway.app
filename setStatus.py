from time import sleep
import pandas as pd
import mysql.connector
from sh import Sh


cfg2 = {
        'stock_url': 'https://oldpremiata.pilcommunication.com/4d/stock/stock.csv',
        'mysql': {
            'host': 'crossover.proxy.rlwy.net', 
            'db_user': 'root', 
            'db_password': 'ICReplqqhsfqsimGVguywqGrBtvVWAWJ',
            'db_name': 'railway', 
            'port':'31393',
            'products_table': 'premiata_products', 
            'stocks_table': 'premiata_stocks',
        }
    }

def db_connect(mysql_cfg):
    return mysql.connector.connect(
        user=mysql_cfg['db_user'],
        password=mysql_cfg['db_password'],
        host=mysql_cfg['host'],
        port=mysql_cfg['port'],
        database=mysql_cfg['db_name']
    )

dbconn = db_connect(cfg2['mysql'])
cur = dbconn.cursor(buffered=True)
print('provo a fare la connessione al db')
print(dbconn)



    



