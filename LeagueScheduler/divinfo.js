// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dgrid/editor", "dijit/form/NumberSpinner",
	"dijit/form/NumberTextBox", "dijit/form/ValidationTextBox", "dijit/form/Form",
	"dijit/layout/StackContainer", "dijit/layout/ContentPane",
	"LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/widgetgen", "put-selector/put", "dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, editor, NumberSpinner,
		NumberTextBox, ValidationTextBox, Form, StackContainer, ContentPane, baseinfo, baseinfoSingleton, WidgetGen,
		put){
		var constant = {
			idproperty_str:'div_id', form_id:'div_form_id', dbname_id:'rrdbname_id',
			inputnum_id:'divinputnum_id',
			inputnum_str:'Number of Divisions',
			dbname_str:'New Division List Name',
			vtextbox_str:'Enter Division List Name',
			ntextbox_str:'Enter Number of Divisions',
			updatebtn_str:"Update Div Info",
			grid_id:"divinfogrid_id",
			text_node_str: 'Division List Name',
			db_type:'rrdb',
			start_datebox_id:'start_dtbox_id',
			end_datebox_id:'end_dtbox_id',
			weeksspinner_id:'sl_spinner_id',
			seasondates_btn_id:'sdbtn_id',
			numweeks:12
		};
		var wizconstant = {
			form_id:'wizdiv_form_id', dbname_id:'wizrrdbname_id',
			inputnum_id:'wizdivinputnum_id',
			resetcpane_id:"resetcpane_id",
			tcpane_id:"wiztextbtncpane_id",
			ndcpane_id:"wiznumdivcpane_id",
			divcpane_id:"wizdivinfocpane_id",
			blankcpane_id:"blankcpane_id",
			infotxt_id:"wizdivinfotxt_id",
			infobtn_id:"wizdivinfobtn_id",
			dform_id:"wizdiv_form_id",
			// grid hosting div id's
			grid_id:"infogrid_id",
			wizid_stem:"wizdiv_",
			pcontainer_suffix_id:"pcontainer_id",
			gcontainer_suffix_id:"gcontainer_id",
			start_datebox_id:'wizstart_dtbox_id',
			end_datebox_id:'wizend_dtbox_id',
			weeksspinner_id:'wizsl_spinner_id',
			seasondates_btn_id:'wizsdbtn_id',
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
						}},"text","click"),
					div_gen: editor({label:"Gender", field:"div_gen", autoSave:true,
						set:function(item) {
							return item.div_gen.trim();
						}}, "text", "click"),
					totalteams: editor({label:"Total Teams", autoSave:true,
						set:function(item) {
							return parseInt(item.totalteams)
						}}, "text", "click"),
					numweeks: editor({label:"Number Weeks", autoSave:true,
						set:function(item) {
							return parseInt(item.numweeks)
						}}, "text", "click"),
					numgdaysperweek: editor({label:"Num Gamedays per Week (per team)", autoSave:true,
						set:function(item) {
							return parseInt(item.numgdaysperweek)
						}}, "text", "click"),
					totalgamedays: {label:"Total Gamedays (per team)",
						set:function(item) {
							return parseInt(item.numgdaysperweek) *
								parseInt(item.numweeks);
						}
					},
					gameinterval: editor({label:"Inter-Game Interval (min)",
						autoSave:true,
						set:function(item) {
							return parseInt(item.gameinterval)
						}}, "text", "click"),
					mingap_days: editor({label:"Minimum Gap (days)", autoSave:true,
						editorArgs:{
							style:'width:70px', value:1, smallDelta:1,
							//id:"mingap_days_spinner_id",
							constraints:{min:1, max:50, places:0}
						}
					}, NumberSpinner),
					maxgap_days: editor({label:"Maximum Gap (days)", autoSave:true,
						editorArgs:{
							style:'width:70px', value:2, smallDelta:1,
							//id:"maxgap_days_spinner_id",
							constraints:{min:1, max:50, places:0}
						}
					}, NumberSpinner)
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
			initialize: function(newgrid_flag, op_type) {
				var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : "wizard";
				var form_id = "";
				var dbname_id = "";
				var inputnum_id = "";
				var grid_id = "";
				if (op_type == "wizard") {
					form_id = wizconstant.form_id;
					dbname_id = wizconstant.dbname_id;
					inputnum_id = wizconstant.inputnum_id;
					grid_id = wizconstant.wizid_stem+wizconstant.grid_id;
				} else {
					form_id = constant.form_id;
					dbname_id = constant.dbname_id;
					inputnum_id = constant.inputnum_id;
					grid_id = constant.grid_id;
				}
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
					server_path:"create_newdbcol/",
					server_key:'info_data',
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
				var op_type = ('op_type' in options_obj)?options_obj.op_type:"advance";
				var grid_id = (op_type == "wizard")?wizconstant.wizid_stem+wizconstant.grid_id:constant.grid_id;
				// write op_type back to options_obj in case it did not exist
				options_obj.op_type = op_type;
				options_obj.serverdata_key = 'info_list';
				options_obj.idproperty = constant.idproperty_str;
				options_obj.server_key = 'info_data';
				options_obj.server_path = "create_newdbcol/";
				options_obj.cellselect_flag = false;
				options_obj.text_node_str = "Division List Name";
				options_obj.grid_id = grid_id;
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
						numgdaysperweek:1, totalgamedays:this.base_numweeks,
						gameinterval:1, mingap_days:1, maxgap_days:2});
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
			create_calendar_input: function(op_type) {
				var divinfogrid_id = (op_type == 'wizard')?wizconstant.wizid_stem+wizconstant.grid_id:constant.grid_id;
				var divinfogrid_node = dom.byId(divinfogrid_id);
				var topdiv_node = put(divinfogrid_node, "-div");
				if (!this.widgetgen) {
					this.widgetgen = new WidgetGen({
						storeutil_obj:this.storeutil_obj,
						server_interface:this.server_interface
					});
				}
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
			create_wizardcontrol: function(pcontainerdiv_node, gcontainerdiv_node) {
				// create cpane control for divinfo wizard pane under menubar
				var pcontainer_id = wizconstant.wizid_stem+wizconstant.pcontainer_suffix_id;
				this.pstackcontainer = new StackContainer({
					doLayout:false,
					style:"float:left; width:80%",
					id:pcontainer_id,
				}, pcontainerdiv_node);
				// reset pane for initialization and after delete
				var reset_cpane = new ContentPane({
					id:wizconstant.wizid_stem+wizconstant.resetcpane_id,
				})
				this.pstackcontainer.addChild(reset_cpane)
				// add div config (number) cpane
				var div_cpane = new ContentPane({
					id:wizconstant.ndcpane_id,
				})
				var div_form = new Form({
					id:wizconstant.dform_id
				})
				div_cpane.addChild(div_form);
				this.pstackcontainer.addChild(div_cpane);
				// add txt + button cpane
				var txtbtn_cpane = new ContentPane({
					id:wizconstant.tcpane_id,
				})
				put(txtbtn_cpane.containerNode, "span[id=$]",
					wizconstant.infotxt_id);
				put(txtbtn_cpane.containerNode, "button[id=$]",
					wizconstant.infobtn_id);
				this.pstackcontainer.addChild(txtbtn_cpane)
				// create grid stack container and grid
				var gcontainer_id = wizconstant.wizid_stem+wizconstant.gcontainer_suffix_id;
				this.gstackcontainer = new StackContainer({
					doLayout:false,
					style:"clear:left",
					id:gcontainer_id
				}, gcontainerdiv_node);
				// add blank pane (for resetting)
				var blank_cpane = new ContentPane({
					id:wizconstant.wizid_stem+wizconstant.blankcpane_id,
				})
				this.gstackcontainer.addChild(blank_cpane);
				// add divinfo cpane and grid div
				var div_cpane = new ContentPane({
					id:wizconstant.divcpane_id,
				})
				put(div_cpane.containerNode, "div[id=$]",
					wizconstant.wizid_stem+wizconstant.grid_id);
				this.gstackcontainer.addChild(div_cpane);
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
		});
});
