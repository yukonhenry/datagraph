define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dijit/form/NumberTextBox", "dijit/form/ValidationTextBox",
	"dijit/form/DateTextBox", "dijit/form/TimeTextBox", "dgrid/editor",
	"LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, NumberTextBox,
		ValidationTextBox, DateTextBox, TimeTextBox, editor, baseinfo,
		baseinfoSingleton, put){
		var constant = {
			idproperty_str:'pref_id', grid_id:'prefinfogrid_id', db_type:'prefdb',
			form_id:'pref_form_id', dbname_id:'prefdbname_id',
			inputnum_id:'prefinputnum_id',
			text_node_str:'Preference List Name',
			updatebtn_str:'Update Preference Info',
			text_node_str: 'Preference List Name',
		};
		return declare(baseinfo, {
			infogrid_store:null, idproperty:constant.idproperty_str,
			db_type:constant.db_type, today:null,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
				this.today = new Date();
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
					pref_id: "ID",
					priority_num: editor({label:"Priority", autoSave:true,
						editorArgs:{
							constraints:{min:1, max:500},
							promptMessage:'Enter Priority Number (lower is higher priority)',
							invalidMessage:'Must be Non-zero integer',
							missingMessage:'Enter Priority',
							value:'1',
							style:'width:6em',
						}}, NumberTextBox),
					div_id: editor({label:"Divison Id", autoSave:true,
						editorArgs:{
							constraints:{min:1, max:50},
							promptMessage:'Enter Division ID',
							invalidMessage:'Must be Non-zero integer',
							missingMessage:'Enter Division ID',
							value:'1',
							style:'width:6em',
						}}, NumberTextBox),
					team_id: editor({label:"Team Id", autoSave:true,
						editorArgs:{
							constraints:{min:1, max:100},
							promptMessage:'Enter Team ID',
							invalidMessage:'Must be Non-zero integer',
							missingMessage:'Enter Team ID',
							value:'1',
							style:'width:6em',
						}}, NumberTextBox),
					game_date: editor({label:'Game Date', autoSave:true,
						editorArgs:{
							style:'width:120px'
						}
					}, DateTextBox),
					start_after: editor({label:'Start After', autoSave:true,
						}, TimeTextBox),
					end_before: editor({label:'End Before', autoSave:true,
						}, TimeTextBox),
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
				var form_reg = registry.byId(constant.form_id);
				var form_node = form_reg.domNode;
				var dbname_reg = null;
				var inputnum_reg = null;
				if (!dbname_node) {
					put(form_node, "label.label_box[for=$]",
						constant.dbname_id, "New Preference List Name");
					var dbname_node = put(form_node,
						"input[id=$][type=text][required=true]",
						constant.dbname_id)
					dbname_reg = new ValidationTextBox({
						value:'',
						regExp:'\\D[\\w]+',
						style:'width:12em',
						promptMessage:'Enter New Preference List -start with letter or _, followed by alphanumeric or _',
						invalidMessage:'start with letter or _, followed by alphanumeric characters and _',
						missingMessage:'enter preference list name'
					}, dbname_node);
					put(form_node, "span.empty_smallgap");
					put(form_node, "label.label_box[for=$]",
						constant.inputnum_id, "Number of Preferences");
					var inputnum_node = put(form_node,
						"input[id=$][type=text][required=true]",
						constant.inputnum_id);
					inputnum_reg = new NumberTextBox({
						value:'1',
						style:'width:5em',
						constraints:{min:1, max:500},
						promptMessage:'Enter Number of Preferences',
						invalidMessage:'Must be Non-zero integer',
						missingMessage:'Enter Number of Preferences (positive integer)'
					}, inputnum_node);
				} else {
					dbname_reg = registry.byId(constant.dbname_id);
					inputnum_reg = registry.byId(constant.inputnum_id);
				}
				var tooltipconfig_list = [{connectId:[constant.inputnum_id],
					label:"Specify Initial Number of Preferences and press ENTER",
					position:['below','after']},
					{connectId:[constant.dbname_id],
					label:"Specify Preference List Name",
					position:['below','after']}];
				var args_obj = {
					dbname_reg:dbname_reg,
					form_reg:form_reg,
					entrynum_reg:inputnum_reg,
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
				options_obj.text_node_str = "Preference List Name";
				options_obj.grid_id = constant.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.getserver_path = 'get_dbcol/'
				options_obj.db_type = constant.db_type;
				this.inherited(arguments);
			},
			getInitialList: function(num) {
				var info_list = new Array();
				for (var i = 1; i < num+1; i++) {
					info_list.push({pref_id:i, div_id:1, team_id:i,
						priority_num:i, game_date:this.today,
						start_after:new Date(2014,0,1,8,0,0),
						end_before:new Date(2014,0,1,17,0,0)});
				}
				return info_list;
			},
		});
});
