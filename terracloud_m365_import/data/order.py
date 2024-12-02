import frappe
from enum import Enum
from dataclasses import dataclass
from datetime import date

class PriceType(Enum):
    """Die Preistypen, die in TerraCloud vorkommen."""
    MONTHLY = '1'
    YEARLY = '5'

@dataclass
class Order:
    """Stellt eine Bestellung aus TerraCloud dar."""
    customer_no: str
    order_no: str
    article_no: str
    quantity: float
    start_date: date
    price_type: PriceType
    
    _subscription_plan: str = None

    def validate(self) -> bool:
        """
        Validiert die Bestelldaten.

        Returns:
            bool: True, wenn die Bestelldaten gültig erscheinen.

        Throws:
            ValueError: Wenn die Bestelldaten Fehler enthalten.
        """
        errors = []

        # Kundennummer: Darf nicht leer sein und muss in der Datenbank existieren
        if not self.customer_no:
            errors.append('Kundennummer fehlt')
        elif not frappe.db.exists('Customer', self.customer_no):
            errors.append(f'Kunde {self.customer_no} nicht gefunden')

        # Bestellnummer: Darf nicht leer sein, da sie als ID im Subscription Plan verwendet wird
        if not self.order_no:
            errors.append('Bestellnummer fehlt')

        # Artikelnummer: Darf nicht leer sein und muss in der Datenbank existieren
        if not self.article_no:
            errors.append('Artikelnummer fehlt')
        elif not frappe.db.exists('Item', self.article_no):
            errors.append(f'Artikel {self.article_no} nicht gefunden')

        # Menge: Muss größer als 0 sein
        if not self.quantity or self.quantity <= 0:
            errors.append('Menge fehlt')

        # Start-Datum: Darf nicht leer sein
        if not self.start_date:
            errors.append('Startdatum fehlt')

        # Preistyp: Darf nicht leer sein
        if not self.price_type:
            errors.append('Preistyp fehlt')

        if errors:
            raise ValueError(f'Ungültige TerraCloud-Bestellung: {", ".join(errors)}')

        return True

    def map_subscription_plan(self, subscription_plan: str):
        """
        Ordnet der Bestellung einen Subscription-Plan zu.

        Args:
            subscription_plan (str): Der Name des Subscription-Plans.
        """
        self._subscription_plan = subscription_plan

    @property
    def subscription_plan(self) -> str:
        """
        Gibt den Namen des zugeordneten Subscription-Plans zurück.

        Returns:
            str: Der Name des Subscription-Plans.
        """
        return self._subscription_plan