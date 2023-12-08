from wix_to_mr import WixToMR
from creer_linsting_commandes import creer_listing_commandes


commandes_wix_mr = WixToMR()
commandes_wix_mr.recuperer_commandes_wix()

for order in commandes_wix_mr.mr_orders:
    print(order)
    print(order['number'])
    commandes_wix_mr.traiter_commande(order['number'])
    

creer_listing_commandes(commandes_wix_mr.mr_orders)




