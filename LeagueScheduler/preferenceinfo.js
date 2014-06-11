define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dijit/form/NumberTextBox", "dijit/form/ValidationTextBox",
	"dijit/form/DateTextBox", "dijit/form/TimeTextBox", "dgrid/editor",
	"dijit/form/Form", "dijit/layout/StackContainer", "dijit/layout/ContentPane",
	"LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/idmgrSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, NumberTextBox,
		ValidationTextBox, DateTextBox, TimeTextBox, editor, Form, StackContainer,
		ContentPane, baseinfo,
		baseinfoSingleton, idmgrSingleton, put){
		var constant = {
			idproperty_str:'pref_id', db_type:'prefdb',
			dbname_str:'New Preference List Name',
			vtextbox_str:'Enter Preference List Name',
			ntextbox_str:'Enter Number of Preferences',
			inputnum_str:'Number of Preferences',
			text_node_str:'Preference List Name',
			updatebtn_str:'Update Preference Info',
			text_node_str: 'Preference List Name',
		};
		var wizconstant = {
			npcpane_id:"wiznumprefcpane_id",
		};
		return declare(baseinfo, {
			infogrid_store:null, idproperty:constant.idproperty_str,
			db_type:constant.db_type, today:null, idmgr_obj:null,
			//divstr_colname, divstr_db_type, widgetgen are all member var's
			// that have to do with the db_type radiobutton /
			// league select drop down
			divstr_colname:"", divstr_db_type:"rrdb", widgetgen:null,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
				this.today = new Date();
				this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
					id:this.idproperty, op_type:this.op_type});
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
					pref_id: "ID",
					priority: editor({label:"Priority", autoSave:true,
						editorArgs:{
							constraints:{min:1, max:500},
							promptMessage:'Enter Priority Number (lower is higher priority)',
							invalidMessage:'Must be Non-zero integer',
							missingMessage:'Enter Priority',
							value:'1',
							//style:'width:6em',
							style:"width:auto",
						}}, NumberTextBox),
					div_id: editor({label:"Divison Id", autoSave:true,
						editorArgs:{
							constraints:{min:1, max:50},
							promptMessage:'Enter Division ID',
							invalidMessage:'Must be Non-zero integer',
							missingMessage:'Enter Division ID',
							value:'1',
							//style:'width:6em',
							style:"width:auto",
						}}, NumberTextBox),
					team_id: editor({label:"Team Id", autoSave:true,
						editorArgs:{
							constraints:{min:1, max:100},
							promptMessage:'Enter Team ID',
							invalidMessage:'Must be Non-zero integer',
							missingMessage:'Enter Team ID',
							value:'1',
							//style:'width:6em',
							style:"width:auto",
						}}, NumberTextBox),
					game_date: editor({label:'Game Date', autoSave:true,
						editorArgs:{
							//style:'width:120px'
							style:"width:auto",
						}
					}, DateTextBox),
					start_after: editor({label:'Start After', autoSave:true,
						editorArgs:{
							style:"width:auto",
						}
					}, TimeTextBox),
					end_before: editor({label:'End Before', autoSave:true,
						editorArgs:{
							style:"width:auto",
						}
					}, TimeTextBox),
				};
				return columnsdef_obj;
			},
			getfixedcolumnsdef_obj: function() {
				// column definition for constraint satisfaction cpane display
				// after schedule is generated
				var columnsdef_obj = {
					pref_id:"Preference ID",
					priority:"Priority",
					div_id:"Division ID",
					div_age:"Age Group",
					div_gen:"Gender",
					team_id:"Team ID",
					game_date:"Game Date",
					start_after:"Start After",
					end_before:"End Before",
					satisfy:"Met"
				}
				return columnsdef_obj;
			},
			modifyserver_data: function(data_list) {
				arrayUtil.forEach(data_list, function(item, index) {
					// save date str to pass into start and end time calc
					// (though it can be a dummy date)
					var game_date_str = item.game_date;
					var start_after_str = item.start_after;
					var end_before_str = item.end_before;
					item.game_date = new Date(game_date_str);
					item.start_after = new Date(game_date_str+' '+start_after_str);
					item.end_before = new Date(game_date_str+' '+end_before_str);
				});
				return data_list;
			},
			modify_toserver_data: function(raw_result) {
				// modify store data before sending data to server
				var newlist = new Array();
				// similar to field data, for the pref grid data convert Data objects to str
				// note we want to keep it as data objects inside of store to
				// maintain direct compatibility with Date and TimeTextBox's
				// and associated picker widgets.
				raw_result.map(function(item) {
					var newobj = lang.clone(item);
					newobj.game_date = newobj.game_date.toLocaleDateString();
					newobj.start_after = newobj.start_after.toLocaleTimeString();
					newobj.end_before = newobj.end_before.toLocaleTimeString();
					return newobj;
				}).forEach(function(obj) {
					newlist.push(obj);
				});
				return newlist;
			},
			initialize: function(newgrid_flag, op_type) {
				var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : "wizard";
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
					label:"Specify Initial Number of Preferences and press ENTER",
					position:['below','after']},
					{connectId:[this.idmgr_obj.dbname_id],
					label:"Specify Preference List Name",
					position:['below','after']}];
				var args_obj = {
					dbname_reg:dbname_reg,
					form_reg:form_reg,
					entrynum_reg:inputnum_reg,
					server_path:"create_newdbcol/",
					server_key:'info_data',
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
				options_obj.grid_id = this.idmgr_obj.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.getserver_path = 'get_dbcol/'
				options_obj.db_type = constant.db_type;
				this.inherited(arguments);
			},
			getInitialList: function(num) {
				var info_list = new Array();
				for (var i = 1; i < num+1; i++) {
					info_list.push({pref_id:i, div_id:1, team_id:i,
						priority:i, game_date:this.today,
						start_after:new Date(2014,0,1,8,0,0),
						end_before:new Date(2014,0,1,17,0,0)});
				}
				return info_list;
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
				var pref_cpane = new ContentPane({
					id:wizconstant.npcpane_id,
				})
				var pref_form = new Form({
					id:this.idmgr_obj.form_id
				})
				pref_cpane.addChild(pref_form);
				this.pstackcontainer.addChild(pref_cpane);
				// add txt + button cpane
				var txtbtn_cpane = new ContentPane({
					id:this.idmgr_obj.textbtncpane_id,
				})
				put(txtbtn_cpane.containerNode, "span[id=$]",
					this.getbtntxtid_obj("wizard", this.idproperty).text_id);
				put(txtbtn_cpane.containerNode, "button[id=$]",
					this.getbtntxtid_obj("wizard", this.idproperty).btn_id);
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
				var prefgrid_cpane = new ContentPane({
					id:this.idmgr_obj.gridcpane_id,
				})
				put(prefgrid_cpane.containerNode, "div[id=$]",
					this.idmgr_obj.grid_id);
				this.gstackcontainer.addChild(prefgrid_cpane);
			},
		});
});
