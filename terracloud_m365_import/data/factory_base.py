from abc import ABC
from frappe.model.document import Document
from terracloud_m365_import.logger import Logger

class FactoryBase(ABC):
    def __init__(self, settings: Document, logger: Logger):
        self.settings = settings
        self.logger = logger