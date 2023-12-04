import requests
import json
from mondialrelay_pyt import MRWebService

# Création du dictionnaire à destination de MRWebService
def creer_dictionnaire_MR(commande):
    pays = commande['shippingInfo']['code'][5-6]

    dico = {}
    
    dico['Enseigne'] = 'BDTEST13'   # à modifier
    dico['ModeCol'] = 'REL'         # à vérifier
    dico['ModeLiv'] = '24R'         # à vérifier
    dico['NDossier'] = commande['number']
    dico['Expe_Langage'] = 'FR'
    dico['Expe_Ad1'] = "L'ÉTOFFE LIBRE X LA CARRIOLE"
    dico['Expe_Ad3'] = 'CERVELLE'
    dico['Expe_Ad4'] = 'LE TOURNEUR'
    dico['Expe_Ville'] = 'SOULEUVRE EN BOCAGE'
    dico['Expe_CP'] = '14350'
    dico['Expe_Pays'] = 'FR'
    dico['Expe_Tel1'] = '0033606920855'
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
            dico['Dest_Tel1'] = '0033' + commande['buyerInfo']['phone'][2-9]
        else:
            dico['Dest_Tel1'] = commande['buyerInfo']['phone']

    dico['Dest_Mail'] = commande['buyerInfo']['email']

    dico['Poids'] = str(float(commande['totals']['weight']) * 1000)
    dico['NbColis'] = '1'
    dico['CRT_Valeur'] = '0'

    dico['COL_Rel_Pays'] = 'FR'
    dico['COL_Rel'] = '67644' # Code VETISA

    dico['LIV_Rel_Pays'] = pays
    dico['LIV_Rel'] = commande['shippingInfo']['code'][8:]

    return dico


# Lecture des tokens pour l'API Wix
with open('account_id.token') as f:
    account_id=f.read().strip('\n')
with open('api_key.token') as f:
    api_key=f.read().strip('\n')


# Récupération du site_id (ici nous avons un seul site)
url = 'https://www.wixapis.com/site-list/v2/sites/query'

headers = {'Content-Type': 'application/json',
           'Authorization': api_key,
           'wix-account-id': account_id
           }

response = requests.post(url, headers=headers)

site_id = response.json()['sites'][0]['id']


# Récupération de la liste des commandes à envoyer

# On ajoute le site_id au Headers de la requete
headers['wix-site-id'] = site_id

url = 'https://www.wixapis.com/stores/v2/orders/query'

# Requète pour tester sur une commande, en fonction de son numéro de commande
query = '{"query":{"filter": "{ \\"number\\": \\"10979\\"}", "sort":"[{\\"dateCreated\\": \\"desc\\"}]"}}'

# Requète permettant de récupérer les commande non envoyées
# query = '{"query":{"filter": "{ \\"fulfillmentStatus\\": \\"NOT_FULFILLED\\"}", "sort":"[{\\"dateCreated\\": \\"desc\\"}]"}}'

response = requests.post(url, headers=headers, data=query)
json_response = response.json()

# On traite les commandes si le mode de livraison est Mondial Relay
for order in json_response['orders']:
    print (f"* Traitement commande N°{order['number']}")
    if order['shippingInfo']['deliveryOption'].startswith("MONDIAL RELAY"):
        print (order['shippingInfo']['deliveryOption']) 

        dico = creer_dictionnaire_MR(order)
        print (dico)



