import frappe
from frappe.model.document import Document
from enum import Enum

class Status(Enum):
    """Die verschiedenen Status, die ein Terracloud-Import-Log haben kann."""
    NEUTRAL = 'Neutral'
    ERROR = 'Fehler'
    SUCCESS = 'Erfolgreich'

class Logger:
    """Stellt einen Logger für einen Terracloud-Import zur Verfügung."""
    def __init__(self, terracloud_import: Document):
        self.terracloud_import = terracloud_import

    def log_status(self, status: Status, entry: str, error_reason: str):
        frappe.get_doc({
            'doctype': 'Terracloud Import Log',
            'terracloud_import': self.terracloud_import.name,
            'timestamp': frappe.utils.now(),
            'status': status.value,
            'entry': entry,
            'error_reason': error_reason
        }).insert(ignore_permissions=True)