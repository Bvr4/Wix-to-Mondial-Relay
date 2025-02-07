from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import datetime


def creer_listing_commandes(commandes):
    now = datetime.datetime.now()
    nom_fichier = f"commandes_{str(now.year)}-{str(now.month)}-{str(now.day)}_{str(now.hour)}-{str(now.minute)}.pdf"
    c = canvas.Canvas(nom_fichier, pagesize=A4)

    w, h = A4
    margin = 50
    x, y = margin, h - margin


    c.setFont("Helvetica-Bold", 14)
    texte = f"Commandes Mondial Relay  {str(now.day)}/{str(now.month)}/{str(now.year)}"
    c.drawString(x, y, texte)
    y -= 20

    font_size = 12

    # On filtre les commandes pour ne garder que celles qui ont été traitées 
    commandes = [commande for commande in commandes if 'traitementOK' in commande and commande['traitementOK']]
    
    for commande in commandes:
        c.drawString(x, y, "")
        y -= font_size + 2

        # On teste si on est pas en bout de page
        if y - font_size*len(commande['lineItems']) < margin:
            print(f'y = {str(y)}, margin = {str(margin)}')
            c.showPage()
            y = h - margin

        c.setFont("Helvetica-Bold", font_size)
        texte= f"Commande N°{commande['number']} - {commande['billingInfo']['contactDetails']['firstName']} {commande['billingInfo']['contactDetails']['lastName']}    ({commande['totalPrice']}€ de marchandise)"
        c.drawString(x, y, texte)
        y -= font_size

        c.setFont("Helvetica", font_size)

        for item in commande['lineItems']:
            texte1 = f"{item['quantity']} * {item['price']['formattedAmount']}  -  {item['totalPriceAfterTax']['formattedAmount']}"
            if len(item['catalogReference']['options']['options']) > 0:
                options = ""
                for option_type, option_value in item['catalogReference']['options']['options'].items():
                    options += f"{option_type} : {option_value} "

                texte2 = f"   ---   {item['productName']['original']}  ({options})"
            else:
                texte2 = f"   ---   {item['productName']['original']}"
            c.drawString(x, y, texte1)
            c.drawString(x+120, y, texte2)
            y -= font_size + 2


    c.showPage()

    c.save()