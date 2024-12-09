import frappe
from frappe.model.document import Document

@frappe.whitelist()
def get_party_name(party_type: str, party: str) -> str:
    '''
    Gibt den Namen eines Vertragspartners einer Subscription zurück.
    Kann der Kunden- oder Lieferantenname sein.

    Args:
        party_type (str): Typ des Vertragspartners (Customer oder Supplier)
        party (str): Name des Vertragspartners

    Returns:
        str: Name des Vertragspartners
    '''
    party_name = None
    if party_type == 'Customer':
        party_name = frappe.db.get_value('Customer', party, 'customer_name')
    elif party_type == 'Supplier':
        party_name = frappe.db.get_value('Supplier', party, 'supplier_name')
    return party_name

def update_party_name(doc: Document, method: str) -> None:
    '''
    Aktualisiert den Namen des Vertragspartners einer Subscription.
    Kann der Kunden- oder Lieferantenname sein.

    Args:
        doc (Document): Subscription Dokument
        method (str): Methodenname
    '''
    party_name = get_party_name(doc.party_type, doc.party)
    doc.party_name = party_name