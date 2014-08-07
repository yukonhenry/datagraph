define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dijit/registry", "put-selector/put", "dojo/domReady!"],
    function(declare, dom, lang, arrayUtil, registry, put) {
        var constant = {
            divconfig_incomplete_mask:0x1,
            fieldconfig_incomplete_mask:0x2,
            prefinfodate_error_mask:0x4
        };
        return declare(null, {
            constructor: function(args) {
                lang.mixin(this, args);
            },
            emit_error: function(error_code) {
                error_msg = "";
                if (error_code & constant.divconfig_incomplete_mask) {
                    error_msg += "Div Config Incomplete;";
                }
                if (error_code & constant.fieldconfig_incomplete_mask) {
                    error_msg += "Field Config Incomplete;";
                }
                if (error_code & constant.prefinfodate_error_mask) {
                    error_msg += "No Field Avail on Pref Date;";
                }
                if (error_msg) {
                    error_msg += "Please recheck config"
                }
                alert(error_msg);
            }
         })
})
