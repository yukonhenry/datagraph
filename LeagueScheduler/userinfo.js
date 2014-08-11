define(["dbootstrap", "dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dojo/keys", "dijit/registry", "dijit/Tooltip", "dijit/ConfirmDialog",
    "dijit/form/ValidationTextBox",
    "dijit/form/Button", "dijit/form/Form", "dijit/form/ValidationTextBox",
    "dijit/layout/ContentPane", "LeagueScheduler/baseinfoSingleton",
    "LeagueScheduler/uistackmanager", "LeagueScheduler/wizuistackmanager",
    "LeagueScheduler/wizardlogic",
    "put-selector/put", "dojo/domReady!"],
    function(dbootstrap, declare, dom, lang, arrayUtil, keys, registry, Tooltip,
        ConfirmDialog, ValidationTextBox, Button, Form, ValidationTextBox,
        ContentPane, baseinfoSingleton, UIStackManager, WizUIStackManager,
        WizardLogic, put) {
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
            userid_name:"", user_cpane:null, tabcontainer:null,
            constructor: function(args) {
                lang.mixin(this, args);
                this.tooltip_list = new Array();
            },
            create: function() {
                // tabcontainer_id defined in index.html
                this.tabcontainer = registry.byId("tabcontainer_id")
                var user_cpane = new ContentPane({
                    title:"User/Organization",
                    id:"user_cpane_id",
                    class:"allonehundred",
                    content:"<br>Welcome to the YukonTR League Scheduler:  Please begin scheduling process by entering an identifier for yourself or organization.  The identifier will be used to save and later retrieve configurations that you have made.<br><br>"
                })
                user_cpane.on("show", function(evt) {
                    console.log("user onshow");
                    user_cpane.domNode.scrollTop = 0;
                })
                user_cpane.on("load", function(evt) {
                    console.log("user onload");
                    user_cpane.domNode.scrollTop = 0;
                })
                this.tabcontainer.addChild(user_cpane);
                this.user_cpane = user_cpane;
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
                        value:'demo',
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
                        //confirm("ID Format is Valid, Creating or Retrieving Entry")
                        var userid_name = username_widget.get("value");
                        this.server_interface.getServerData(
                            'check_user/'+userid_name,
                            lang.hitch(this, this.process_check),
                            null, {userid_name:userid_name});
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
                        content:"User/Org ID: <strong>"+userid_name+"</strong> exists<br> Press OK to confirm, Cancel to select different ID",
                        onExecute: lang.hitch(this, this.user_confirm, userid_name)
                    })
                    idconfirm_dialog.show();
                    // positive result value indicates userid exists
                } else {
                    idconfirm_dialog = new ConfirmDialog({
                        title:"UserID Confirm",
                        content:"New User/Org ID: <strong>"+userid_name+"</strong><br>Press OK to create, Cancel to select different ID",
                        //onExecute: lang.hitch(this, this.create_userid, userid_name)
                        onExecute: lang.hitch(this, function(event) {
                            this.server_interface.getServerData(
                                'create_user/'+userid_name,
                                lang.hitch(this, this.create_user_callback), null,
                                {userid_name:userid_name});
                        })
                    })
                    idconfirm_dialog.show();
                }
            },
            create_user_callback: function(adata, options_obj) {
                // callback func for create_user to server
                this.user_confirm(options_obj.userid_name);
            },
            user_confirm: function(userid_name) {
                // assign to member var userid_name, only after confirmed by user
                // and created in server
                // since userid is used by many other objects, store in
                // baseinfoSingleton, though it will be passed to all of the info
                // objects
                baseinfoSingleton.set_userid_name(userid_name);
                this.userid_name = userid_name;
                //
                this.server_interface.getServerData('get_dbcollection/'+userid_name,
                    lang.hitch(this, this.dbcollection_callback));
            },
            dbcollection_callback: function(adata) {
                var dbcollection_list = [
                    {db_type:'rrdb', db_list:adata.rrdbcollection_list},
                    {db_type:'tourndb', db_list:adata.tourndbcollection_list},
                    {db_type:'fielddb', db_list:adata.fielddb_list},
                    {db_type:'newscheddb', db_list:adata.newscheddb_list},
                    {db_type:'prefdb', db_list:adata.prefdb_list},
                    {db_type:'teamdb', db_list:adata.teamdb_list},
                    {db_type:'conflictdb', db_list:adata.conflictdb_list}];
                // store initial data returned from server
                this.storeutil_obj.store_init_dbcollection(dbcollection_list)
                // create advanced and wiz ui stackmanagers
                var uistackmgr = new UIStackManager();
                this.storeutil_obj.uistackmgr = uistackmgr;
                var wizuistackmgr = new WizUIStackManager();
                this.storeutil_obj.wizuistackmgr = wizuistackmgr;
                var wizardlogic_obj = new WizardLogic({
                    server_interface:this.server_interface,
                    storeutil_obj:this.storeutil_obj,
                    schedutil_obj:this.schedutil_obj,
                    wizuistackmgr:wizuistackmgr,
                    userid_name:this.userid_name});
                var wizcontainer_cpane = wizardlogic_obj.create();
                // create advanced pane
                this.storeutil_obj.init_advanced_UI(this.userid_name);
                this.tabcontainer.selectChild(wizcontainer_cpane);
                this.tabcontainer.removeChild(this.user_cpane);
            }
        })
})
