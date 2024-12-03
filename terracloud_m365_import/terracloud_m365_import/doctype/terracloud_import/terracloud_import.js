frappe.ui.form.on('Terracloud Import', {
    refresh: function(frm) {
        if (!frm.is_new() && frm.doc.import_status !== 'Abgeschlossen') {

            // Button: Import starten
            frm.add_custom_button(__('Start Import'), function() {
                frappe.msgprint(__('Import wird gestartet. Bitte warten.'));
                frappe.call({
                    method: 'terracloud_m365_import.terracloud_m365_import.doctype.terracloud_import.terracloud_import.process_import',
                    args: {
                        'terracloud_import_id': frm.doc.name
                    },
                    callback: function() {
                        frappe.msgprint(__('Import beendet.'));
                    }
                });
            });

            // Button: Daten löschen (nur in DEV)
            if (frappe.boot.developer_mode) {
                frm.add_custom_button(__('Daten löschen'), function() {
                    frappe.msgprint(__('Daten werden gelöscht. Bitte warten.'));
                    frappe.call({
                        method: 'terracloud_m365_import.terracloud_m365_import.doctype.terracloud_import.terracloud_import.delete_data',
                        callback: function() {
                            frappe.msgprint(__('Daten gelöscht.'));
                        }
                    });
                });
            }
        }
    }
});