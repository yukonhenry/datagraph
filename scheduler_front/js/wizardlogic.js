// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dojox/widget/Wizard", "dojox/widget/WizardPane",
	"dijit/DropDownMenu", "dijit/form/Button", "dijit/layout/StackContainer",
	"dijit/layout/ContentPane", "scheduler_front/baseinfoSingleton",
	"scheduler_front/wizuistackmanager", "scheduler_front/divinfo",
	"scheduler_front/tourndivinfo", "scheduler_front/fieldinfo",
	"scheduler_front/preferenceinfo", "scheduler_front/newschedulerbase",
	"scheduler_front/teaminfo", "scheduler_front/conflictinfo",
	"scheduler_front/idmgrSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry, Wizard, WizardPane,
		DropDownMenu, Button, StackContainer, ContentPane,
		baseinfoSingleton, WizUIStackManager, divinfo, tourndivinfo,
		fieldinfo, preferenceinfo, newschedulerbase, teaminfo, conflictinfo,
		idmgrSingleton,
		put) {
		// id's for widgets that only exist within wizard context so manage them here instead
		// of idmgrsingleton
		var constant = {
			divradio1_id:'wizdivradio1_id', divradio2_id:'wizdivradio2_id',
			divselect_id:'wizdivselect_id', init_db_type:"rrdb",
			top_cpane_id:'wiztop_cpane_id', divstcontainer_id:"wizdivstcontainer_id"
		};
		return declare(null, {
			storeutil_obj:null, server_interface:null, widgetgen_obj:null,
			schedutil_obj:null, wizardid_list:null, wizuistackmgr:null,
			userid_name:"", db_type:constant.init_db_type,
			divstackcontainer:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.wizardid_list = idmgrSingleton.get_idmgr_list('op_type', 'wizard');
			},
			create: function() {
				// tabconatiner examples:
				// http://dojotoolkit.org/reference-guide/1.9/dijit/layout/TabContainer-examples.html
				//wizard documentation:
				// http://archive.dojotoolkit.org/nightly/dojotoolkit/dojox/widget/tests/test_Wizard.html
				//https://github.com/dojo/dojox/blob/master/widget/tests/test_Wizard.html
				var tabcontainer = registry.byId("tabcontainer_id");
				var container_cpane = registry.byId(constant.top_cpane_id);
				if (container_cpane) {
					container_cpane.resize();
					return
				}
				container_cpane = new ContentPane({title:"Step-by-Step UI", class:'allauto', id:constant.top_cpane_id, tooltip:"Start here to cover all of the Configuration steps"});
				container_cpane.on("show", lang.hitch(this, function(evt) {
					console.log("Wizard onshow");
					if (this.wizuistackmgr && this.wizuistackmgr.current_grid) {
						this.wizuistackmgr.current_grid.resize();
					}
					container_cpane.domNode.scrollTop = 0;
				}))
				tabcontainer.addChild(container_cpane);
				// ref http://archive.dojotoolkit.org/nightly/checkout/dijit/tests/layout/test_TabContainer_noLayout.html
				// for doLayout:false effects
				var wizard_reg = new Wizard({
					title:"Scheduling Wizard/Start Here",
					// style below should have size that will be greater or equal
					// than child WizardPanes
					class:'allauto',
					//style:"width:600px; height:500px",
					nextButtonLabel:"Next Configuration"
				});
				container_cpane.addChild(wizard_reg);

				//--------------------//
				// Create informational starting pane
				var content_str = "<p style='font-size:larger'>User/Organization ID: <strong>"+this.userid_name+"</strong></p>";
				content_str += "Welcome to the YukonTR League Scheduler.  The main purpose of this scheduler is to not only generate schedules for large leagues, but to also accomodate constraints and/or preferences with scheduling.<br><br>To take maximum advantage use of the tool, make sure you understand what you are trying to accomplish through your scheduling efforts.  In addition, division and field data about your League will need to be entered:<br><br>This wizard will take you through six steps of configuration before you generate your schedule:<ul><li><strong>Division Information</strong> - Number of Teams, how many games they play in a season, length of season, length of games, and how often they play</li><br><li><strong>Field Information</strong> - Field labels, which divisions play on the field, availability of fields (date and times).  There is an optional separate calendar UI to enter exceptions and special restrictions on availability - for example temporary field closures or one-time availability of fields</li><br><li><strong>Team Information</strong> - (Optional) For each team, assign team name and also any fields that are designated as home field(s) for that team (both assignments are optional)</li><br><li><strong>Preference Information</strong> - (Optional) If any team has time preferences on when games should be scheduled, the scheduler will attempt to meet those requests.  Configured priorities will guide the scheduler in how aggressively it will disrupt the fairness of the schedule to meet the preference.</li><br><li><strong>Team Conflict Information</strong> - (Optional) If any two teams are recognized to have time conflicts throughout the season (for example coaches coaching multiple teams), the conflicting teams can be specified so that the scheduler attempts to avoid scheduling matches at the same time.  As an administrator, you will need to assign priorities to each confict specification.</li><br><li><strong>Schedule Generation</strong> - In the final step, choose the configured division/field/preference lists that are needed to generate the Schedule.  Generation is done with a single button press; Results are generated under additional tabs that are created.  Both web-based and hardcopy (.xls) output of the schedules are supported.</li></ul><br><b>Begin</b> by pressing 'Next Configuration' button in the bottom-right of the Pane"
				var intro_wpane = new WizardPane({
					content:content_str,
					//class:'allonehundred'
					//style:"width:100px; height:100px"
				})
				wizard_reg.addChild(intro_wpane);
				//---------------------//
				// --- DIVISION INFO-----//
				var topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Division-relation information.  A division is defined as the group of teams that will interplay with each other.  Define name, # of teams, # of games in season, length of each game, and minimum/maximum days that should lapse between games for each team.</i><br><br>";
				// radio button to choose between rrd and tourndb
				// select value is a dummy value as popup subemnu is used instead of select]
				// divcpanemap_array is a list of mapping objects, with each object
				// providing maps for db_type, cpane_id, and info_obj
				// current used only to resize pane-resident grids if switched
				// into pane
				var divcpanemap_array = new Array();
				this.widgetgen_obj.create_dbtype_radiobtn(topdiv_node,
					constant.divradio1_id, constant.divradio2_id, this.db_type,
					this, this.radio1_callback, this.radio2_callback,
					divcpanemap_array);
				var stack_node = put(topdiv_node, "div");
				// create stackcontainer to manage separate cpane -
				// one for RR, other for Tourn
				this.divstackcontainer = new StackContainer({
					doLayout:false,
					style:"float:left; width:80%",
					id:constant.divstcontainer_id,
				}, stack_node);
				// Haven't exactly figured out why, but generate both RR and Tourn
				// div config content pane's during first create.  Otherwise,
				// when creating the missing content pane during run time (when
				// radio button is selected) causes html button dom (outlines)
				// to be visible before the dojo widgets are created.
				arrayUtil.forEach(["rrdb", "tourndb"], function(item) {
					var cpane_id = this.generate_divcpane_id(item);
					var info_obj = this.generate_divcpane(item, cpane_id);
					divcpanemap_array.push({db_type:item,
						cpane_id:cpane_id, info_obj:info_obj})
				}, this)
				var divinfo_wpane = new WizardPane({
					content:topdiv_node,
				})
				wizard_reg.addChild(divinfo_wpane);
				//--------------------------------------//
				// Field Config Pane
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Field-availability -relation information.  Specify name of the field, dates/times available, and the divisions that will be using the fields.  Note for detailed date/time configuration or to specify exceptions, click 'Detailed Config' to bring up calendar UI to specify dates/times.</i><br><br>";
				var fieldinfo_obj = new fieldinfo({
					server_interface:this.server_interface,
					uistackmgr_type:this.wizuistackmgr,
					storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
					schedutil_obj:this.schedutil_obj, op_type:"wizard"});
				menubar_node = put(topdiv_node, "div");
				this.storeutil_obj.create_menubar('field_id', fieldinfo_obj, true, menubar_node);
				pcontainerdiv_node = put(topdiv_node, "div")
				gcontainerdiv_node = put(topdiv_node, "div")
				fieldinfo_obj.create_wizardcontrol(pcontainerdiv_node,
					gcontainerdiv_node);
				var fieldinfo_wpane = new WizardPane({
					content:topdiv_node,
					//class:'allauto'
					//style:"width:500px; height:400px; border:1px solid red"
					onShow: function() {
						if ("editgrid" in fieldinfo_obj &&
							fieldinfo_obj.editgrid) {
							fieldinfo_obj.editgrid.schedInfoGrid.resize();
						}
					}
				})
				wizard_reg.addChild(fieldinfo_wpane);
				//-------------------------------------------//
				// ------------- TEAM INFO Pane  ----------------
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Assign team-related information.  Specify name of the team (for identification purposes) and any preferred fields for that team. As a default, schedule is created assuming there is field-use fairness across all fields, regardless of whether a team is designated as home/away.  If teams are associated with certain fields for home games, assign them in the grid below.</i><br><br>";
				// radio button to choose between rrd and tourndb
				var idstr_obj = this.get_idstr_obj('team_id');
				// put the dropdown button first before the radio button id's
				// putting it after causes some problems with the location of the div's
				// Somehow put selector puts the button node after the pcontainerdiv_node even though the latter is create after the button
				// node is created.  Might be related to the fact that  create_db_type_radiobtn has some <br>s generated after the radio
				// button nodes; instead of putting the button node after that,
				// it decides to put the pcontainerdiv_node first. (the button node
				// shows up after the pcontainerdiv)
				//var ddbtn_node = put(topdiv_node, "button[type=button]");
				var teaminfo_obj = new teaminfo({
					server_interface:this.server_interface,
					uistackmgr_type:this.wizuistackmgr,
					storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
					schedutil_obj:this.schedutil_obj, op_type:"wizard"});
				menubar_node = put(topdiv_node, "div");
				// No menubar for team_id as there is no create/delete operations
				// for teaminfo grids
				this.storeutil_obj.create_menubar('team_id', teaminfo_obj, true, menubar_node);
				pcontainerdiv_node = put(topdiv_node, "div")
				gcontainerdiv_node = put(topdiv_node, "div")
				teaminfo_obj.create_wizardcontrol(pcontainerdiv_node,
					gcontainerdiv_node);
				var teaminfo_wpane = new WizardPane({
					content:topdiv_node,
					//class:'allauto'
					//style:"width:500px; height:400px; border:1px solid red"
					onShow: function() {
						if ("editgrid" in teaminfo_obj && teaminfo_obj.editgrid) {
							teaminfo_obj.editgrid.schedInfoGrid.resize();
						}
					}
				})
				wizard_reg.addChild(teaminfo_wpane);
				//-------------------------------------------//
				// Preference Config Pane
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Scheduling Preferences that concern teams.  The league administrator has the disgression to grant prioritized scheduling to teams. Use the table to grant time scheduling priorities.  Note that satisfying scheduling preferences is a best-effort feature and is not guaranteed.  Raising the priority level increases probability that preference will be satisfied.</i><br><br>";
				var prefinfo_obj = new preferenceinfo({
					server_interface:this.server_interface,
					uistackmgr_type:this.wizuistackmgr,
					storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
					schedutil_obj:this.schedutil_obj, op_type:"wizard"});
				menubar_node = put(topdiv_node, "div");
				this.storeutil_obj.create_menubar('pref_id', prefinfo_obj, true, menubar_node);
				pcontainerdiv_node = put(topdiv_node, "div")
				gcontainerdiv_node = put(topdiv_node, "div")
				prefinfo_obj.create_wizardcontrol(pcontainerdiv_node,
					gcontainerdiv_node);
				var prefinfo_wpane = new WizardPane({
					content:topdiv_node,
					//class:'allauto'
					//style:"width:500px; height:400px; border:1px solid red"
					onShow: function() {
						if ("editgrid" in prefinfo_obj && prefinfo_obj.editgrid) {
							prefinfo_obj.editgrid.schedInfoGrid.resize();
						}
					}
				})
				wizard_reg.addChild(prefinfo_wpane);
				//----------------------------------------------//
				// Conflicts Config Pane
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Specify any requests for avoiding time conflicts between teams.  Example use cases may include coaches coaching multiple teams, a coach that coaches one team and plays on another, or trying to ease the burden for certain parents that have many children playing the league.  The league administrator can try to accomodate these requests by specifying these conflicts.  However, priorities must be assigned to each of the specified conflicts.  As with the Preference feature in the previous pane, avoiding the time conflicts is a best-effort feature and results are not guaranteed.  Raising the priority level increases probability that the time conflict will be avoid, but the administrator also needs to be cognizant that fairness for other teams could be compromised depending on the prioritiy level assigned.</i><br><br>";
				var conflictinfo_obj = new conflictinfo({
					server_interface:this.server_interface,
					uistackmgr_type:this.wizuistackmgr,
					storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
					schedutil_obj:this.schedutil_obj, op_type:"wizard"});
				menubar_node = put(topdiv_node, "div");
				this.storeutil_obj.create_menubar('conflict_id', conflictinfo_obj, true, menubar_node);
				pcontainerdiv_node = put(topdiv_node, "div")
				gcontainerdiv_node = put(topdiv_node, "div")
				conflictinfo_obj.create_wizardcontrol(pcontainerdiv_node,
					gcontainerdiv_node);
				var conflictinfo_wpane = new WizardPane({
					content:topdiv_node,
					//class:'allauto'
					//style:"width:500px; height:400px; border:1px solid red"
					onShow: function() {
						if ("editgrid" in conflictinfo_obj &&
							conflictinfo_obj.editgrid) {
							conflictinfo_obj.editgrid.schedInfoGrid.resize();
						}
					}
				})
				wizard_reg.addChild(conflictinfo_wpane);
				//----------------------------------------------//
				// Schedule Generation
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Select Parameters - Divsion List (required), Field List (required), and Preference List (optional) and name the Schedule.  After the parameters are selected using the dropdown element, press the 'Generate' button.  Additional tabs will be created after the schedule is generated, each with a different view into the schedule - by division, by team, by field.  Fairness metrics are also displayed in a separate tab.</i><br><br>";
				var newschedinfo_obj = new newschedulerbase({
					server_interface:this.server_interface,
					uistackmgr_type:this.wizuistackmgr,
					storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
					schedutil_obj:this.schedutil_obj, op_type:"wizard"});
				menubar_node = put(topdiv_node, "div");
				this.storeutil_obj.create_menubar('newsched_id', newschedinfo_obj, true, menubar_node);
				pcontainerdiv_node = put(topdiv_node, "div")
				gcontainerdiv_node = put(topdiv_node, "div")
				newschedinfo_obj.create_wizardcontrol(pcontainerdiv_node,
					gcontainerdiv_node);
				var newschedinfo_wpane = new WizardPane({
					content:topdiv_node,
					//class:'allauto'
					//style:"width:500px; height:400px; border:1px solid red"
					doneFunction: function() {
						alert("Feedback Appreciated on YukonTR Scheduler - Contact:henry@yukontr.com")
					}
				})
				/////////////////////
				wizard_reg.addChild(newschedinfo_wpane);
				wizard_reg.startup();
				wizard_reg.resize();
				container_cpane.resize();
				return container_cpane;
			},
			delete_menu_elements: function(menu_widget) {
				// delete all elements of menu (menu widget to be reused to
				// create another)
				var elem_array = menu_widget.getChildren()
				if (elem_array.length > 0) {
					// remove existing submenu elements before
					// recreating submenu with switched over db elements
					arrayUtil.forEach(elem_array, function(item) {
						menu_widget.removeChild(item);
					})
				}
			},
			repopulate_ddownmenu: function(db_type, widget_obj) {
				var db_list = this.storeutil_obj.getfromdb_store_value(db_type, 'name');
				var edit_ddownmenu_widget = widget_obj.edit;
				var del_ddownmenu_widget = widget_obj.del;
				var info_obj = widget_obj.info_obj;
				// delete elements from both edit and delete ddown menus
				this.delete_menu_elements(edit_ddownmenu_widget);
				this.delete_menu_elements(del_ddownmenu_widget);
				// repopulate ddownmenus
				// edit ddownmenu
				this.storeutil_obj.generateDBCollection_smenu(edit_ddownmenu_widget, db_list, this.wizuistackmgr,
					this.wizuistackmgr.check_getServerDBInfo,
					{db_type:db_type, info_obj:info_obj,
						storeutil_obj:this.storeutil_obj, op_type:"wizard"})
				this.storeutil_obj.generateDBCollection_smenu(del_ddownmenu_widget, db_list, this.storeutil_obj,
					this.storeutil_obj.delete_dbcollection,
					{db_type:db_type, storeutil_obj:this.storeutil_obj,
						op_type:"wizard"});
			},
			// switch to div or tourndiv info cpane dependent on
			// db_type
			switch_divcpane: function(db_type, divcpanemap_array) {
				var cpane_id = this.generate_divcpane_id(db_type)
				// find the matching object based on db_type
				// match with cpane_id is an extra check for consistency
				var match_obj = arrayUtil.filter(divcpanemap_array,
					function(item) {
						return item.db_type == db_type &&
							item.cpane_id == cpane_id;
					}
				)[0]
				// get actual cpane widget and corresponding info object
				// and for grid resize if there is an onshow signal
				var cpane_widget = registry.byId(cpane_id);
				var info_obj = match_obj.info_obj;

				cpane_widget.set("onShow", function() {
					if ("editgrid" in info_obj && info_obj.editgrid &&
						"schedInfoGrid" in info_obj.editgrid &&
						info_obj.editgrid.schedInfoGrid) {
						info_obj.editgrid.schedInfoGrid.resize();
					}
				})
				this.divstackcontainer.selectChild(cpane_id);
			},
			radio1_callback: function(divcpanemap_array, event) {
				if (event) {
					this.db_type = 'rrdb';
					this.switch_divcpane(this.db_type, divcpanemap_array);
				}
			},
			radio2_callback: function(divcpanemap_array, event) {
				if (event) {
					this.db_type = 'tourndb';
					this.switch_divcpane(this.db_type, divcpanemap_array);
				}
			},
			get_idstr_obj: function(id) {
				var idmgr_obj = this.getuniquematch_obj(this.wizardid_list,
					'id', id);
				return idmgr_obj.idstr_obj;
			},
			getuniquematch_obj: function(list, key, value) {
				var match_list = arrayUtil.filter(list,
					function(item) {
						return item[key] == value;
					});
				return match_list[0];
			},
			generate_dbtype_id: function(idbase, db_type, idtype) {
				// db_type will be either "rrdb" or "tourndb" so strip off "db"
				var db_str = db_type.replace("db","");
				return "wiz" + idbase + db_str + idtype + "_id"
			},
			generate_divcpane_id: function(db_type) {
				return this.generate_dbtype_id("div", db_type, "cpane")
			},
			generate_divcpane: function(db_type, cpane_id) {
				var div_cpane = new ContentPane({
					id:cpane_id
				})
				this.divstackcontainer.addChild(div_cpane);
				var container_node = div_cpane.containerNode;
				var divinfo_obj = null;
				var idproperty = null;
				// create default divinfo or tourninfo obj
				if (db_type == 'rrdb') {
					divinfo_obj = new divinfo({
						server_interface:this.server_interface,
						uistackmgr_type:this.wizuistackmgr,
						storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
						schedutil_obj:this.schedutil_obj, op_type:"wizard"});
					idproperty ="div_id";
				} else {
					divinfo_obj = new tourndivinfo({
						server_interface:this.server_interface,
						uistackmgr_type:this.wizuistackmgr,
						storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
						schedutil_obj:this.schedutil_obj, op_type:"wizard"});
					idproperty = "tourndiv_id";
				}
				// create default menubar and attached ddown menu widgets
				var menubar_node = put(container_node, "div");
				//var edit_ddownmenu_widget = new DropDownMenu();
				//var del_ddownmenu_widget = new DropDownMenu();
				this.storeutil_obj.create_menubar(idproperty, divinfo_obj, true,
					menubar_node);
				var pcontainerdiv_node = put(container_node, "div")
				var gcontainerdiv_node = put(container_node, "div")
				divinfo_obj.create_wizardcontrol(pcontainerdiv_node,
					gcontainerdiv_node);
				return divinfo_obj;
			}
		})
	}
);
