import requests
import json
import os
from mondialrelay_pyt import make_shipping_label
import logging

class WixToMR():
    def __init__(self):
        path = os.path.realpath(__file__) 
        dir = os.path.dirname(path) 
        dir_config = dir.replace('sources', 'config')
        dir_tokens = dir.replace('sources', 'tokens')

        # Lecture des informations sur l'expéditeur, stockées dans un json
        with open(dir_config + '/informations_expediteur.json') as f:
            self.infos_expe = json.load(f)

        # Lecture des informations sur la collecte et le mode de livraison, stockées dans un json
        with open(dir_config + '/informations_collecte_et_mode_de_livraison.json') as f:
            self.infos_collecte_mode_livraison = json.load(f)

        # Lecture des tokens pour l'API Wix
        with open(dir_tokens + '/wix_account_id.token') as f:
            wix_account_id=f.read().strip('\n')
        with open(dir_tokens + '/wix_api_key.token') as f:
            wix_api_key=f.read().strip('\n')

        # Lecture des tokens pour l'API Mondial Relay
        with open(dir_tokens + '/mr_enseigne.token') as f: 
            self.mr_enseigne=f.read().strip('\n')
        with open(dir_tokens + '/mr_private_key.token') as f:
            self.mr_private_key=f.read().strip('\n')

        # Récupération des site_id 
        url = 'https://www.wixapis.com/site-list/v2/sites/query'

        self.headers = {'Content-Type': 'application/json',
                'Authorization': wix_api_key,
                'wix-account-id': wix_account_id
                }

        response = requests.post(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Impossible de récupérer les informations de sites Wix")
        
        self.sites = response.json()['sites']
        self.choisir_site(0) 

    # Selection du site Wix
    def choisir_site(self, n):
        self.site_id = self.sites[n]['id']

        # On ajoute (ou met à jour) le site_id au Headers de la requete
        self.headers['wix-site-id'] = self.site_id

    # Récupération de la liste des commandes à envoyer
    def recuperer_commandes_wix(self):
        url = 'https://www.wixapis.com/ecom/v1/orders/search'

        # Requète permettant de récupérer les commande non envoyées
        query = '{"search":{"filter": {"$or": [{"fulfillmentStatus": "NOT_FULFILLED"}, {"fulfillmentStatus": "PARTIALLY_FULFILLED"}]}, "sort":[{"fieldName": "dateCreated"}, {"order": "DESC"}]}}'

        response = requests.post(url, headers=self.headers, data=query)
        if response.status_code != 200:
            raise Exception("Impossible de récupérer les commandes en attente chez Wix")
        
        json_response = response.json()

        print(json_response['orders'][0])

        # On filtre les commandes pour ne garder que celles avec Mondial Relay comme mode de livraison
        self.mr_orders = [order for order in json_response['orders'] if ('shippingInfo' in order and order['shippingInfo']['title'].startswith("MONDIAL RELAY"))]

    # Traitement d'une commande : téléchargement du bon Mondial Relay + MAJ infos livraisons chez Wix
    def traiter_commande(self, order_number):
        # On récupère la commande demandée
        try:
            order = [order for order in self.mr_orders if order['number']==order_number][0]
        except:
            raise IndexError("Ce numéro de commande n'existe pas dans la liste des commandes en attente : " + str(order_number))
        
        logging.info(f"Traitement commande N°{order['number']} - {order['billingInfo']['contactDetails']['firstName']} {order['billingInfo']['contactDetails']['lastName']}")

        dico = self.creer_dictionnaire_MR(order)
        logging.debug(dico)

        items_to_fulfill = self.creer_items_fuflfillment(order)
        logging.debug("items to fulfill : " + str(items_to_fulfill))

        # Création étiquette Mondial Relay
        req_mr = make_shipping_label(dico)
        logging.debug(req_mr)

        # # Téléchargement du pdf contenant l'étiquette
        etiquette = requests.get(req_mr['Url'])
        open(f"etiquette_{req_mr['ShipmentNumber']}.pdf", "wb").write(etiquette.content)

        # Mise à jour des informations Wix sur la livraison
        url = 'https://www.wixapis.com/ecom/v1/fulfillments/orders/' + order['id'] + '/create-fulfillment' 
        query =  '{"fulfillment": {"lineItems": ' + json.dumps(items_to_fulfill) + ',"trackingInfo": {"shippingProvider": "Mondial Relay", "trackingNumber": "' + str(req_mr['ShipmentNumber']) + '"}}}' # à vérifier !!
        
        response = requests.post(url, headers=self.headers, data=query) 
        if response.status_code != 200:
            raise Exception(f"Impossible de mettre à jour le status de la commande {order['number']}")
        
        order['traitementOK'] = True

    # Création du dictionnaire à destination de MRWebService
    def creer_dictionnaire_MR(self, order):
        dico = {}        

        dico['Login'] = self.mr_enseigne + 'BDTEST@business-api.mondialrelay.com'   # à vérifier !
        dico['Password'] = self.mr_private_key
        dico['CustomerId'] = self.mr_enseigne
        dico['Culture'] = 'fr-FR'
        dico['OutputFormat'] = '10x15'

        dico['OrderNo'] = str(order['number'])
        dico['DeliveryMode'] = self.infos_collecte_mode_livraison['ModeLiv']
        dico['DeliveryLocation'] = order['shippingInfo']['code'][5:]
        dico['CollectionMode'] = self.infos_collecte_mode_livraison['ModeCol']
        dico['ParcelWeight'] = str(int(float(order['totals']['weight']) * 1000))

        dico['SenderStreetname'] = self.infos_expe['ExpeNomRue']
        dico['SenderHouseNo'] = self.infos_expe['ExpeNoRue']
        dico['SenderCountryCode'] = self.infos_expe['ExpePays']
        dico['SenderPostCode'] = self.infos_expe['ExpeCP']
        dico['SenderCity'] = self.infos_expe['ExpeVille']
        dico['SenderAddressAdd1'] = self.infos_expe['ExpeAd1']
        dico['SenderAddressAdd2'] = self.infos_expe['ExpeAd2']
        dico['SenderAddressAdd3'] = self.infos_expe['ExpeAd3']
        dico['SenderPhoneNo'] = self.infos_expe['ExpeTel1']
        
        dico['RecipientCountryCode'] = order['recipientInfo']['address']['country']
        dico['RecipientAddressAdd1'] = order['recipientInfo']['contactDetails']['lastName'] + order['recipientInfo']['contactDetails']['firstName']
        dico['RecipientEmail'] = order['buyerInfo']['email']

        # Si l'adresse de l'acheteur est indiquée on la donne à MR, sinon on donne l'adresse du point relay
        if 'addressLine' in order['recipientInfo']['address']:
            dico['RecipientStreetname'] = order['recipientInfo']['address']['addressLine']
        else:
            dico['RecipientStreetname'] = order['shippingInfo']['logistics']['pickupDetails']['address']['addressLine']            
        if 'city' in order['recipientInfo']['address']:
            dico['RecipientCity'] = order['recipientInfo']['address']['city']
        else:
            dico['RecipientCity'] = order['shippingInfo']['logistics']['pickupDetails']['address']['city']
        if 'postalCode' in order['recipientInfo']['address']:
            dico['RecipientPostCode'] = order['recipientInfo']['address']['postalCode']
        else:
            dico['RecipientPostCode'] = order['shippingInfo']['logistics']['pickupDetails']['address']['postalCode']

        # On traite les cas particuliers des numéros de téléphones
        if 'phone' in order['recipientInfo']['contactDetails']:
            phone = order['recipientInfo']['contactDetails']['phone'].replace(" ", "")
            if phone.startswith('06') or phone.startswith('07'):
                dico['RecipientPhoneNo'] = '0033' + phone[1:]
            elif phone.startswith('33') and len(phone) == 11:
                dico['RecipientPhoneNo'] = '00' + phone
            elif phone.startswith('320032'):
                dico['RecipientPhoneNo'] = phone[3:]
            else:
                dico['RecipientPhoneNo'] = phone

        return dico
    
    # Creation de la liste des items dont on update le fullfilment status (items qui vont être livrés = tous les items physiques)
    def creer_items_fuflfillment(self, order):
        liste = []
        for item in order['lineItems']:
            if item['itemType']['preset'] == 'PHYSICAL':
                info = {'index':  item['id'],
                        'quantity': item['quantity']
                        }
                liste.append(info)
        return liste