// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dojo/store/Observable","dojo/store/Memory","dijit/registry",
	"dijit/DropDownMenu", "dijit/PopupMenuItem", "dijit/MenuItem",
	"dijit/MenuBar", "dijit/MenuBarItem", "dijit/PopupMenuBarItem",
	"dijit/Tooltip", "dijit/form/DropDownButton", "dijit/layout/ContentPane",
	"scheduler_front/baseinfoSingleton", "scheduler_front/widgetgen",
	"scheduler_front/divinfo", "scheduler_front/fieldinfo",
	"scheduler_front/newschedulerbase", "scheduler_front/preferenceinfo",
	"scheduler_front/tourndivinfo", "scheduler_front/teaminfo",
	"scheduler_front/conflictinfo",
	"put-selector/put",
	"dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, Observable, Memory,
		registry, DropDownMenu, PopupMenuItem, MenuItem, MenuBar, MenuBarItem,
		PopupMenuBarItem, Tooltip, DropDownButton, ContentPane,
		baseinfoSingleton, WidgetGen, DivInfo, FieldInfo, NewSchedulerBase,
		PreferenceInfo, TournDivInfo, TeamInfo, ConflictInfo, put) {
		var constant = {
			idtopmenu_list:[
				{id:'div_id', label_str:"Configure League Divisions",
					help_str:"Configure Division/Fields for Round Robin League Schedule", mbaritem_id:"divmbaritem_id", db_type:'rrdb'},
				{id:'tourndiv_id', label_str:"Tournament format",
					help_str:"Configure Division/Fields for Tournament Schedule",
					mbaritem_id:"tourndivmbaritem_id", db_type:'tourndb'},
				{id:'field_id', label_str:"Specify Fields",
					help_str:"Configure Field Information",
					mbaritem_id:"fieldmbaritem_id", db_type:'fielddb'},
				{id:'newsched_id', label_str:"Generate Schedule",
					help_str:"Configure Final Set of Parameters and Generate",
					mbaritem_id:"newschedmbaritem_id", db_type:'newscheddb'},
				{id:'pref_id', label_str:"Scheduling Preferences",
					help_str:"Configure Preferences List",
					mbaritem_id:"prefmbaritem_id", db_type:'prefdb'},
				{id:'team_id', label_str:"Specify Teams", help_str:"Configure Team-specific information/constraints", db_type:'teamdb'},
				{id:'conflict_id', label_str:"Specify Time Conflicts", help_str:"Configure any teams that should avoid time conflicts",
					db_type:'conflictdb'}
			],
			initmenu_list:[
				{id:'div_id', label_str:"Create New Division Info",
					help_str:"To Create, Click"},
				{id:'tourndiv_id', label_str:"Create New Tournament Division Info",
					help_str:"To Create, Click"},
				{id:'field_id', label_str:"Create New Field List",
					help_str:"To Create, Click Here"},
				{id:'newsched_id', label_str:"Generate New Schedule",
					help_str:"To Create Schedule Paramenters and Generate, Click"},
				{id:'pref_id', label_str:"Create New Preference List",
					help_str:"To Create Preferences, Click Here"},
				{id:'team_id', label_str:"Create New Team List",
					help_str:"To Create Team List, Click Here"},
				{id:'conflict_id', label_str:"Create New Conflicts List",
					help_str:"To Create Conflicts List, Click Here"}
			],
			editmenu_list:[
				{id:'div_id', db_type:'rrdb', label_str:"Edit Division Info",
					help_str:"To Edit, Click and Select Previously Saved Division List Name"},
				{id:'tourndiv_id', db_type:'tourndb',
					label_str:"Edit Division Info",
					help_str:"To Edit, Click and Select Previously Saved Division List Name"},
				{id:'field_id', db_type:'fielddb', label_str:"Edit Field List",
					help_str:"To Edit, Click and Select Previously Saved Field List Name"},
				{id:'newsched_id', db_type:'newscheddb',
					label_str:"Regenerate Schedule",
					help_str:"To Regenerate, Click and Select Previously Saved Schedule Name"},
				{id:'pref_id', db_type:'prefdb', label_str:"Edit Preference List",
					help_str:"To Edit, Click and Select Previously Saved Preference List Name"},
				{id:'team_id', db_type:'teamdb', label_str:"Edit Team List",
					help_str:"To Edit, Click and Select Previously Division/Team List Name"},
				{id:'conflict_id', db_type:'conflictdb',
					label_str:"Edit Conflict List",
					help_str:"To Edit, Click and Select Previously Division/Team List Name"}
			],
			delmenu_list:[
				{id:'div_id', db_type:'rrdb', label_str:"Delete Division Info",
					help_str:"To Delete, Click and Select Previously Saved Division List Name"},
				{id:'tourndiv_id', db_type:'tourndb',
					label_str:"Delete Division Info",
					help_str:"To Delete, Click and Select Previously Saved Division List Name"},
				{id:'field_id', db_type:'fielddb', label_str:"Delete Field List",
					help_str:"To Delete, Click and Select Previously Saved Field List Name"},
				{id:'newsched_id', db_type:'newscheddb',
					label_str:"Delete Schedule",
					help_str:"To Delete, Click and Select Previously Saved Schedule Name"},
				{id:'pref_id', db_type:'prefdb', label_str:"Delete Preference List",
					help_str:"To Delete, Click and Select Previously Saved Team List Name"},
				{id:'team_id', db_type:'teamdb', label_str:"Delete Team List",
					help_str:"To Delete, Click and Select Previously Saved Team List Name"},
				{id:'conflict_id', db_type:'conflictdb',
					label_str:"Delete Conflict List",
					help_str:"To Delete, Click and Select Previously Saved Conflict List Name"}
			],
			adv_dbselect_radio1_id:"adv_dbselect_radio1_id",
			adv_dbselect_radio2_id:"adv_dbselect_radio2_id",
			init_sched_type:"L"
		};
		return declare(null, {
			dbselect_store:null, schedutil_obj:null, uistackmgr:null,
			server_interface:null, dbstore_list:null, wizuistackmgr:null,
			userid_name:"", rrdbmenureg_list:null, fielddbmenureg_list:null,
			tdbmenureg_list:null, nsdbmenureg_list:null,
			prefdbmenureg_list:null, teamdbmenureg_list:null,
			conflictdbmenureg_list:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.dbstore_list = new Array();
				// idProperty not assigned as we are using an 'id' field
				//this.dbselect_store = new Observable(new Memory({data:new Array(),
				//	idProperty:'name'}));
				// round robin menu register list
				this.rrdbmenureg_list = new Array();
				// tournament menu register list
				this.tdbmenureg_list = new Array();
				// field menu register list
				this.fielddbmenureg_list = new Array();
				// new sched/generate menu list
				this.nsdbmenureg_list = new Array();
				// preference menu list
				this.prefdbmenureg_list = new Array();
				// team menu list
				this.teamdbmenureg_list = new Array();
				// conflict nmenu list
				this.conflictdbmenureg_list = new Array();
			},
			createdb_store: function(db_list, db_type) {
				/* create store for db name labels which are used for select dropdowns
				follow observable store model followed by
				https://www.sitepen.com/blog/2011/02/15/dojo-object-stores/
				http://dojotoolkit.org/reference-guide/1.9/dojo/store/Observable.html#dojo-store-observable
				Note we can't tie the store directly to select since we are
				using dropdown->menuitem instead of select
				Assume db_list is a list of objects {name:, config_status:}
				that is returned from server
				Note instead of having one large store that handles all db_types,
				create a list of stores, where each store is specific to a db_type */
				var dbselect_store = new Observable(new Memory({data:new Array(),
					idProperty:'name'}));
				// add initial entry
				arrayUtil.forEach(db_list, function(item, index) {
					var store_obj = null;
					// if divstr_db_type exists in the db collection info,
					// add to the local store object
					if ("divstr_db_type" in item) {
						store_obj = {name:item.name,
							config_status:item.config_status,
							divstr_db_type:item.divstr_db_type};
					} else {
						store_obj = {name:item.name,
							config_status:item.config_status};
					}
					dbselect_store.add(store_obj);
				});
				this.dbstore_list.push({db_type:db_type,
					dbselect_store:dbselect_store});
				// ref http://dojotoolkit.org/reference-guide/1.9/dojo/store/Observable.html
				// http://www.sitepen.com/blog/2011/02/15/dojo-object-stores/
				var dbtype_result = dbselect_store.query();
				dbtype_result.observe(lang.hitch(this, function(object, removeIndex, insertIndex) {
					// get all newsched obj's - typically there can be one each for
					// advanced and wizard modes
					var newsched_obj_list = baseinfoSingleton.get_obj_list('newsched_id');
					if (removeIndex > -1) {
						// note removing by index only may not be reliable
						// other option is to pass in the object and then search
						// the reg children to find a math on the label
						this.regenDelDBCollection_smenu(removeIndex, db_type);
						arrayUtil.forEach(newsched_obj_list,
						function(register_obj) {
							// look at baseinfosingleton register_obj function for
							// correct register obj definition
							var newsched_obj = register_obj.obj;
							if (newsched_obj.selectexists_flag) {
								// increment index by one as select includes
								// generic 0-th entry
								newsched_obj.removefrom_select(db_type,
									removeIndex+1);
							}
						})
					}
					if (insertIndex > -1) {
						this.regenAddDBCollection_smenu(insertIndex,
							object, db_type);
						arrayUtil.forEach(newsched_obj_list,
						function(register_obj) {
							var newsched_obj = register_obj.obj;
							if (newsched_obj.selectexists_flag) {
								newsched_obj.addto_select(db_type, object.name,
									insertIndex);
							}
						})
					}
				}));
			},
			nodupdb_validate: function(colname, id) {
				var match_obj = this.getuniquematch_obj(constant.editmenu_list, 'id', id);
				var db_type = match_obj.db_type;
				var dbselect_store = this.getselect_store(db_type);
				if (dbselect_store) {
					return dbselect_store.query({name:colname,
						config_status:1}).total == 0;
				} else
					return null;
			},
			// get store that matches db_type from the list of stores
			getselect_store: function(db_type) {
				var match_list = arrayUtil.filter(this.dbstore_list,
					function(item) {
						return item.db_type == db_type;
					}
				);
				if (match_list.length > 0) {
					return match_list[0].dbselect_store;
				} else
					return null;
			},
			// add entry to dbselect store
			addtodb_store: function(colname, id, config_status, divstr_db_type) {
				var match_obj = this.getuniquematch_obj(constant.editmenu_list, 'id', id);
				var db_type = match_obj.db_type;
				var dbselect_store = this.getselect_store(db_type);
				var query_obj = null;
				// query also with divstr_db_type if it exists
				if (typeof divstr_db_type !== "undefined")
					query_obj = {name:colname, divstr_db_type:divstr_db_type};
				else
					query_obj = {name:colname};
				var result_list = dbselect_store.query(query_obj);
				if (result_list.total == 0) {
					query_obj.config_status = config_status; // add status field
					dbselect_store.add(query_obj);
				} else {
					var match_obj = result_list[0];
					match_obj.config_status = config_status;
					dbselect_store.put(match_obj);
				}
			},
			getfromdb_store_value:function(args_obj) {
				var db_type = args_obj.db_type;
				var key = args_obj.key;
				var query_obj = {};
				if ('config_status' in args_obj) {
					query_obj.config_status = args_obj.config_status;
				}
				if ('actualsched_type' in args_obj && db_type == "fielddb") {
					var divstr_db_type = (args_obj.actualsched_type == "L") ?
						"rrdb":"tourndb";
					query_obj.divstr_db_type = divstr_db_type
				}
				var dbselect_store = this.getselect_store(db_type);
				var dbtype_result = dbselect_store.query(query_obj)
					.map(function(item){
						return item[key];
					});
				return dbtype_result;
			},
			removefromdb_store: function(item, db_type) {
				// confirm format of id field
				var dbselect_store = this.getselect_store(db_type);
				dbselect_store.remove(item);
			},
			store_init_dbcollection: function(data_list) {
				arrayUtil.forEach(data_list, function(item) {
					this.createdb_store(item.db_list, item.db_type)
				}, this)
			},
			init_advanced_UI: function(userid_name, widgetgen_obj) {
				// ADVANCE MENU target
				// save data to local db and create menu structure for advanced
				// pane
				// Note: Order in of single-level items in Menu structure is
				// determined by order of objects in info_obj_list
				this.userid_name = userid_name;
				var newschedbase_obj = new NewSchedulerBase({
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					uistackmgr_type:this.uistackmgr, userid_name:userid_name,
					storeutil_obj:this, op_type:"advance"});
				var divinfo_obj = new DivInfo({
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					uistackmgr_type:this.uistackmgr, userid_name:userid_name,
					storeutil_obj:this, op_type:"advance"});
				var tourndivinfo_obj = new TournDivInfo({
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					uistackmgr_type:this.uistackmgr, userid_name:userid_name,
					storeutil_obj:this, op_type:"advance"});
				var fieldinfo_obj = new FieldInfo({
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					uistackmgr_type:this.uistackmgr, userid_name:userid_name,
					storeutil_obj:this, op_type:"advance"});
				var preferenceinfo_obj = new PreferenceInfo({
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					uistackmgr_type:this.uistackmgr, userid_name:userid_name,
					storeutil_obj:this, op_type:"advance"});
				var teaminfo_obj = new TeamInfo({
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					uistackmgr_type:this.uistackmgr, userid_name:userid_name,
					storeutil_obj:this, op_type:"advance"});
				var conflictinfo_obj = new ConflictInfo({
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					uistackmgr_type:this.uistackmgr, userid_name:userid_name,
					storeutil_obj:this, op_type:"advance"});
				// sched_type legend:
				// 'L': League/Round Robin
				// 'T': Tournament
				// 'B': Both, applies to both League and Tournament
				var info_obj_list = [
					{id:'div_id', info_obj:divinfo_obj, sched_type:'L'},
					{id:'tourndiv_id', info_obj:tourndivinfo_obj,
						sched_type:'T'},
					{id:'field_id', info_obj:fieldinfo_obj, sched_type:'B'},
					{id:'team_id', info_obj:teaminfo_obj, sched_type:'L'},
					{id:'pref_id', info_obj:preferenceinfo_obj,
						sched_type:'L'},
					{id:'conflict_id', info_obj:conflictinfo_obj,
						sched_type:'L'},
					{id:'newsched_id', info_obj:newschedbase_obj,
						sched_type:'B'},
				]
				var args_list = new Array();
				//var editpane = registry.byId("editPane");
				var tabcontainer = registry.byId("tabcontainer_id")
				var advanced_cpane = registry.byId("editPane");
				if (advanced_cpane) {
					return;
				}
				advanced_cpane = new ContentPane({
					title:"Advanced UI",
					id:"editPane",
					class:"allonehundred",
				})
				advanced_cpane.on("show", lang.hitch(this, function(evt) {
					console.log("advanced onshow");
					// only uistackmgr relevant for resizing (and not wizuistackmgr)
					if (this.uistackmgr && this.uistackmgr.current_grid) {
						this.uistackmgr.current_grid.resize();
					}
					advanced_cpane.domNode.scrollTop = 0;
				}))
				advanced_cpane.on("load", function(evt) {
					console.log("advanced onload");
					advanced_cpane.domNode.scrollTop = 0;
				})
				tabcontainer.addChild(advanced_cpane)
				var topdiv_node = advanced_cpane.containerNode;
				// instead of adding the dropdown btn by cpane.addChild, create
				// btn on top of node created by put. Do this so that we can place
				// text verbiage above button about user id.  Tried adding text
				// with cpane.content but placement disrupts the location of widgets
				// created within cpane
				var useridtext_node = put(topdiv_node, "div");
				useridtext_node.innerHTML = "<p style='font-size:larger'>User/Organization ID: <strong>"+
					userid_name+"</strong></p>"
				// create ddown_menu widget here so that it can be passed to
				// radio button callback
				var editddown_menu = new DropDownMenu({
				})
				widgetgen_obj.create_dbtype_radiobtn(topdiv_node,
					constant.adv_dbselect_radio1_id,
					constant.adv_dbselect_radio2_id, "rrdb",
					this, this.radio1_callback, this.radio2_callback,
					{ddownmenu_widget:editddown_menu,
						info_obj_list:info_obj_list});
				var editddown_btn_node = put(topdiv_node, "button[id=$][type=button]","editddown_btn_id");

				var editddown_btn = new DropDownButton({
					class:"primary editsched",
					label:"Select Configuration",
					dropDown:editddown_menu
				}, editddown_btn_node)
				this.create_dropdown(constant.init_sched_type, info_obj_list,
					editddown_menu)
				/*
				arrayUtil.forEach(info_obj_list, function(item) {
					var id = item.id;
					if (id == 'div_id' || id == 'tourndiv_id') {
						args_list.push({id:id, info_obj:item.info_obj})
					} else {
						this.create_menu(id, item.info_obj, true, editddown_menu);
					}
				}, this) */
				// specify parameters for the two-level menu
				// first specify for the divinfo dropdown
				// menu_index is the display position in the parent_ddown widget
				// Note general positioining in menu is not as flexible even with
				// use of menu_index - a position index does not work unless there
				// is already a menu structure created with at least that menu index
				// items - index x requires that x+1 entries have  already been
				// created.
				/*
				var args_obj = {parent_ddown_reg:editddown_menu,
					args_list:args_list, label_str: "Division Info",
					menu_index:0}
				this.create_divmenu(args_obj); */
				// create other cpane stacks
				this.uistackmgr.create_paramcpane_stack(advanced_cpane);
				this.uistackmgr.create_grid_stack(advanced_cpane);
			},
			create_divmenu: function(args_obj) {
				// ADVANCE menu target
				// programmatic instantiation of submenus for divinfo and
				// tourndivinfo menu info
				var parent_ddown_reg = args_obj.parent_ddown_reg;
				var args_list = args_obj.args_list;
				var div_ddown_reg = new DropDownMenu();
				var div_popup_reg = new PopupMenuItem({
					label:args_obj.label_str,
					popup:div_ddown_reg,
				})
				parent_ddown_reg.addChild(div_popup_reg, args_obj.menu_index);
				arrayUtil.forEach(args_list, function(item, index) {
					this.create_menu(item.id, item.info_obj, true, div_ddown_reg,
						index)
				}, this)
			},
			create_menu: function(id, info_obj, delflag, ddown_reg) {
				// ADVANCE MENU target
				var match_obj = this.getuniquematch_obj(constant.idtopmenu_list,
					'id', id);
				var idtop_ddown_reg = new DropDownMenu();
				var idtop_popup_reg = new PopupMenuItem({
					label:match_obj.label_str,
					popup:idtop_ddown_reg,
				})
				ddown_reg.addChild(idtop_popup_reg);
				// create new info menu items
				match_obj = this.getuniquematch_obj(constant.initmenu_list,
					'id', id);
				var menu_reg = new MenuItem({
					label:match_obj.label_str,
					onClick:lang.hitch(this.uistackmgr, this.uistackmgr.check_initialize, info_obj)
				})
				idtop_ddown_reg.addChild(menu_reg);
				// edit menu; get submenu names based on db_type
				match_obj = this.getuniquematch_obj(constant.editmenu_list,
					'id', id);
				var ddownmenu_reg = new DropDownMenu();
				var popup_reg = new PopupMenuItem({
					label:match_obj.label_str,
					popup:ddownmenu_reg
				})
				idtop_ddown_reg.addChild(popup_reg);
				var db_type = match_obj.db_type;
				// create respective db menu
				args_obj = {db_type:db_type, key:'name',
					actualsched_type:info_obj.actualsched_type};
				var db_list = this.getfromdb_store_value(args_obj);
				this.generateDBCollection_smenu(ddownmenu_reg,
					db_list, this.uistackmgr, this.uistackmgr.check_getServerDBInfo,
					{db_type:db_type, info_obj:info_obj, storeutil_obj:this,
						op_type:"advance"})
				if (delflag) {
					match_obj = this.getuniquematch_obj(constant.delmenu_list,
						'id', id);
					// set up menus for delete if required
					// ref http://dojotoolkit.org/reference-guide/1.9/dijit/form/DropDownButton.html#dijit-form-dropdownbutton
					// http://dojotoolkit.org/reference-guide/1.9/dijit/Menu.html
					// NOTE: example in ref above shows a 'popup' property, but the
					// API spec for dijit/popupmenuitem does NOT have that property
					//idtop_ddown_reg = registry.byId(match_obj.parent_id)
					ddownmenu_reg = new DropDownMenu();
					popup_reg = new PopupMenuItem({
						label:match_obj.label_str,
						popup:ddownmenu_reg
					})
					idtop_ddown_reg.addChild(popup_reg);
					db_type = match_obj.db_type;
					// create respective del db menu
					this.generateDBCollection_smenu(ddownmenu_reg,
						db_list, this, this.delete_dbcollection,
						{db_type:db_type, storeutil_obj:this, op_type:"advance"});
				}
			},
			create_menubar: function(id, info_obj, delflag, mbar_node,
				edit_ddownmenu_widget, del_ddownmenu_widget) {
				// WIZARD pane target function
				// Similar to create_menu, except create a horizontal menubar instead
				// ddownmenu_widgets (for edit and delete) are optional parameters
				var edit_ddownmenu_widget = (typeof edit_ddownmenu_widget === "undefined" ||
					edit_ddownmenu_widget === null) ? new DropDownMenu() : edit_ddownmenu_widget;
				var del_ddownmenu_widget = (typeof del_ddownmenu_widget === "undefined" ||
					del_ddownmenu_widget === null) ? new DropDownMenu() : del_ddownmenu_widget;
				var tooltipconfig_list = new Array();
				// Create horizontal menubar
				var mbar_widget = new MenuBar({
					style:"width:40em; height:auto"}, mbar_node);
				//-----------------------------//
				// Create first element, which is a MenuBarItem that supports click to create new info item
				match_obj = this.getuniquematch_obj(constant.initmenu_list,
					'id', id);
				var mbaritem_widget = new MenuBarItem({
					id:match_obj.mbaritem_id,
					label:match_obj.label_str,
					style:"color:green; font:bold",
					onClick:lang.hitch(this.wizuistackmgr, this.wizuistackmgr.check_initialize, info_obj)
					//onClick:lang.hitch(info_obj, info_obj.wizinitialize)
				})
				// create tooltip config info for menubaritem
				tooltipconfig_list.push({
					connect_node:mbaritem_widget.domNode,
					label_str:match_obj.help_str});
				mbar_widget.addChild(mbaritem_widget);
				//-----------------------------//
				// Create second element, which is the edit menu
				match_obj = this.getuniquematch_obj(constant.editmenu_list,
					'id', id);
				var popmbaritem_widget = new PopupMenuBarItem({
					label:match_obj.label_str,
					style:"color:blue; font:bold",
					popup:edit_ddownmenu_widget
				})
				tooltipconfig_list.push({
					connect_node:popmbaritem_widget.domNode,
					label_str:match_obj.help_str});
				mbar_widget.addChild(popmbaritem_widget);
				var db_type = match_obj.db_type;
				// create respective db menu and populate dropdown
				args_obj = {db_type:db_type, key:'name'};
				var db_list = this.getfromdb_store_value(args_obj);
				this.generateDBCollection_smenu(edit_ddownmenu_widget,
					db_list, this.wizuistackmgr,
					this.wizuistackmgr.check_getServerDBInfo,
					{db_type:db_type, info_obj:info_obj, storeutil_obj:this,
						op_type:"wizard"})
				//----------------------------------------//
				// add delete menu items
				//if (delflag) {
				match_obj = this.getuniquematch_obj(constant.delmenu_list,
					'id', id);
				// set up menus for delete if required
				// ref http://dojotoolkit.org/reference-guide/1.9/dijit/form/DropDownButton.html#dijit-form-dropdownbutton
				// http://dojotoolkit.org/reference-guide/1.9/dijit/Menu.html
				// NOTE: example in ref above shows a 'popup' property, but the
				// API spec for dijit/popupmenuitem does NOT have that property
				//idtop_ddown_reg = registry.byId(match_obj.parent_id)
				popmbaritem_widget = new PopupMenuBarItem({
					label:match_obj.label_str,
					popup:del_ddownmenu_widget,
					style:"color:orange; font:bold",
				})
				tooltipconfig_list.push({
					connect_node:popmbaritem_widget.domNode,
					label_str:match_obj.help_str});
				mbar_widget.addChild(popmbaritem_widget);
				db_type = match_obj.db_type;
				// create respective del db menu
				this.generateDBCollection_smenu(del_ddownmenu_widget,
					db_list, this, this.delete_dbcollection,
					{db_type:db_type, storeutil_obj:this, op_type:"wizard"});
				//}
				var tooltip = null;
				var tooltipconfig = null;
				arrayUtil.forEach(tooltipconfig_list, function(item) {
					tooltipconfig = {
						connectId:[item.connect_node],
						label:item.label_str,
						position:['above','after']};
					tooltip = new Tooltip(tooltipconfig);
				})
				mbar_widget.startup();
			},
			getuniquematch_obj: function(list, key, value) {
				var match_list = arrayUtil.filter(list,
					function(item) {
						return item[key] == value;
					});
				return match_list[0];
			},
			getLabelDropDown_list: function(args_obj) {
				var db_type = args_obj.db_type;
				var label_str = args_obj.label_str;
				var config_status = args_obj.config_status;
				var init_colname = args_obj.init_colname;
				// get list of db's from store that have been completed
				args_obj.key = 'name';
				var label_list = this.getfromdb_store_value(args_obj);
				var select_flag = init_colname?false:true;
				// select_flag for the first entry is false if there is an init_colname
				var option_list = [{label:label_str, value:"",
					selected:select_flag}];
				arrayUtil.forEach(label_list, function(item, index) {
					select_flag = (init_colname && init_colname == item)
						? true:false;
					option_list.push({label:item, value:item, selected:select_flag});
				});
				return option_list;
			},
			delete_dbcollection: function(options_obj, event) {
				//console.log("delete dbcollection evt="+event);
				var item = options_obj.item;
				// items = event.label works as long as the calling function that
				// creates that menuitems is using the item value as the label
				//var item = event.label;
				var server_path = constant.delserver_path;
				var db_type = options_obj.db_type
				this.removefromdb_store(item, db_type);
				var match_obj = this.getuniquematch_obj(constant.delmenu_list,
					'db_type', db_type);
				var idproperty = match_obj.id;
				var uistackmgr = (options_obj.op_type == "wizard") ? this.wizuistackmgr:this.uistackmgr;
				uistackmgr.reset_cpane(idproperty);
				/*
				this.uistackmgr.switch_pstackcpane(
					{idproperty:idproperty, p_stage:"preconfig",
					entry_pt:"fromddel"});
				this.uistackmgr.switch_gstackcpane(idproperty, true, null) */
				this.server_interface.getServerData(server_path+this.userid_name+'/'+db_type+'/'+item,
					this.server_interface.server_ack);
			},
			// review usage of hitch to provide context to event handlers
			// http://dojotoolkit.org/reference-guide/1.9/dojo/_base/lang.html#dojo-base-lang
			generateDBCollection_smenu: function(submenu_reg, submenu_list, onclick_context, onclick_func, options_obj) {
				var options_obj = options_obj || {};
				arrayUtil.forEach(submenu_list, function(item, index) {
					// a new copy of options_obj needs to be created before
					// assigning a different item value for each menu entry
					// however lang.clone does not work as objects in options_obj
					// are initiated by calling constructors
					// http://dojotoolkit.org/documentation/tutorials/1.10/augmenting_objects/
					var dupoptions_obj = declare.safeMixin({}, options_obj);
					dupoptions_obj.item = item;
					var smenuitem = new MenuItem({label: item,
						onClick: lang.hitch(onclick_context, onclick_func,
							dupoptions_obj)
					});
    				submenu_reg.addChild(smenuitem);
				});  // context should be function
				// use itemclick on entire menu widget instead of onclicks on
				// individual menuitems
				// ref http://dojotoolkit.org/documentation/tutorials/1.10/menus/
				//submenu_reg.set("onItemClick", lang.hitch(onclick_context, onclick_func, options_obj));
				if (typeof options_obj.db_type !== 'undefined') {
					var dbmenureg_list = this.get_dbmenureg_list(options_obj.db_type);
					// note options_obj does not include item value
					dbmenureg_list.push({reg:submenu_reg,
						context:onclick_context, func:onclick_func,
						options_obj:options_obj});
				}
			},
			regenDelDBCollection_smenu: function(delindex, db_type) {
				var dbmenureg_list = this.get_dbmenureg_list(db_type);
				arrayUtil.forEach(dbmenureg_list, function(dbmenudata) {
					var dbmenureg = dbmenudata.reg;
					dbmenureg.removeChild(delindex);
				});
			},
			regenAddDBCollection_smenu: function(insertIndex, object, db_type) {
				var dbmenureg_list = this.get_dbmenureg_list(db_type);
				var item_name = object.name;
				arrayUtil.forEach(dbmenureg_list, function(dbmenudata) {
					var dbmenureg = dbmenudata.reg;
					var options_obj = dbmenudata.options_obj;
					// use safemixin to prevent copying of objects to reinitialize
					// with constructors
					var dupoptions_obj = declare.safeMixin({}, options_obj);
					dupoptions_obj.item = item_name;
					var smenuitem = new MenuItem({label:item_name,
						onClick:lang.hitch(dbmenudata.context, dbmenudata.func,
							dupoptions_obj)});
    				dbmenureg.addChild(smenuitem, insertIndex);
				});
			},
			get_dbmenureg_list: function(db_type) {
				var dbmenureg_list = null;
				if (db_type == 'rrdb')
					dbmenureg_list = this.rrdbmenureg_list;
				else if (db_type == 'tourndb')
					dbmenureg_list = this.tdbmenureg_list;
				else if (db_type == 'fielddb')
					dbmenureg_list = this.fielddbmenureg_list;
				else if (db_type == 'newscheddb')
					dbmenureg_list = this.nsdbmenureg_list;
				else if (db_type == 'prefdb')
					dbmenureg_list = this.prefdbmenureg_list;
				else if (db_type == 'teamdb')
					dbmenureg_list = this.teamdbmenureg_list;
				else if (db_type == 'conflictdb')
					dbmenureg_list = this.conflictdbmenureg_list;
				else {
					dbmenureg_list = [];
					console.log("Error get_dbmenureg_list: Invalid db_type");
				}
				return dbmenureg_list;
			},
			// Switch to league/rourndrobin config
			radio1_callback: function(args_obj, event) {
				if (event) {
					this.clear_create_dropdown(args_obj, "L")
				}
			},
			// switch to tournament config
			radio2_callback: function(args_obj, event) {
				if (event) {
					this.clear_create_dropdown(args_obj, "T")
				}
			},
			// called from radio button, sched type switch
			// clear out old menu structure and create new one based on
			// switched sched type
			clear_create_dropdown: function(args_obj, sched_type) {
				ddownmenu_widget = args_obj.ddownmenu_widget;
				info_obj_list = args_obj.info_obj_list;
				ddownmenu_widget.destroyDescendants();
				this.uistackmgr.reset_activecpane();
				this.create_dropdown(sched_type, info_obj_list,
					ddownmenu_widget);
			},
			// Create main dropdown menu list
			create_dropdown: function(sched_type, info_obj_list, ddownmenu_widget) {
				var sched_info_obj_list = arrayUtil.filter(
					info_obj_list, function(item) {
					return item.sched_type == sched_type ||
						item.sched_type == 'B';
				})
				arrayUtil.forEach(sched_info_obj_list, function(item) {
					var id = item.id;
					var info_obj = item.info_obj;
					// attach designated sched type to info_obj
					// (only useful for info_obj's that can be used for both,
					// as idproperty for others uniquely identifies sched type,
					// but for now assign sched_type to all info_obj's)
					info_obj.actualsched_type = sched_type;
					this.create_menu(id, item.info_obj, true, ddownmenu_widget);
				}, this)
			}
		})
	}
);
