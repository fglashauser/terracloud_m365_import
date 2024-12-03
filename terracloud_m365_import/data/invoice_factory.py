from .factory_base import FactoryBase
import frappe
from frappe.model.document import Document
from .order import Order, PriceType
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import calendar

class InvoiceFactory(FactoryBase):
    '''
    Stellt Methoden zur Generierung von Rechnungen zur Verfügung.
    '''

    def create_invoice(self, order: Order, from_date: date, to_date: date) -> Document:
        '''
        Erstellt eine Rechnung für eine Bestellung und berechnet dabei den fälligen Betrag.

        Args:
            order (Order): Die Bestellung.
            from_date (date): Das Startdatum des Abrechnungszeitraums.
            to_date (date): Das Enddatum des Abrechnungszeitraums.
        '''
        # Rechnung erstellen
        invoice = frappe.new_doc('Sales Invoice')
        invoice.title = order.subscription.invoice_title
        invoice.customer = order.customer_no
        invoice.due_date = datetime.now().date()
        invoice.taxes_and_charges = order.subscription.sales_tax_template
        invoice.subscription = order.subscription.name
        invoice.from_date = from_date
        invoice.to_date = to_date

        # Artikel laden
        item = frappe.get_doc('Item', order.article_no)

        # Rechnungspositionen hinzufügen
        invoice.append('items', {
            'item_code': item.name,
            'item_name': item.item_name,
            'description': self._update_item_description(item.description),
            'qty': order.quantity,
            'uom': item.stock_uom,
            'rate': self.get_unit_price(order, from_date, to_date)
        })

    def get_unit_price(self, order: Order, from_date: date, to_date: date) -> float | None:
        '''
        Berechnet den Preis für eine Bestellung (pro Stück) im gegebenen Zeitraum.

        Args:
            order (Order): Die Bestellung.
            from_date (date): Das Startdatum des Abrechnungszeitraums.
            to_date (date): Das Enddatum des Abrechnungszeitraums.

        Returns:
            float: Der Preis für die Bestellung im gegebenen Zeitraum. None, falls kein Preis gefunden wurde.
        '''
        # Feststellen, ob ein ganzer Preis oder anteiliger berechnet werden muss
        if order.price_type == PriceType.MONTHLY and to_date == from_date + relativedelta(months=1):
            bill_full_price = True
        elif order.price_type == PriceType.YEARLY and to_date == from_date + relativedelta(years=1):
            bill_full_price = True

        # Preis pro Stück berechnen
        unit_price = self._get_full_unit_price(order, from_date) if bill_full_price \
            else self._get_partial_unit_price(order, from_date, to_date)

        return unit_price

    def _get_partial_unit_price(self, order: Order, from_date: date, to_date: date) -> float | None:
        '''
        Berechnet den Preis für eine Bestellung im gegebenen Zeitraum.
        Der Preis bezieht sich auf ein einzelnes Stück des Artikels.

        Args:
            order (Order): Die Bestellung.
            from_date (date): Das Startdatum des Abrechnungszeitraums.
            to_date (date): Das Enddatum des Abrechnungszeitraums.

        Returns:
            float: Der anteilige Preis für die Bestellung im gegebenen Zeitraum.
        '''
        # Zuerst den vollen Preis über die Preisliste holen
        full_price = self._get_full_unit_price(order, from_date)
        if not full_price:
            return None

        delta = to_date - from_date
        billing_days = delta.days + 1 # Einschließlich beider Tage

        year = from_date.year

        # Anzahl der Tage im Monat oder Jahr berechnen
        if order.price_type == PriceType.MONTHLY:
            month = from_date.month
            all_days = calendar.monthrange(year, month)[1]
        elif order.price_type == PriceType.YEARLY:
            all_days = 366 if calendar.isleap(year) else 365

        # Preis pro Tag berechnen
        daily_price = full_price / all_days
        billing_price = daily_price * billing_days
        
        return round(billing_price, 2)
    
    def _get_full_unit_price(self, order: Order, valuation_date: date) -> float | None:
        '''
        Berechnet den vollen Preis für einen Artikel anhand des Bewertungsdatums.
        Sucht in der konfigurierten Preisliste nach dem Preis des Artikels.
        Sucht zuerst einen kundenspezifischen Preis, dann den allgemeinen Preis.
        Der Preis bezieht sich auf ein einzelnes Stück des Artikels.

        Args:
            order (Order): Die Bestellung.
            valuation_date (date): Das Bewertungsdatum.

        Returns:
            float: Der volle Preis des Artikels. None, falls kein Preis gefunden wurde.
        '''
        price_list = self.settings.price_list

        # Kundenspezifischen Preis suchen
        filters = {
            'item_code': order.article_no,
            'customer': order.customer_no,
            'price_list': price_list,
            'valid_from': ('<=', valuation_date),
            'valid_upto': ('>=', valuation_date)
        }
        price = frappe.get_value('Item Price', filters, 'price_list_rate')
        if price:
            return price
        
        # Kein Kundenpreis gefunden -> Allgemeinen Preis suchen
        filters.pop('customer')
        price = frappe.get_value('Item Price', filters, 'price_list_rate')

        return price
    
    def _update_item_description(self, description: str, from_date: date, to_date: date) -> str:
        '''
        Ergänzt die Beschreibung eines Artikels um den Abrechnungszeitraum.

        Args:
            description (str): Die Beschreibung des Artikels.
            from_date (date): Das Startdatum des Abrechnungszeitraums.
            to_date (date): Das Enddatum des Abrechnungszeitraums.

        Returns:
            str: Die ergänzte Beschreibung.
        '''
        description = '' if not description else description # Default-Wert
        description = f"<p><strong><u>Zeitraum:</u></strong><u> {from_date.strftime('%d.%m.%Y')} - {to_date.strftime('%d.%m.%Y')}</u></p>{description}"
        return description
