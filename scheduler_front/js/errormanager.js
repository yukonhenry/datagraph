define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dijit/registry", "dijit/ConfirmDialog", "put-selector/put", "dojo/domReady!"],
    function(declare, dom, lang, arrayUtil, registry, ConfirmDialog, put) {
        var constant = {
            divconfig_incomplete_mask:0x1,
            fieldconfig_incomplete_mask:0x2,
            prefinfodate_error_mask:0x4,
            generate_error_mask:0x8
        };
        return declare(null, {
            constructor: function(args) {
                lang.mixin(this, args);
            },
            emit_error: function(error_code, custom_msg) {
                error_msg = "";
                if (error_code & constant.divconfig_incomplete_mask) {
                    error_msg += "Division Configuration Incomplete;";
                }
                if (error_code & constant.fieldconfig_incomplete_mask) {
                    error_msg += "Field Configuration Incomplete; "+custom_msg;
                }
                if (error_code & constant.prefinfodate_error_mask) {
                    error_msg += "No Field Available on Preference Date;";
                }
                if (error_code & constant.generate_error_mask) {
                    error_msg += "Generation Error-"+custom_msg+". ";
                }
                if (error_msg) {
                    error_msg += "Please recheck configuration";
                }
                var error_dialog = new ConfirmDialog({
                    title: "Error Message", content:error_msg,
                });
                error_dialog.show();
            }
         });
});
