from wix_to_mr import WixToMR
from creer_linsting_commandes import creer_listing_commandes
import datetime
import logging
import customtkinter as ctk
import threading
import time
import os

class ScrollableCheckBoxFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, item_list, command=None, **kwargs):
        super().__init__(master, **kwargs)

        self.command = command
        self.checkbox_list = []
        for i, item in enumerate(item_list):
            self.add_item(item)

    def add_item(self, item):
        checkbox = ctk.CTkCheckBox(self, text=item)
        if self.command is not None:
            checkbox.configure(command=self.command)
        checkbox.pack(pady=5, padx=5, anchor='w')
        self.checkbox_list.append(checkbox)

    def get_checked_items(self):
        return [int(checkbox.cget("text").split(" ")[0]) for checkbox in self.checkbox_list if checkbox.get() == 1]
    
    def select_all_items(self):
        for checkbox in self.checkbox_list:
            checkbox.select()

    def deselect_all_items(self):
        for checkbox in self.checkbox_list:
            checkbox.deselect()

    def remove_all_items(self):
        for checkbox in self.checkbox_list:
            checkbox.destroy()
        self.checkbox_list.clear()


def update_label(label, label_value):
    label.configure(text=label_value)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x550+400+150")
        self.title("Wix to Mondial Relay")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.frame = ctk.CTkFrame(master=self)
        self.frame.pack(pady=20, padx=40, fill="both", expand=True)

        self.label = ctk.CTkLabel(master=self.frame, text="Commandes en attente de livraison Mondial Relay", padx=30, corner_radius=6)
        self.label.pack(pady=12, padx=10)

        self.check_box_frame = ScrollableCheckBoxFrame(master=self.frame, item_list="0", width=400, height=300)
        self.check_box_frame.pack(pady=(0,12), padx=10)


        self.bouton_tout_selectionner = ctk.CTkButton(master=self.frame, text="Tout sélectionner", command=self.check_box_frame.select_all_items)
        self.bouton_tout_selectionner.pack(pady=0, padx=150, side=ctk.LEFT, fill=ctk.X)

        self.bouton_tout_selectionner = ctk.CTkButton(master=self.frame, text="Tout désélectionner", command=self.check_box_frame.deselect_all_items)
        self.bouton_tout_selectionner.pack(pady=0, padx=0, side=ctk.LEFT, fill=ctk.X)

        self.bouton_creer_etiquettes = ctk.CTkButton(master=self, text="Créer les étiquettes Mondial Relay", font=("Arial", 20), command=self.start_processing_thread)
        self.bouton_creer_etiquettes.pack(pady=(0, 20), padx=40, fill="both", expand=True)

    def start_processing_thread(self):
        global processing_thread
        processing_thread = threading.Thread(target=self.traiter_donnees)
        processing_thread.daemon = True
        processing_thread.start()

    def traiter_donnees(self):
        # Création d'une fenêtre "pop up".
        secondary_window =ctk.CTkToplevel()
        secondary_window.title("Traitement en cours...")
        secondary_window.geometry("350x200+650+300")

        label = ctk.CTkLabel(master=secondary_window, text="Le traitement va démarrer")
        label.pack(padx=10, pady=10)

        num_commandes_selectionnees = self.check_box_frame.get_checked_items()

        progressbar = ctk.CTkProgressBar(master=secondary_window, mode="indeterminate")
        progressbar.pack(padx=20, pady=30)
        progressbar.start()
        secondary_window.focus()

        for num_commande in num_commandes_selectionnees:
            time.sleep(0.5)
            texte = f"traitement de la commande {num_commande}"
            print(texte)
            self.after(0, update_label, *(label, texte))
            try:
                self.commandes_wix_mr.traiter_commande(num_commande)
            except Exception as e:
                logging.error(f"Problème lors du traitement de la commande {num_commande} ")
                logging.exception(e)

        progressbar.set(1)
        progressbar.stop()
        texte = "Creation du listing des commandes"
        self.after(0, update_label, *(label, texte))
        creer_listing_commandes(self.commandes_wix_mr.mr_orders)
        texte = "Traitement terminé, vous pouvez fermer la fenêtre"
        self.after(0, update_label, *(label, texte))
        
        # Création du bouton pour fermer (détruire) la fenêtre.
        button_close = ctk.CTkButton(
            secondary_window,
            text="Fermer",
            command=secondary_window.destroy
        )
        button_close.pack(padx=20, pady=30)

        # On met à jour la liste des commandes wix affichées (celles non traitées)
        self.after(0, self.get_infos_commandes_wix)
        
    def get_infos_commandes_wix(self):
        self.check_box_frame.remove_all_items()

        logging.info("Récupération des informations chez Wix")
        try:
            self.commandes_wix_mr = WixToMR()
            self.commandes_wix_mr.recuperer_commandes_wix()
        except Exception as e:
            logging.exception(e)
            raise e
            
        liste = [f"{order['number']} - {order['billingInfo']['contactDetails']['firstName']} {order['billingInfo']['contactDetails']['lastName']}" for order in self.commandes_wix_mr.mr_orders]
        for item in liste:
            self.check_box_frame.add_item(item)


if __name__ == "__main__":
    path = os.path.realpath(__file__) 
    dir = os.path.dirname(path) 
    dir_log = dir.replace('sources', 'log')
    now = datetime.datetime.now()
    log_name = f"log_{str(now.year)}-{str(now.month)}-{str(now.day)}_{str(now.hour)}-{str(now.minute)}.log"
    logging.basicConfig(filename=dir_log +'/' + log_name, level=logging.DEBUG)

    app = App()
    app.get_infos_commandes_wix()
    app.mainloop() 

