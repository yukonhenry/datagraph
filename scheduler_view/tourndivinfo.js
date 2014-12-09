// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dgrid/editor", "dijit/form/NumberTextBox",
	"dijit/form/ValidationTextBox","LeagueScheduler/baseinfo",
	"LeagueScheduler/baseinfoSingleton", "put-selector/put",
	"dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, editor, NumberTextBox,
		ValidationTextBox, baseinfo, baseinfoSingleton, put) {
		var constant = {
			idproperty_str:"tourndiv_id",
			updatebtn_str:"Update Tourn Div Info",
			grid_id:"tourndivinfogrid_id",
			text_node_str: 'Tournament Division List Name',
			db_type:'tourndb',
			inputnum_str:'Number of Tournament Divisions',
			dbname_str:'New Tourn Division List Name',
			vtextbox_str:'Enter Tourn Division List Name',
			ntextbox_str:'Enter Number of Tourn Divisions',
		};
		return declare(baseinfo, {
			idproperty:constant.idproperty_str, db_type:constant.db_type,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
			},
			getcolumnsdef_obj: function() {
				// IMPORTANT: make sure one field matches the idproperty string, if
				// the idproperty is going to be used at the idProperty field for
				// the store
				var columnsdef_obj = {
					tourndiv_id: "Div ID",
					div_age: editor({label:"Age", autoSave:true,
						set:function(item) {
							// trim any leading or trailing whitespace characters
							return item.div_age.trim();
						}}, "text","click"),
					div_gen: editor({label:"Gender", autoSave:true,
						set:function(item) {
							return item.div_gen.trim();
						}}, "text","click"),
					totalteams: editor({label:"Total Teams", autoSave:true,
						set:function(item) {
							return parseInt(item.totalteams)
						}}, "text", "click"),
					totalgamedays: editor({label:"RR games", autoSave:true,
						set:function(item) {
							return parseInt(item.totalgamedays)
						}}, "text", "click"),
					gameinterval: editor({label:"Inter-Game Interval (min)",
						autoSave:true,
						set:function(item) {
							return parseInt(item.gameinterval)
						}}, "text", "click"),
					mingap_time: editor({label:"Per-team Minimum Gap (min)",
						autoSave:true,
						set:function(item) {
							return parseInt(item.mingap_time)
						}}, "text", "click"),
					elimination_type: editor({label:"Elimination Type",
						autoSave:true,
						set:function(item) {
							return item.elimination_type.trim().toUpperCase()
						}}, "text", "click"),
					thirdplace_enable: editor({label:"Gen 3rd Place Match",
						autoSave:true,
						set:function(item) {
							return item.thirdplace_enable.trim().toUpperCase()
						}}, "text", "click")
				};
				return columnsdef_obj;
			},
			getfixedcolumnsdef_obj: function () {
				var columnsdef_obj = {
					tourndiv_id:"Div ID",
					div_age:"Age Group/Primary Group ID",
					div_gen:"Gender/Secondary Group ID",
					totalteams:"Total #Teams",
					totalgamedays:"Total # Games",
					gameinterval:"Game Interval(min)",
					mingap_time:"Minimum Gap Time(min)",
					elimination_type:"Elimination Type",
					thirdplace_enable:"Gen 3rd Place Match"
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
				var tooltipconfig_list = [{connectId:[constant.inputnum_id],
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
					// make sure one of the keys matches the idProperty used for
					// store.
					info_list.push({tourndiv_id:i, div_age:"", div_gen:"",
						totalteams:2, totalgamedays:2, gameinterval:80,
						mingap_time:120, elimination_type:'D',
						thirdplace_enable:'N'});
				}
				return info_list;
			},
			get_gridhelp_list: function() {
				var gridhelp_list = [
					{id:'tourndiv_id', help_str:"Identifier, Non-Editable"},
					{id:'div_age', help_str:"Age or Primary Division Identifier, click cell to edit"},
					{id:'div_gen', help_str:"Gender or Secondary Division Identifier, click cell to edit"},
					{id:'totalteams', help_str:"Total # of Teams in the Division, click cell to edit"},
					{id:'totalgamedays', help_str:"Number of games each team should play in the round robin portion of the tournament"},
					{id:'gameinterval', help_str:"NOTE: Assign Time interval between scheduled games on a field, e.g. the length of a single game plus break between games; click cell to edit"},
					{id:'mingap_time', help_str:"NOTE: Specify the minimum time gap between the end of one game and the start of the next (for each team)"},
					{id:'elimination_type', help_str:"Elimination tournament type('C'- Consolation; 'D'- double elimination; 'S'- single elimination"},
					{id:'thirdplace_enable', help_str:"3rd Place Match Generation required? ('Y'- Yes; 'N'- No"}]
				return gridhelp_list;
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
						if (prop == 'totalteams') {
							if (item[prop] < 2) {
								console.log("tourndivinfo:checkconfig:need at least two teams");
								break_flag = true;
								break;
							}
						} else if (prop == 'totalgamedays') {
							if (item[prop] < 1) {
								console.log("tourndivinfo:checkconfig:need at least one bracket");
								break_flag = true;
								break;
							}
						} else if (prop == 'elimination_type') {
							// grab first character (trim and upper case converion
							// already completed in editor command)
							var prop_item = item[prop].charAt(0);
							if (prop_item != 'C' && prop_item != 'S' &&
								prop_item != 'D') {
								console.log("tourndivinfo:checkconfig:specify single, double, or consolation elim type");
								break_flag = true;
								break;
							}
						} else if (prop == 'thirdplace_enable') {
							// trim string (both sides), convert to upper case,
							// and grab first character
							var prop_item = item[prop].charAt(0);
							if (prop_item != 'Y' && prop_item != 'N') {
								console.log("tourndivinfo:checkconfig: Specify 'Y' or 'N' for enabling/disabling 3rd place match generation");
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
			}
		});
});
