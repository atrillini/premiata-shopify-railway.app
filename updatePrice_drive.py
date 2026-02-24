from pickle import TRUE
import time
from sh import Sh
import pandas as pd
import yaml
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import json
import hashlib
import os
import requests
import re
from decimal import Decimal, InvalidOperation

googleobj = """
{
  "type": "service_account",
  "project_id": "pil-associati",
  "private_key_id": "4d2dff048ca02e646154cbfa18b1050b87179601",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCN1XJ8Ai/nCi5n\nwyXW+tu/jyrRTVz3HypBmPdaqXOtlLij9bhyK4alLleev17KqxxbQWPhqm7rvuWe\nicSyeWexFkb8DPW2mVOXU9lPWXzpcwfZfF0z1D9/cDYuoX/pMfWPeA/yA1bv5KXM\nPW6phjbtU1eeWtTO4AoQnl086O+23dM2gYNe+69nS4qN0GYOBxcS+MDIQJ4Ypivl\norWNMdE9Zd4rQSN3QW18fRBakVIDYjybl3B+9Iz/+3ezRMXxz1aCR3Kjh7JE2Jeb\nbGUEK4lT3NsjCZ/9vKbhP04XpgkTW67HR5TiSRxhP78riF92mgTUx2He8baoPtRp\nUzg1hcrPAgMBAAECggEAJuifq/JDptttqIxp5IRT5USGp/1Tm/1iL7WhYa8rqzop\nvtzpOPTEzqqcYdG41NtE/6m8F0uUezqWrju4CIfykKt+VKXPgESmoFRhwHlZoYcr\nZ5fMz6uRscmcK4WlW9kXNsDmiussncm5TAKsSXgmuEtNNYVQbOIcELwI8u0p2Z2v\nNkdSfFzqR5+cifQ6f40VAqxqBaYMULi1w0Cye1ykK9u8x873zLAk/WWmrQlevqrG\nGO1ueH1C7oKZ7AQRfDnGEorTdEODHhuSrH3UAzQpmPxBeTsLu2yiCzo/AzzFoKQo\nYaGbDUL0q6IeRN4/j5Gly3wH1BlQ5h2VSVyItxCj7QKBgQDFlIxoFui8sm4EhIlp\nOumSzS+kDONqwHnFNGMQRq4hwLkY6xR444xlkpGglvfvT356RZWRt4v8ohhH1Mpq\nJSfb4ihapNUJrwH1d1FzcudHmqryM/on87AxEJOeVWObrapaz5+T+/rlipIJPhh2\n8WA7CPTZ+DvsKNq12RuoNEfJDQKBgQC3xUcBwU0Vto3hmcXwKXmfTVkC2BVmVqDM\nyca5BG2p/29edP+conIPsBIfn3zhuSTJMkfZslhnTdbgzdbthP+sLGo4Tz/rpn7f\ne5Op7BxEyGIYlepa2WjNVNeY0AKxyEnF2xQMVetsZBzbOjNZj6crOepc5ZrCAxNk\nNx/ucfR0SwKBgQDDyuEYhRs9YtQDRhOlY+vyvcJoHx19vB7vfWptxpzodcL3Hn27\nDkMipIwLR4+KZow/PpVpQSpHv5mwFP5BEXDeRM8YhB9Y6URXq1XbwhHOs0aTnU5Y\nKPSAqpyeWp/Ktd4K/5RzYVDQBvGQlyhHNgrWdZmuJn+7FwElE3CEzsoUQQKBgHlp\nKqpsLSNlQoOD9pPesu2eSmponGrKXN4viMz/sfwYOFntblrrr/PRXYfq9LSkfzs1\nruaSv3kwogBPvemabtgvV9Xv9ckYbMX1fO9MgLiosraPhQ+Uh3rwzKe29bDDJIpF\nXQ9xTGKGGdJ0tyw6jjUuxDmvr/jx00Pob343Z0vVAoGAcpvkGL8xvVkQ0Ucbet3v\ngs3h6p7xuP64WqTLW48iIMdOSPS7mZ+BB706yBGGd8ldjQ72+VVZ27TxJFdf5eNF\nLyrd9eLjFn9mipS7tV1WKQX4oFO8HeISs/AWlEKbhziQRkvIvmpiRsall2nMSyqS\nAScIk4eN/LMaFS0djK16vEA=\n-----END PRIVATE KEY-----\n",
  "client_email": "api-python@pil-associati.iam.gserviceaccount.com",
  "client_id": "117759516401184102852",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/api-python%40pil-associati.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
"""


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

sa = json.loads(googleobj)
pk = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCN1XJ8Ai/nCi5n\nwyXW+tu/jyrRTVz3HypBmPdaqXOtlLij9bhyK4alLleev17KqxxbQWPhqm7rvuWe\nicSyeWexFkb8DPW2mVOXU9lPWXzpcwfZfF0z1D9/cDYuoX/pMfWPeA/yA1bv5KXM\nPW6phjbtU1eeWtTO4AoQnl086O+23dM2gYNe+69nS4qN0GYOBxcS+MDIQJ4Ypivl\norWNMdE9Zd4rQSN3QW18fRBakVIDYjybl3B+9Iz/+3ezRMXxz1aCR3Kjh7JE2Jeb\nbGUEK4lT3NsjCZ/9vKbhP04XpgkTW67HR5TiSRxhP78riF92mgTUx2He8baoPtRp\nUzg1hcrPAgMBAAECggEAJuifq/JDptttqIxp5IRT5USGp/1Tm/1iL7WhYa8rqzop\nvtzpOPTEzqqcYdG41NtE/6m8F0uUezqWrju4CIfykKt+VKXPgESmoFRhwHlZoYcr\nZ5fMz6uRscmcK4WlW9kXNsDmiussncm5TAKsSXgmuEtNNYVQbOIcELwI8u0p2Z2v\nNkdSfFzqR5+cifQ6f40VAqxqBaYMULi1w0Cye1ykK9u8x873zLAk/WWmrQlevqrG\nGO1ueH1C7oKZ7AQRfDnGEorTdEODHhuSrH3UAzQpmPxBeTsLu2yiCzo/AzzFoKQo\nYaGbDUL0q6IeRN4/j5Gly3wH1BlQ5h2VSVyItxCj7QKBgQDFlIxoFui8sm4EhIlp\nOumSzS+kDONqwHnFNGMQRq4hwLkY6xR444xlkpGglvfvT356RZWRt4v8ohhH1Mpq\nJSfb4ihapNUJrwH1d1FzcudHmqryM/on87AxEJOeVWObrapaz5+T+/rlipIJPhh2\n8WA7CPTZ+DvsKNq12RuoNEfJDQKBgQC3xUcBwU0Vto3hmcXwKXmfTVkC2BVmVqDM\nyca5BG2p/29edP+conIPsBIfn3zhuSTJMkfZslhnTdbgzdbthP+sLGo4Tz/rpn7f\ne5Op7BxEyGIYlepa2WjNVNeY0AKxyEnF2xQMVetsZBzbOjNZj6crOepc5ZrCAxNk\nNx/ucfR0SwKBgQDDyuEYhRs9YtQDRhOlY+vyvcJoHx19vB7vfWptxpzodcL3Hn27\nDkMipIwLR4+KZow/PpVpQSpHv5mwFP5BEXDeRM8YhB9Y6URXq1XbwhHOs0aTnU5Y\nKPSAqpyeWp/Ktd4K/5RzYVDQBvGQlyhHNgrWdZmuJn+7FwElE3CEzsoUQQKBgHlp\nKqpsLSNlQoOD9pPesu2eSmponGrKXN4viMz/sfwYOFntblrrr/PRXYfq9LSkfzs1\nruaSv3kwogBPvemabtgvV9Xv9ckYbMX1fO9MgLiosraPhQ+Uh3rwzKe29bDDJIpF\nXQ9xTGKGGdJ0tyw6jjUuxDmvr/jx00Pob343Z0vVAoGAcpvkGL8xvVkQ0Ucbet3v\ngs3h6p7xuP64WqTLW48iIMdOSPS7mZ+BB706yBGGd8ldjQ72+VVZ27TxJFdf5eNF\nLyrd9eLjFn9mipS7tV1WKQX4oFO8HeISs/AWlEKbhziQRkvIvmpiRsall2nMSyqS\nAScIk4eN/LMaFS0djK16vEA=\n-----END PRIVATE KEY-----\n",


print("SA client_email:", sa.get("client_email"))
print("Has literal \\n in private_key:", "\\n" in sa.get("private_key",""))
print("Has real newline in private_key:", "\n" in sa.get("private_key",""))
# Definire l'ambito delle API

print("private_key_id:", sa["private_key_id"])
print("sha256 prefix:", hashlib.sha256(pk.encode()).hexdigest()[:16])
# Fix fondamentale per Railway / env vars (newline nella private_key)
# Caricare le credenziali dal file JSON
#creds = ServiceAccountCredentials.from_json_keyfile_name("pil-associati-4d2dff048ca0.json", scope)
creds = Credentials.from_service_account_info(sa, scopes=[
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
req = Request()
# Autenticazione e connessione al client di Google Sheets
try:
    creds.refresh(req)
    print("Token OK")
except Exception as e:
    print("Refresh error:", e)
exit()

_num_re = re.compile(r'[-+]?\d+(?:[.,]\d+)?')

query_get_products_by_tag = """
query getProductsByTag($query: String!, $first: Int!, $after: String) {
  products(first: $first, after: $after, query: $query) {
    edges {
      cursor
      node {
        id
        title
        tags
        metafield(namespace: "my_fields", key: "prodottofinito") {
          value
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""
'''
# Query GraphQL
query_get_products_by_tag = """
query getProductsByTag($tag: String!, $first: Int, $after: String) {
  products(first: $first, after: $after, query: $tag) {
    edges {
      node {
        id
        title
        tags
       metafield(namespace: "my_fields", key: "prodottofinito") {
          value
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

# Funzione per ottenere prodotti con un certo tag
def get_products_by_tag(tag_list, first=250):
    if isinstance(tag_list, list):
        # Costruisci la query logica
        query_expr = " AND ".join([f"tag:'{t}'" for t in tag_list])
    else:
        query_expr = f"tag:'{tag_list}'"
    variables = {
        "tag": query_expr,
        "first": first
    }
    result = execute_graphql(query_get_products_by_tag, variables)

    if result["data"]["products"]["edges"]:
        products = result["data"]["products"]["edges"]
        #for product in products:
            #print(f"✅ {product['node']['title']} (ID: {product['node']['id']}) - Tags: {product['node']['tags']}")
        return products
    else:
        print(f"❌ Nessun prodotto trovato con il tag '{tag_list}'")
        return None
'''    
def build_tag_query(tag_list, mode="AND"):
    """
    mode: "AND" oppure "OR"
    """
    if isinstance(tag_list, (list, tuple, set)):
        joiner = f" {mode} "
        return joiner.join([f"tag:'{t}'" for t in tag_list])
    return f"tag:'{tag_list}'"


def get_all_products_by_tag(tag_list, first=250, mode="AND"):
    query_expr = build_tag_query(tag_list, mode=mode)

    all_products = []
    after = None

    while True:
        variables = {
            "query": query_expr,
            "first": first,
            "after": after
        }

        result = execute_graphql(query_get_products_by_tag, variables)
        products_conn = result["data"]["products"]

        edges = products_conn["edges"]
        all_products.extend(edges)

        page_info = products_conn["pageInfo"]
        if not page_info["hasNextPage"]:
            break

        after = page_info["endCursor"]

    return all_products

def is_valid_amount(raw) -> bool:
    """
    True se raw rappresenta un importo numerico != 0.
    Esclude '-', ' -', None, stringhe non numeriche e zeri tipo '0', '0.00', '0.00 TWD'.
    Gestisce spazi e valuta attaccata.
    """
    if raw is None:
        return False

    s = str(raw).strip()

    # caso trattino
    if s == '-':
        return False

    # estrai il primo numero dalla stringa (gestisce '0.00 TWD', ' 715.00', ecc.)
    m = _num_re.search(s)
    if not m:
        return False

    num_str = m.group(0).replace(',', '.')  # supporto virgola decimale
    try:
        val = Decimal(num_str)
    except InvalidOperation:
        return False

    return val != 0

def process_prices(df):
    price_data = {}
   
    for index, row in df.iterrows():
        
        # remove currencies
        #row = [str(n).replace('€', '') for n in row]
        #row = [str(n).replace('₩','') for n in row]
        #row = [str(n).replace('HK$','') for n in row]
        #row = [str(n).replace('₽','') for n in row]
        #row = [str(n).replace('¥','') for n in row]
        #row = [str(n).replace('$','') for n in row]
        #row = [str(n).replace('£','') for n in row]
        # remove spaces
        #row = [str(n).replace(' ', '') for n in row]
        # remove k separator
        #row = [str(n).replace('.', '') for n in row]
        # replace comma with point
       #row = [str(n).replace(',', '.') for n in row]
        #print(row)
        #exit()
        
        amountEurIT = row['Italy EUR'].replace('€', '')
        #print(amountEurIT)
        #exit()
        amountEurEU = row['Europe EUR'].replace('€', '')
        amountEurKRW = row['Korea KRW'].replace('₩', '')
        amountEurHK = row['Hong Kong HKD'].replace('HK$', '')
        amountEurCH = row['China RMB'].replace('¥', '')
        amountEurEEU = row[' Khazakistan, Georgia, Ukraina, Bielorussia, Armenia, Azerbaigian, Kirghizistan, Moldavia, Mongolia, Tagikistan, Uzbekistan EUR'].replace('€', '')
        amountEurJP = row['Japan JPY'].replace('¥', '')
        amountEurUSD = row['USA USD'].replace('$', '')
        amountEurUK = row['UK GBP'].replace('£', '')
        amountEurTW = row['TAIWAN TWD'].replace('$', '')
        amountEurTW = amountEurTW.replace('TWD', '')
     

      
        amountEurIT = amountEurIT.replace('.','')
        amountEurEU = amountEurEU.replace('.','')
        amountEurKRW = amountEurKRW.replace('.','')
        amountEurHK = amountEurHK.replace('.','')
        amountEurCH = amountEurCH.replace('.','')
        amountEurEEU = amountEurEEU.replace('.','')
        amountEurJP = amountEurJP.replace('.','')
        amountEurUSD = amountEurUSD.replace('.','')
        amountEurUK = amountEurUK.replace('.','')
        amountEurTW = amountEurTW.replace('.','')

        amountEurIT = amountEurIT.replace(',','.')
        amountEurEU = amountEurEU.replace(',','.')
        amountEurKRW = amountEurKRW.replace(',','.')
        amountEurHK = amountEurHK.replace(',','.')
        amountEurCH = amountEurCH.replace(',','.')
        amountEurEEU = amountEurEEU.replace(',','.')
        amountEurJP = amountEurJP.replace(',','.')
        amountEurUSD = amountEurUSD.replace(',','.')
        amountEurUK = amountEurUK.replace(',','.')
        amountEurTW = amountEurTW.replace(',','.')
       
        price_data[row['PRODOTTO FINITO']] = {
            "price": {
                "amount": amountEurIT,
                "currency": "EUR",
                "plid": "30373773659",
                "country_code" : 'IT'
            },
            "price_eu": {
                "amount": amountEurEU,
                "currency": "EUR",
                "plid": "14367785169",
                "country_code" : 'FR'
            },
            "price_ko": {
                "amount": amountEurKRW,
                "currency": "KRW",
                "plid": "14588805329",
                "country_code" : 'KR'
            },
            "price_cn": {
                "amount": amountEurCH,
                "currency": "CNY",
                "plid": "14588707025",
                "country_code" : 'CN'
            },
            "price_hk": {
                "amount": amountEurHK,
                "currency": "HKD",
                "plid": "14588739793",
                "country_code" : 'HK'
            },
            "price_est": {
                "amount": amountEurEEU,
                "currency": "EUR",
                "plid": "14367817937",
                "country_code" : 'LT'
            },
            "price_jp": {
                "amount": amountEurJP,
                "currency": "JPY",
                "plid": "14588772561",
                "country_code" : 'JP'
            },
            "price_other": {
                "amount": amountEurUSD,
                "currency": "USD",
                "plid": "14356545745",
                "country_code" : 'AU'
            },
            "price_uk": {
                "amount": amountEurUK,
                "currency": "GBP",
                "plid": "14835253457",
                "country_code" : 'GB'
            },
            "price_tw": {
                "amount": amountEurTW,
                "currency": "TWD",
                "plid": "31715819867",
                "country_code" : 'TW'
            }
        }
    return price_data


# Definire l'ambito delle API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

sa = json.loads(os.environ["GOOGLE_SA_JSON"])
# Fix fondamentale per Railway / env vars (newline nella private_key)
sa["private_key"] = sa["private_key"].replace("\\n", "\n")
# Caricare le credenziali dal file JSON
#creds = ServiceAccountCredentials.from_json_keyfile_name("pil-associati-4d2dff048ca0.json", scope)
creds = Credentials.from_service_account_info(sa, scopes=[
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
# Autenticazione e connessione al client di Google Sheets
client = gspread.authorize(creds)

# Apertura del foglio di calcolo tramite l'ID
spreadsheet = client.open_by_key('1xbS99GN35XFNdLNmHFC0jjRNnqCm9AOEpLAQJinE9KQ')

# Lettura di un foglio specifico
worksheet = spreadsheet.worksheet("SS26")  
data = worksheet.get_all_values()

headers = data[0]
rows = data[1:]

df = pd.DataFrame(rows, columns=headers)
#print(df)
#exit()
# Stampare i dati
#for row in data:
    #print(row)
    #exit()


with open("./config.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    shopify = Sh(cfg['premiata']['shopify'])

# Configurazione
SHOPIFY_STORE_URL = 'https://'+cfg['premiata']['shopify']['shop_url']  # Sostituisci con il tuo URL
API_VERSION = cfg['premiata']['shopify']['version']  # Usa la versione più recente dell'API
ACCESS_TOKEN = cfg['premiata']['shopify']['token']  # Sostituisci con il tuo token
#METAOBJECT_DEFINITION_ID = "gid://shopify/MetaobjectDefinition/17010622730"  # metaobjectfatture
GRAPHQL_ENDPOINT = f"{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/graphql.json"

# Intestazioni per la richiesta
headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": ACCESS_TOKEN
}

# Funzione per eseguire una query o mutation GraphQL
def execute_graphql(query, variables=None):
    payload = {"query": query, "variables": variables or {}}
    response = requests.post(GRAPHQL_ENDPOINT, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Errore GraphQL: {response.status_code} - {response.text}")


#prices = pd.read_csv('./geo_fw24_agg.csv', sep=';', header=None)
prices = process_prices(df)
prods = get_all_products_by_tag(["price230226_3"], mode="AND")


#prods = shopify.get_all_products()
#shopify.updateTag(prods, 'changefw22prices_u2')
#exit()
print('in totale fetchati ' +str(len(prods)))
for pr in prods:
                print(pr['node']['metafield']['value'])
    #if('price110325_2' in p.tags):
        
        #for m in p.metafields():
            #if(m.key == 'prodottofinito'):
                
                if(pr['node']['metafield']['value'] in prices):
                    p = shopify.get_prod(pr['node']['id'].split("/")[-1])
                    price_obj = prices[pr['node']['metafield']['value']]
                    #print(price_obj)
                    #exit()
                 
                    for k in price_obj.keys():
                        po = []
                        
                        if(k == 'price'):
                            for v in p.variants:
                                if(price_obj['price']['amount'] == ''):
                                    print('[\] No price found for product ' + pr['node']['metafield']['value']) # type: ignore
                                    continue
                                if(float(v.price) != float(price_obj['price']['amount'])):
                                    v.price = price_obj['price']['amount']
                                    v.save()
                                    print('Updated product ' + str(p.id) + ' - ' + pr['node']['metafield']['value'] + ' -> ' + 'ITALY')

                        
                            #continue
                        #if(price_obj[k]['amount'] != '-'):
                        if is_valid_amount(price_obj[k]['amount']):
                         for v in p.variants:
                                
                                actualpriceobj = shopify.GetContextPriceForProduct(v.id,price_obj[k]['country_code'])
                                actualprice = actualpriceobj['data']['productVariant']['contextualPricing']['price']['amount']
                                if(price_obj['price']['amount'] == ''):
                                    print('[\] No price found for product ' + pr['node']['metafield']['value']) # type: ignore
                                    continue
                                if(float(price_obj[k]['amount']) != float(actualprice)):
                                    po.append({
                                        'price': {
                                            'amount': price_obj[k]['amount'],
                                            'currencyCode': price_obj[k]['currency']
                                        },
                                        'variantId': 'gid://shopify/ProductVariant/' + str(v.id)
                                    })
                                #else:
                                    #print('il prodotto '+m.value+ ' del listino '+k+' non ha variazione di prezzo, non lo aggiorno')
                         if(po):
                            print('[] Updating product ' + str(p.id) + ' - ' + pr['node']['metafield']['value'] + ' -> ' + k)
                            shopify.update_price(price_obj[k]['plid'], po)
                            time.sleep(0.5)
                         
                    
                
                else:
                    print('[\] No price found for product ' + pr['node']['metafield']['value']) # type: ignore
    
