// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dojox/widget/Wizard", "dojox/widget/WizardPane",
	"dijit/DropDownMenu", "dijit/form/DropDownButton", "dijit/form/Button",
	"dijit/form/DropDownButton", "dijit/layout/ContentPane",
	"LeagueScheduler/baseinfoSingleton", "LeagueScheduler/widgetgen",
	"LeagueScheduler/wizuistackmanager", "LeagueScheduler/divinfo",
	"LeagueScheduler/tourndivinfo", "LeagueScheduler/fieldinfo",
	"LeagueScheduler/preferenceinfo", "LeagueScheduler/newschedulerbase",
	"LeagueScheduler/teaminfo", "LeagueScheduler/idmgrSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry, Wizard, WizardPane,
		DropDownMenu, DropDownButton, Button, DropDownButton, ContentPane,
		baseinfoSingleton, WidgetGen, WizUIStackManager, divinfo, tourndivinfo,
		fieldinfo, preferenceinfo, newschedulerbase, teaminfo, idmgrSingleton,
		put) {
		var constant = {
			divradio1_id:'wizdivradio1_id', divradio2_id:'wizdivradio2_id',
			divselect_id:'wizdivselect_id', init_db_type:"rrdb",
		};
		return declare(null, {
			storeutil_obj:null, server_interface:null, widgetgen_obj:null,
			schedutil_obj:null, wizardid_list:null, wizuistackmgr:null,
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
				var wizuistackmgr = new WizUIStackManager();
				this.wizuistackmgr = wizuistackmgr;
				this.storeutil_obj.wizuistackmgr = wizuistackmgr;
				var tabcontainer = registry.byId("tabcontainer_id");
				var container_cpane = new ContentPane({title:"Scheduling Wizard", class:'allauto', id:"wiztop_cpane_id"});
				container_cpane.on("show", lang.hitch(this, function(evt) {
					console.log("Wizard onshow");
					/*
					if (this.uistackmgr && this.uistackmgr.current_grid) {
						this.uistackmgr.current_grid.resize();
					} */
					if (this.wizuistackmgr && this.wizuistackmgr.current_grid) {
						this.wizuistackmgr.current_grid.resize();
					}
					container_cpane.domNode.scrollTop = 0;
				}))
				tabcontainer.addChild(container_cpane);
				//tabcontainer.selectChild(container_cpane);
				//container_cpane.resize();
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
				var content_str = "Welcome to the YukonTR League Scheduler.  The main purpose of this scheduler is to not only generate schedules for large leagues, but to also accomodate constraints and/or preferences with scheduling.<br><br>To take maximum advantage use of the tool, make sure you understand what you are trying to accomplish through your scheduling efforts.  In addition, division and field data about your League will need to be entered:<br><br>This wizard will take you through 3 steps of configuration before you generate your schedule:<ul><li><strong>Division Information</strong> - Number of Teams, how many games they play in a season, length of season, length of games, and how often they play</li><br><li><strong>Field Information</strong> - Field labels, which divisions play on the field, availability of fields (date and times).  There is a separate calendar UI to enter exceptions and special restrictions on availability</li><br><li><strong>Preference Information</strong>(Optional) If any team has time and/or location constraints, they can be specified.  As an administrator, you will need to assign priorities to the preferences as the scheduler will only make a best effort to meet the preferences.</li><br><li><strong>Schedule Generation</strong>  In the final step, choose the configured division/field/preference lists that are needed to generate the Schedule.  Generation is done with a single button press; Results are generated under additional tabs that are created.</li></ul><br><b>Begin</b> by pressing 'Next Configuration' button in the bottom-right of the Pane"
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
				// get/create widgetgen obj
				if (!this.widgetgen_obj) {
					this.widgetgen_obj = new WidgetGen({
						storeutil_obj:this.storeutil_obj,
						server_interface:this.server_interface
					});
				}
				// radio button to choose between rrd and tourndb
				this.widgetgen_obj.create_dbtype_radiobtn(topdiv_node,
					constant.divradio1_id, constant.divradio2_id,
					constant.init_db_type,
					this, this.radio1_callback, this.radio2_callback,
					'div_id_type_select');
				var divinfo_obj = new divinfo({
					server_interface:this.server_interface,
					uistackmgr_type:wizuistackmgr, storeutil_obj:this.storeutil_obj,
					schedutil_obj:this.schedutil_obj, op_type:"wizard"});
				var menubar_node = put(topdiv_node, "div");
				this.storeutil_obj.create_menubar('div_id', divinfo_obj, true, menubar_node);
				var pcontainerdiv_node = put(topdiv_node, "div")
				var gcontainerdiv_node = put(topdiv_node, "div")
				divinfo_obj.create_wizardcontrol(pcontainerdiv_node,
					gcontainerdiv_node);
				//this.wizuistackmgr.initstacks('div_id');
				var divinfo_wpane = new WizardPane({
					content:topdiv_node,
					//class:'allauto'
					//style:"width:500px; height:400px; border:1px solid red"
					onShow: function() {
						if (divinfo_obj.editgrid) {
							divinfo_obj.editgrid.schedInfoGrid.resize();
						}
					}
				})
				wizard_reg.addChild(divinfo_wpane);
				//--------------------------------------//
				// Field Config Pane
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Field-availability -relation information.  Specify name of the field, dates/times available, and the divisions that will be using the fields.  Note for detailed date/time configuration or to specify exceptions, click 'Detailed Config' to bring up calendar UI to specify dates/times.</i><br><br>";
				var fieldinfo_obj = new fieldinfo({
					server_interface:this.server_interface,
					uistackmgr_type:wizuistackmgr, storeutil_obj:this.storeutil_obj,
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
						if (fieldinfo_obj.editgrid) {
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
				this.widgetgen_obj.create_dbtype_radiobtn(topdiv_node,
					idstr_obj.radiobtn1_id, idstr_obj.radiobtn2_id,
					constant.init_db_type,
					this, this.radio1_callback, this.radio2_callback,
					"team_id");
				/*
				var ddmenu_widget = new DropDownMenu()
				var ddbtn_widget = new DropDownButton({
					class:"primary",
					label:"Select League",
					//style:"margin-left:25px",
					dropDown:ddmenu_widget,
					style:"margin-right:12px"
				}, ddbtn_node); */
				var teaminfo_obj = new teaminfo({
					server_interface:this.server_interface,
					uistackmgr_type:wizuistackmgr, storeutil_obj:this.storeutil_obj,
					schedutil_obj:this.schedutil_obj, op_type:"wizard"});
				/*
				this.storeutil_obj.create_dropdown_menu(ddmenu_widget,
					constant.init_db_type, this.widgetgen_obj, teaminfo_obj); */
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
						if (teaminfo_obj.editgrid) {
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
					uistackmgr_type:wizuistackmgr, storeutil_obj:this.storeutil_obj,
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
						if (prefinfo_obj.editgrid) {
							prefinfo_obj.editgrid.schedInfoGrid.resize();
						}
					}
				})
				wizard_reg.addChild(prefinfo_wpane);
				//----------------------------------------------//
				// Schedule Generation
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Select Parameters - Divsion List (required), Field List (required), and Preference List (optional) and name the Schedule.  After the parameters are selected using the dropdown element, press the 'Generate' button.  Additional tabs will be created after the schedule is generated, each with a different view into the schedule - by division, by team, by field.  Fairness metrics are also displayed in a separate tab.</i><br><br>";
				var newschedinfo_obj = new newschedulerbase({
					server_interface:this.server_interface,
					uistackmgr_type:wizuistackmgr, storeutil_obj:this.storeutil_obj,
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
				//-----------------//
				//Add parameter stack container panes
				/*
				this.uistackmgr.create_paramcpane_stack(container_cpane);
				// we might not need the error node beow
				put(container_cpane.domNode, "div.style_none#divisionInfoInputGridErrorNode")
				this.uistackmgr.create_grid_stack(container_cpane);
				*/
			},
			radio1_callback: function(select_id, event) {

			},
			radio2_callback: function(select_id, event) {

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
		})
	}
);
