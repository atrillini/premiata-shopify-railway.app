from time import sleep
import pandas as pd
import yaml
import mysql.connector
from sh import Sh

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_product_db(cursor, table, sku):
    query = ("SELECT * FROM " + table + " WHERE sku = '" + sku + "'")

    cursor.execute(query)
    res = cursor.fetchone()

    return res

prods = [
   "MAS07088", "LUC07101", "MOED6443", "MIQD6074", "MOED7058", "CON06980", "CON06979", "BSKD6925", "BOED7031", "BSKD6923", "M4519LA"
]
cfg2 = {
        'stock_url': 'https://oldpremiata.pilcommunication.com/4d/stock/stock.csv',
        'mysql': {
            'host': '35.205.119.178', 
            'db_user': 'root', 
            'db_password': '8iNL4BM7ij7HsFPE',
            'db_name': 'ml_giacenze', 
            'products_table': 'premiata_products', 
            'stocks_table': 'premiata_stocks'
        }
    }


def db_connect(mysql_cfg):
    return mysql.connector.connect(
        user=mysql_cfg['db_user'],
        password=mysql_cfg['db_password'],
        host=mysql_cfg['host'],
        database=mysql_cfg['db_name']
    )

with open("./config.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    shopify = Sh(cfg['premiata']['shopify'])
    #prods = shopify.get_all_products()
   
    dbconn = db_connect(cfg2['mysql'])
    cur = dbconn.cursor(buffered=True)
    '''
    for p in prods:
        id = get_product_db(cur,cfg2['mysql']['products_table'],p)
        if id is not None and len(id) > 2:
            id = id[2]
            shopify.update_product_status(id, 'DRAFT')
            print('prodotto '+p+ ' aggiornato stato')
        else:
            print('prodotto '+p+ ' non trovato nel db')
                      
    '''
   

    


    



