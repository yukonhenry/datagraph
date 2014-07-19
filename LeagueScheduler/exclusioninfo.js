define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dijit/registry", "dijit/form/NumberTextBox", "dijit/form/ValidationTextBox",
    "dgrid/editor",
    "LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
    "LeagueScheduler/idmgrSingleton",
    "put-selector/put", "dojo/domReady!"],
    function(declare, dom, lang, arrayUtil, registry, NumberTextBox,
        ValidationTextBox, editor,
        baseinfo, baseinfoSingleton, idmgrSingleton, put) {
        var constant = {
            idproperty_str:'exclusion_id', db_type:'exclusiondb',
            dbname_str:"New Exclusion List Name",
            vtextbox_str:'Enter Exclusion List Name',
            ntextbox_str:'Enter Number of Team Exclusions',
            inputnum_str:'Number of Team Conflicts',
            text_node_str:'Exclusion List Name',
            updatebtn_str:'Update Exclusion Info',
        };
        return declare(baseinfo, {
            idproperty:constant.idproperty_str,
            db_type:constant.db_type, idmgr_obj:null,
            divstr_colname:"", divstr_db_type:"rrdb", widgetgen:null,
            constructor: function(args) {
                lang.mixin(this, args);
                baseinfoSingleton.register_obj(this, constant.idproperty_str);
                this.today = new Date();
                this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
                    id:this.idproperty, op_type:this.op_type});
            },
            getcolumnsdef_obj: function() {
                var columnsdef_obj = {
                    exclusion_id:"ID",
                    priority: editor({label:"Priority", autoSave:true,
                        editorArgs:{
                            constraints:{min:1, max:500},
                            promptMessage:'Enter Priority Number (lower is higher priority)',
                            invalidMessage:'Must be Non-zero integer',
                            missingMessage:'Enter Priority',
                            value:'1',
                            //style:'width:6em',
                            style:"width:auto",
                        }}, NumberTextBox),
                    div_1_id: {label:"Division",
                        renderCell: lang.hitch(this, this.div_select_render)
                    },
                    team_1_id: {label:"Team ID",
                        renderCell: lang.hitch(this, this.team_select_render)
                    },
                    div_2_id: {label:"Conflict Division",
                        renderCell: lang.hitch(this, this.div_select_render)
                    },
                    team_2_id: {label:"Conflict Team ID",
                        renderCell: lang.hitch(this, this.team_select_render)
                    },
                }
            },
            initialize: function(newgrid_flag, op_type) {
                var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : op_type;
                var form_reg = registry.byId(this.idmgr_obj.form_id);
                var form_node = form_reg.domNode;
                var dbname_reg = registry.byId(this.idmgr_obj.dbname_id);
                var inputnum_reg = null;
                if (!dbname_reg) {
                    put(form_node, "label.label_box[for=$]",
                        this.idmgr_obj.dbname_id, constant.dbname_str);
                    var dbname_node = put(form_node,
                        "input[id=$][type=text][required=true]",
                        this.idmgr_obj.dbname_id)
                    dbname_reg = new ValidationTextBox({
                        value:'',
                        regExp:'\\D[\\w]+',
                        style:'width:12em',
                        promptMessage:constant.vtextbox_str + '-start with letter or _, followed by alphanumeric or _',
                        invalidMessage:'start with letter or _, followed by alphanumeric characters and _',
                        missingMessage:constant.vtextbox_str
                    }, dbname_node);
                    put(form_node, "span.empty_smallgap");
                    put(form_node, "label.label_box[for=$]",
                        this.idmgr_obj.inputnum_id, constant.inputnum_str);
                    var inputnum_node = put(form_node,
                        "input[id=$][type=text][required=true]",
                        this.idmgr_obj.inputnum_id);
                    inputnum_reg = new NumberTextBox({
                        value:'1',
                        style:'width:5em',
                        constraints:{min:1, max:500},
                        promptMessage:constant.ntextbox_str,
                        invalidMessage:'Must be Non-zero integer',
                        missingMessage:constant.ntextbox_str+' (positive integer)'
                    }, inputnum_node);
                } else {
                    inputnum_reg = registry.byId(this.idmgr_obj.inputnum_id);
                }
                var tooltipconfig_list = [{connectId:[this.idmgr_obj.inputnum_id],
                    label:"Specify Initial Number of Conflicts and press ENTER",
                    position:['below','after']},
                    {connectId:[this.idmgr_obj.dbname_id],
                    label:"Specify Exclusion List Name",
                    position:['below','after']}];
                var args_obj = {
                    dbname_reg:dbname_reg,
                    form_reg:form_reg,
                    entrynum_reg:inputnum_reg,
                    text_node_str: constant.text_node_str,
                    grid_id:this.idmgr_obj.grid_id,
                    updatebtn_str:constant.updatebtn_str,
                    tooltipconfig_list:tooltipconfig_list,
                    newgrid_flag:newgrid_flag,
                    cellselect_flag:true,
                    op_type:op_type
                }
                this.showConfig(args_obj);
            },
            getInitialList: function(num) {
                var info_list = new Array();
                for (var i = 1; i < num+1; i++) {
                    info_list.push({exclusion_id:i, priority:2,
                        div_1_id:"", team_1_id:"",
                        div_2_id:"", team_2_id:""});
                }
                return info_list;
            },
        })
})
