frappe.ui.form.on('Terracloud Import', {
    refresh: function(frm) {
        if (!frm.is_new() && frm.doc.import_status !== 'Abgeschlossen') {
            frm.add_custom_button(__('Start Import'), function() {
                frappe.call({
                    method: 'terracloud_m365_import.terracloud_m365_import.doctype.terracloud_import.terracloud_import.process_import',
                    args: {
                        'terracloud_import_id': frm.doc.name
                    },
                    callback: function() {
                        frappe.msgprint(__('Import gestartet.'));
                    }
                });
            });
        }
    }
});