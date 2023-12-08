import requests
import json
import os
from mondialrelay_pyt import MRWebService
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

        # Récupération du site_id 
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
        url = 'https://www.wixapis.com/stores/v2/orders/query'

        # Requète pour tester sur une commande, en fonction de son numéro de commande
        # query = '{"query":{"filter": "{ \\"number\\": \\"10997\\"}", "sort":"[{\\"dateCreated\\": \\"desc\\"}]"}}'

        # Requète permettant de récupérer les commande non envoyées
        query = '{"query":{"filter": "{ \\"fulfillmentStatus\\": \\"NOT_FULFILLED\\"}", "sort":"[{\\"dateCreated\\": \\"desc\\"}]"}}'

        response = requests.post(url, headers=self.headers, data=query)
        if response.status_code != 200:
            raise Exception("Impossible de récupérer les commandes en attente chez Wix")
        
        json_response = response.json()

        # On filtre les commandes pour ne garder que celles avec Mondial Relay comme mode de livraison
        self.mr_orders = [order for order in json_response['orders'] if order['shippingInfo']['deliveryOption'].startswith("MONDIAL RELAY")]

    # Traitement d'une commande : téléchargement du bon Mondial Relay + MAJ infos livraisons chezz Wix
    def traiter_commande(self, order_number):
        # On récupère la commande demandée
        try:
            order = [order for order in self.mr_orders if order['number']==order_number][0]
        except:
            raise IndexError("Ce numéro de commande n'existe pas dans la liste des commandes en attente")

        dico = self.creer_dictionnaire_MR(order)
        logging.debug(dico)

        # Création étiquette Mondial Relay
        connexion_mr = MRWebService(self.mr_private_key)
        req_mr = connexion_mr.make_shipping_label(dico)
        logging.debug(req_mr)

        # Téléchargement du pdf contenant l'étiquette
        url_etiquette_10x15 = req_mr['URL_Etiquette'].replace('format=A4', 'format=10x15')
        etiquette = requests.get(url_etiquette_10x15)
        open(f"etiquette_{req_mr['ExpeditionNum']}.pdf", "wb").write(etiquette.content)

        # Mise à jour des informations Wix sur la livraison
        url = 'https://www.wixapis.com/stores/v2/orders/' + order['id'] + '/fulfillments'
        query =  '{"fulfillment": {"lineItems": [{"index": 1,"quantity": 1}],"trackingInfo": {"shippingProvider": "Mondial Relay", "trackingNumber": "' + str(req_mr['ExpeditionNum']) + '"}}}'
        response = requests.post(url, headers=self.headers, data=query) 
        if response.status_code != 200:
            raise Exception(f"Impossible de mettre à jour le status de la commande {order['number']}")
        # print(response)

        order['traitementOK'] = True

    # Création du dictionnaire à destination de MRWebService
    def creer_dictionnaire_MR(self, order):
        pays = order['shippingInfo']['code'][5:7]

        dico = {}        
        dico['Enseigne'] = self.mr_enseigne  
        dico['ModeCol'] = self.infos_collecte_mode_livraison['ModeCol']        # valeur à vérifier
        dico['ModeLiv'] = self.infos_collecte_mode_livraison['ModeLiv']        # valeur à vérifier
        dico['NDossier'] = str(order['number'])
        dico['Expe_Langage'] = 'FR'
        dico['Expe_Ad1'] = self.infos_expe['Expe_Ad1'] 
        dico['Expe_Ad3'] = self.infos_expe['Expe_Ad3']
        dico['Expe_Ad4'] = self.infos_expe['Expe_Ad4']
        dico['Expe_Ville'] = self.infos_expe['Expe_Ville']
        dico['Expe_CP'] = self.infos_expe['Expe_CP']
        dico['Expe_Pays'] = self.infos_expe['Expe_Pays']
        dico['Expe_Tel1'] = self.infos_expe['Expe_Tel1']
        dico['Dest_Langage'] = order['buyerLanguage'].upper()
        dico['Dest_Ad1'] = order['buyerInfo']['firstName'] + " " + order['buyerInfo']['lastName']

        # Si l'adresse de l'acheteur est indiquée on la donne à MR, sinon on donne l'adresse du point relay
        if 'addressLine1' in order['billingInfo']['address']:
            dico['Dest_Ad3'] = order['billingInfo']['address']['addressLine1']
        else:
            dico['Dest_Ad3'] = order['shippingInfo']['pickupDetails']['pickupAddress']['addressLine1']
        if 'addressLine2' in order['billingInfo']['address']:
            dico['Dest_Ad4'] = order['billingInfo']['address']['addressLine2']
        if 'city' in order['billingInfo']['address']:
            dico['Dest_Ville'] = order['billingInfo']['address']['city']
        else:
            dico['Dest_Ville'] = order['shippingInfo']['pickupDetails']['pickupAddress']['city']
        if 'zipCode' in order['billingInfo']['address']:
            dico['Dest_CP'] = order['billingInfo']['address']['zipCode']
        else:
            dico['Dest_CP'] = order['shippingInfo']['pickupDetails']['pickupAddress']['zipCode']
        
        if len(dico['Dest_Ad3']) > 32:
            if not 'Dest_Ad4' in dico:
                dico['Dest_Ad4'] = dico['Dest_Ad3'][32:63]
            dico['Dest_Ad3'] = dico['Dest_Ad3'][:31]

        dico['Dest_Pays'] = pays

        if 'phone' in order['buyerInfo']:
            if order['buyerInfo']['phone'].startswith('06'):
                dico['Dest_Tel1'] = '0033' + order['buyerInfo']['phone'][1:]
            elif order['buyerInfo']['phone'].startswith('33') and len(order['buyerInfo']['phone']) == 11:
                dico['Dest_Tel1'] = '00' + order['buyerInfo']['phone']
            elif order['buyerInfo']['phone'].startswith('320032'):
                dico['Dest_Tel1'] = order['buyerInfo']['phone'][3:]
            else:
                dico['Dest_Tel1'] = order['buyerInfo']['phone']

        dico['Dest_Mail'] = order['buyerInfo']['email']
        dico['Poids'] = str(int(float(order['totals']['weight']) * 1000))
        dico['NbColis'] = '1'
        dico['CRT_Valeur'] = '0'
        dico['COL_Rel_Pays'] = 'FR'
        dico['COL_Rel'] = self.infos_collecte_mode_livraison['COL_Rel'] 
        dico['LIV_Rel_Pays'] = pays
        dico['LIV_Rel'] = order['shippingInfo']['code'][8:]

        return dico