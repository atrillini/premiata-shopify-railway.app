import pandas as pd
from sh import Sh
import base64
import json
from time import sleep
from datetime import datetime
import mysql.connector
import yaml

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
cfg = {
    "premiata_shopify": {
        "api_key": os.getenv("premiata-shopofy-api_key"),
        "token": os.getenv("premiata-shopofy-token"),
        "shop_url": os.getenv("premiata-shopofy_shop_url"),
        "location_id": os.getenv("premiata-shopofy-location_id"),
        "version": os.getenv("premiata-shopofy-version")
    }
   }
shopify = Sh(cfg['premiata_shopify'])
def process_stocks(stock_df):
    stocks = []
    for index, stock_data in stock_df.iterrows():
        stock = {
            'store': stock_data[0],
            'code': stock_data[1],
            'var': stock_data[2],
            'qty': stock_data[3],
            "pcode": stock_data[4]
        }
        stocks.append(stock)
    return stocks


def map_stocks(stock_data_processed,db_cursor):
    stocks = {}

    # Ottiene la lista degli articoli di abbigliamento dal DB
    apparellist = get_apparel_db(db_cursor, 'premiata_products')
    
    for row in stock_data_processed:
        code = row['code']
        size = row['var']
        qty = row['qty']
        store = row['store']
        
        # Se lo store è 24 e il codice non è in apparellist, salta l'iterazione
        if store == 24 and code not in apparellist:
            continue
        
        # Se il codice non è già presente nel dizionario stocks, lo inizializziamo
        if code not in stocks:
            stocks[code] = {
                'variants': [
                    {
                        'size': size,
                        'qty': qty,
                        'store': store
                    }
                ]
            }
        else:
            # Controlliamo se la stessa size è già presente per lo store 18
            variant_found = False
            for variant in stocks[code]['variants']:
                if variant['size'] == size:
                    # Se lo store è diverso, sommiamo le quantità
                    if store != variant['store']:
                        variant['qty'] += qty
                    variant_found = True
                    break
            
            # Se non abbiamo trovato una variante corrispondente, ne aggiungiamo una nuova
            if not variant_found:
                stocks[code]['variants'].append({
                    'size': size,
                    'qty': qty,
                    'store': store
                })
    
    return stocks

def read_stocks_file(file_path):
    return pd.read_csv(file_path, sep=',')

def db_connect(mysql_cfg):
    return mysql.connector.connect(
        user=mysql_cfg['db_user'],
        password=mysql_cfg['db_password'],
        host=mysql_cfg['host'],
        database=mysql_cfg['db_name']
    )

def get_product_db(cursor, table, sku):
    query = ("SELECT * FROM " + table + " WHERE sku = '" + sku + "'")

    cursor.execute(query)
    res = cursor.fetchone()

    return res

def get_product_4d(cursor, table, codice_4d):
    query = ("SELECT * FROM " + table + " WHERE codice_4d = '" + codice_4d + "'")
    

    cursor.execute(query)
    res = cursor.fetchone()
  
    return res

def get_all_product_db(cursor, table):
    query = ("SELECT * FROM " + table)

    cursor.execute(query)
    res = cursor.fetchall()

    return res

def get_apparel_db(cursor, table):
    query = ("SELECT codice_4d FROM " + table + " WHERE tags LIKE '%apparel%'")
    
    cursor.execute(query)
    res = cursor.fetchall()
    apparellist_strings = [item[0] for item in res]

    return apparellist_strings

def add_stock_record(cursor, table, conn, code, variant, qty, shid, inv_id,codice_4d):
    query = (
        "INSERT INTO " + table + " (code, variant, qty, sync_date, shopify_id, inventory_item_id,codice_4d) VALUES (%s, %s, %s, %s, %s, %s, %s)")
    values = (code, variant, qty, datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S'), shid, inv_id,codice_4d)

    cursor.execute(query, values)
    conn.commit()

def add_product_record(cursor, table, conn, sku, shid, codice_4d,tags):
    query = (
        "INSERT INTO " + table + " (sku, shid, codice_4d,tags) VALUES (%s, %s, %s, %s)")
    values = (sku, shid, codice_4d,tags)

    cursor.execute(query, values)
    conn.commit()

def get_current_stock(cursor, table, code, variant):
    query = "SELECT * FROM " + table + " WHERE code = %s AND variant = %s"
    values = (code, variant)

    cursor.execute(query, values)
    res = cursor.fetchone()

    return res

def get_current_stock_4d(cursor, table, code, variant):
    query = "SELECT * FROM " + table + " WHERE codice_4d = %s AND variant = %s"
    values = (code, variant)
    cursor.execute(query, values)
    res = cursor.fetchone()

    return res

def update_stock_record(cursor, table, conn, code, variant,  qty):
    query = "UPDATE " + table + \
        " SET qty = %s, sync_date = %s WHERE codice_4d = %s AND variant = %s"
    values = (qty, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code, variant)

    cursor.execute(query, values)
    conn.commit()

def format_string_file(s):
    string_formatted = ''
    for r in s.split('\n'):
        if(not r or r == 'b'): continue
        string_formatted += r + '\n'
    return string_formatted

def update_stocks(cfg):
    log_string = ''

    # stock file url
    file_path = cfg['stock_url']

    #mysql conf
    mysql_cfg = cfg['mysql']

    # db stock table name
    stock_table_name = mysql_cfg['stocks_table']
    products_table_name = mysql_cfg['products_table']

    stock_df = read_stocks_file(file_path)
    stock_df.fillna('', inplace=True)
    stock_processed = process_stocks(stock_df)
    stock_processed = list(
    filter(lambda x: (x['store'] in [18,24]), stock_processed))
   
    db_connection = db_connect(mysql_cfg)
    db_cursor = db_connection.cursor(buffered=True)

    stocks = map_stocks(stock_processed,db_cursor)
    allprod = get_all_product_db(db_cursor,products_table_name)
    prod_to_reset = []
    for dbpr in allprod:
        pff = dbpr[1]
        fourdcode = dbpr[7]
        if(fourdcode not in stocks.keys()):
            prod_to_reset.append(pff)
            print(pff +' - ' + fourdcode + ' non è nel file di stock')
    '''
    for s in stocks.keys():
        
        if(s != 'KITSR_12085'):
            continue
        print(s)
        print(stocks[s]['variants'])
    exit()    
    '''
    '''
    pf = ("DRA00406","BEBB9444","BEBB9450")
    fourdcode = []
    for p in pf:
        prodottofinito = shopify.get_product_id_by_metafield("my_fields","prodottofinito",p)
        if(prodottofinito['products']['edges']):
            fourdcode.append(prodottofinito["products"]["edges"][0]["node"]["metafield"]['value'])
    '''
    for p_r in prod_to_reset:
        if(p_r == 'GIFTCARD'):
            continue
        allstock = get_all_stock_db(db_cursor,stock_table_name,p_r)
        for st in allstock:
            inv_id = st[6]
            new_qty = 0
            qty = st[3]
            size = st[2]
            sku = st[1]

            if(qty != new_qty):
                if(shopify.update_stock(inv_id, new_qty)):
                        update_stock_record(
                            db_cursor, stock_table_name, db_connection, sku, size, new_qty)
                        print('[+] ' + sku + ' -> Updated variant and reset ' + str(size) + ' from ' + str(qty) + ' to -> ' + str(new_qty))
                        
                else:
                       
                        print('Error while updating stock ' + str(size) + ' -> ' + sku)
        
    for sku in stocks.keys():
        
        #if(sku != 'SKYBV_12031'):
            #continue
        # get product from db
       
        #if sku not in fourdcode:
            #continue
        db_prod = get_product_4d(db_cursor, mysql_cfg['products_table'], sku)
        
        if(not db_prod): continue
       
        # cycle all variants
        for var in stocks[sku]['variants']:

           
            
            if('1U' in db_prod[6]):
                 if var['size'] == '1':
                    var['size'] = 'U'

            if('DT' in db_prod[6]):
                 if var['size'] == '1':
                    var['size'] = 'Default title'

            if('34U' in db_prod[6]):
                 if var['size'] == '34':
                    var['size'] = 'U'
                
            if('156|258' in db_prod[6]):
                 if var['size'] == '1':
                    var['size'] = '56'
                 if var['size'] == '2':
                    var['size'] = '58'
                 if var['size'] == '16':
                    var['size'] = '60'

            if('letter' in db_prod[6]):
                 if var['size'] == '1':
                    var['size'] = 'XS'
                 if var['size'] == '2':
                    var['size'] = 'S'
                 if var['size'] == '3':
                    var['size'] = 'M'
                 if var['size'] == '4':
                    var['size'] = 'L'
                 if var['size'] == '5':
                    var['size'] = 'XL'
                 if var['size'] == '6':
                    var['size'] = 'XXL'
            
            
            var['size'] = var['size'].replace(",", ".")
            
            # get variant from db 
            
            res = get_current_stock_4d(db_cursor, mysql_cfg['stocks_table'], sku, var['size'])
            
            if(not res):
                if(var['qty']>0):
                    print('non trovo la taglia '+ var['size'] + ' del prodotto ' + str(sku))
             
            else:
                
                new_qty = var['qty']
                qty = res[3]
                var_id = res[5]
                inv_id = res[6]
               
                if(qty != new_qty):
                   

                    if(shopify.update_stock(inv_id, new_qty)):
                        update_stock_record(
                            db_cursor, stock_table_name, db_connection, sku, var['size'], new_qty)
                        print('[+] ' + sku + ' -> Updated variant ' + str(var['size']) + ' from ' + str(qty) + ' to -> ' + str(new_qty))
                        
                    else:
                       
                       print('Error while updating stock ' + var['size'] + ' -> ' + sku)
                
    
    #string_to_push = format_string_file(old_string + log_string)
    #blob.upload_from_string(string_to_push)
    #return "{" + string_to_push + "}"



   

    # call update stocks
#dbconn = db_connect(cfg['mysql'])
#cur = dbconn.cursor(buffered=True)
update_stocks(cfg)
#prods = shopify.get_all_products()
#shopify.updateTag(prods, 'changefw22prices_u2')
#exit()

