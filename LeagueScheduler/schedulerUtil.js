/* look at examples in http://dojotoolkit.org/documentation/tutorials/1.9/modules/
for loadable module design and syntax  also ref
http://dojotoolkit.org/documentation/tutorials/1.9/declare/ and
http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html for class constructor syntax
http://dojotoolkit.org/documentation/tutorials/1.9/augmenting_objects/*/
define(["dbootstrap", "dojo/dom", "dojo/dom-construct", "dojo/_base/declare", "dojo/_base/lang", "dojo/dom-class",
	"dojo/_base/array","dijit/registry", "dijit/MenuItem",
	"LeagueScheduler/editgrid", "dojo/domReady!"],
	function(dbootstrap, dom, domConstruct, declare, lang, domClass, arrayUtil, registry, MenuItem,
		EditGrid){
		var calendarMapObj = {1:'Sept 7', 2:'Sept 14', 3:'Sept 21', 4:'Sept 28', 5:'Oct 5',
			6:'Oct 12', 7:'Oct 19', 8:'Oct 26', 9:'Nov 2', 10:'Nov 9', 11:'Nov 16', 12:'Nov 23'};
		var fieldMapObj = {1:'Sequoia Elem 1', 2:'Sequoia Elem 2',3:'Pleasant Hill Elem 1',
			4:'Pleasant Hill Elem 2',
			5:'Pleasant Hill Elem 3', 6:'Golden Hills 1', 7:'Golden Hills 2',
			8:'Mountain View Park', 9:'Pleasant Hill Middle 1', 10:'Pleasant Hill Middle 2',
			11:'Pleasant Hill Middle 3', 12:'Nancy Boyd Park', 13:'Strandwood Elem',
			14:'Sequoia Middle', 15:'Gregory Gardens Elem', 16:'Pleasant Hill Park',
			17:'Sequoia Middle U14', 18:'Hidden Lakes', 19:'Waterfront', 20:'CP Turf'};
		var status_dom = dom.byId("dbstatus_txt");
		var status1_dom = dom.byId("dbstatus1_txt");
		return declare(null, {
			leaguedata: null, server_interface:null, editGrid:null,
			constructor: function(args) {
				//declare.safeMixin(this, args);
				// augmenting object tutorial referenced above says lang.mixin is a better choise
				// than declare.safeMixin
				lang.mixin(this, args);
			},
			getCalendarMap: function(gameday_id) {
				return calendarMapObj[gameday_id];
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
			generateDivSelectDropDown: function(select_reg) {
				// ref http://stackoverflow.com/questions/13932225/dojo-and-dynamically-added-options-to-dijit-form-select
				option_array = [{label:"Select Division", value:"", selected:true}];
				arrayUtil.forEach(this.leaguedata, function(item, index) {
					divstr = item.agediv + item.gender;
					// division code is 1-index based so increment by 1
					option_array.push({label:divstr, value:index+1, selected:false});
				});
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
				target_dom = dom.byId(dom_name);
				hrefstr = "";
				arrayUtil.forEach(ldata_array, function(item, index) {
					divstr = item.agediv + item.gender;
					urlstr = "http://localhost/doc/xls/"+divstr+"_schedule.xls";
					labelstr = divstr + " Schedule";
					hrefstr += "<a href="+urlstr+">"+labelstr+"</a> ";
				});
				domConstruct.place(hrefstr, target_dom);
			},
			createTeamSchedLinks: function(ldata_array, dom_name) {
				// loop through each division, and with second loop that loops
				// through each team_id, create string for <a href=
				// then create dom entry w. domConstruct.create call
				// http://dojotoolkit.org/documentation/tutorials/1.9/dom_functions/
				target_dom = dom.byId(dom_name);
				target_dom.innerHTML = "";
				arrayUtil.forEach(ldata_array, function(item, index) {
					divstr = item.agediv + item.gender;
					numteams = item.totalteams;
					divheaderstr = "<u>"+divstr+" Teams</u><br>";
					hrefstr = "";
					for (var i = 1; i < numteams+1; i++) {
						if (i < 10) {
							teamstr = '0' + i;
						} else {
							teamstr = i.toString();
						}
						dtstr = divstr+teamstr;
						urlstr = "http://localhost/doc/xls/"+dtstr+"_schedule.xls";
						labelstr = dtstr + " Schedule";
						hrefstr += "<a href="+urlstr+">"+labelstr+"</a> ";
					}
					domConstruct.create("p",{innerHTML:divheaderstr+hrefstr},target_dom);
				});  //foreach
			},  //createTeamSchedLinks
			generateDB_smenu: function(dbcollection_list, db_smenu_name, schedtype_grid, serv_function) {
				var dbcollection_smenu_reg = registry.byId(db_smenu_name);
				var columnsdef_obj = schedtype_grid.columnsdef_obj;
				var options_obj = {'columnsdef_obj':columnsdef_obj};
				this.generateDBCollection_smenu(dbcollection_smenu_reg,dbcollection_list, this, serv_function, options_obj);
			},
			// review usage of hitch to provide context to event handlers
			// http://dojotoolkit.org/reference-guide/1.9/dojo/_base/lang.html#dojo-base-lang
			generateDBCollection_smenu: function(submenu_reg, submenu_list, onclick_context, onclick_func, options_obj) {
				var options_obj = options_obj || {};
				arrayUtil.forEach(submenu_list, function(item, index) {
					options_obj.item = item;
					var smenuitem = new MenuItem({label: item,
						onClick: lang.hitch(onclick_context, onclick_func, options_obj) });
    				submenu_reg.addChild(smenuitem);
				});
			},
			default_alert: function(options_obj) {
				var item = options_obj.item;
				alert(item);
			},
			delete_divdbcollection: function(options_obj) {
				var item = options_obj.item;
				this.server_interface.getServerData("delete_divdbcol/"+item,
					this.server_interface.server_ack);
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
			getServerDBDivInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				var item = options_obj.item;
				this.server_interface.getServerData("get_dbcol/"+item,
					lang.hitch(this, this.createEditGrid), null, options_obj);
			},
			getServerDBSchedInfo: function(options_obj) {
				var item = options_obj.item;
				this.makeVisible(dom.byId("schedDBSelectDiv"));
				this.generateDivSelectDropDown(registry.byId("schedDBDivisionSelect"));
				this.server_interface.getServerData("get_scheddbcol/"+item,
					lang.hitch(this, this.createEditGrid), null, options_obj);
			},
			createEditGrid: function(divdata, options_obj) {
				// don't create grid if a grid already exists and it points to the same schedule db col
				// if grid needs to be generated, make sure to clean up prior to recreating editGrid
				var colname = options_obj.item;
				var columnsdef_obj = options_obj.columnsdef_obj;
				if (!this.editGrid || colname != this.editGrid.colname) {
					if (this.editGrid) {
						this.editGrid.cleanup();
						delete this.editGrid;
					}
					if (!this.server_interface)
						console.log("no server interface");
					this.editGrid = new EditGrid({griddata_list:divdata.divinfo_list,
						colname:colname,
						server_interface:this.server_interface,
						grid_name:"divisionInfoInputGrid",
						error_node:dom.byId("divisionInfoInputGridErrorNode"),
						text_node:dom.byId("divisionInfoNodeText"),
						submitbtn_reg:registry.byId("updatesubmit_btn"),
						updatebtn_node:dom.byId("divisionInfoUpdateBtnText")});
					this.editGrid.recreateSchedInfoGrid(columnsdef_obj);
				} else {
					alert("same schedule selected");
				}
			}

		});
	}
);
