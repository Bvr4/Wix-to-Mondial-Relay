# Wix to Mondial Relay
Ce script à pour but de faire un lien entre l'api Wix et l'api Mondial Relay, afin de : 
- récupérer les commandes en attente de traitement sur la boutique Wix
- pour les commandes avec livraison Mondial Relay : envoyer les informations vers Mondial Relay pour la création d'étiquettes
- télécharger les étiquettes de livraison Mondial Relay
- mettre à jour les informations de livraison sur la plateforme Wix pour les différentes commandes
- générer un pdf avec la liste des produits pour chaque commande traitée dans le script

## Prérequis
Pour fonctionner le script utilise la bibliothèque mondialrelay_pyt.  
Des clés sont à récupérer au près des fournisseurs d'api (tokens).