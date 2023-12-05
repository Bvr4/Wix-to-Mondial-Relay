import requests
import json
import os
from mondialrelay_pyt import MRWebService
from creer_linsting_commandes import creer_listing_commandes

# Création du dictionnaire à destination de MRWebService
def creer_dictionnaire_MR(commande, enseigne, collecte_mode_livraison, expediteur):
    pays = commande['shippingInfo']['code'][5:7]

    dico = {}
    
    dico['Enseigne'] = enseigne  
    dico['ModeCol'] = collecte_mode_livraison['ModeCol']        # valeur à vérifier
    dico['ModeLiv'] = collecte_mode_livraison['ModeLiv']        # valeur à vérifier
    dico['NDossier'] = str(commande['number'])
    dico['Expe_Langage'] = 'FR'
    dico['Expe_Ad1'] = expediteur['Expe_Ad1'] 
    dico['Expe_Ad3'] = expediteur['Expe_Ad3']
    dico['Expe_Ad4'] = expediteur['Expe_Ad4']
    dico['Expe_Ville'] = expediteur['Expe_Ville']
    dico['Expe_CP'] = expediteur['Expe_CP']
    dico['Expe_Pays'] = expediteur['Expe_Pays']
    dico['Expe_Tel1'] = expediteur['Expe_Tel1']
    dico['Dest_Langage'] = pays
    dico['Dest_Ad1'] = commande['buyerInfo']['firstName'] + " " + commande['buyerInfo']['lastName']

    if 'addressLine1' in commande['billingInfo']['address']:
        dico['Dest_Ad3'] = commande['billingInfo']['address']['addressLine1']
    if 'addressLine2' in commande['billingInfo']['address']:
        dico['Dest_Ad4'] = commande['billingInfo']['address']['addressLine2']
    if 'city' in commande['billingInfo']['address']:
        dico['Dest_Ville'] = commande['billingInfo']['address']['city']
    if 'zipCode' in commande['billingInfo']['address']:
        dico['Dest_CP'] = commande['billingInfo']['address']['zipCode']
    
    dico['Dest_Pays'] = pays

    if 'phone' in commande['buyerInfo']:
        if commande['buyerInfo']['phone'].startswith('06'):
            dico['Dest_Tel1'] = '0033' + commande['buyerInfo']['phone'][1:]
        else:
            dico['Dest_Tel1'] = commande['buyerInfo']['phone']

    dico['Dest_Mail'] = commande['buyerInfo']['email']

    dico['Poids'] = str(int(float(commande['totals']['weight']) * 1000))
    dico['NbColis'] = '1'
    dico['CRT_Valeur'] = '0'

    dico['COL_Rel_Pays'] = 'FR'
    dico['COL_Rel'] = collecte_mode_livraison['COL_Rel'] 

    dico['LIV_Rel_Pays'] = pays
    dico['LIV_Rel'] = commande['shippingInfo']['code'][8:]

    return dico

path = os.path.realpath(__file__) 
dir = os.path.dirname(path) 
dir_config = dir.replace('sources', 'config')
dir_tokens = dir.replace('sources', 'tokens')

# Lecture des informations sur l'expéditeur, stockées dans un json
with open(dir_config + '/informations_expediteur.json') as f:
    infos_expe = json.load(f)

# Lecture des informations sur la collecte et le mode de livraison, stockées dans un json
with open(dir_config + '/informations_collecte_et_mode_de_livraison.json') as f:
    infos_collecte_mode_livraison = json.load(f)

# Lecture des tokens pour l'API Wix
with open(dir_tokens + '/wix_account_id.token') as f:
    wix_account_id=f.read().strip('\n')
with open(dir_tokens + '/wix_api_key.token') as f:
    wix_api_key=f.read().strip('\n')

# Lecture des tokens pour l'API Mondial Relay
with open(dir_tokens + '/mr_enseigne.token') as f:
    mr_enseigne=f.read().strip('\n')
with open(dir_tokens + '/mr_private_key.token') as f:
    mr_private_key=f.read().strip('\n')


# Récupération du site_id (ici nous avons un seul site)
url = 'https://www.wixapis.com/site-list/v2/sites/query'

headers = {'Content-Type': 'application/json',
           'Authorization': wix_api_key,
           'wix-account-id': wix_account_id
           }

response = requests.post(url, headers=headers)

site_id = response.json()['sites'][0]['id']


# Récupération de la liste des commandes à envoyer

# On ajoute le site_id au Headers de la requete
headers['wix-site-id'] = site_id

url = 'https://www.wixapis.com/stores/v2/orders/query'

# Requète pour tester sur une commande, en fonction de son numéro de commande
# query = '{"query":{"filter": "{ \\"number\\": \\"10997\\"}", "sort":"[{\\"dateCreated\\": \\"desc\\"}]"}}'

# Requète permettant de récupérer les commande non envoyées
query = '{"query":{"filter": "{ \\"fulfillmentStatus\\": \\"NOT_FULFILLED\\"}", "sort":"[{\\"dateCreated\\": \\"desc\\"}]"}}'

response = requests.post(url, headers=headers, data=query)
json_response = response.json()

# création connexion à MR
connexion_mr = MRWebService(mr_private_key)

# On filtre les commandes pour ne garder que celles avec Mondial Relay comme mode de livraison
mr_orders = [order for order in json_response['orders'] if order['shippingInfo']['deliveryOption'].startswith("MONDIAL RELAY")]


for order in mr_orders:
    print (f"* Traitement commande N°{order['number']} - {order['shippingInfo']['deliveryOption']}")

    dico = creer_dictionnaire_MR(order, mr_enseigne, infos_collecte_mode_livraison, infos_expe)
    print (dico)

    req_mr = connexion_mr.make_shipping_label(dico)
    print (req_mr)

    # Téléchargement du pdf contenant l'étiquette
    url_etiquette_10x15 = req_mr['URL_Etiquette'].replace('format=A4', 'format=10x15')
    etiquette = requests.get(url_etiquette_10x15)
    open(f"etiquette_{req_mr['ExpeditionNum']}.pdf", "wb").write(etiquette.content)

    # Mise à jour des informations Wix sur la livraison
    url = 'https://www.wixapis.com/stores/v2/orders/' + order['id'] + '/fulfillments'
    query =  '{"fulfillment": {"lineItems": [{"index": 1,"quantity": 1}],"trackingInfo": {"shippingProvider": "Mondial Relay", "trackingNumber": "' + str(req_mr['ExpeditionNum']) + '"}}}' # à tester !
    response = requests.post(url, headers=headers, data=query)  # à tester !
    print(response)

creer_listing_commandes(mr_orders)