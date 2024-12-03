import frappe
from frappe.model.document import Document
from terracloud_m365_import.data.order import Order, PriceType
from terracloud_m365_import.data.order_factory import OrderFactory
from terracloud_m365_import.data.subscription_plan_factory import SubscriptionPlanFactory
from terracloud_m365_import.data.subscription_factory import SubscriptionFactory
from terracloud_m365_import.data.invoice_factory import InvoiceFactory
from terracloud_m365_import.logger import Logger
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class OrderImporter:
    '''
    Hauptklasse für den Import von TerraCloud-Bestellungen.

    Verarbeitet einen angestoßenen TerraCloud-Import (über den DocType 'Terracloud Import').
    Liest die hochgeladene .csv-Datei aus und erstellt entsprechende Subscriptions.

    Es werden die Subscription Plans erstellt, die die Bestellungen repräsentieren.
    Das Mapping erfolgt anhand der TerraCloud-Bestellnummer.

    Die Artikelnummern müssen mit den TerraCloud-Artikelnummern übereinstimmen.
    Ebenso müssen die Kundennummern mit den TerraCloud-Kundennummern übereinstimmen.
    Nicht gefundene Artikelnummern oder Kundennummern werden ignoriert.

    Monatliche Abrechnungen werden pro Kunde zusammengefasst.
    Jährliche Abrechnungen werden pro Bestellung erstellt.
    '''
    def __init__(self, terracloud_import: Document, settings: Document):
        '''
        Initialisiert den Importer.

        Args:
            terracloud_import (Document): Der TerraCloud-Import, der verarbeitet werden soll.
            settings (Document): Die globalen Einstellungen für den Import.
        '''
        self.terracloud_import = terracloud_import
        self.settings = settings
        self.logger = Logger(terracloud_import)
        self.order_factory = OrderFactory(settings, self.logger)
        self.subscription_plan_factory = SubscriptionPlanFactory(settings, self.logger)
        self.subscription_factory = SubscriptionFactory(settings, self.logger)
        self.invoice_factory = InvoiceFactory(settings, self.logger)

    def start_import(self):
        '''
        Startet den Import.
        '''
        # Bestellungen aus CSV auslesen
        file_url = self.terracloud_import.csv_file
        file_doc = frappe.get_doc('File', {'file_url': file_url})
        file_path = file_doc.get_full_path()
        orders = self.order_factory.create_from_terracloud_csv(file_path)

        # FILTER: Alle Bestellungen: Überprüfen, ob bereits Subscription Plan existiert (Abgleich über Bestellnummer) -> Log ("bereits existent")
        orders = self.order_factory.filter_new_orders(orders, log_existing=True)

        # Subscription Plans erstellen
        subscription_plan_factory = SubscriptionPlanFactory(self.settings, self.logger)
        orders = subscription_plan_factory.create_from_orders(orders)

        # Nach Kundennummer zusammenfassen
        grouped_orders = self.order_factory.group_orders_by_customer(orders)

        # Bestellungen pro Kunde verarbeiten
        for customer_no, orders in grouped_orders.items():
            self._process_yearly_orders(customer_no, self.order_factory.get_yearly_orders(orders))
            self._process_monthly_orders(customer_no, self.order_factory.get_monthly_orders(orders))

            # Verpasste Rechnungen erstellen
            for order in orders:
                self._create_missed_invoices(order)


    def _process_yearly_orders(self, customer_no: str, orders: list[dict]) -> None:
        '''
        Verarbeitet jährliche Bestellungen eines Kunden.
        Erstellt für jede Bestellung eine eigene Subscription.

        Args:
            customer_no (str): Die Kundennummer.
            orders (list[dict]): Die Liste der Bestellungen mit gemappten Subscription-Plänen.
        '''
        # Keine Überprüfung auf existierende Subscriptions, da jede Bestellung eine eigene Subscription erhält
        for order in orders:
            self.subscription_factory.create_subscription(customer_no, PriceType.YEARLY, [order])

    def _process_monthly_orders(self, customer_no: str, orders: list[Order]) -> None:
        '''
        Verarbeitet monatliche Bestellungen eines Kunden.
        Fasst die Bestellungen pro Kunde zusammen und erstellt eine Subscription
        oder fügt diese der bestehenden Subscription hinzu.

        Args:
            customer_no (str): Die Kundennummer.
            orders (list[Order]): Die Liste der Bestellungen.
        '''
        # Bestehende Subscription suchen
        subscription = self.subscription_factory.find_existing_monthly_subscription(customer_no)

        # Subscription erstellen, falls nicht vorhanden
        if not subscription:
            self.subscription_factory.create_subscription(customer_no, PriceType.MONTHLY, orders)
        else:
            # Bestehende Subscription aktualisieren
            self.subscription_factory.append_to_existing_subscription(subscription, orders)

    def _create_missed_invoices(self, order: Order) -> None:
        '''
        Erstellt verpasste Rechnungen für eine Bestellung.
        Erstellt anteilige und ganze Rechnungen für den Zeitraum zwischen Bestelldatum und Abo-Startdatum.

        Args:
            order (Order): Die Bestellung.

        Raises:
            ValueError: Falls die Bestellung oder Subscription nicht gefunden wurde
        '''
        if not order or not order.subscription:
            raise ValueError('Can\'t create missing invoices. Order or Subscription not found')

        # Das Startdatum der Bestellung ist das Startdatum der ersten Rechnnung
        start_date = order.start_date

        # Die Rechnungserzeugung soll bis zum Abo-Startdatum erfolgen
        end_date = order.subscription.current_invoice_start

        current_start = start_date
        while current_start < end_date:

            # End-Datum der aktuellen Rechnung anhand Abrechnungs-Intervall bestimmen
            if order.price_type == PriceType.MONTHLY:
                current_end = current_start + relativedelta(months=1)
            elif order.price_type == PriceType.YEARLY:
                current_end = current_start + relativedelta(years=1)
            else:
                break

            # End-Datum beschneiden falls es das Abo-Startdatum überschreitet
            current_end = min(current_end, end_date)

            # Es soll nur der Leistungs-Zeitraum betrachtet werden: 1 Tag abziehen
            current_end -= relativedelta(days=1)

            # Rechnung erstellen
            self.invoice_factory.create_invoice(order, current_start, current_end)

            # Nächsten Rechnungsstart bestimmen
            current_start = current_end + relativedelta(days=1)