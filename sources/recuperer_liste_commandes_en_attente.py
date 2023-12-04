import requests
import json

# Script permettant, pour les tests, de récupérer la liste des commandes en attente et de les écrire dans un fichier json


with open('account_id.token') as f:
    account_id=f.read().strip('\n')
with open('api_key.token') as f:
    api_key=f.read().strip('\n')


# Récupération du site_id
url = 'https://www.wixapis.com/site-list/v2/sites/query'

headers = {'Content-Type': 'application/json',
           'Authorization': api_key,
           'wix-account-id': account_id
           }

response = requests.post(url, headers=headers)

site_id = response.json()['sites'][0]['id']

# On ajoute le site_id au Headers de la requete
headers['wix-site-id'] = site_id

url = 'https://www.wixapis.com/stores/v2/orders/query'

query = '{"query":{"filter": "{ \\"fulfillmentStatus\\": \\"NOT_FULFILLED\\"}", "sort":"[{\\"dateCreated\\": \\"desc\\"}]"}}'

response = requests.post(url, headers=headers, data=query)
json_response = response.json()

with open('commandes_en_attente.json', 'w') as f:
    f.write(json.dumps(json_response))