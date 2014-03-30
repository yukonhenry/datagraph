/* look at examples in http://dojotoolkit.org/documentation/tutorials/1.9/modules/
for loadable module design and syntax  also ref
http://dojotoolkit.org/documentation/tutorials/1.9/declare/ and
http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html for class constructor syntax
http://dojotoolkit.org/documentation/tutorials/1.9/augmenting_objects/*/
define(["dbootstrap", "dojo/dom", "dojo/dom-construct", "dojo/_base/declare", "dojo/_base/lang", "dojo/dom-class",
	"dojo/_base/array","dijit/registry", "dijit/MenuItem", "dijit/form/Button",
	"LeagueScheduler/editgrid","LeagueScheduler/divinfo", "LeagueScheduler/fieldinfo", "dojo/domReady!"],
	function(dbootstrap, dom, domConstruct, declare, lang, domClass, arrayUtil,
		registry, MenuItem, Button, EditGrid, DivInfo, FieldInfo){
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
		};
		var status_dom = dom.byId("dbstatus_txt");
		var status1_dom = dom.byId("dbstatus1_txt");
		return declare(null, {
			leaguedata: null, server_interface:null, editGrid:null,
			rrdbmenureg_list:null, fielddbmenureg_list:null, tdbmenureg_list:null,
			constructor: function(args) {
				//declare.safeMixin(this, args);
				// augmenting object tutorial referenced above says lang.mixin is a better choise
				// than declare.safeMixin
				lang.mixin(this, args);
				this.rrdbmenureg_list = new Array();
				this.tdbmenureg_list = new Array();
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
			// following function is robust whether nodelist is a n Array
			// or a scalar dom node
			updateDBstatus_nodelist: function(dbstatus, nodelist) {
				// ref http://stackoverflow.com/questions/767486/how-do-you-check-if-a-variable-is-an-array-in-javascript
				if (nodelist instanceof Array) {
					arrayUtil.forEach(nodelist, function(item) {
						this.updateDBstatus_node(dbstatus, item);
					}, this)
				} else {
					this.updateDBstatus_node(dbstatus, nodelist);
				}
			},
			updateDBstatus_node: function(dbstatus, node) {
				if (dbstatus) {
					node.innerHTML = "Schedule in database, Ready";
					node.style.color = 'green';
				} else {
					node.innerHTML = "Schedule Not Ready";
					node.style.color = 'red';
				}
			},
			makeVisible: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			},
			makeInvisible: function(dom_name) {
				domClass.replace(dom_name, "style_none", "style_inline");
			},
			generateDivSelectDropDown: function(select_reg, info_list) {
				// ref http://stackoverflow.com/questions/13932225/dojo-and-dynamically-added-options-to-dijit-form-select
				// for closure http://stackoverflow.com/questions/4726611/function-used-from-within-javascript-dojo-closure-using-this-notation-is-undef
				// without 3rd argument for  forEach, scope is global
				// http://stackoverflow.com/questions/148901/is-there-a-better-way-to-do-optional-function-parameters-in-javascript
				var info_list = (typeof info_list === "undefined") ? this.leaguedata : info_list;
				var option_list = [{label:"Select Division", value:"", selected:true}];
				arrayUtil.forEach(info_list, function(item, index) {
					var divstr = item.div_age + item.div_gen;
					// division code is 1-index based so increment by 1
					option_list.push({label:divstr, value:index+1, selected:false});
				});
				select_reg.addOption(option_list);
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
					if (db_type == 'rrdb') {
						this.rrdbmenureg_list.push({reg:submenu_reg,
							context:onclick_context, func:onclick_func,
							options_obj:options_obj});
					} else if (db_type == 'tourndb') {
						this.tdbmenureg_list.push({reg:submenu_reg,
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
				var dbmenureg_list = null;
				if (db_type == 'rrdb')
					dbmenureg_list = this.rrdbmenureg_list;
				else if (db_type == 'tourndb')
					dbmenureg_list = this.tdbmenureg_list;
				else
					dbmenureg_list = this.fielddbmenureg_list;
				arrayUtil.forEach(dbmenureg_list, function(dbmenudata) {
					var dbmenureg = dbmenudata.reg;
					dbmenureg.removeChild(delindex);
				});
			},
			regenAddDBCollection_smenu: function(insertIndex, object, db_type) {
				var dbmenureg_list = null;
				//var db_type = object.db_type;
				if (db_type == 'rrdb')
					dbmenureg_list = this.rrdbmenureg_list;
				else if (db_type == 'tourndb')
					dbmenureg_list = this.tdbmenureg_list;
				else
					dbmenureg_list = this.fielddbmenureg_list;
				var item_name = object.name;
				//var divinfo_obj = new DivInfo({server_interface:this.server_interface, schedutil_obj:this});
				arrayUtil.forEach(dbmenureg_list, function(dbmenudata) {
					var dbmenureg = dbmenudata.reg;
					var options_obj = dbmenudata.options_obj;
					options_obj.item = item_name;
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
			detect_arrayduplicate: function(arry) {
				// detect duplicate elements in array
				// ref http://stackoverflow.com/questions/840781/easiest-way-to-find-duplicate-values-in-a-javascript-array
				var sorted_arry = arry.sort();
				var results = [];
				for (var i = 0; i < arry.length - 1; i++) {
					if (sorted_arry[i + 1] == sorted_arry[i]) {
						results.push(sorted_arry[i]);
					}
				}
				return results;
			}
		})
	}
);
