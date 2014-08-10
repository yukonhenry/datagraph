define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dojo/keys", "dijit/registry", "dijit/Tooltip", "dijit/ConfirmDialog",
    "dijit/form/ValidationTextBox",
    "dijit/form/Button", "dijit/form/Form", "dijit/form/ValidationTextBox",
    "dijit/layout/ContentPane", "LeagueScheduler/baseinfoSingleton",
    "put-selector/put", "dojo/domReady!"],
    function(declare, dom, lang, arrayUtil, keys, registry, Tooltip, ConfirmDialog,
        ValidationTextBox, Button, Form, ValidationTextBox, ContentPane,
        baseinfoSingleton, put) {
        var constant = {
            idproperty_str:'user_id',
            init:"init",
            dbtype_str:'userdb',
            idname_str:"Enter User/Organization ID",
            form_id:"userform_id",
            name_id:"username_id",
            btn_id:"userbtn_id"
        };
        return declare(null, {
            idproperty:constant.idproperty_str, keyup_handle:null,
            server_interface:null, tooltip_list:null,
            constructor: function(args) {
                lang.mixin(this, args);
                this.tooltip_list = new Array();
            },
            create: function() {
                // tabcontainer_id defined in index.html
                var tabcontainer = registry.byId("tabcontainer_id")
                var user_cpane = new ContentPane({
                    title:"User/Organization",
                    id:"user_cpane",
                    class:"allonehundred",
                    content:"<br>Welcome to the YukonTR League Scheduler:  Please begin scheduling process by entering identifier for yourself or organization:<br><br>"
                })
                user_cpane.on("show", function(evt) {
                    console.log("user onshow");
                    user_cpane.domNode.scrollTop = 0;
                })
                user_cpane.on("load", function(evt) {
                    console.log("user onload");
                    user_cpane.domNode.scrollTop = 0;
                })
                tabcontainer.addChild(user_cpane);
                var userform_id = constant.form_id;
                var userform_widget = registry.byId(userform_id)
                if (!userform_widget) {
                    // create all elements under the form
                    userform_widget = new Form({
                        id:constant.form_id
                    })
                    user_cpane.addChild(userform_widget);
                    var userform_node = userform_widget.domNode;
                    var username_id = constant.name_id;
                    put(userform_node, "label.label_box[for=$]",
                        username_id, "Enter User or Organization ID (alphanumeric, no spaces)");
                    put(userform_node, "span.empty_tinygap");
                    var username_node = put(userform_node,
                        "input[id=$][type=text][required=true]",
                        username_id)
                    var username_widget = new ValidationTextBox({
                        value:'test',
                        regExp:'\\D[\\w]+',
                        style:'width:12em',
                        promptMessage:constant.idname_str + '-start with letter or _, followed by alphanumeric or _',
                        invalidMessage:'start with letter or _, followed by alphanumeric characters and _, no spaces',
                        missingMessage:constant.idname_str
                    }, username_node);
                    var tooltipconfig = {connectId:[username_id],
                        label:"Specify User/Organization ID and press Enter",
                        position:['below','after']};
                    this.tooltip_list.push(new Tooltip(tooltipconfig));
                    put(userform_node, "span.empty_tinygap");
                    var args_obj = {
                        userform_widget:userform_widget,
                        username_widget:username_widget
                    }
                    var userbtn_node = put(userform_node,
                        "button.dijitButton[id=$][type=submit]", constant.btn_id);
                    var userbtn_widget = new Button({
                        label:"Submit",
                        disabled:false,
                        class:"success",
                        onClick: lang.hitch(this, this.process_input, args_obj)
                    }, userbtn_node);
                    userbtn_widget.startup();
                    if (this.keyup_handle)
                        this.keyup_handle.remove();
                    this.keyup_handle = username_widget.on("keyup", lang.hitch(this, this.process_input, args_obj));
                } else {
                    username_widget = registry.byId(username_id);
                }
            },
            process_input: function(args_obj, event) {
                if (event.type == "click" ||
                    (event.type == "keyup" && event.keyCode == keys.ENTER)) {
                    var userform_widget = args_obj.userform_widget;
                    var username_widget = args_obj.username_widget;
                    if (userform_widget.validate()) {
                        confirm("ID Format is Valid, Creating or Retrieving Entry")
                        var userid_name = username_widget.get("value");
                        this.server_interface.getServerData(
                            'check_user/'+userid_name,
                            lang.hitch(this, this.process_check),
                            {userid_name:userid_name});
                    }
                    if (this.keyup_handle)
                        this.keyup_handle.remove();
                }
            },
            process_check: function(adata, options_obj) {
                var userid_name = options_obj.userid_name;
                var result = adata.result;
                var idconfirm_dialog = null;
                if (result) {
                    idconfirm_dialog = new ConfirmDialog({
                        title:"UserID Confirm",
                        content:"User/Org ID "+userid_name+" exists; Press OK to confirm, Cancel to select different ID"
                    })
                    idconfirm_dialog.show();
                    // positive result value indicates userid exists
                    baseinfoSingleton.set_userid_name(userid_name);
                    this.storeutil_obj.enable_menu(userid_name);
                } else {
                    idconfirm_dialog = new ConfirmDialog({
                        title:"UserID Confirm",
                        content:"New User/Org ID "+userid_name+"; Press OK to create, Cancel to select different ID"
                    })
                    idconfirm_dialog.show();
                }
            }
        })
})
