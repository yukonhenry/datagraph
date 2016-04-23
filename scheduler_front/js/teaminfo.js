define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dijit/form/TextBox", "dijit/form/NumberTextBox",
	"dijit/form/DropDownButton", "dijit/form/Select", "dgrid/Editor", "dijit/TooltipDialog",
	"dijit/form/CheckBox", "dijit/form/Button",
	"dijit/form/Form", "dijit/layout/StackContainer", "dijit/layout/ContentPane",
	"scheduler_front/baseinfo", "scheduler_front/baseinfoSingleton",
	"scheduler_front/idmgrSingleton", "scheduler_front/editgrid",
	"put-selector/put", "dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, TextBox, NumberTextBox,
		DropDownButton, Select, editor, TooltipDialog, CheckBox, Button,
		Form, StackContainer,
		ContentPane, baseinfo,
		baseinfoSingleton, idmgrSingleton, EditGrid, put){
		var constant = {
			idproperty_str:'team_id', db_type:'teamdb',
			dbname_str:'New Team List Name',
			vtextbox_str:'Enter Team List Name',
			ntextbox_str:'Enter Number of Teams',
			inputnum_str:'Number of Teams',
			text_node_str:'League/Division List Name',
			updatebtn_str:'Update Team Info',
			day_list:['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
			// entry_pt id's
			init:"init", fromdb:"fromdb",  fromdel:"fromdel",
		};
		return declare(baseinfo, {
			idproperty:constant.idproperty_str,
			store_idproperty:"dt_id",
			db_type:constant.db_type,
			//divstr_colname, divstr_db_type, widgetgen are all member var's
			// that have to do with the db_type radiobutton /
			// league select drop down
			divstr_colname:"", divstr_db_type:"rrdb", widgetgen:null,
			divfield_list:null, serverinfo_list:null,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
				this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
					id:this.idproperty, op_type:this.op_type,
					sched_type:this.sched_type});
			},
			getcolumnsdef_obj: function() {
				var columnsdef_list = [
					{field: "tm_id", label: "ID"},
					{field: "tm_name", label:"Team Name", autoSave:true,
						editorArgs:{trim:true, style:"width:auto"},
						editor:TextBox, editOn:"click"},
					{field: "af_list", label:"Home Field(s)",
						renderCell: lang.hitch(this, this.af_field_render)},
					{field: "prefdays", label: "Preferred Week Days",
					 renderCell: lang.hitch(this, this.prefdays_render)},
					{field:"priority", label:"Priority", autoSave:true,
						editorArgs:{
							constraints:{min:1, max:500},
							promptMessage:'Enter Priority Number (lower is higher priority)',
							invalidMessage:'Must be Non-zero integer',
							missingMessage:'Enter Priority',
							value:'1',
							style:"width:auto",
						}, editor:NumberTextBox},
				];
				return columnsdef_list;
			},
			getfixedcolumnsdef_obj: function() {
				// column definition for constraint satisfaction cpane display
				// after schedule is generated
				var columnsdef_obj = {
					tm_id:"Team ID",
					priority:"Priority",
					prefdays:"Preference Days",
					satisfy:"Met"
				}
				return columnsdef_obj;
			},
			modifyserver_data: function(data_list, divstr_obj) {
			},
			modify_toserver_data: function(raw_result) {
				//var filtered = arrayUtil.filter(raw_result, function(item) {
				//	return item.af_list.length > 0 || item.prefdays
				//})
				var newlist = arrayUtil.map(raw_result, function(item) {
					// leave out dt_id to send to server (recreate when
					// data returned from server)
					return {tm_id:item.tm_id, tm_name:item.tm_name, priority: item.priority,
						af_list:item.af_list, div_id:item.div_id, prefdays: item.prefdays}
				})
				return newlist;
			},
			initialize: function(newgrid_flag, op_type) {
				var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : op_type;
				var param_cpane = registry.byId(this.idmgr_obj.numcpane_id);
				//var topdiv_node = put("div");
				this.initabovegrid_UI(param_cpane.containerNode);
				this.uistackmgr_type.switch_pstackcpane({idproperty:this.idproperty,
					p_stage: "preconfig", entry_pt:constant.init});
				// switch to blank cpane
				this.uistackmgr_type.switch_gstackcpane(this.idproperty, true);
				this.checkdelete_txtbtn();
				// null out member var that tracks server data
				this.serverinfo_list = null;
			},
			getServerDBInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				// switch gstack cpane to blank
				// how pstack cpane will go direct to config
				this.uistackmgr_type.switch_gstackcpane(this.idproperty, true);
				// delete text btn nodes so that we can recreate them again
				this.checkdelete_txtbtn();
				if (!('op_type' in options_obj))
					options_obj.op_type = this.op_type;
				options_obj.cellselect_flag = false;
				options_obj.text_node_str = constant.text_node_str;
				options_obj.grid_id = this.idmgr_obj.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				var item = options_obj.item;
				// define key for object returned from server to get
				// status of configuration - config_status
				this.server_interface.getServerData("get_dbcol/"+
					this.userid_name+'/'+constant.db_type+'/'+options_obj.item+'/'+this.sched_type,
					lang.hitch(this, this.prepgrid_data));
			},
			getInitialList: function(num, div_id, colname) {
				var info_list = new Array();
				for (var i = 1; i < num+1; i++) {
					info_list.push({tm_id:i, tm_name:"", af_list:[],
					div_id:div_id, dt_id:"dv"+div_id+"tm"+i,
					colname:colname, prefdays: "", priority: i});
				}
				this.startref_id += num;
				return info_list;
			},
			get_gridhelp_list: function() {
				var gridhelp_list = [
					{id:'tm_id', help_str:"Identifier, Non-Editable"},
					{id:'tm_name', help_str:"Enter Team Name or Identifier"},
					{id:"af_list", help_str:"Select Field Preferences for Home Games, if any (default all fields assigned to division)"},
					{id:"prefdays", help_str:"Select Days-of_Week Preference for Team, if any"},
					{id:'priority', help_str:"Priority of the preference - assign positive integer, lower value is higher priority"},
				]
				return gridhelp_list;
			},
			prepgrid_data: function(server_data) {
				// handler for teamid server data
				// first extract divstr info - colname and db_type
				var divstr_obj = server_data.divstr_obj;
				if (divstr_obj.config_status) {
					this.divstr_colname = divstr_obj.colname;
					this.divstr_db_type = divstr_obj.db_type;
				}
				// get data that will be sent to store to create grid
				this.serverinfo_list = server_data.info_list;
				var divstr_list = divstr_obj.info_list;
				/*
				divstr_list.sort(function(a,b) {
					return a.div_id-b.div_id
				}); */
				arrayUtil.forEach(divstr_list, function(item) {
					item.divstr = item.div_age+item.div_gen;
				})
				this.set_div_select(divstr_list);
			},
			set_div_select: function(divstr_list) {
				var option_list = [{label:"Select Division", value:"",
						selected:true, totalteams:0}]
				if (divstr_list && divstr_list.length > 0) {
					arrayUtil.forEach(divstr_list, function(item) {
						var option_obj = {label:item.divstr, value:item.div_id,
							selected:false, totalteams:item.totalteams,
							divfield_list:item.divfield_list}
						// data value is read from the store and corresponds to
						// stored div_id value for that row
						option_list.push(option_obj);
					})
				}
				var divselect_id = this.op_prefix+"tm_divselect_id";
				var divselect_widget = registry.byId(divselect_id);
				if (!divselect_widget) {
					// place division select above grid (division select) should
					// always be visible when grid is present
					var topdiv_node = registry.byId(this.idmgr_obj.textbtncpane_id).containerNode;
					put(topdiv_node, "label.label_box[for=$]",
						divselect_id, "Select Division");
					var divselect_node = put(topdiv_node,
						"select[id=$][name=$]", divselect_id, divselect_id);
					var eventoptions_obj = {option_list:option_list.slice(1),
						topdiv_node:topdiv_node};
					var divselect_widget = new Select({
						//name:name_str,
						options:option_list,
						onChange: lang.hitch(this, this.create_team_grid, eventoptions_obj)
					}, divselect_node);
				} else {
					// reset option list, with initial selection back to default
					divselect_widget.set("options", option_list);
				}
				divselect_widget.startup();
				this.uistackmgr_type.switch_pstackcpane({idproperty:this.idproperty,
					p_stage: "config", entry_pt:constant.init});
				//this.uistackmgr_type.switch_gstackcpane(this.idproperty, true);
			},
			create_team_grid: function(options_obj, div_id_event) {
				// create_team_grid may be called even if there is an existing grid:
				// a different division may be selected.  In that case a local
				// sotre will exist
				var option_list = options_obj.option_list;
				var topdiv_node = options_obj.topdiv_node;
				var text_id = this.idmgr_obj.text_id;
				var args_obj = null;
				var span_node = dom.byId(text_id);
				if (!span_node) {
					put(topdiv_node, "span.empty_smallgap[id=$]", text_id);
				}
				var btn_id = this.idmgr_obj.btn_id;
				var btn_node = dom.byId(btn_id);
				if (!btn_node) {
					put(topdiv_node, "button[id=$]", this.idmgr_obj.btn_id);
				}
				var match_option = arrayUtil.filter(option_list,
					function(item) {
						return item.value == div_id_event;
					})[0]
				this.totalrows_num = match_option.totalteams;
				this.divfield_list = match_option.divfield_list;
				// name for the team list in teaminfo obj is restricted to be
				// a division id name
				this.activegrid_colname = this.divstr_colname;
				// check if there is a local store
				var info_list = null;
				// query object for the store - use query to filter display to grid
				// in this example, show only the data where div_id matches -
				// div_id is determined by the division select
				var query_obj = {div_id:div_id_event}
				if (this.is_newgrid_required()) {
					var columnsdef_obj = this.getcolumnsdef_obj();
					if (this.serverinfo_list && this.serverinfo_list.length > 0) {
						// if server data is available use that
						info_list = this.serverinfo_list;
						// check that the server data includes current
						// div_id data; if not, append initialization data
						if (!arrayUtil.some(info_list, function(item) {
							return item.div_id == div_id_event;
						})) {
							info_list = info_list.concat(this.getInitialList(
								this.totalrows_num, div_id_event,
								this.activegrid_colname));
						}
					} else {
						info_list = this.getInitialList(this.totalrows_num,
						div_id_event, this.activegrid_colname);
					}
					info_list.sort(function(a,b) {
						return a.tm_id-b.tm_id
					});
					this.editgrid = new EditGrid({
						griddata_list:info_list,
						colname:this.activegrid_colname,
						server_interface:this.server_interface,
						grid_id:this.idmgr_obj.grid_id,
						idproperty:this.idproperty,
						store_idproperty:this.store_idproperty,
						cellselect_flag:false,
						info_obj:this, userid_name:this.userid_name,
						uistackmgr_type:this.uistackmgr_type,
						storeutil_obj:this.storeutil_obj,
						db_type:this.db_type
					})
					this.editgrid.recreateSchedInfoGrid(columnsdef_obj, query_obj);
					args_obj = {
						newgrid_flag:true
					}
				} else {
					if (this.infogrid_store) {
						// for dstore, all queries are promise-based
						// http://dstorejs.io
						this.infogrid_store.filter(query_obj).fetch().then(lang.hitch(this, function(results) {
							if (results.length > 0) {
								// store already provides data for the div_id, just
								// do a store query switch
								args_obj = {colname:this.activegrid_colname,
									queryonly_flag:true, query_obj:query_obj}
							} else {
								if (this.serverinfo_list && this.serverinfo_list.length > 0) {
									// if server data exists, use that
									info_list = this.serverinfo_list;
									// check that the server data includes current
									// div_id data; if not, append initialization data
									if (!arrayUtil.some(info_list, function(item) {
										return item.div_id == div_id_event;
									})) {
										info_list = info_list.concat(
											this.getInitialList(this.totalrows_num,
												div_id_event, this.activegrid_colname));
									}
								} else {
									// if div_id data does not exist, add initilization data
									info_list = this.getInitialList(
										this.totalrows_num, div_id_event,
										this.activegrid_colname);
								}
								info_list.sort(function(a,b) {
									return a.tm_id-b.tm_id
								});
								args_obj = {
									colname:this.activegrid_colname,
									griddata_list:info_list, queryonly_flag:false,
									query_obj:query_obj, store_idproperty:"dt_id"
								}
							}
							this.editgrid.addreplace_store(args_obj);
						}))
					} else {
						console.log("Code Logic Error:teaminfo:create_team_grid: store should exist");
					}
					// next args_obj is for reconfig_infobtn
					args_obj = {
						newgrid_flag:false
					}
				}
				args_obj.swapcpane_flag = true;
				args_obj.updatebtn_str = constant.updatebtn_str;
				args_obj.text_node_str = constant.text_node_str;
				args_obj.idproperty = this.idproperty;
				args_obj.colname = this.activegrid_colname;
				args_obj.entry_pt = constant.init;
				args_obj.op_type = this.op_type;
				this.reconfig_infobtn(args_obj);
				// null out server data tracking
				this.serverinfo_list = null;
			},
			af_field_render: function(object, data_list, node) {
				var tm_id = object.tm_id;
				var content_str = "";
				var checkbox_list = new Array();
				var span_id = "";
				if (this.divfield_list) {
					// this.divfield_list gets set prior to call to create grid
					// and will indicate the checkboxes required
					// create content_str for the checkboxes and labels that
					// will populate the tooltipdialog
					arrayUtil.forEach(this.divfield_list, function(item) {
						var field_id = item.field_id;
						var field_name = item.field_name;
						var idstr = this.op_prefix+"tmfield_checkbox"+tm_id+
							field_id+"_id";
						content_str += '<input type="checkbox" data-dojo-type="dijit/form/CheckBox" style="color:green" id="'+
						idstr+
						'" value="'+field_id+'"><label for="'+idstr+'"> Field:<strong>'+field_name+'</strong></label><br>';
						checkbox_list.push({id:idstr, field_name:field_name});
					}, this)
					var options_obj = {checkbox_list:checkbox_list, dt_id:object.dt_id,
						topdiv_node:node, }
					var button_id = this.op_prefix+"tmfield_btn"+tm_id+"_id";
					// create span_id for text display next to dropdown
					span_id = "span"+button_id;
					// pass it to af_process event handler too
					options_obj.span_id = span_id;
					// add button through adding declarative description into
					// content string instead of instantiating directly and adding
					// using addChild() - the latter does not work in a subsequent
					// loop when the checkbox content string has to be reassigned but
					// the button already exists.  Reassinging the content nullifies
					// the child button widget, but it is not possible to do another
					// addChild() with the button widget
					content_str += "<button data-dojo-type='dijit/form/Button' class ='info' type='submit' id='"+button_id+"'>Save</button>";
				} else {
					content_str = "Insufficient prior configuration: Check to make sure both division and fields are defined first"
				}
				// define parameters for the tooltip dialog
				var tipdialog_prefix = this.op_prefix+"tmfield_tdialog";
				var tipdialog_id = tipdialog_prefix+tm_id+"_id";
				var tipdialog_widget = registry.byId(tipdialog_id);
				if (!tipdialog_widget) {
					var tipdialog_widget = new TooltipDialog({
						id:tipdialog_id,
						content:content_str
					})
				} else {
					tipdialog_widget.set("content", content_str);
				}
				//tipdialog_widget.startup();
				var display_str = "";
				if (this.divfield_list) {
					// enable checkboxes if render gets passed with data from
					// the store
					arrayUtil.forEach(data_list, function(field_id) {
						var idstr = this.op_prefix+"tmfield_checkbox"+tm_id+
							field_id+"_id";
						var checkbox_widget = registry.byId(idstr);
						checkbox_widget.set("checked", true);
						var match_obj = arrayUtil.filter(this.divfield_list,
						function(item) {
							return item.field_id == field_id
						})[0]
						display_str += match_obj.field_name+',';
					}, this)
					// set callback for button in dialogtooltip
					var button_widget = registry.byId(button_id);
					// button widget should already exist at this point
					if (button_widget) {
						button_widget.set("onClick",
							lang.hitch(this, this.af_dialogbtn_process, options_obj))
					} else {
						console.log("Error: teaminfo af_field render - tooltipdialog button should exist")
					}
				}
				// define parameters for the ddown button embedded in grid cell
				var team_ddown_prefix = this.op_prefix+"tmfield_ddown";
				var team_ddown_id = team_ddown_prefix+tm_id+"_id";
				var team_ddown_widget = registry.byId(team_ddown_id);
				if (!team_ddown_widget) {
					var ddown_node = put(node, "div");
					team_ddown_widget = new DropDownButton({
						label:"Home Field(s)",
						class:"info",
						dropDown:tipdialog_widget
					}, ddown_node)
					//team_ddown_widget.startup();
				}
				// if there is data, display checked fieldnames next to dropdown
				if (display_str.length > 0) {
					// trim off last comma
					display_str = display_str.substring(0,
						display_str.length-1);
					// write to node next to dropdown buton
					var span_node = dom.byId(span_id);
					if (!span_node) {
						span_node = put(node, "span.empty_tinygap[id=$]",
							span_id, display_str);
					} else {
						span_node.innerHTML = display_str;
					}
				}
			},
			af_dialogbtn_process: function(options_obj, event) {
				//callback function for affinity field tooltipdialog button
				var checkbox_list = options_obj.checkbox_list;
				var dt_id = options_obj.dt_id;
				var topdiv_node = options_obj.topdiv_node;
				var span_id = options_obj.span_id;
				var value_list = new Array();
				var display_str = "";
				// loop through each checkbox to see if there is a value
				arrayUtil.forEach(checkbox_list, function(item) {
					var checkbox_id = item.id;
					var field_name = item.field_name;
					var checkbox_widget = registry.byId(checkbox_id);
					var checkbox_value = checkbox_widget.get("value");
					if (checkbox_value) {
						// create str to store (str of integer id elements)
						value_list.push(parseInt(checkbox_value));
						display_str += field_name+',';
					}
				})
				// trim off last comma
				display_str = display_str.substring(0, display_str.length-1);
				var span_node = dom.byId(span_id);
				if (!span_node) {
					span_node = put(topdiv_node, "span.empty_tinygap[id=$]",
						span_id, display_str);
				} else {
					span_node.innerHTML = display_str;
				}
				if (this.editgrid) {
					var infostore = this.edigrid.schedInfoStore;
					infostore.get(dt_id).then(function(store_elem) {
						store_elem.af_list = value_list;
						infostore.put(store_elem);
					});
				}
			},
			prefdays_render: function(object, data_list, node) {
				var team_id = object.tm_id;
				var prefdays_dialog_id = this.op_prefix+"prefdays_tooltip"+team_id+'_id';
				var prefdays_ddownbtn_prefix = this.op_prefix+"prefdays_ddropdownbtn";
				var prefdays_ddownbtn_id = prefdays_ddownbtn_prefix+team_id+'_id';

				var checkbox_ids = arrayUtil.map(constant.day_list, function(day) {
					return {id: this.op_prefix+'tmprefdays_'+ day+team_id+"_id", day: day}
				}, this);
				var content_str = checkbox_ids.reduce(function(memo,  item, index) {
					memo += '<input type="checkbox" data-dojo-type="dijit/form/CheckBox" style="color:green" id="'+item.id+
						'" value='+index+'><label for="'+item.id+'">'+item.day+'</label> ';
					if (index%2)
						memo += '<br>';
					return memo;
				}, "")
				var button_id = this.op_prefix+'prefdays_dialogbtn'+team_id+'_id';
				content_str += '<br><button data-dojo-type="dijit/form/Button" type="submit" id="'+button_id+'">Save</button>'
				var prefdays_dialog = registry.byId(prefdays_dialog_id);
				if (!prefdays_dialog) {
					prefdays_dialog = new TooltipDialog({
						id:prefdays_dialog_id,
						content: content_str
		    		});
				} else {
					prefdays_dialog.set('content', content_str);
				}
				var prefdays_dialogprop_obj = {team_id:team_id,
					checkbox_ids:checkbox_ids, dt_id: object.dt_id,
    			day_list:constant.day_list};
    		var button_reg = registry.byId(button_id);
    		button_reg.on("click",
    			lang.hitch(this,this.prefdays_dialogbtn_process, prefdays_dialogprop_obj));
    		var dropdown_btn = registry.byId(prefdays_ddownbtn_id);
    		if (!dropdown_btn) {
					dropdown_btn = new DropDownButton({dropDown:prefdays_dialog, id:prefdays_ddownbtn_id});
					dropdown_btn.startup();
    		} else {
    			dropdown_btn.set('dropDown', prefdays_dialog);
    		}
    		if (object.prefdays) {
   				var args_obj = {dialogprop_obj:prefdays_dialogprop_obj,
    				check_str:object.prefdays, team_id: team_id,
    				display_list:prefdays_dialogprop_obj.day_list,
    				dropdownbtn_prefix:prefdays_ddownbtn_prefix,
    				index_offset:0}
    			this.init_checkbox(args_obj);
    		} else {
    			dropdown_btn.set("label", "Config");
    		}
    		node.appendChild(dropdown_btn.domNode);
				return dropdown_btn;
			},
			prefdays_dialogbtn_process: function(prefdays_dialogprop_obj, event) {
				var dt_id = prefdays_dialogprop_obj.dt_id;
				var team_id = prefdays_dialogprop_obj.team_id;
				var checkbox_ids = prefdays_dialogprop_obj.checkbox_ids;
				var day_list = prefdays_dialogprop_obj.day_list;
				var checked = arrayUtil.filter(checkbox_ids, function(item) {
					var checkbox_reg = registry.byId(item.id);
					return checkbox_reg.get("checked")
				})
				var display_str = checked.reduce(function(memo, item) {
					memo += item.day + ',';
					return memo;
				}, "");
				var value_str = checked.reduce(function(memo, item) {
					var checkbox_reg = registry.byId(item.id);
					memo += checkbox_reg.get("value") + ',';
					return memo;
				}, "");
				// trim off last comma
				display_str = display_str.substring(0, display_str.length-1);
				value_str = value_str.substring(0, value_str.length-1);
				if (this.editgrid) {
					this.editgrid.schedInfoStore.get(dt_id).then(
						lang.hitch(this, function(store_elem){
							store_elem.prefdays = value_str;
							this.editgrid.schedInfoStore.put(store_elem);
						})
					);
					// because of trouble using dgrid w observable store, directly update dropdownbtn instead of dgrid cell with checkbox info
					var prefdays_dropdownbtn_reg = registry.byId(this.op_prefix+"prefdays_ddropdownbtn"+team_id+"_id");
					prefdays_dropdownbtn_reg.set('label', display_str);
				}
			},
			// mark checkboxes depending on state of store
			init_checkbox: function(args_obj) {
				var dialogprop_obj = args_obj.dialogprop_obj;
				var check_str = args_obj.check_str;
				var display_list = args_obj.display_list;
				var dropdownbtn_prefix = args_obj.dropdownbtn_prefix;
				var index_offset = args_obj.index_offset;
				var team_id = dialogprop_obj.team_id;
				var checkbox_ids = dialogprop_obj.checkbox_ids;
				var display_str = "";
				arrayUtil.forEach(check_str.split(','), function(item) {
					var index = parseInt(item)-index_offset;
					var checkbox_reg = registry.byId(checkbox_ids[index].id);
					checkbox_reg.set("checked", true);
					display_str += display_list[index]+',';
				});
				display_str = display_str.substring(0, display_str.length-1);
				var dropdownbtn_reg = registry.byId(dropdownbtn_prefix+team_id+"_id");
				dropdownbtn_reg.set('label', display_str);
			},
			create_wizardcontrol: function(pcontainerdiv_node, gcontainerdiv_node) {
				// create cpane control for divinfo wizard pane under menubar
				this.pstackcontainer = new StackContainer({
					doLayout:false,
					style:"float:left; width:80%",
					id:this.idmgr_obj.pcontainer_id
				}, pcontainerdiv_node);
				// reset pane for initialization and after delete
				var reset_cpane = new ContentPane({
					id:this.idmgr_obj.resetcpane_id
				})
				this.pstackcontainer.addChild(reset_cpane)
				// add pref config (number) cpane
				// Note there is no number input form, but we will use the cpane
				// to host the dropdown select used in lieu of the input text box
				var team_cpane = new ContentPane({
					id:this.idmgr_obj.numcpane_id,
				})
				this.pstackcontainer.addChild(team_cpane);
				// add txt + button cpane
				var txtbtn_cpane = new ContentPane({
					id:this.idmgr_obj.textbtncpane_id,
				})
				/*
				put(txtbtn_cpane.containerNode, "span[id=$]",
					this.idmgr_obj.text_id);
				put(txtbtn_cpane.containerNode, "button[id=$]",
					this.idmgr_obj.btn_id); */
				this.pstackcontainer.addChild(txtbtn_cpane)
				// create grid stack container and grid
				this.gstackcontainer = new StackContainer({
					doLayout:false,
					style:"clear:left",
					id:this.idmgr_obj.gcontainer_id
				}, gcontainerdiv_node);
				// add blank pane (for resetting)
				var blank_cpane = new ContentPane({
					id:this.idmgr_obj.blankcpane_id
				})
				this.gstackcontainer.addChild(blank_cpane);
				// add divinfo cpane and grid div
				var teamgrid_cpane = new ContentPane({
					id:this.idmgr_obj.gridcpane_id,
					class:'grid_cpane'
				})
				put(teamgrid_cpane.containerNode, "div[id=$]",
					this.idmgr_obj.grid_id);
				this.gstackcontainer.addChild(teamgrid_cpane);
			},
			checkdelete_txtbtn: function() {
				var text_id = this.idmgr_obj.text_id;
				var btn_id = this.idmgr_obj.btn_id;
				var btn_widget = registry.byId(btn_id);
				if (btn_widget) {
					btn_widget.destroyRecursive();
				}
				var text_node = dom.byId(text_id);
				if (text_node) {
					put(text_node, "!");
				}
				var btn_node = dom.byId(btn_id);
				if (btn_node) {
					put(btn_node, "!");
				}
			}
		});
});
