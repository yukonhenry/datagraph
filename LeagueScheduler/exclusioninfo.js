define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dijit/registry", "dijit/form/NumberTextBox", "dijit/form/ValidationTextBox",
    "dijit/form/Select", "dgrid/editor",
    "LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
    "LeagueScheduler/idmgrSingleton",
    "put-selector/put", "dojo/domReady!"],
    function(declare, dom, lang, arrayUtil, registry, NumberTextBox,
        ValidationTextBox, Select, editor,
        baseinfo, baseinfoSingleton, idmgrSingleton, put) {
        var constant = {
            idproperty_str:'exclusion_id', db_type:'exclusiondb',
            dbname_str:"New Exclusion List Name",
            vtextbox_str:'Enter Exclusion List Name',
            ntextbox_str:'Enter Number of Team Exclusions',
            inputnum_str:'Number of Team Conflicts',
            text_node_str:'Exclusion List Name',
            updatebtn_str:'Update Exclusion Info',
            div_select_base:"exdiv_select",
            team_select_base:"exteam_select"
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
                return columnsdef_obj;
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
            get_gridhelp_list: function() {
                var gridhelp_list = [
                    {id:'exclusion_id', help_str:"Identifier, Non-Editable"},
                    {id:'priority',
                        help_str:"Priority of the conflict - assign positive integer, lower value is higher priority"},
                    {id:'div_1_id',
                        help_str:"Select Division for the first conflict team"},
                    {id:'team_1_id',
                        help_str:"Select Team ID for the first conflict team"},
                    {id:'div_2_id',
                        help_str:"Select Division for the second conflict team"},
                    {id:'team_2_id',
                        help_str:"Select Team ID for the second conflict team"}]
                return gridhelp_list;
            },
            div_select_render: function(object, data, node) {
                var exclusion_id = object.exclusion_id;
                // .columnId gives the column name
                var div_select_prefix = this.op_prefix+constant.div_select_base+
                    node.columnId;
                // get unique widget id
                var div_select_id = div_select_prefix+exclusion_id+"_id";
                var div_select_widget = registry.byId(div_select_id);
                var divstr_list = baseinfoSingleton.get_watch_obj('divstr_list',
                    this.op_type, 'exclusion_id');
                var option_list = new Array();
                var eventoptions_obj = null;
                if (divstr_list && divstr_list.length > 0) {
                    option_list.push({label:"Select Division", value:"",
                        selected:false, totalteams:0});
                    arrayUtil.forEach(divstr_list, function(item) {
                        var option_obj = {label:item.divstr, value:item.div_id,
                            selected:false, totalteams:item.totalteams}
                        // data value is read from the store and corresponds to
                        // stored div_id value for that row
                        if (item.div_id == data) {
                            option_obj.selected = true;
                        }
                        option_list.push(option_obj);
                    })
                    // create options list to pass to the team select event handler
                    eventoptions_obj = {exclusion_id:exclusion_id,
                        // slice leaves out the 0-th element
                        option_list:option_list.slice(1)}
                } else {
                    // default if no divstr_list is read in
                    option_list.push({label:"Select League first", selected:true, value:""});
                }
                // create select node to place widget - use passed in node as reference
                if (!div_select_widget) {
                    var select_node = put(node, "select");
                    div_select_widget = new Select({
                        options:option_list, style:"width:auto",
                        id:div_select_id,
                    }, select_node)
                } else {
                    div_select_widget.set("options", option_list)
                    // NOTE - if widget exists, it should already be attached to
                    // node - confirm why we did the appendChild here again
                    node.appendChild(div_select_widget.domNode)
                }
                if (eventoptions_obj) {
                    div_select_widget.set("onChange",
                        lang.hitch(this, this.set_gridteam_select, eventoptions_obj))
                }
                div_select_widget.startup();
            },
            team_select_render: function(object, data, node) {
                var exclusion_id = object.exclusion_id;
                // node.columnId gives the column id where the rendering
                // is occuring
                var columnId = node.columnId;
                // extract of the column number (str type) in embedded in columnId
                // example: extract '1' from team_1_id, '2' from team_2_id, etc
                var column_num_str = columnId.substring(columnId.indexOf('_')+1,
                    columnId.lastIndexOf('_'))
                var div_id = object['div_'+column_num_str+'_id']
                var team_select_prefix = this.op_prefix+
                    constant.team_select_base+columnId;
                // get unique widget id
                var team_select_id = team_select_prefix+exclusion_id+"_id";
                var team_select_widget = registry.byId(team_select_id);
                var option_list = new Array();
                var divstr_list = baseinfoSingleton.get_watch_obj('divstr_list',
                    this.op_type, 'exclusion_id');
                if (divstr_list && divstr_list.length > 0) {
                    var match_obj = arrayUtil.filter(divstr_list,
                        function(item) {
                        return item.div_id == div_id;
                    })[0];
                    for (var team_id = 1; team_id < match_obj.totalteams+1;
                        team_id++) {
                        var option_obj = {label:team_id.toString(),
                            value:team_id, selected:false};
                        if (team_id == data) {
                            option_obj.selected = true;
                        }
                        option_list.push(option_obj);
                    }
                } else {
                    option_list.push({label:"Select Division first", selected:true, value:""});
                }
                // create select node to place widget - use passed in node as reference
                if (!team_select_widget) {
                    var select_node = put(node, "select");
                    team_select_widget = new Select({
                        options:option_list, style:"width:auto",
                        id:team_select_id,
                        onChange: lang.hitch(this, function(event) {
                            var exclusion_obj = this.editgrid.schedInfoStore.get(
                                exclusion_id);
                            exclusion_obj['team_'+column_num_str+'_id'] = event;
                            this.editgrid.schedInfoStore.put(exclusion_obj);
                        })
                    }, select_node)
                } else {
                    team_select_widget.set("options", option_list)
                    node.appendChild(team_select_widget.domNode);
                }
                team_select_widget.startup();
            },
            set_griddiv_select: function(divstr_list) {
                // called from baseinfoSingleton watch obj callback for division
                // string list
                // baseinfoSingleton has already done a check for existence of
                // editgrid obj and grid itself
                // Reference newschedulerbase/createdivselect_dropdown and
                // also same method in prefinfo
                var exclusion_grid = this.editgrid.schedInfoGrid;
                // initialize option_list for the select dropdown in the
                // select div dropdowns (ome for each conflict config)
                var option_list = [{label:"Select Division", value:"",
                    selected:true, totalteams:0}];
                arrayUtil.forEach(divstr_list, function(item, index) {
                    option_list.push({label:item.divstr, value:item.div_id,
                        selected:false, totalteams:item.totalteams})
                })
                var div_select_base = this.op_prefix+constant.div_select_base;
                arrayUtil.forEach(['div_1_id', 'div_2_id'], function(col_id) {
                    // iterate for each div_id selection columns (one for each
                    // conflict)
                    var div_select_prefix = div_select_base + col_id;
                    for (var row_id = 1; row_id < this.totalrows_num+1;
                        row_id++) {
                        var div_select_id = div_select_prefix+row_id+"_id";
                        var div_select_widget = registry.byId(div_select_id);
                        if (div_select_widget) {
                            // the select widget should be there, but check for existence anyway
                            var copy_list = lang.clone(option_list);
                            div_select_widget.set("options", copy_list);
                            var options_obj = {
                                divcol_id:col_id,
                                exclusion_id:row_id,
                                option_list:option_list.slice(1)
                            }
                            div_select_widget.set("onChange", lang.hitch(this,
                                this.set_gridteam_select, options_obj));
                            div_select_widget.startup();
                        }
                    }
                }, this);
            },
            set_gridteam_select: function(options_obj, divevent) {
                // set select dropdown for team id column in the exclusion grid
                var divoption_list = options_obj.option_list;
                var exclusion_id = options_obj.exclusion_id;
                var divcol_id = options_obj.divcol_id;
                var exclusion_obj = this.editgrid.schedInfoStore.get(exclusion_id);
                exclusion_obj[divcol_id] = divevent;
                this.editgrid.schedInfoStore.put(exclusion_obj);
                // find the totalteams match corresponding to the div_id event
                var match_option = arrayUtil.filter(divoption_list,
                    function(item) {
                        return item.value == divevent;
                    })[0]
                var option_list = [{label:"Select Team", value:"",
                    selected:true}];
                for (var team_id = 1; team_id < match_option.totalteams+1;
                    team_id++) {
                    option_list.push({label:team_id.toString(), value:team_id, selected:false})
                }
                var column_num_str = divcol_id.substring(divcol_id.indexOf('_')+1,
                    divcol_id.lastIndexOf('_'))
                var teamcol_id = 'team_'+column_num_str+'_id';
                var team_select_prefix = this.op_prefix+
                    constant.team_select_base+teamcol_id;
                var team_select_id = team_select_prefix+exclusion_id+"_id";
                var team_select_widget = registry.byId(team_select_id);
                if (team_select_widget) {
                    team_select_widget.set("options", option_list);
                    /*
                    team_select_widget.set("onChange", lang.hitch(this, function(event) {
                        var pref_obj = this.editgrid.schedInfoStore.get(pref_id);
                        pref_obj.team_id = event;
                        this.editgrid.schedInfoStore.put(pref_obj);
                    })) */
                    team_select_widget.startup()
                }
            }
        })
})
