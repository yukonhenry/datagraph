define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
    "dijit/registry", "dijit/form/NumberTextBox", "dijit/form/ValidationTextBox",
    "dijit/form/Select", "dgrid/Editor",
    "scheduler_front/baseinfo", "scheduler_front/baseinfoSingleton",
    "scheduler_front/idmgrSingleton",
    "put-selector/put", "dojo/domReady!"],
    function(declare, dom, lang, arrayUtil, registry, NumberTextBox,
        ValidationTextBox, Select, editor,
        baseinfo, baseinfoSingleton, idmgrSingleton, put) {
        var constant = {
            idproperty_str:'conflict_id', db_type:'conflictdb',
            dbname_str:"New Conflict List Name",
            vtextbox_str:'Enter Conflict List Name',
            ntextbox_str:'Enter Number of Team Conflicts',
            inputnum_str:'Number of Team Conflicts',
            text_node_str:'Conflict List Name',
            updatebtn_str:'Update Conflict Info',
            div_select_base:"exdiv_select",
            team_select_base:"exteam_select",
            //******************//
            // Change Maps below if grid design (with respect to columns) changes
            //******************//
            // define map from info_obj table column property to
            // parameters (column number of table derived from node.columnId)
            // the map value is used to construct the id for the select widget
            // corresponding to div_1_id, div_2_id respectively.
            divselect_id_map:{div_1_id:"2", div_2_id:"4"},
            reverse_divselect_id_map:{"2":"div_1_id", "4":"div_2_id"},
            // similar mapping for team select id generation
            // obj values correspond to column numbers for the conflict info grid
            teamselect_id_map:{div_1_id:"3", div_2_id:"5"},
            reverseteamselect_id_map:{'3':"div_1_id", '5':"div_2_id"}
        };
        return declare(baseinfo, {
            idproperty:constant.idproperty_str,
            store_idproperty:"col"+constant.idproperty_str,
            db_type:constant.db_type, idmgr_obj:null,
            divstr_colname:"", divstr_db_type:"rrdb", widgetgen:null,
            constructor: function(args) {
                lang.mixin(this, args);
                baseinfoSingleton.register_obj(this, constant.idproperty_str);
                this.today = new Date();
                this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
                    id:this.idproperty, op_type:this.op_type,
                    sched_type:this.sched_type});
            },
            getcolumnsdef_obj: function() {
                var columnsdef_list = [
                    {field:"conflict_id", label:"ID"},
                    {field:"priority", label:"Priority", autoSave:true,
                        editorArgs:{
                            constraints:{min:1, max:500},
                            promptMessage:'Enter Priority Number (lower is higher priority)',
                            invalidMessage:'Must be Non-zero integer',
                            missingMessage:'Enter Priority',
                            value:'1',
                            //style:'width:6em',
                            style:"width:auto",
                        }, editor:NumberTextBox},
                    {field:"div_1_id", label:"Division",
                        renderCell: lang.hitch(this, this.div_select_render)
                    },
                    {field:"team_1_id", label:"Team ID",
                        renderCell: lang.hitch(this, this.team_select_render)
                    },
                    {field:"div_2_id", label:"Conflict Division",
                        renderCell: lang.hitch(this, this.div_select_render)
                    },
                    {field:"team_2_id", label:"Conflict Team ID",
                        renderCell: lang.hitch(this, this.team_select_render)
                    },
                ]
                return columnsdef_list;
            },
            getfixedcolumnsdef_obj: function() {
                // col definition for displaying conflict satisfaction cpane
                // after schedule is generated
                var columnsdef_obj = {
                    conflict_id:"Conflict ID",
                    priority:"Priority",
                    div_1_id:"Division", team_1_id:"Team",
                    div_2_id:"Conflict Division", team_2_id:"Conflict Team",
                    conflict_num:"Game Conflicts",
                    conflict_avoid:"Avoided"
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
                    label:"Specify Conflict List Name",
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
            getInitialList: function(num, colname) {
                var info_list = new Array();
                for (var i = 1; i < num+1; i++) {
                    info_list.push({conflict_id:i, priority:2,
                        div_1_id:"", team_1_id:"",
                        div_2_id:"", team_2_id:"",
                        colconflict_id:this.startref_id+i,
                        colname:colname});
                }
                this.startref_id += num;
                return info_list;
            },
            getServerDBInfo: function(options_obj) {
                // note third parameter maps to query object, which in this case
                // there is none.  But we need to provide some argument as js does
                // not support named function arguments.  Also specifying "" as the
                // parameter instead of null might be a better choice as the query
                // object will be emitted in the jsonp request (though not consumed
                // at the server)
                if (!('op_type' in options_obj))
                    options_obj.op_type = this.op_type;
                options_obj.cellselect_flag = false;
                options_obj.text_node_str = "Conflict List Name";
                options_obj.grid_id = this.idmgr_obj.grid_id;
                options_obj.updatebtn_str = constant.updatebtn_str;
                options_obj.db_type = constant.db_type;
                this.inherited(arguments);
            },
            get_gridhelp_list: function() {
                var gridhelp_list = [
                    {id:'conflict_id', help_str:"Identifier, Non-Editable"},
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
            modify_toserver_data: function(raw_result) {
                var newlist = arrayUtil.map(raw_result, function(item) {
                    // leave out dt_id to send to server (recreate when
                    // data returned from server)
                    return {conflict_id:item.conflict_id,
                        priority:item.priority,
                        div_1_id:item.div_1_id, div_2_id:item.div_2_id,
                        team_1_id:item.team_1_id, team_2_id:item.team_2_id
                    }
                })
                return newlist;
            },
            modifyserver_data: function(data_list, divstr_obj) {
                // see comments for fieldinfo modifyserver_data - process divstr
                // data; separately process data_list (especially dates)
                this.divstr_colname = divstr_obj.colname;
                this.divstr_db_type = divstr_obj.db_type;
                var config_status = divstr_obj.config_status;
                var info_list = divstr_obj.info_list;
                /*
                info_list.sort(function(a,b) {
                    return a.div_id-b.div_id
                }) */
                // create radio button pair to select
                // schedule type - rr or tourn
                var infogrid_node = dom.byId(this.idmgr_obj.grid_id);
                var topdiv_node = put(infogrid_node, "-div");
                if (this.divstr_colname && this.divstr_db_type) {
                    this.create_dbselect(
                        this.idmgr_obj.league_select_id,
                        this.divstr_db_type, this.divstr_colname, topdiv_node);
                } else {
                    this.initabovegrid_UI(topdiv_node);
                }
                if (config_status) {
                    var divstr_list = arrayUtil.map(info_list,
                    function(item) {
                        return {'divstr':item.div_age + item.div_gen,
                            'div_id':item.div_id, 'totalteams':item.totalteams};
                    })
                    baseinfoSingleton.set_watch_obj('divstr_list', divstr_list,
                        this.op_type, 'conflict_id');
                }
                return data_list;
            },
            div_select_render: function(object, data, node) {
                var conflict_id = object.conflict_id;
                // .columnId gives the column name
                var div_select_prefix = this.op_prefix+constant.div_select_base+
                    node.columnId;
                // get unique widget id
                var divselect_id = div_select_prefix+conflict_id+"_id";
                var div_select_widget = registry.byId(divselect_id);
                var divstr_list = baseinfoSingleton.get_watch_obj('divstr_list',
                    this.op_type, 'conflict_id');
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
                    // structure should be identical to the options_obj created
                    // in
                    eventoptions_obj = {conflict_id:conflict_id,
                        // slice leaves out the 0-th element
                        option_list:option_list.slice(1),
                        divcol_id: constant.reverse_divselect_id_map[node.columnId] }
                } else {
                    // default if no divstr_list is read in
                    option_list.push({label:"Select League first", selected:true, value:""});
                }
                // create select node to place widget - use passed in node as reference
                if (!div_select_widget) {
                    var select_node = put(node, "select");
                    div_select_widget = new Select({
                        options:option_list, style:"width:auto",
                        id:divselect_id,
                    }, select_node);
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
                var conflict_id = object.conflict_id;
                // node.columnId gives the column id where the rendering
                // is occuring
                var columnId = node.columnId;
                // changes due to dgrid 0.4 transition
                var div_id_key = constant.reverseteamselect_id_map[columnId];
                var key_id = div_id_key.substring(div_id_key.indexOf('_')+1,
                    div_id_key.lastIndexOf('_'));
                var div_id = object[div_id_key]
                var team_select_prefix = this.op_prefix+
                    constant.team_select_base+columnId;
                // get unique widget id
                var team_select_id = team_select_prefix+conflict_id+"_id";
                var team_select_widget = registry.byId(team_select_id);
                var option_list = new Array();
                var divstr_list = baseinfoSingleton.get_watch_obj('divstr_list',
                    this.op_type, 'conflict_id');
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
                            var infostore = this.editgrid.schedInfoStore;
                            infostore.get(conflict_id).then(
                            function(conflict_obj) {
                                conflict_obj['team_'+key_id+'_id'] = event;
                                infostore.put(conflict_obj);
                            });
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
                var conflict_grid = this.editgrid.schedInfoGrid;
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
                    var div_select_prefix = div_select_base +
                        constant.divselect_id_map[col_id];
                    for (var row_id = 1; row_id < this.totalrows_num+1;
                        row_id++) {
                        var divselect_id = div_select_prefix+row_id+"_id";
                        var div_select_widget = registry.byId(divselect_id);
                        if (div_select_widget) {
                            // the select widget should be there, but check for existence anyway
                            var copy_list = lang.clone(option_list);
                            div_select_widget.set("options", copy_list);
                            var options_obj = {
                                divcol_id:col_id,
                                conflict_id:row_id,
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
                // set select dropdown for team id column in the conflict grid
                var divoption_list = options_obj.option_list;
                var conflict_id = options_obj.conflict_id;
                var divcol_id = options_obj.divcol_id;
                this.editgrid.schedInfoStore.get(conflict_id).then(
                    lang.hitch(this, function(conflict_obj) {
                        conflict_obj[divcol_id] = divevent;
                        this.editgrid.schedInfoStore.put(conflict_obj);
                    })
                );
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
                var teamcol_id = constant.teamselect_id_map[divcol_id]
                var team_select_prefix = this.op_prefix+
                    constant.team_select_base+teamcol_id;
                var team_select_id = team_select_prefix+conflict_id+"_id";
                var team_select_widget = registry.byId(team_select_id);
                if (team_select_widget) {
                    team_select_widget.set("options", option_list);
                    team_select_widget.startup()
                }
            },
            checkconfig_status: function(raw_result) {
                // check if config is complete.  For conflict_info, also check to
                // make sure div_id's are different within the same conflict id.
                // Conflicts involving two more teams in the same division are not
                // supported as teams will need to play each other at the same
                // time slot.
                var config_status = 0;
                var alert_msg = "";
                if (arrayUtil.some(raw_result, function(item) {
                    // if .some returns true, then there was at least one
                    // condition detected that indicates config is Not complete.
                    var break_flag = false;
                    for (var prop in item) {
                        if (item[prop] === "") {
                            alert_msg = "Empty Field column "+prop;
                            break_flag = true;
                            break;
                        }
                    }
                    if (item.div_1_id == item.div_2_id) {
                        alert_msg = "Conflict must be from different divs";
                        break_flag = true;
                    }
                    return break_flag;
                })) {
                    console.log("Not all fields complete or legal for "+
                        this.idproperty+" but saving");
                    alert(alert_msg);
                } else {
                    config_status = 1;
                }
                return config_status;
            }
         })
})
