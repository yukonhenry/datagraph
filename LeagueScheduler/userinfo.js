define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dojo/keys", "dijit/registry", "dijit/Tooltip", "dijit/form/ValidationTextBox",
    "dijit/form/Button", "put-selector/put", "LeagueScheduler/baseinfo",
    "dojo/domReady!"],
    function(declare, dom, lang, arrayUtil, keys, registry, Tooltip,
        ValidationTextBox, Button, put, baseinfo) {
        var constant = {
            idproperty_str:'user_id',
            init:"init",
            dbtype_str:'userdb',
            idname_str:"Enter User/Organization ID",
        };
        return declare(baseinfo, {
            idproperty:constant.idproperty_str,
            userid_name:"",
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
                var idname_id = this.idmgr_obj.idname_id;
                var idname_widget = null;
                var idname_node = dom.byId(idname_id);
                if (!idname_node) {
                    put(form_node, "label.label_box[for=$]",
                        idname_id, constant.idname_str);
                    put(form_node, "span.empty_tinygap");
                    idname_node = put(form_node,
                        "input[id=$][type=text][required=true]",
                        idname_id)
                    idname_widget = new ValidationTextBox({
                        value:'',
                        regExp:'\\D[\\w]+',
                        style:'width:12em',
                        promptMessage:constant.idname_str + '-start with letter or _, followed by alphanumeric or _',
                        invalidMessage:'start with letter or _, followed by alphanumeric characters and _',
                        missingMessage:constant.idname_str
                    }, idname_node);
                    // define tooltip help
                    var tooltipconfig = {connectId:[idname_id],
                        label:"Specify User/Organization ID and press Enter",
                        position:['below','after']};
                    this.tooltip_list.push(new Tooltip(tooltipconfig));
                    put(form_node, "span.empty_tinygap");
                    var args_obj = {
                        idname_widget:idname_widget,
                        form_widget:form_widget
                    }
                    var btn_node = put(form_node,
                        "button.dijitButton[id=$][type=submit]", btn_id);
                    var btn_widget = new Button({
                        label:"Submit",
                        disabled:false,
                        class:"success",
                        onClick: lang.hitch(this, this.process_input, args_obj)
                    }, btn_node);
                    btn_widget.startup();
                } else {
                    idname_widget = registry.byId(idname_id);
                }
                this.uistackmgr_type.switch_pstackcpane({idproperty:this.idproperty,
                    p_stage: "preconfig", entry_pt:constant.init});
                if (this.keyup_handle)
                    this.keyup_handle.remove();
                this.keyup_handle = idname_widget.on("keyup", lang.hitch(this, this.process_input, args_obj));
            },
            process_input: function(args_obj, event) {
                if (event.type == "click" ||
                    (event.type == "keyup" && event.keyCode == keys.ENTER)) {
                    var form_widget = args_obj.form_widget;
                    var idname_widget = args_obj.idname_widget;
                    if (form_widget.validate()) {
                        confirm("ID Format is Valid, Creating or Retrieving Entry")
                        this.userid_name = idname_widget.get("value");
                    }
                }
            },
            enable_menu: function(adata) {

            }
        })
})
