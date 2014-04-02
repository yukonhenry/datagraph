// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dgrid/editor",
	"LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/widgetgen", "put-selector/put", "dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, editor,
		baseinfo, baseinfoSingleton, WidgetGen, put){
		var constant = {
			infobtn_id:"infoBtnNode_id",
			idproperty_str:"div_id",
			updatebtn_str:"Update Div Info",
			grid_id:"divinfogrid_id",
			text_node_str: 'Schedule Name',
			db_type:'rrdb',
			start_datebox_id:'start_dtbox_id',
			end_datebox_id:'end_dtbox_id',
			weeksspinner_id:'sl_spinner_id',
			seasondates_btn_id:'sdbtn_id',
			numweeks:12
		};
		return declare(baseinfo, {
			infogrid_store:null, idproperty:constant.idproperty_str,
			db_type:constant.db_type,
			base_numweeks:0, widgetgen:null,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
					div_id: "Div ID",
					div_age: editor({label:"Age", field:"div_age", autoSave:true,
						set:function(item) {
							// trim any leading or trailing whitespace characters
							return item.div_age.trim();
						}},"text","dblclick"),
					div_gen: editor({label:"Gender", field:"div_gen", autoSave:true,
						set:function(item) {
							return item.div_gen.trim();
						}}, "text", "dblclick"),
					totalteams: editor({label:"Total Teams", autoSave:true,
						set:function(item) {
							return parseInt(item.totalteams)
						}}, "text", "dblclick"),
					numweeks: editor({label:"Number Weeks", autoSave:true,
						set:function(item) {
							return parseInt(item.numweeks)
						}}, "text", "dblclick"),
					numgdaysperweek: editor({label:"Num Gamedays per Week (per team)", autoSave:true,
						set:function(item) {
							return parseInt(item.numgdaysperweek)
						}}, "text", "dblclick"),
					totalgamedays: {label:"Total Gamedays (per team)",
						set:function(item) {
							return parseInt(item.numgdaysperweek) *
								parseInt(item.numweeks);
						}
					/*
						get:function(item) {
							return item.numweeks*item.numgdaysperweek;
						}, */
					},
					gameinterval: editor({label:"Inter-Game Interval (min)",
						autoSave:true,
						set:function(item) {
							return parseInt(item.gameinterval)
						}}, "text", "dblclick"),
				};
				return columnsdef_obj;
			},
			// column definition for fixed (uneditable) grid used for schedule
			// result grid
			getfixedcolumnsdef_obj: function () {
				var columnsdef_obj = {
					div_id:"Div ID",
					div_age:"Age Group",
					div_gen:"Gender (or secondary field)",
					totalteams:"Total #Teams",
					totalgamedays:"Total # Games",
					gameinterval:"Game Interval(min)"
				};
				return columnsdef_obj;
			},
			initialize: function(newgrid_flag) {
				var form_name = "newdivinfo_form_id";
				var form_reg = registry.byId(form_name);
				var input_reg = registry.byId("newdivinfo_input_id");
				var divnum_reg = registry.byId("divnum_input_id");
				var tooltipconfig_list = [{connectId:['divnum_input_id'],
					label:"Specify Number of Divisions and press ENTER",
					position:['below','after']},
					{connectId:['newdivinfo_input_id'],
					label:"Specify Schedule Name",
					position:['below','after']}];
				var args_obj = {
					dbname_reg:input_reg,
					form_reg:form_reg,
					entrynum_reg:divnum_reg,
					server_path:"create_newdbcol/",
					server_key:'info_data',
					text_node_str: constant.text_node_str,
					grid_id:constant.grid_id,
					updatebtn_str:constant.updatebtn_str,
					tooltipconfig_list:tooltipconfig_list,
					newgrid_flag:newgrid_flag,
					cellselect_flag:false
				}
				this.showConfig(args_obj);
			},
			getServerDBInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				options_obj.serverdata_key = 'info_list';
				options_obj.idproperty = constant.idproperty_str;
				options_obj.server_key = 'info_data';
				options_obj.server_path = "create_newdbcol/";
				options_obj.cellselect_flag = false;
				options_obj.text_node_str = "Division List Name";
				options_obj.grid_id = constant.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.getserver_path = 'get_dbcol/'
				options_obj.db_type = constant.db_type;
				this.inherited(arguments);
			},
			getInitialList: function(divnum) {
				var info_list = new Array();
				for (var i = 1; i < divnum+1; i++) {
					info_list.push({div_id:i, div_age:"", div_gen:"",
					                  totalteams:2, numweeks:this.base_numweeks,
					                  numgdaysperweek:1,
					                  totalgamedays:this.base_numweeks,
					                  gameinterval:1});
				}
				return info_list;
			},
			update_numweeks: function(numweeks) {
				this.infogrid_store.query({})
				.forEach(lang.hitch(this, function(obj) {
					obj.numweeks = numweeks;
					obj.totalgamedays = numweeks*obj.numgdaysperweek;
					this.infogrid_store.put(obj);
				}))
			},
			create_calendar_input: function() {
				var divinfogrid_node = dom.byId(constant.grid_id);
				var topdiv_node = put(divinfogrid_node, "-div");
				if (!this.widgetgen) {
					this.widgetgen = new WidgetGen({
						storeutil_obj:this.storeutil_obj,
						server_interface:this.server_interface
					});
				}
				args_obj = {
					topdiv_node:topdiv_node,
					start_datebox_id:constant.start_datebox_id,
					end_datebox_id:constant.end_datebox_id,
					spinner_id:constant.weeksspinner_id,
					numweeks:constant.numweeks,
					seasondates_btn_id:constant.seasondates_btn_id
				}
				this.widgetgen.create_calendarspinner_input(args_obj);
			},
			checkconfig_status: function(raw_result){
				// do check to make sure all fields have been filled.
				// note construct of using arrayUtil.some works better than
				// query.filter() as loop will exit immediately if .some() returns
				// true.
				// config_status is an integer type as booleans cannot be directly
				// be transmitted to server (sent as 'true'/'false' string)
				// Baseline implementation - if need to customize, do so in
				// inherited child class
				var config_status = 0;
				if (arrayUtil.some(raw_result, function(item, index) {
					// ref http://stackoverflow.com/questions/8312459/iterate-through-object-properties
					// iterate through object's own properties too see if there
					// any unfilled fields.  If so alert and exit without sending
					// data to server
					var break_flag = false;
					for (var prop in item) {
						if (prop == 'totalgamedays') {
							// for totalgamedays column we want at least positive gamedays
							if (item[prop] <= 0) {
								console.log("divinfo:checkconfig:need at least one total gameday");
								break_flag = true;
								break;
							}
						} else if (prop == 'totalteams') {
							if (item[prop] < 2) {
								console.log("divinfo:checkconfig:need at least two teams");
								break_flag = true;
								break;
							}
						} else {
							if (item[prop] === "") {
								//alert("Not all fields in grid filled out, but saving");
								break_flag = true;
								break;
							}
						}
					}
					return break_flag;
				})) {
					// insert return statement here if plan is to prevent saving.
					console.log("Not all fields complete for "+this.idproperty+
						" but saving");
				} else {
					config_status = 1;
				}
				return config_status;
			},
		});
});
