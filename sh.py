from pathlib import Path
import shopify
import hashlib
import json


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class Sh:
    def __init__(self, cfg):
        # set shopify site
        self.endpoint = (
            "https://"
            + cfg["api_key"]
            + ":"
            + cfg["token"]
            + "@"
            + cfg["shop_url"]
            + "/admin"
        )
        self.location_id = cfg["location_id"]
        self.api_version = cfg["version"]
        self.shop_url = cfg["shop_url"]
        self.token = cfg["token"]
        self.api_key = cfg["api_key"]

        shopify.ShopifyResource.set_site(self.endpoint)

    def create_product(self, product_data):

        print(
            bcolors.OKBLUE
            + "[#] Creating product "
            + product_data["sku"]
            + bcolors.ENDC
        )

        new_prod = shopify.Product()

        new_prod.title = product_data["title"]
        new_prod.sku = product_data["sku"]
        new_prod.weight = product_data["weight"]
        # new_prod.handle = product_data['handle']
        new_prod.product_type = "Shoes"
        new_prod.status = "draft"
        new_prod.body_html = " "  # product_data['descr']
        new_prod.tags = product_data["tags"]
        new_prod.published_scope = "global"
        new_prod.vendor = product_data["vendor"]

        success = new_prod.save()
        if not success:
            print(
                bcolors.FAIL
                + "[-] Product error -> "
                + str(new_prod.errors.full_messages())
                + bcolors.ENDC
            )
            return

        print(bcolors.OKCYAN + "[+] Shopify product added" + bcolors.ENDC)

        # SET METAFIELDS

        try:
            # self.set_metafields(new_prod.id, product_data)
            self.set_metafields_m885(new_prod.id, product_data)
            print(bcolors.OKCYAN + "[+] Metafields added" + bcolors.ENDC)
        except Exception as e:
            print(
                bcolors.FAIL
                + "[-] Setting metafields error -> "
                + str(e)
                + bcolors.ENDC
            )

        # SET IMAGES
        images = product_data["images"].replace(" ", "").split(",")
        for img in images:

            try:
                image_path = "images/" + img
                image_name = img.split(".")[0]
                image_position = image_name.split("_")[1]
            except:
                print(
                    bcolors.WARNING
                    + "[-] Image not found -> "
                    + image_name
                    + bcolors.ENDC
                )

            try:
                self.set_product_image(new_prod.id, image_path, image_position)
                print(
                    bcolors.OKCYAN
                    + "[+] Image "
                    + str(image_position)
                    + " setted"
                    + bcolors.ENDC
                )
            except:
                print(
                    bcolors.WARNING
                    + "[-] Setting image error -> "
                    + image_name
                    + bcolors.ENDC
                )

        return new_prod.id

    def get_all_products(self, limit=100):
        get_next_page = True
        since_id = 0
        while get_next_page:
            products = shopify.Product.find(since_id=since_id, limit=limit)
            """status='active"""
            for product in products:
                yield product
                since_id = product.id

            if len(products) < limit:
                get_next_page = False

    def getcolletionProducts(self, products, limit=100):
        get_next_page = True
        since_id = 0
        while get_next_page:
            products = products

            for product in products:
                yield product
                since_id = product.id

            if len(products) < limit:
                get_next_page = False

    def getCollection(self, id):
        return shopify.SmartCollection.find(id)

    def check_all_images(self):
        for p in self.get_all_products():
            if p and not p.images:
                for var in p.variants:
                    v = shopify.Variant.find(var.id)
                    print(v.sku.split(" ")[0] + "-" + var.option2)
                    break

    def get_customers(self, limit=100):
        get_next_page = True
        since_id = 0
        while get_next_page:
            customers = shopify.Customer.find(since_id=since_id, limit=limit)

            for customer in customers:
                yield customer
                since_id = customer.id

            if len(customers) < limit:
                get_next_page = False
    
    def searchCustomer(self, stringa):
        results = shopify.Customer.search(query=stringa)
        return results
    
    def remove_product_image(self, shid):
        prod = shopify.Product.find(shid)
        prod.images = []
        prod.save()


    def set_product_image(self, shid, image_path, position):
       
        image = shopify.Image()
        image.product_id = shid
        image.position = position
        image.alt = image_path
        prod = shopify.Product.find(shid)
        with open(image_path, "rb") as f:
            filename = image_path.split("/")[-1][0]
            encoded = f.read()
            image.attach_image(encoded, filename=filename)
       
        prod.images.append(image)
        prod.save()

    def get_all_orders(self):
        orders = shopify.Order.find(status="any")
        return orders

    def create_variant(self, shid, sku, price, option1, option2):
        p = shopify.Product.find(shid)

        if len(p.variants) < 2 and (
            p.variants[0].option1 == "Default Title" or p.variants[0].option1 == "14.5"
        ):
            p.options = [{"name": "Size"}, {"name": "Color"}]
            var = shopify.Variant()

            var.option1 = option1
            var.option2 = option2
            var.sku = sku + " " + str(option1)
            var.price = float(price)
            var.fullfilment_service = "manual"
            var.inventory_management = "shopify"
            var.requires_shipping = True
            p.variants = [var]
            p.save()

        else:

            var = shopify.Variant()
            var.option1 = option1
            var.option2 = option2
            var.sku = sku + " " + str(option1)
            var.price = price
            var.fullfilment_service = "manual"
            var.inventory_management = "shopify"
            var.requires_shipping = True

            # attach variant
            p.variants.append(var)
            p.save()

        # return variant id
        for x in p.variants:
            if x.option1 == option1:
                return x.id
        return False

    def check_variant_exist(self, prod, option1):
        for v in prod.variants:
            if v.option1 == option1: #and v.option2 == option2:
                return v
        return False

    def get_prod(self, shid):
        p = shopify.Product.find(shid)
        return p

    def get_var(self, varid):
        v = shopify.Variant.find(varid)
        return v

    def set_product_type(self, types_data):
        for p in self.get_all_products():
            for index, row in types_data.iterrows():
                if row["name"] in p.title:
                    p.product_type = row["type"]
                    p.save()

    def set_metafields(self, shid, product_data):
        prod = shopify.Product.find(shid)
        
       
        prod.add_metafield(
                shopify.Metafield(
                    {
                        "key": "discount_miinto_price",
                        "value": product_data,
                        "type": "decimal",
                        "namespace": "my_fields",
                    }
                )
            )
        """prod.add_metafield(
            shopify.Metafield(
                {
                    'key': 'Forma',
                    'value': product_data['shape'],
                    'type': 'single_line_text_field',
                    'namespace': 'ftmeta'
                }
            )
        )
        
        if product_data["material"]:
            prod.add_metafield(
                shopify.Metafield(
                    {
                        "key": "Material",
                        "value": product_data["material"],
                        "type": "single_line_text_field",
                        "namespace": "ftmeta",
                    }
                )
            )
        if product_data["model"]:
            prod.add_metafield(
                shopify.Metafield(
                    {
                        "key": "Model",
                        "value": product_data["model"],
                        "type": "single_line_text_field",
                        "namespace": "ftmeta",
                    }
                )
            )
        """
        prod.save()

    def set_metafields_m885(self, shid, product_data):
        prod = shopify.Product.find(shid)
        if product_data["pcode"]:
            prod.add_metafield(
                shopify.Metafield(
                    {
                        "key": "prodottofinito",
                        "value": product_data["pcode"],
                        "type": "single_line_text_field",
                        "namespace": "my_fields",
                    }
                )
            )
        if product_data["4d"]:
            prod.add_metafield(
                shopify.Metafield(
                    {
                        "key": "codice_4d",
                        "value": product_data["4d"],
                        "type": "single_line_text_field",
                        "namespace": "my_fields",
                    }
                )
            )
        if product_data["hs"]:
            prod.add_metafield(
                shopify.Metafield(
                    {
                        "key": "hs",
                        "value": product_data["hs"],
                        "type": "single_line_text_field",
                        "namespace": "my_fields",
                    }
                )
            )
        if product_data["combination"]:
            prod.add_metafield(
                shopify.Metafield(
                    {
                        "key": "abbinamento",
                        "value": product_data["combination"],
                        "type": "single_line_text_field",
                        "namespace": "my_fields",
                    }
                )
            )
        prod.save()

    def get_product_images(self, shid):
        p = shopify.Product.find(shid)
        return p.images

    def add_metafield(self, shid, key, ptype, value):
        prod = shopify.Product.find(shid)
        prod.add_metafield(
            shopify.Metafield(
                {"key": key, "value": value, "type": ptype, "namespace": "global"}
            )
        )
        prod.save()

    def reset_variants(self, shid):
        p = shopify.Product.find(shid)
        var_ids = []
        for v in p.variants:
            var_ids.append("gid://shopify/ProductVariant/" + str(v.id))
        self.remove_variants(shid, var_ids)

    def get_variant_id(self, conf_shid, variant_size):
        conf = shopify.Product.find(str(conf_shid))

        for var in conf.variants:
            variant = shopify.Variant.find(var.id)
            if variant.option1 == variant_size:
                return variant.id
        return None

    def get_inventory_items_id(self, shid):
        p = shopify.Product.find(shid)
        # for v in p.
        # return var.inventory_item_id

    def get_inventory_item_id(self, var_shid):
        var = shopify.Variant.find(var_shid)
        return var.inventory_item_id

    def remove_variant(self, variant_id):
        #if not shid or len(variants_id) < 1:
            #return
        
        #p = shopify.Product.find(shid)
        document = Path("./queries.graphql").read_text()
        query_data = {
            "id": "gid://shopify/ProductVariant/" + str(variant_id)
        }
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="productVariantDelete",
            )
        )

        if not result["data"]["productVariantDelete"]["userErrors"]:
            print(bcolors.OKBLUE + "[+] Variant removed" + bcolors.ENDC)
        else:
            print(
                bcolors.FAIL
                + "Error while removing variants: "
                + str(result["data"]["productVariantDelete"]["userErrors"])
                + bcolors.ENDC
            )

    def remove_variants(self, shid, variants_id):
        #if not shid or len(variants_id) < 1:
            #return
        
        p = shopify.Product.find(shid)
        document = Path("./queries.graphql").read_text()
        query_data = {
            "productId": "gid://shopify/Product/" + str(p.id),
            "variantsIds": variants_id,
        }
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="productVariantsBulkDelete",
            )
        )

        if not result["data"]["productVariantsBulkDelete"]["userErrors"]:
            print(bcolors.OKBLUE + "[+] Variants removed" + bcolors.ENDC)
        else:
            print(
                bcolors.FAIL
                + "Error while removing variants: "
                + str(result["data"]["productVariantsBulkDelete"]["userErrors"])
                + bcolors.ENDC
            )

    def getProdInventoryId(self, shid):
        if not shid:
            return
       
        document = Path("./queries.graphql").read_text()
        query_data = {
            "id": "gid://shopify/Product/" + str(shid),
        }
       
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="ProductVariantDetails",
            )
        )

        return result
    
    def get_product_id_by_metafield(self, namespace, key, value):
        
        #document = Path("./queries.graphql").read_text()
       
        query_data = {
            "namespace": str(namespace),
            "key": str(key),
            "value": str(value)
        }
       
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                 # Costruzione dinamica della query
    query = f"""
    query {{
      products(first: 1, query: "metafield:{namespace}.{key}:{value}") {{
        edges {{
          node {{
            id
            title
            status
          }}
        }}
      }}
    }}
    """,
                variables=query_data
                #operation_name="get_product_id_by_metafield",
            )
        )
        
        return result['data']

    def update_stock(self, inv_id, qty):
        # time.sleep(0.5)
      
        try:
            inv_l = shopify.InventoryLevel.set(self.location_id, inv_id, qty)
            return inv_l.available == qty
        except:
            return False

    def adjust_stock(self, data):

        document = Path("./queries.graphql").read_text()

        query_data = {
            "inventoryItemAdjustments": [],
            "locationId": "gid://shopify/Location/" + self.location_id,
        }

        for el in data:
            query_data["inventoryItemAdjustments"].append(
                {
                    "availableDelta": el["qty"],
                    "inventoryItemId": "gid://shopify/InventoryItem/"
                    + str(el["inv_id"]),
                }
            )

        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="inventoryBulkAdjustQuantityAtLocation",
            )
        )

        if not result["data"]["inventoryBulkAdjustQuantityAtLocation"]["userErrors"]:
            print(bcolors.OKBLUE + "[+] Variant updated" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + "Error while updating stock" + bcolors.ENDC)

    def updateMetafieldGQ(self, data):

        document = Path("./queries.graphql").read_text()

      
        # Struttura per la query
       
        query_data = {
            
             "metafields": [
    {
                "namespace": data["namespace"],
                "key": data["key"],
                "value": str(data["value"]),
                "type": data["type"],
                "ownerId": data["owner_id"],
    }
  ]
                }
       

        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="MetafieldsSet",
            )
        )
       
        # Gestione dei risultati
        if not result["data"]["metafieldsSet"]["userErrors"]:
            print("[+] Metafield aggiornato con successo.")
        else:
            print("[-] Errore nell'aggiornamento del metafield:")
            print(result["data"]["metafieldsSet"]["userErrors"])

    def update_price(self, price_list_id, prices):
        document = Path("./queries.graphql").read_text()

        query_data = {
            "priceListId": "gid://shopify/PriceList/" + price_list_id,
            "prices": prices,
        }

        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="priceListFixedPricesAdd",
            )
        )

        # print(result)

        if not result["data"]["priceListFixedPricesAdd"]["userErrors"]:
            print(bcolors.OKBLUE + "[+] Variant price updated" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + "Error while updating stock price" + bcolors.ENDC)

    def GetContextPriceForProduct(self, id, country):
        document = Path("./queries.graphql").read_text()

        query_data = {
            "id": "gid://shopify/ProductVariant/" + str(id),
            "country": country,
        }

        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="GetContextPriceForProduct",
            )
        )

        return result


    def get_maket_plid(self, id):
        query = (
            'query { market(id: "gid://shopify/Market/'
            + str(id)
            + '") { priceList { id } } } '
        )
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)
        result = shopify.GraphQL().execute(query=query)
        print(result)

    def update_translationTitle(self, shid, l_code, title_old, title):

        digest_title = hashlib.sha256(title_old.encode("utf-8")).hexdigest()
       

        document = Path("./queries.graphql").read_text()

        query_data = {
            "id": "gid://shopify/Product/" + shid,
            "translations": [
                {
                    "key": "title",
                    "value": title,
                    "locale": l_code,
                    "translatableContentDigest": digest_title,
                }
            ],
        }
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        try:
            result = json.loads(
                shopify.GraphQL().execute(
                    query=document,
                    variables=query_data,
                    operation_name="CreateTranslation",
                )
            )
        except:
            print(bcolors.FAIL + "Error while updating translation" + bcolors.ENDC)
            return

        # print(result)

        if not result["data"]["translationsRegister"]["userErrors"]:
            print(bcolors.OKBLUE + "[+] Product translation updated" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + "Error while updating translation" + bcolors.ENDC)
 
    def update_translationDesc(self, shid, l_code, text_old, text):

        digest_text = hashlib.sha256(text_old.encode("utf-8")).hexdigest()

        document = Path("./queries.graphql").read_text()

        query_data = {
            "id": "gid://shopify/Product/" + shid,
            "translations": [
                {
                    "key": "body_html",
                    "value": text,
                    "locale": l_code,
                    "translatableContentDigest": digest_text,
                }
            ],
        }
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        try:
            result = json.loads(
                shopify.GraphQL().execute(
                    query=document,
                    variables=query_data,
                    operation_name="CreateTranslation",
                )
            )
            
        except:
           
            print(bcolors.FAIL + "Error while updating translation" + bcolors.ENDC)
            return

        

        if not result["data"]["translationsRegister"]["userErrors"]:
            print(bcolors.OKBLUE + "[+] Product translation updated" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + "Error while updating translation" + bcolors.ENDC)

    def update_product_status(self, product_id, status):
        # Leggi la mutation dal file queries.graphql
        document = Path("./queries.graphql").read_text()

        # Prepara i dati della query
        query_data = {
            "productId": "gid://shopify/Product/" + product_id,
            "status": status,
        }

        # Attiva la sessione Shopify
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        try:
            # Esegui la mutation
            result = json.loads(
                shopify.GraphQL().execute(
                    query=document,
                    variables=query_data,
                    operation_name="UpdateProductStatus",
                )
            )
            
        except Exception as e:
            print(f"Error while updating product status: {e}")
            return

        # Controlla il risultato
        if not result["data"]["productUpdate"]["userErrors"]:
            print("[+] Product status updated successfully")
        else:
            errors = result["data"]["productUpdate"]["userErrors"]
            for error in errors:
                print(f"Error: {error['message']}")

    def update_translationTitle(self, shid, l_code, title_old, title):

        digest_title = hashlib.sha256(title_old.encode("utf-8")).hexdigest()
       

        document = Path("./queries.graphql").read_text()

        query_data = {
            "id": "gid://shopify/Product/" + shid,
            "translations": [
                {
                    "key": "title",
                    "value": title,
                    "locale": l_code,
                    "translatableContentDigest": digest_title,
                }
            ],
        }
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        try:
            result = json.loads(
                shopify.GraphQL().execute(
                    query=document,
                    variables=query_data,
                    operation_name="CreateTranslation",
                )
            )
        except:
            print(bcolors.FAIL + "Error while updating translation" + bcolors.ENDC)
            return

        # print(result)

        if not result["data"]["translationsRegister"]["userErrors"]:
            print(bcolors.OKBLUE + "[+] Product translation updated" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + "Error while updating translation" + bcolors.ENDC)
 
    def update_translationPcare(self, mid, l_code, text_old, text):

        digest_text = hashlib.sha256(text_old.encode("utf-8")).hexdigest()

        document = Path("./queries.graphql").read_text()

        query_data = {
            "id": "gid://shopify/Metafield/" + mid,
            "translations": [
                {
                    "key": "product_care",
                    "value": text,
                    "locale": l_code,
                    "translatableContentDigest": digest_text,
                }
            ],
        }
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        try:
            result = json.loads(
                shopify.GraphQL().execute(
                    query=document,
                    variables=query_data,
                    operation_name="CreateTranslation",
                )
            )
            print(result)
        except:
            print(result)
            #print(bcolors.FAIL + "Error while updating translation" + bcolors.ENDC)
            return

        

        if not result["data"]["translationsRegister"]["userErrors"]:
            print(bcolors.OKBLUE + "[+] Product translation updated" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + "Error while updating translation" + bcolors.ENDC)
    ##


    def getMetafield(self, id):
        return shopify.Metafield.find(id)

    def set_product_position(self, collection_id, product_id, position):

        document = Path("./queries.graphql").read_text()

        query_data = {
            "id": "gid://shopify/Collection/" + collection_id,
            "moves": {
                "id": "gid://shopify/Product/" + product_id,
                "newPosition": position,
            },
        }
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="collectionReorderProducts",
            )
        )
        return
        print(result)

        if not result["data"]["collectionReorderProducts"]["userErrors"]:
            print(bcolors.OKBLUE + "[+] Product translation updated" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + "Error while updating translation" + bcolors.ENDC)

    def test(self):
        ps = shopify.Order.find(order="order_number asc", status="any")
        for p in ps:
            print(p.name)

    def get_order_id_by_name(self, order_name):

            # Legge la query GraphQL dal file queries.graphql
        document = Path("./queries2.graphql").read_text()

        # Variabili da passare alla query
        query_data = {
            "orderName": order_name  # Assicurati che sia nel formato corretto, es: "#1001"
        }

        # Attiva la sessione Shopify
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        # Esegue la query GraphQL
        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="getOrderIdByName",  # Assicurati che il nome dell'operazione sia corretto
            )
        )
       
        # Controlla se ci sono risultati validi
        if result.get("data") and result["data"]["orders"]["edges"]:
            gid = result["data"]["orders"]["edges"][0]["node"]["id"]
            order_id = gid.split("/")[-1]  # Estrae solo l'ID numerico
            return order_id
        else:
            print("[-] Order not found")
            return None
    

    def updateStatus(self, prods, status):
        prod = ["STED6942",
"STED6483",
"STED6485",
"BEL07042",
"MASD7004",
"MASD7009",
"MASD7096",
"CON07076"]
        for p in prods:

            for m in p.metafields():
                if m.key == "prodottofinito" and m.value in prod:
                   # if 'saldi2023' not in p.tags :
                        p.status = status
                        p.save()
                        print("[+] prodotto elaborato " + m.value)

    def checkStatus(self, prods, status):
        prod = [
"BEB0019V",
"BEB0008V",
"BEB0014V",
"BEB0034V",
"BEB0013V",
"DIVB2029",
"DIVB2031",
"LUCV1868",
"LUCV1869",
"ROBB2032",
"SKYB9351",
"SKYB9356",
"SKYB9368",
"SKYB9367",
"SKYV9353",
"SKYV9357",
"SKYV9358",
"SKYV9359",
"SKYV9369",
"WALV1856",
"M6698A",
"M6780B",
"M6781B",
"BOED6767",
"BOED6772",
"BSKD6780",
"BSK06775",
"BSK06779",
"32080D",
"32156G",
"32161A",
"32161B",
"BEL06278",
"BET05603",
"CAS06341",
"CAS06719",
"CAS06720",
"ERI05669",
"ERI05670",
"LUC06603",
"LUC07089",
"MAS06621",
"MAS06626",
"MIL06794",
"MIL06829",
"NOU06655",
"NOU06658",
"BLA2119",
"BLA2121",
"LIG2124",
"VEN2127",
"WON2125",
"DRA00299",
"DRA00352",
"DRAD0298",
"MOE06726",
"MOE06731",
"MOE06732",
"MOED6737",
"RYA06815",
"RYA06817",
"SHA00360",
"SHA00361",
"SHA00362",
"STE06645",
"STED6659",
"ERI06141",
"MAS06627",
"SHAD0288",
"LYN2100",
"BOO2103",
"32050E",
"BSK06778",
"BETHCS",
"LAN4586B",
"BOED6766",
"MIL07014",
"PACBAL06",
"PACBAL08",
"BLA2120",
"PACBAL07",
"STE06652"
 ]
        for p in prods:

            for m in p.metafields():
                if m.key == "prodottofinito" and m.value in prod:
                   # if 'saldi2023' not in p.tags :
                        p.status = status
                        p.save()
                        print("[+] prodotto elaborato " + m.value)


    def updateTag(self, prods, tag):
        prod = ["PACBAL11",
"M6917B",
"M6941A",
"M6942A",
"M6946A",
"M6964A",
"M6966F",
"M7006A",
"M7007B",
"BOE07341",
"BSKD7309",
"BSKD7317",
"BSKD7320",
"BSKD7515",
"32156M",
"32156ZB",
"32164C",
"32261B",
"32266A",
"32269C",
"32269A",
"32271A",
"32272B",
"32274A",
"32288A",
"JAC07495",
"JAC07496",
"JAC07497",
"JAC07498",
"JAC07499",
"LAN07204",
"LAN07206",
"LAN07207",
"LAU07479",
"MAS07087",
"MAS07235",
"MAS07238",
"MASD7400",
"MIK07209",
"MIK07244",
"MIL07442",
"MIL07446",
"DRA00400",
"MOE07299",
"MOE07303",
"QUI07322",
"QUI07324",
"QUI07325",
"QUI07500",
"QUID7422",
"RYA07329",
"RYA07331",
"SHA00409",
"STE07503",
"STE07535",
"ANDB9330",
"M6780A",
"BOE06758",
"BOE06759",
"BOE06762",
"BOE06763",
"BSKD6783",
"BSK06777",
"32050D",
"32102Z",
"32154C",
"32166A",
"32166B",
"CAS06346",
"MAS05684",
"MASD5661",
"MASD6681",
"MASD6682",
"MIL06788",
"MIL06795",
"NOU06698",
"NOU06699",
"MOED6736",
"QUI06686",
"RYA06818",
"STE06652",
"STED6667",
"ERI06142",
"32050A",
"STE06970",
"BEL06283",
"STE05439",
"M6732H"]
        for p in prods:
            #if(p.status != 'active'):
                     #continue
            #print('sto elaborando il prodotto' + p.title)         
            for m in p.metafields():
               #print('elaboro prodotto '+ p.title)
                if m.key == "prodottofinito" and m.value in prod:
                    #if 'miinto' in p.tags :
                      #if 'fw24' in p.tags:
                        p.tags += "," + tag
                        p.save()
                        print("[+] prodotto elaborato " + p.title)
                


    def uploadImageforMetafield(self,urlimage,codeimage):
        
        document = Path("queries2.graphql").read_text()

        query_data = {
            "files": {
                "alt": str(codeimage),
                "contentType": "IMAGE",
                "originalSource": urlimage,
            }
        }
        
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        result = json.loads(
            shopify.GraphQL().execute(
                query=document, variables=query_data, operation_name="fileCreate"
            )
        )
       
        '''
        created_at = result["data"]["fileCreate"]["files"][0]["createdAt"]
        
        result2 = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables={"created_at": created_at},
                operation_name="getfileurl",
            )
        )
        img_url = result2["data"]["files"]["edges"][0]["node"]["image"]["url"]
        return img_url
        '''
      
    def checkLastFiles(self,filename):
        document = Path("queries2.graphql").read_text()
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)
        
        result2 = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables={"query": "filename:" + filename},
                operation_name="getfileurl",
            )
        )
        try:
            img_url = result2["data"]["files"]["edges"][0]["node"]["image"]['url']
            return img_url
        except:
            print('non ho trovato la foto per il nome '+filename )

    def get_orders_from(self, dtmin, dtmax, limit=100):
        get_next_page = True
        since_id = 0
        while get_next_page:
            orders = shopify.Order.find(since_id=since_id, created_at_min=dtmin, created_at_max=dtmax, limit=limit, status='any')

            for order in orders: # type: ignore
                yield order
                since_id = order.id

            if len(orders) < limit:
                get_next_page = False

    def add_product_tag(self, product_id, new_tag):
        # Legge la query GraphQL dal file queries.graphql
        document = Path("./queries.graphql").read_text()

        # Creazione della sessione Shopify
        session = shopify.Session(self.shop_url, self.api_version, self.token)
        shopify.ShopifyResource.activate_session(session)

        # Ottenere i tag attuali del prodotto
        query_get_tags = """
        query getProductTags($id: ID!) {
        product(id: $id) {
            tags
        }
        }
        """
        
        result_tags = json.loads(
            shopify.GraphQL().execute(
                query=query_get_tags,
                variables={"id": "gid://shopify/Product/" + product_id}
            )
        )

        if "data" in result_tags and result_tags["data"]["product"]:
            current_tags = result_tags["data"]["product"]["tags"]
        else:
            print("[-] Error retrieving current tags")
            return

        # Aggiungere il nuovo tag alla lista senza duplicati
        updated_tags = list(set(current_tags + [new_tag]))

        # Costruzione del payload per aggiornare i tag del prodotto
        query_data = {
            "id": "gid://shopify/Product/" + product_id,
            "tags": updated_tags
        }

        # Esegue la mutation per aggiornare i tag
        result = json.loads(
            shopify.GraphQL().execute(
                query=document,
                variables=query_data,
                operation_name="addTagToProduct"
            )
        )

        # Verifica il risultato
        if not result["data"]["productUpdate"]["userErrors"]:
            print(f"[+] Tag '{new_tag}' aggiunto al prodotto {product_id}")
        else:
            print("[-] Errore durante l'aggiornamento dei tag")
    