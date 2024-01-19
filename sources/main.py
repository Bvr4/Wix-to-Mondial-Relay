from wix_to_mr import WixToMR
from creer_linsting_commandes import creer_listing_commandes
import datetime
import logging
import customtkinter as ctk
import threading
import time


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

    def remove_item(self, item):
        for checkbox in self.checkbox_list:
            if item == checkbox.cget("text")[:5]:
                checkbox.destroy()
                self.checkbox_list.remove(checkbox)
                return

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
            self.checkbox_list.remove(checkbox)




def traiter_donnees():
    # Create secondary (or popup) window.
    secondary_window =ctk.CTkToplevel()
    secondary_window.title("Traitement en cours...")
    # secondary_window.config(width=300, height=200)
    secondary_window.geometry("350x200+650+300")

    label = ctk.CTkLabel(master=secondary_window, text="Le traitement va démarrer")
    label.pack(padx=10, pady=10)

    num_commandes_selectionnees = check_box_frame.get_checked_items()

    progressbar = ctk.CTkProgressBar(master=secondary_window, mode="indeterminate")
    progressbar.pack(padx=20, pady=30)
    progressbar.start()
    secondary_window.focus()

    for num_commande in num_commandes_selectionnees:
        time.sleep(0.5)
        texte = f"traitement de la commande {num_commande}"
        print(texte)
        root.after(0, update_label, *(label, texte))
        try:
            commandes_wix_mr.traiter_commande(num_commande)
        except Exception as e:
            logging.error(f"Problème lors du traitement de la commande {num_commande} ")
            logging.exception(e)

        root.after(0, check_box_frame.remove_item, int(num_commande)) # fonctionne pas


    progressbar.set(1)
    progressbar.stop()
    texte = "Creation du listing des commandes"
    root.after(0, update_label, *(label, texte))
    creer_listing_commandes(commandes_wix_mr.mr_orders)
    texte = "Traitement terminé, vous pouvez fermer la fenêtre"
    root.after(0, update_label, *(label, texte))
    
    # Create a button to close (destroy) this window.
    button_close = ctk.CTkButton(
        secondary_window,
        text="Fermer",
        command=secondary_window.destroy
    )
    # button_close.place(x=75, y=75)
    button_close.pack(padx=20, pady=30)

    # root.after(0, check_box_frame.remove_all_items)

    # root.after(0, get_infos_commandes_wix)
    
    # secondary_window.grab_set()  # Modal.


def update_label(label, label_value):
    label.configure(text=label_value)


def get_infos_commandes_wix():
    check_box_frame.remove_all_items()

    logging.info("Récupération des informations chez Wix")
    try:
        commandes_wix_mr = WixToMR()
        commandes_wix_mr.recuperer_commandes_wix()
    except Exception as e:
        logging.exception(e)
        raise e
        
    liste = [f"{order['number']} - {order['buyerInfo']['firstName']} {order['buyerInfo']['lastName']}" for order in commandes_wix_mr.mr_orders]
    for item in liste:
        check_box_frame.add_item(item)

    return commandes_wix_mr

def start_processing_thread():
    global processing_thread
    processing_thread = threading.Thread(target=traiter_donnees)
    processing_thread.daemon = True
    processing_thread.start()


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.geometry("800x550+400+150")
root.title("Wix to Mondial Relay")

frame = ctk.CTkFrame(master=root)
frame.pack(pady=20, padx=40, fill="both", expand=True)

label = ctk.CTkLabel(master=frame, text="Commandes en attente de livraison Mondial Relay", padx=30, corner_radius=6)
label.pack(pady=12, padx=10)

check_box_frame = ScrollableCheckBoxFrame(master=frame, item_list="0", width=400, height=300)
check_box_frame.pack(pady=(0,12), padx=10)


bouton_tout_selectionner = ctk.CTkButton(master=frame, text="Tout sélectionner", command=check_box_frame.select_all_items)
bouton_tout_selectionner.pack(pady=0, padx=150, side=ctk.LEFT, fill=ctk.X)

bouton_tout_selectionner = ctk.CTkButton(master=frame, text="Tout désélectionner", command=check_box_frame.deselect_all_items)
bouton_tout_selectionner.pack(pady=0, padx=0, side=ctk.LEFT, fill=ctk.X)

bouton_creer_etiquettes = ctk.CTkButton(master=root, text="Créer les étiquettes Mondial Relay", font=("Arial", 20), command=start_processing_thread)
bouton_creer_etiquettes.pack(pady=(0, 20), padx=40, fill="both", expand=True)



if __name__ == "__main__":
    now = datetime.datetime.now()
    log_name = f"log_{str(now.year)}-{str(now.month)}-{str(now.day)}_{str(now.hour)}-{str(now.minute)}.log"
    logging.basicConfig(filename='log/' + log_name, level=logging.DEBUG)

    commandes_wix_mr = get_infos_commandes_wix()

    root.mainloop() 






