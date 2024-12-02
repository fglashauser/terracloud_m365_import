from .factory_base import FactoryBase
import frappe
from frappe.model.document import Document
from .order import Order, PriceType
from datetime import datetime
import csv
from terracloud_m365_import.logger import Logger, Status

class OrderFactory(FactoryBase):
    """Stellt Methoden zur Generierung von Terracloud Bestellobjekten zur Verfügung."""

    def create_from_terracloud_csv(self, csv_file_path: str) -> list[Order]:
        """Erstellt Bestellobjekte aus einer CSV-Datei von TerraCloud."""
        orders = []

        # CSV-Datei einlesen
        data = OrderFactory._parse_csv(csv_file_path)

        # Bestellungen erstellen
        for row in data:
            order = Order(
                customer_no=row['CustomID'],
                order_no=row['Bestellnummer'],
                article_no=row['Artikelnummer'],
                quantity=float(row['Menge']),
                start_date=datetime.strptime(row['MicrosoftSubscriptionStartDate'], '%d.%m.%Y %H:%M:%S').date(),
                price_type=PriceType(row['Preistyp'])
            )

            # Bestellung validieren
            try:
                order.validate()
            except Exception as e:
                self.logger.log_status(Status.ERROR, order.order_no, str(e))
                continue
            
            orders.append(order)
        
        return orders

    def filter_new_orders(self, orders: list[Order], log_existing: bool = False) -> list[Order]:
        """Filtert Bestellungen, die noch nicht in der Datenbank existieren.
        
        Args:
            orders (list[Order]): Die Liste der Bestellungen.
            log_existing (bool): Ob existierende Bestellungen geloggt werden sollen.

        Returns:
            list[Order]: Die Liste der neuen Bestellungen.
        """
        new_orders = []
        for order in orders:
            if not frappe.db.exists('Subscription Plan', {'seller_orderno': order.order_no}):
                new_orders.append(order)
            elif log_existing:
                self.logger.log_status(Status.NEUTRAL, order.order_no, 'Bestellung existiert bereits')
        return new_orders

    def group_orders_by_customer(self, orders: list[Order]) -> dict:
        """Gruppiert Bestellungen nach der Kundennummer."""
        grouped_orders = {}
        for order in orders:
            if order.customer_no not in grouped_orders:
                grouped_orders[order.customer_no] = []
            grouped_orders[order.customer_no].append(order)
        return grouped_orders
    
    def get_yearly_orders(self, orders: list[Order]) -> list[Order]:
        """Filtert Bestellungen mit jährlicher Abrechnung."""
        return [order for order in orders if order.price_type == PriceType.YEARLY]
    
    def get_monthly_orders(self, orders: list[Order]) -> list[Order]:
        """Filtert Bestellungen mit monatlicher Abrechnung."""
        return [order for order in orders if order.price_type == PriceType.MONTHLY]

    @staticmethod
    def _parse_csv(file_path: str):
        data = []
        with open(file_path, mode='r', encoding='latin-1') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                data.append(row)
        return data