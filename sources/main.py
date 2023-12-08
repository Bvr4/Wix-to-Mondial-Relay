from wix_to_mr import WixToMR
from creer_linsting_commandes import creer_listing_commandes
import datetime
import logging

now = datetime.datetime.now()
log_name = f"log_{str(now.year)}-{str(now.month)}-{str(now.day)}_{str(now.hour)}-{str(now.minute)}.log"
logging.basicConfig(filename='log/' + log_name, level=logging.DEBUG)

logging.info("Récupération des informations chez Wix")
try:
    commandes_wix_mr = WixToMR()
    commandes_wix_mr.recuperer_commandes_wix()
except Exception as e:
    logging.exception(e)
    raise e

logging.info('Traiteement des commandes')
for order in commandes_wix_mr.mr_orders:
    message = f"Traitement commande N°{order['number']} - {order['buyerInfo']['firstName']} {order['buyerInfo']['lastName']}"
    print(message)
    logging.info(message)
    
    try:
        commandes_wix_mr.traiter_commande(order['number'])
    except Exception as e:
        logging.error(f"Problème lors du traitement de la commande {order['number']} ")
        logging.exception(e)
    

creer_listing_commandes(commandes_wix_mr.mr_orders)




