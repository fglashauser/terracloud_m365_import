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
def process_import(terracloud_import_id) -> None:
    '''
    Verarbeitet einen Terracloud-Import.
    Liest die hochgeladene .csv-Datei aus und erstellt entsprechende Subscriptions.

    Monatliche Abrechnungen werden pro Kunde zusammengefasst.
    Jährliche Abrechnungen werden pro Bestellung erstellt.
    '''
    terracloud_import = frappe.get_doc('Terracloud Import', terracloud_import_id)
    settings = frappe.get_single('Terracloud Import Settings')
    
    order_importer = OrderImporter(terracloud_import, settings)
    order_importer.start_import()

@frappe.whitelist()
def delete_data() -> None:
    '''
    Löscht alle Rechnungen, Subscriptions und Subscription Plans.
    ACHTUNG: Nur auf Dev-Seiten verwenden!
    '''
    frappe.db.delete('Sales Invoice')
    frappe.db.delete('Subscription')
    frappe.db.delete('Subscription Plan')