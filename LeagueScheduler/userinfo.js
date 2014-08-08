define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dijit/registry", "dijit/Tooltip", "dijit/form/ValidationTextBox",
    "dijit/form/Button", "put-selector/put", "LeagueScheduler/baseinfo",
    "dojo/domReady!"],
    function(declare, dom, lang, arrayUtil, registry, Tooltip, ValidationTextBox,
        Button, put, baseinfo) {
        var constant = {
            idproperty_str:'user_id',
            init:"init",
            db_type:'userdb',
            dbname_str:"Enter User/Organization ID",
        };
        return declare(baseinfo, {
            server_interface:null, db_type:constant.db_type,
            idproperty:constant.idproperty_str,
            constructor: function(args) {
                lang.mixin(this, args);
            },
            is_newgrid_required: function() {
                return false;
            },
            initialize: function(ignore_flag, op_type) {
                var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : op_type;
                var form_id = this.idmgr_obj.form_id;
                // form_widget is already created create paramstack
                var form_widget = registry.byId(form_id);
                var form_node = form_widget.domNode;
                var btn_id = this.idmgr_obj.btn_id;
                var dbname_id = this.idmgr_obj.dbname_id;
                var dbname_widget = null;
                var dbname_node = dom.byId(dbname_id);
                if (!dbname_node) {
                    put(form_node, "label.label_box[for=$]",
                        dbname_id, constant.dbname_str);
                    put(form_node, "span.empty_tinygap");
                    dbname_node = put(form_node,
                        "input[id=$][type=text][required=true]",
                        dbname_id)
                    dbname_reg = new ValidationTextBox({
                        value:'',
                        regExp:'\\D[\\w]+',
                        style:'width:12em',
                        promptMessage:constant.dbname_str + '-start with letter or _, followed by alphanumeric or _',
                        invalidMessage:'start with letter or _, followed by alphanumeric characters and _',
                        missingMessage:constant.dbname_str
                    }, dbname_node);
                    // define tooltip help
                    var tooltipconfig = {connectId:[dbname_id],
                        label:"Specify User/Organization ID and press Enter",
                        position:['below','after']};
                    this.tooltip_list.push(new Tooltip(tooltipconfig));
                    put(form_node, "span.empty_tinygap");
                    var btn_node = put(form_node,
                        "button.dijitButton[id=$][type=submit]", btn_id);
                    var btn_widget = new Button({
                        label:"Submit",
                        disabled:false,
                        class:"success",
                        onClick: lang.hitch(this, this.process_input)
                    }, btn_node);
                    btn_widget.startup();
                } else {
                    dbname_reg = registry.byId(dbname_id);
                }
                this.uistackmgr_type.switch_pstackcpane({idproperty:this.idproperty,
                    p_stage: "preconfig", entry_pt:constant.init});
            },
            process_input: function() {

            }
        })
})
