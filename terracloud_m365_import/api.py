import frappe

@frappe.whitelist()
def start_import(terracloud_import_id):
    frappe.enqueue(
        'terracloud_m365_import.terracloud_m365_import.doctype.terracloud_import.terracloud_import.process_import',
        terracloud_import_id=terracloud_import_id
    )
