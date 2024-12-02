import frappe
from frappe.model.document import Document
import csv
import io
from collections import defaultdict
from datetime import datetime
from terracloud_m365_import.data.order import Order
from terracloud_m365_import.data.order_factory import OrderFactory
from terracloud_m365_import.data.subscription_plan_factory import SubscriptionPlanFactory
from terracloud_m365_import.logger import Logger
from terracloud_m365_import.data.order_importer import OrderImporter

class TerracloudImport(Document):
	pass

@frappe.whitelist()
def process_import(terracloud_import_id):
    """
    Verarbeitet einen Terracloud-Import.
    Liest die hochgeladene .csv-Datei aus und erstellt entsprechende Subscriptions.

    Monatliche Abrechnungen werden pro Kunde zusammengefasst.
    Jährliche Abrechnungen werden pro Bestellung erstellt.
    """
    terracloud_import = frappe.get_doc('Terracloud Import', terracloud_import_id)
    settings = frappe.get_single('Terracloud Import Settings')
    
    order_importer = OrderImporter(terracloud_import, settings)
    order_importer.start_import()
    



@frappe.whitelist()
def process_import_old(terracloud_import_id):
    terracloud_import = frappe.get_doc('Terracloud Import', terracloud_import_id)
    settings = frappe.get_single('Terracloud Import Settings')
    
	# Bestellungen aus CSV auslesen
    file_url = terracloud_import.csv_file
    file_doc = frappe.get_doc('File', {'file_url': file_url})
    file_path = file_doc.get_full_path()
    data = parse_csv(file_path)

	# Nach Kundennummer zusammenfassen
    grouped_data = group_orders(data)
    
    for custom_id, orders in grouped_data.items():
        
		# Kunden auf Existenz überprüfen (anhand Kundennummer bzw. DocType-Name)
        if not frappe.db.exists('Customer', custom_id):
            log_error(terracloud_import.name, custom_id, 'Kunde nicht gefunden')
            continue

        # Kunde laden
        customer = frappe.get_doc('Customer', custom_id)
        
		# Überprüfen, ob Subscription für Kunde bereits existiert
        subscription = get_subscription(customer.name)
        if not subscription:
            # Neue Subscription erstellen
            subscription = create_subscription(customer, settings)

		# Bestellungen durchgehen
        for order in orders:
            try:
                if subscription_plan_exists(order['Bestellnummer']):
                    log_status(terracloud_import.name, 'Neutral', order['Bestellnummer'], 'Subscription existiert bereits')
                    continue
                create_subscription(order, customer, terracloud_import.name)
                log_status(terracloud_import.name, 'Erfolgreich', order['Bestellnummer'], '')
            except Exception as e:
                log_error(terracloud_import.name, order['Bestellnummer'], str(e))
    terracloud_import.import_status = 'Abgeschlossen'
    terracloud_import.save()
    frappe.db.commit()

def parse_csv(file_path):
    data = []
    with open(file_path, mode='r', encoding='latin-1') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            data.append(row)
    return data

def group_orders(data):
    grouped_data = defaultdict(list)
    for row in data:
        custom_id = row.get('CustomID')
        grouped_data[custom_id].append(row)
    return grouped_data

def get_subscription(customer_name: str) -> Document | None:
    '''Überprüft, ob für den Kunden bereits eine Subscription existiert.
    Verwendet dabei die Kunden-ID und überprüft, ob die Subscription durch einen Import erstellt wurde.
    
    Args:
		customer_name (str): Der Name des Kunden
        
    Returns:
		frappe.Document | None: Die Subscription, falls vorhanden, sonst None
    '''
    subscription_name = frappe.db.get_value(
        'Subscription',
        {
            'party': customer_name,
            'terracloud_import_log': ['!=', '']
        },
        'name'
    )
    if subscription_name:
        return frappe.get_doc('Subscription', subscription_name)
    else:
        return None

def subscription_plan_exists(seller_orderno):
    return frappe.db.exists('Subscription Plan', {'seller_orderno': seller_orderno})

def create_subscription_plan(order, customer: Document) -> Document:
    '''Erstellt einen Subscription Plan basierend auf den Bestelldaten'''
    subscription_plan = frappe.get_doc({
        'doctype': 'Subscription Plan',
        'plan_name': f'M365 {customer.customer_name}',
        'seller_orderno': order['Bestellnummer'],
        'quantity': order['Menge'],
        'billing_interval': 'Monthly' if order['Preistyp'] == '1' else 'Yearly',
        # Weitere Felder entsprechend den Anforderungen
    })
    subscription_plan.insert(ignore_permissions=True)

def create_subscription(customer: Document, settings: Document) -> Document:
	'''Erstellt eine Subscription für den Kunden basierend auf den Einstellungen
    
    Args:
		customer (frappe.Document): Das Kunden-Dokument
		settings (frappe.Document): Die Einstellungen für den Import
    
    Returns:
		frappe.Document: Die erstellte Subscription
    '''

    # Logik zur Erstellung der Subscription
	subscription = frappe.get_doc({
        'doctype': 'Subscription',
        'party_type': 'Customer',
        'party': customer.name,
        'title': f'M365 {customer.customer_name}',
        'invoice_title': settings.invoice_title,
        'mode_of_payment': settings.mode_of_payment,
        'start_date': calculate_start_date(order['MicrosoftSubscriptionStartDate'], order['Preistyp']),
        'subscription_plan': subscription_plan.name,
        'terracloud_import': 1,
        'import_date': frappe.utils.nowdate(),
        'import_id': import_id
    })
	subscription.insert(ignore_permissions=True)

def calculate_start_date(start_date_str: str, preistyp: str) -> datetime.date:
    '''Berechnet das Startdatum der Subscription basierend auf dem Preistyp.
    Das ist der nächst mögliche Termin in der Zukunft
    
    Args:
		start_date_str (str): Das Startdatum als String aus der .csv-Datei
		preistyp (str): Der Preistyp als String aus der .csv-Datei (1 = monatlich, 5 = jährlich)
    
    Returns:
		datetime.date: Das berechnete Startdatum
	'''
    date_format = '%d.%m.%Y %H:%M:%S'
    start_date = datetime.strptime(start_date_str, date_format)
    # Logik zur Berechnung des nächsten Startdatums basierend auf Preistyp
    return start_date.date()

def log_status(terracloud_import_name, status, entry, error_reason):
    frappe.get_doc({
        'doctype': 'Terracloud Import Log',
        'terracloud_import': terracloud_import_name,
        'timestamp': frappe.utils.now(),
        'status': status,
        'entry': entry,
        'error_reason': error_reason
    }).insert(ignore_permissions=True)

def log_error(terracloud_import_name, entry, error_reason):
    log_status(terracloud_import_name, 'Fehler', entry, error_reason)
