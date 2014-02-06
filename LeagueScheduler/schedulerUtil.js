/* look at examples in http://dojotoolkit.org/documentation/tutorials/1.9/modules/
for loadable module design and syntax  also ref
http://dojotoolkit.org/documentation/tutorials/1.9/declare/ and
http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html for class constructor syntax
http://dojotoolkit.org/documentation/tutorials/1.9/augmenting_objects/*/
define(["dbootstrap", "dojo/dom", "dojo/dom-construct", "dojo/_base/declare", "dojo/_base/lang", "dojo/dom-class",
	"dojo/_base/array","dijit/registry", "dijit/MenuItem", "dijit/form/Button",
	"LeagueScheduler/editgrid","LeagueScheduler/divinfo", "LeagueScheduler/baseinfoSingleton", "LeagueScheduler/fieldinfo", "dojo/domReady!"],
	function(dbootstrap, dom, domConstruct, declare, lang, domClass, arrayUtil,
		registry, MenuItem, Button, EditGrid, DivInfo, baseinfoSingleton,
		FieldInfo){
		var calendarMapObj = {1:'Sept 7', 2:'Sept 14', 3:'Sept 21', 4:'Sept 28', 5:'Oct 5',
			6:'Oct 12', 7:'Oct 19', 8:'Oct 26', 9:'Nov 2', 10:'Nov 9', 11:'Nov 16', 12:'Nov 23'};
		var tournCalendarMapObj = {1:'Oct 26', 2:'Oct 27', 3:'Nov 2', 4:'Nov 3', 5:'Nov 9', 6:'Nov 10'};
		var fieldMapObj = {1:'Sequoia Elem 1', 2:'Sequoia Elem 2',3:'Pleasant Hill Elem 1',
			4:'Pleasant Hill Elem 2',
			5:'Pleasant Hill Elem 3', 6:'Golden Hills 1', 7:'Golden Hills 2',
			8:'Mountain View Park', 9:'Pleasant Hill Middle 1', 10:'Pleasant Hill Middle 2',
			11:'Pleasant Hill Middle 3', 12:'Nancy Boyd Park', 13:'Strandwood Elem',
			14:'Sequoia Middle', 15:'Gregory Gardens Elem', 16:'Pleasant Hill Park',
			17:'Sequoia Middle U14', 18:'Hidden Lakes', 19:'Waterfront', 20:'CP Turf'};
		var constant = {
			infobtn_id:"infoBtnNode_id",
			fielddb_type:"fielddb"
		};
		var status_dom = dom.byId("dbstatus_txt");
		var status1_dom = dom.byId("dbstatus1_txt");
		return declare(null, {
			leaguedata: null, server_interface:null, editGrid:null,
			dbmenureg_list:null, fielddbmenureg_list:null,
			constructor: function(args) {
				//declare.safeMixin(this, args);
				// augmenting object tutorial referenced above says lang.mixin is a better choise
				// than declare.safeMixin
				lang.mixin(this, args);
				this.dbmenureg_list = new Array();
				this.fielddbmenureg_list = new Array();
			},
			getCalendarMap: function(gameday_id) {
				return calendarMapObj[gameday_id];
			},
			getTournCalendarMap: function(gameday_id) {
				return tournCalendarMapObj[gameday_id];
			},
			getFieldMap: function(field_id) {
				return fieldMapObj[field_id];
			},
			tConvert: function(time) {
				// courtesy http://stackoverflow.com/questions/13898423/javascript-convert-24-hour-time-of-day-string-to-12-hour-time-with-am-pm-and-no
  				// Check correct time format and split into components
  				time = time.toString ().match (/^([01]\d|2[0-3])(:)([0-5]\d)(:[0-5]\d)?$/) || [time];

  				if (time.length > 1) { // If time format correct
    				time = time.slice (1);  // Remove full string match value
    				time[5] = +time[0] < 12 ? ' am' : ' pm'; // Set AM/PM
    				time[0] = +time[0] % 12 || 12; // Adjust hours
  				}
  				return time.join (''); // return adjusted time or original string
			},
			updateDBstatusline: function(dbstatus) {
				arrayUtil.forEach([status_dom, status1_dom], function(item_dom, index) {
					if (dbstatus) {
						item_dom.innerHTML = "Schedule in database, Ready";
						item_dom.style.color = 'green';
					} else {
						item_dom.innerHTML = "Schedule Not Ready";
						item_dom.style.color = 'red';
					}
				});
			},
			makeVisible: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			},
			makeInvisible: function(dom_name) {
				domClass.replace(dom_name, "style_none", "style_inline");
			},
			generateDivSelectDropDown: function(select_reg, divinfo_list) {
				// ref http://stackoverflow.com/questions/13932225/dojo-and-dynamically-added-options-to-dijit-form-select
				// for closure http://stackoverflow.com/questions/4726611/function-used-from-within-javascript-dojo-closure-using-this-notation-is-undef
				// without 3rd argument for  forEach, scope is global
				// http://stackoverflow.com/questions/148901/is-there-a-better-way-to-do-optional-function-parameters-in-javascript
				var divinfo_list = (typeof divinfo_list === "undefined") ? this.leaguedata : divinfo_list;
				var option_array = [{label:"Select Division", value:"", selected:true}];
				arrayUtil.forEach(divinfo_list, function(item, index) {
					var divstr = item.div_age + item.div_gen;
					// division code is 1-index based so increment by 1
					option_array.push({label:divstr, value:index+1, selected:false});
				}, this);
				select_reg.addOption(option_array);
			},
			getNumberTeams: function(div_id) {
				// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/array.html#dojo-base-array
				var result_array = arrayUtil.filter(this.leaguedata, function(item) {
					return item.div_id == div_id;
				});
				return result_array[0].totalteams;
			},
			createSchedLinks: function(ldata_array, dom_name) {
				var target_dom = dom.byId(dom_name);
				var hrefstr = "";
				arrayUtil.forEach(ldata_array, function(item, index) {
					var divstr = item.div_age + item.div_gen;
					var urlstr = "http://localhost/doc/xls/"+divstr+"_schedule.xls";
					var labelstr = divstr + " Schedule";
					hrefstr += "<a href="+urlstr+">"+labelstr+"</a> ";
				});
				domConstruct.place(hrefstr, target_dom);
			},
			createTeamSchedLinks: function(ldata_array, dom_name) {
				// loop through each division, and with second loop that loops
				// through each team_id, create string for <a href=
				// then create dom entry w. domConstruct.create call
				// http://dojotoolkit.org/documentation/tutorials/1.9/dom_functions/
				var target_dom = dom.byId(dom_name);
				target_dom.innerHTML = "";
				arrayUtil.forEach(ldata_array, function(item, index) {
					var divstr = item.div_age + item.div_gen;
					var numteams = item.totalteams;
					var divheaderstr = "<u>"+divstr+" Teams</u><br>";
					var hrefstr = "";
					var teamstr = "";
					for (var i = 1; i < numteams+1; i++) {
						if (i < 10) {
							teamstr = '0' + i;
						} else {
							teamstr = i.toString();
						}
						var dtstr = divstr+teamstr;
						var urlstr = "http://localhost/doc/xls/"+dtstr+"_schedule.xls";
						var labelstr = dtstr + " Schedule";
						hrefstr += "<a href="+urlstr+">"+labelstr+"</a> ";
					}
					domConstruct.create("p",{innerHTML:divheaderstr+hrefstr},target_dom);
				});  //foreach
			},  //createTeamSchedLinks
			generateDB_smenu: function(dbcollection_list, db_smenu_name, sched_context, serv_function, options_obj) {
				var options_obj = options_obj || {};
				var dbcollection_smenu_reg = registry.byId(db_smenu_name);
				var columnsdef_obj = options_obj.info_obj.getcolumnsdef_obj();
				options_obj.columnsdef_obj = columnsdef_obj;
				this.generateDBCollection_smenu(dbcollection_smenu_reg,dbcollection_list, sched_context, serv_function, options_obj);
			},
			// review usage of hitch to provide context to event handlers
			// http://dojotoolkit.org/reference-guide/1.9/dojo/_base/lang.html#dojo-base-lang
			generateDBCollection_smenu: function(submenu_reg, submenu_list, onclick_context, onclick_func, options_obj) {
				var options_obj = options_obj || {};
				arrayUtil.forEach(submenu_list, function(item, index) {
					var smenuitem = new MenuItem({label: item,
						onClick: function() {
							// update options_obj in actual onclick handler
							// when it is called
							options_obj.item = item;
							var onclick_direct = lang.hitch(onclick_context, onclick_func);
							onclick_direct(options_obj);}});
    				submenu_reg.addChild(smenuitem);
				});  // context should be function
				if (typeof options_obj.db_type !== 'undefined') {
					var db_type = options_obj.db_type;
					if (db_type == 'db') {
						this.dbmenureg_list.push({reg:submenu_reg,
							context:onclick_context, func:onclick_func,
							options_obj:options_obj});
					} else if (db_type == 'fielddb') {
						this.fielddbmenureg_list.push({reg:submenu_reg,
							context:onclick_context, func:onclick_func,
							options_obj:options_obj});
					}
				}
			},
			default_alert: function(options_obj) {
				var item = options_obj.item;
				alert(item);
			},
			regenDelDBCollection_smenu: function(delindex, db_type) {
				var dbmenureg_list = (db_type == 'db') ? this.dbmenureg_list : this.fielddbmenureg_list;
				arrayUtil.forEach(dbmenureg_list, function(dbmenudata) {
					var dbmenureg = dbmenudata.reg;
					dbmenureg.removeChild(delindex);
					/*
					arrayUtil.forEach(dbmenureg.getChildren(), function(smenuitem, index2) {
						if (smenuitem.get('label') == item_name) {
							dbmenureg.removeChild(smenuitem);
						}
					}); */
				});
				// also delete current active grid if it corresponds to the deleted db
				/*
				if (baseinfoSingleton.get_active_grid_name() == item_name) {
					var active_grid = baseinfoSingleton.get_active_grid();
					if (active_grid) {
						active_grid.cleanup();
					}
				} */
			},
			regenAddDBCollection_smenu: function(object, insertIndex) {
				var dbmenureg_list = (object.db_type == 'db') ? this.dbmenureg_list : this.fielddbmenureg_list;
				var item_name = object.label;
				//var divinfo_obj = new DivInfo({server_interface:this.server_interface, schedutil_obj:this});
				arrayUtil.forEach(dbmenureg_list, function(dbmenudata) {
					var dbmenureg = dbmenudata.reg;
					var options_obj = dbmenudata.options_obj;
					var smenuitem = new MenuItem({label:item_name,
						onClick:lang.hitch(dbmenudata.context, dbmenudata.func, options_obj)});
    				dbmenureg.addChild(smenuitem, insertIndex);
				});
			},
			getCupSchedule: function(options_obj) {
				var item = options_obj.item;
				this.server_interface.getServerData("getcupschedule/"+item,
					this.server_interface.server_ack);
			},
			export_rr2013: function(options_obj) {
				var item = options_obj.item;
				this.server_interface.getServerData("export_rr2013/"+item,
					this.server_interface.server_ack);
			},
			createEditGrid: function(server_data, options_obj) {
				// don't create grid if a grid already exists and it points to the same schedule db col
				// if grid needs to be generated, make sure to clean up prior to recreating editGrid
				var colname = options_obj.item;
				var columnsdef_obj = options_obj.columnsdef_obj;
				var divisioncode = options_obj.divisioncode || 0;
				var idproperty = options_obj.idproperty;
				var server_key = options_obj.server_key;
				// if server data is fielddb information, then we need to do
				// some data conversion (convert to date obj) before passing onto grid
				// Note server_key is key for outgoing request
				// serverdata_key is for incoming data
				var data_list = server_data[options_obj.serverdata_key];
				if (server_key == constant.fielddb_type) {
					if (idproperty == 'field_id') {
						arrayUtil.forEach(data_list, function(item, index) {
							// save date str to pass into start and end time calc
							// (though it can be a dummy date)
							var start_str = item.start_date;
							var end_str = item.end_date;
							item.start_date = new Date(start_str);
							item.end_date = new Date(end_str);
							item.start_time = new Date(start_str+' '+item.start_time);
							item.end_time = new Date(end_str+' '+item.end_time);
						})
					} else {
						alert('check db_type and idproperty consistency');
					}
				}
				if (!this.server_interface) {
					console.log("no server interface");
					alert("no server interface, check if service running");
				}
/*
				if (!this.editgrid || !baseinfoSingleton.get_active_grid() || colname != this.editgrid.colname ||
				    idproperty != this.editgrid.idproperty ||
				    divisioncode != this.editgrid.divisioncode) {
					if (this.editgrid &&
						this.editgrid.idproperty == idproperty) {
						this.editgrid.cleanup();
						delete this.editgrid;
					}
*/
				if (options_obj.newgrid_flag) {
					this.editgrid = new EditGrid({griddata_list:data_list,
						colname:colname,
						server_interface:this.server_interface,
						grid_id:options_obj.grid_id,
						error_node:dom.byId("divisionInfoInputGridErrorNode"),
						idproperty:idproperty,
						server_path:options_obj.server_path,
						server_key:options_obj.server_key,
						cellselect_flag:options_obj.cellselect_flag,
						info_obj:options_obj.info_obj,
						uistackmgr:options_obj.uistackmgr,
						storeutil_obj:options_obj.storeutil_obj});
					this.editgrid.recreateSchedInfoGrid(columnsdef_obj);
					baseinfoSingleton.set_active_grid(this.editgrid);
					baseinfoSingleton.set_active_grid_name(colname);
				} else {
					this.editgrid.replace_store(data_list);
				}
				// need to rethink structure of setting up and maintaining
				// updatebtn_widget
				if (idproperty != 'sched_id') {
					var text_str = options_obj.text_node_str + ": <b>"+colname+"</b>";
					options_obj.text_node.innerHTML = text_str;
					var updatebtn_widget = this.getInfoBtn_widget(
						options_obj.updatebtn_str, idproperty);
					updatebtn_widget.set("onClick", lang.hitch(this.editgrid,
						this.editgrid.sendDivInfoToServer));
					var btn_callback = lang.hitch(this.editgrid, this.editgrid.sendDivInfoToServer);
				}
				if (options_obj.swapcpane_flag) {
					options_obj.uistackmgr.switch_pstackcpane(idproperty, "config",
						text_str, btn_callback);
				}
			},
			getInfoBtn_widget: function(label_str, idproperty_str) {
				var infobtn_widget = registry.byId(constant.infobtn_id);
				if (infobtn_widget) {
					var info_type = infobtn_widget.get('info_type');
					if (info_type != idproperty_str) {
						infobtn_widget.set('label', label_str);
						infobtn_widget.set('info_type', idproperty_str);
					}
				} else {
					infobtn_widget = new Button({
						label:label_str,
						type:"button",
						class:"primary",
						info_type:idproperty_str
					}, constant.infobtn_id);
					infobtn_widget.startup();
				}
				return infobtn_widget;
			},
		})
	}
);
