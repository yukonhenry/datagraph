// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/_base/declare", "dojo/dom", "dojo/Deferred",
	"dojo/_base/lang", "dojo/_base/array", "dijit/Dialog",
	"dijit/registry", "dgrid/Editor", "dijit/form/NumberSpinner",
	"dijit/form/NumberTextBox", "dijit/form/ValidationTextBox", "dijit/form/Form",
	"dijit/layout/StackContainer", "dijit/layout/ContentPane",
	"scheduler_front/baseinfo", "scheduler_front/baseinfoSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(declare, dom, Deferred, lang, arrayUtil, Dialog,
		registry, editor, NumberSpinner,
		NumberTextBox, ValidationTextBox, Form, StackContainer, ContentPane,
		baseinfo, baseinfoSingleton, put){
		var constant = {
			idproperty_str:'div_id',
			inputnum_str:'Number of Divisions',
			dbname_str:'New Division List Name',
			vtextbox_str:'Enter Division List Name',
			ntextbox_str:'Enter Number of Divisions',
			updatebtn_str:"Update Div Info",
			text_node_str: 'Division List Name',
			db_type:'rrdb',
			start_datebox_id:'start_dtbox_id',
			end_datebox_id:'end_dtbox_id',
			weeksspinner_id:'sl_spinner_id',
			seasondates_btn_id:'sdbtn_id',
			numweeks:12,
			bye_value: 0,
			play_value: 1
		};
		var wizconstant = {
			//ndcpane_id:"wiznumdivcpane_id",
			// grid hosting div id's
			start_datebox_id:'wizstart_dtbox_id',
			end_datebox_id:'wizend_dtbox_id',
			weeksspinner_id:'wizsl_spinner_id',
			seasondates_btn_id:'wizsdbtn_id',
			numweeks:12
		};
		return declare(baseinfo, {
			idproperty:constant.idproperty_str,
			db_type:constant.db_type,
			base_numweeks:0, oddnumradio_value:-1, oddnum_dialog:null,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
			},
			getcolumnsdef_obj: function() {
				var columnsdef_list = [
					{field: "div_id", label: "Div ID"},
					{field: "div_age", label:"Age", autoSave:true,
						set:function(item) {
							// trim any leading or trailing whitespace characters
							return item.div_age.trim();
						}, editor:"text", editOn:"click"},
					{field: "div_gen", label:"Gender", autoSave:true,
						set:function(item) {
							return item.div_gen.trim();
						}, editor:"text", editOn:"click"},
					{field:"totalteams", label:"Total Teams", autoSave:true,
						set:function(item) {
							return parseInt(item.totalteams)
						}, editor:"text", editOn:"click"},
					{field:"numweeks", label:"Number Weeks", autoSave:true,
						set:function(item) {
							return parseInt(item.numweeks)
						}, editor:"text", editOn:"click"},
					{field:"numgdaysperweek", label:"#Games per week per team", autoSave:true,
						set:function(item) {
							return parseInt(item.numgdaysperweek)
						}, editor:"text", editOn:"click"},
					{field:"totalgamedays", label:"Total Gamedays per team",
						set:function(item) {
							return parseInt(item.numgdaysperweek) *
								parseInt(item.numweeks);
						}
					},
					{field:"gameinterval", label:"Inter-Game Interval (min)",
						autoSave:true,
						set:function(item) {
							return parseInt(item.gameinterval)
						}, editor:"text", editOn: "click"},
					{field:"mingap_days", label:"Minimum Gap (days)", autoSave:true,
						change_flag:false,
						editorArgs:{
							style:'width:70px', value:1, smallDelta:1,
							//id:"mingap_days_spinner_id",
							constraints:{min:1, max:50, places:0}
						},
						set:function(item) {
							// give a better initial estimate for the mingap_days
							// dependent on numgdaysperweek value
							if (this.change_flag) {
								this.change_flag = false;
								return (7/item.numgdaysperweek-1)
							}
						}, editor:NumberSpinner},
					{field:"maxgap_days", label:"Maximum Gap (days)", autoSave:true,
						change_flag:false,
						editorArgs:{
							style:'width:70px', value:2, smallDelta:1,
							constraints:{min:1, max:50, places:0}
						},
						set:function(item) {
							if (this.change_flag) {
								this.change_flag = false;
								return (7/item.numgdaysperweek+1)
							}
						}, editor:NumberSpinner}
				];
				return columnsdef_list;
			},
			// column definition for fixed (uneditable) grid used for schedule
			// result grid
			getfixedcolumnsdef_obj: function () {
				var columnsdef_obj = {
					div_id:"Div ID",
					div_age:"Age Group/Primary Group ID",
					div_gen:"Gender/Secondary Group ID",
					totalteams:"Total #Teams",
					totalgamedays:"Total # Games",
					gameinterval:"Game Interval(min)"
				};
				return columnsdef_obj;
			},
			initialize: function(newgrid_flag, op_type) {
				var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : op_type;
				var form_id = this.idmgr_obj.form_id;
				var dbname_id = this.idmgr_obj.dbname_id;
				var inputnum_id = this.idmgr_obj.inputnum_id;
				var grid_id = this.idmgr_obj.grid_id;
				var form_reg = registry.byId(form_id);
				var form_node = form_reg.domNode;
				var dbname_reg = null;
				var inputnum_reg = null;
				var dbname_node = dom.byId(dbname_id);
				if (!dbname_node) {
					put(form_node, "label.label_box[for=$]",
						dbname_id, constant.dbname_str);
					dbname_node = put(form_node,
						"input[id=$][type=text][required=true]",
						dbname_id)
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
						inputnum_id, constant.inputnum_str);
					var inputnum_node = put(form_node,
						"input[id=$][type=text][required=true]",
						inputnum_id);
					inputnum_reg = new NumberTextBox({
						value:'1',
						style:'width:5em',
						constraints:{min:1, max:500},
						promptMessage:constant.ntextbox_str,
						invalidMessage:'Must be Non-zero integer',
						missingMessage:constant.ntextbox_str+' (positive integer)'
					}, inputnum_node);
				} else {
					dbname_reg = registry.byId(dbname_id);
					inputnum_reg = registry.byId(inputnum_id);
				}
				var tooltipconfig_list = [{connectId:[inputnum_id],
					label:"Specify Number of Divisions and press ENTER",
					position:['below','after']},
					{connectId:[dbname_id],
					label:"Specify Schedule Name",
					position:['below','after']}];
				var args_obj = {
					dbname_reg:dbname_reg,
					form_reg:form_reg,
					entrynum_reg:inputnum_reg,
					text_node_str: constant.text_node_str,
					grid_id:grid_id,
					updatebtn_str:constant.updatebtn_str,
					tooltipconfig_list:tooltipconfig_list,
					newgrid_flag:newgrid_flag,
					cellselect_flag:false,
					op_type:op_type
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
				// write op_type back to options_obj in case it did not exist
				if (!('op_type' in options_obj))
					options_obj.op_type = this.op_type;
				options_obj.cellselect_flag = false;
				options_obj.text_node_str = "Division List Name";
				options_obj.grid_id = this.idmgr_obj.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.db_type = constant.db_type;
				this.inherited(arguments);
			},
			getInitialList: function(divnum) {
				var info_list = new Array();
				for (var i = 1; i < divnum+1; i++) {
					info_list.push({div_id:i, div_age:"", div_gen:"",
						totalteams:10, numweeks:this.base_numweeks,
						numgdaysperweek:1, totalgamedays:this.base_numweeks,
						gameinterval:60, mingap_days:5, maxgap_days:8});
				}
				return info_list;
			},
			get_gridhelp_list: function() {
				var gridhelp_list = [
					{id:'div_id', help_str:"Identifier, Non-Editable"},
					{id:'div_age', help_str:"Age or Primary Division Identifier, click cell to edit"},
					{id:'div_gen', help_str:"Gender or Secondary Division Identifier, click cell to edit"},
					{id:'totalteams', help_str:"Total # of Teams in the Division, click cell to edit"},
					{id:'numweeks', help_str:"Total # of weeks in a season for a team in the Division, use 'Transfer Dates' button to calculate #weeks, or click cell to edit"},
					{id:'numgdaysperweek', help_str:"# of games that a team in the division will play each week, click cell to edit"},
					{id:'totalgamedays', help_str:"total #games for each team, (#weeks x #gamedays per week) save bye games in the schedule if there are an odd number of teams in the division, Non-editable"},
					{id:'gameinterval', help_str:"NOTE: Assign Time interval between scheduled games on a field, e.g. the length of a single game plus break between games; click cell to edit"},
					{id:'mingap_days', help_str:"NOTE: Assign the minimum # days that should elapse between consecutive games for a given team, unit is in days"},
					{id:'maxgap_days', help_str:"NOTE: Assign the maximum # days that should elapse between consecutive games for a given team, unit is in days"}]
				return gridhelp_list;
			},
			update_numweeks: function(numweeks) {
				this.infogrid_store.filter({})
				.forEach(lang.hitch(this, function(obj) {
					obj.numweeks = numweeks;
					obj.totalgamedays = numweeks*obj.numgdaysperweek;
					this.infogrid_store.put(obj);
				}))
			},
			create_calendar_input: function(op_type) {
				var divinfogrid_node = dom.byId(this.idmgr_obj.grid_id);
				var topdiv_node = put(divinfogrid_node, "-div");
				var constant_obj = (op_type == 'wizard')?wizconstant:constant;
				var args_obj = {
					topdiv_node:topdiv_node,
					start_datebox_id:constant_obj.start_datebox_id,
					end_datebox_id:constant_obj.end_datebox_id,
					spinner_id:constant_obj.weeksspinner_id,
					numweeks:constant_obj.numweeks,
					seasondates_btn_id:constant_obj.seasondates_btn_id,
					op_type:op_type
				}
				this.widgetgen.create_calendarspinner_input(args_obj);
			},
			checkconfig_status: function(raw_result) {
				// do check to make sure all fields have been filled.
				// note construct of using arrayUtil.some works better than
				// query.filter() as loop will exit immediately if .some() returns
				// true.
				// config_status is an integer type as booleans cannot be directly
				// be transmitted to server (sent as 'true'/'false' string)
				// Baseline implementation - if need to customize, do so in
				// inherited child class
				var config_status = 0;
				var alert_msg = "";
				if (arrayUtil.some(raw_result, function(item, index) {
					// ref http://stackoverflow.com/questions/8312459/iterate-through-object-properties
					// iterate through object's own properties too see if there
					// any unfilled fields.  If so alert and exit without sending
					// data to server
					var break_flag = false;
					var mingap_days = -1;
					for (var prop in item) {
						if (prop == 'totalgamedays') {
							// for totalgamedays column we want at least positive gamedays
							if (item[prop] <= 0) {
								console.log("divinfo:checkconfig:need at least one total gameday");
								alert_msg = "Need totalgameday value"
								break_flag = true;
								break;
							}
						} else if (prop == 'totalteams') {
							if (item[prop] < 2) {
								console.log("divinfo:checkconfig:need at least two teams");
								alert_msg = "Need >=2 teams"
								break_flag = true;
								break;
							}
						} else if (prop == 'mingap_days') {
							mingap_days = item[prop]
						} else if (prop == 'maxgap_days') {
							if (item[prop] <= mingap_days) {
								console.log("divinfo:checkconfig: maxgap value needs to be larger than or equal to mingap value");
								alert_msg = "Need Max >= Min"
								break_flag = true;
								break;
							}
						} else {
							if (item[prop] === "") {
								alert_msg = "Empty Field"
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
					alert(alert_msg);
				} else {
					config_status = 1;
				}
				return config_status;
			},
			oddnumradio1_callback: function(event) {
				if (event) {
					this.oddnumradio_value = constant.bye_value;
				}
			},
			oddnumradio2_callback: function(event) {
				if (event) {
					this.oddnumradio_value = constant.play_value;
				}
			},
			oddnumsubmit_callback: function(deferred_obj, raw_result, event) {
				this.oddnum_dialog.hide();
				var oddnum_mode = this.oddnumradio_value;
				deferred_obj.resolve({oddnum_mode:oddnum_mode});
				/*
				var oddnum_mode = this.oddnumradio_value;
				if (oddnum_mode == 1) {
					// if oddnum mode is 1, add a virtual team for game scheduling
					// this allows all teams to have one game every game day
					// one team will play twice.  Right now we will manually change
					// the virtual team# to a real team# after the schedule is
					// generated
					arrayUtil.forEach(raw_result, function(item) {
						var totalteams = item['totalteams'];
						if (totalteams%2 == 1) {
							item['totalteams']++;
						}
					})
					deferred_obj.resolve({oddnum_mode:oddnum_mode,
						raw_result:raw_result});
				} else {
					deferred_obj.resolve({oddnum_mode:oddnum_mode});
				}
				*/
			},
			get_server_key_obj: function(raw_result) {
				var deferred_obj = new Deferred();
				var break_flag = false;
				if (arrayUtil.some(raw_result, function(item) {
					var totalteams = item['totalteams'];
					if (totalteams%2 == 1) {
						return true;
					} else {
						return false;
					}
				})) {
					this.oddnumradio_value = constant.bye_value;
					// pass deferredobj and rawresult as they will be used
					// if oddnum mode is 1
					var args_obj = {init_radio_value: "BYE",
						context:this,
						radio1_callback:this.oddnumradio1_callback,
						radio2_callback:this.oddnumradio2_callback,
						submit_callback:this.oddnumsubmit_callback,
						deferred_obj:deferred_obj,
						raw_result:raw_result};
					this.oddnum_dialog = this.widgetgen.get_radiobtn_dialog(args_obj);
					this.oddnum_dialog.show();
				} else {
					// no odd numbered teams
					deferred_obj.resolve({oddnum_mode:-1});
				}
				return deferred_obj.promise;
			},
		});
});
