import frappe
from frappe.model.document import Document
from .factory_base import FactoryBase
from .order import Order, PriceType
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

class SubscriptionFactory(FactoryBase):
    '''
    Stellt Methoden zur Generierung von Subscription-Objekten zur Verfügung.
    '''
    
    def create_subscription(self, customer_no: str, price_type: PriceType, orders: list[Order]) -> None:
        '''
        Erstellt eine Subscription für einen Kunden.
        
        Args:
            customer_no (str): Die Kundennummer.
            orders (list[Order]): Die Liste der Bestellungen.
        '''
        # Überprüfen ob mindestens eine Bestellung vorhanden ist
        if not orders:
            return

        # Basis der Subscription erstellen
        subscription = frappe.new_doc('Subscription')
        subscription.party_type = 'Customer'
        subscription.party = customer_no
        subscription.title = f'M365 {customer_no} ({ "jährlich" if price_type == PriceType.YEARLY else "monatlich" })'
        subscription.mode_of_payment = self.settings.mode_of_payment
        subscription.invoice_title = self.settings.invoice_title
        subscription.terracloud_import_link = self.logger.terracloud_import.name
        subscription.terracloud_billing_interval = 'Year' if price_type == PriceType.YEARLY else 'Month'
        subscription.start_date = SubscriptionFactory.get_next_month_first_day() \
            if price_type == PriceType.MONTHLY \
            else SubscriptionFactory.get_next_year_day()
        subscription.generate_invoice_at = 'Beginning of the current subscription period'
        subscription.follow_calendar_months = self.settings.follow_calendar_months
        subscription.generate_new_invoices_past_due_date = self.settings.generate_new_invoices_past_due_date
        subscription.submit_generated_invoices = self.settings.submit_generated_invoices
        subscription.sales_tax_template = self.settings.sales_tax_template

        # Subscription Plans hinzufügen
        for order in orders:
            order.map_subscription(subscription)
            subscription.append('plans', {
                'plan': order.subscription_plan,
                'qty': order.quantity
            })

        # Subscription speichern
        subscription.insert()
        frappe.db.commit()

    def append_to_existing_subscription(self, subscription: Document, orders: list[Order]) -> None:
        '''
        Fügt Bestellungen einer existierenden Subscription hinzu.
        
        Args:
            subscription (frappe.Document): Die Subscription.
            orders (list[Order]): Die Liste der Bestellungen.
        '''
        for order in orders:
            order.map_subscription(subscription)
            subscription.append('plans', {
                'plan': order.subscription_plan,
                'qty': order.quantity
            })
        subscription.save()
        frappe.db.commit()

    def find_existing_monthly_subscription(self, customer_no) -> Document | None:
        '''
        Sucht nach einer existierenden monatlichen Subscription für einen Kunden.
        
        Args:
            customer_no (str): Die Kundennummer.
        
        Returns:
            frappe.Document | None: Die Subscription, falls vorhanden, sonst None
        '''
        subscription = frappe.get_all('Subscription', filters={
            'party_type': 'Customer',
            'party': customer_no,
            'terracloud_billing_interval': 'Month'
        }, limit=1)

        return subscription[0] if subscription else None

    @staticmethod
    def get_next_month_first_day() -> date:
        '''
        Berechnet den ersten Tag des nächsten Monats basierend auf dem tatsächlichen Startdatum.
        
        Args:
            actual_start_date (date): Das tatsächliche Startdatum.
        
        Returns:
            date: Der erste Tag des nächsten Monats.
        '''
        next_month = datetime.now() + relativedelta(months=1)
        return date(next_month.year, next_month.month, 1)
    
    @staticmethod
    def get_next_year_day() -> date:
        '''
        Berechnet den ersten Tag des nächsten Jahres basierend auf dem tatsächlichen Startdatum.
        
        Args:
            actual_start_date (date): Das tatsächliche Startdatum.
        
        Returns:
            date: Der erste Tag des nächsten Jahres.
        '''
        next_year = datetime.now() + relativedelta(years=1)
        return date(next_year.year, 1, 1)
