define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dijit/registry",
    "dgrid/editor",
    "dijit/layout/StackContainer", "dijit/layout/ContentPane",
    "LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
    "LeagueScheduler/idmgrSingleton",
    "put-selector/put", "dojo/domReady!"],
    function(declare, dom, lang, arrayUtil, registry, editor, StackContainer,
        ContentPane, baseinfo,
        baseinfoSingleton, idmgrSingleton, put) {
        var constant = {
            idproperty_str:'exclusion_id', db_type:'exclusiondb',
        };
        return declare(baseinfo, {
            idproperty:constant.idproperty_str,
            db_type:constant.db_type, idmgr_obj:null,
            constructor: function(args) {
                lang.mixin(this, args);
                baseinfoSingleton.register_obj(this, constant.idproperty_str);
                this.today = new Date();
                this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
                    id:this.idproperty, op_type:this.op_type});
            },
        })
})
