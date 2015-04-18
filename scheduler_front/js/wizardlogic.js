// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dojox/widget/Wizard", "dojox/widget/WizardPane",
	"dijit/DropDownMenu", "dijit/form/Button", "dijit/layout/StackContainer",
	"dijit/layout/ContentPane", "scheduler_front/baseinfoSingleton",
	"scheduler_front/wizuistackmanager", "scheduler_front/divinfo",
	"scheduler_front/tourndivinfo", "scheduler_front/fieldinfo",
	"scheduler_front/preferenceinfo", "scheduler_front/newschedulerbase",
	"scheduler_front/teaminfo", "scheduler_front/conflictinfo",
	"scheduler_front/idmgrSingleton", "scheduler_front/errormanager",
	"put-selector/put", "dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry, Wizard, WizardPane,
		DropDownMenu, Button, StackContainer, ContentPane,
		baseinfoSingleton, WizUIStackManager, divinfo, tourndivinfo,
		fieldinfo, preferenceinfo, newschedulerbase, teaminfo, conflictinfo,
		idmgrSingleton, ErrorManager,
		put) {
		// id's for widgets that only exist within wizard context so manage them here instead
		// of idmgrsingleton
		var constant = {
			divradio1_id:'wizdivradio1_id', divradio2_id:'wizdivradio2_id',
			divselect_id:'wizdivselect_id', init_sched_type:"L",
			top_cpane_id:'wiztop_cpane_id', divstcontainer_id:"wizdivstcontainer_id"
		};
		return declare(null, {
			storeutil_obj:null, server_interface:null, widgetgen_obj:null,
			schedutil_obj:null, wizardid_list:null, wizuistackmgr:null,
			wizuistackmgr_list:null,
			userid_name:"",  sched_type:constant.init_sched_type,
			divstackcontainer:null,
			wizard_reg:null, errormgr_obj:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.wizardid_list = idmgrSingleton.get_idmgr_list(
					{op_type:'wizard', sched_type:constant.init_sched_type});
				this.wizuistackmgr = arrayUtil.filter(this.wizuistackmgr_list,
					function(item) {
						return item.sched_type == constant.init_sched_type;
					}
				)[0].wizuistackmgr;
				this.errormgr_obj = new ErrorManager();
			},
			getschedTypeWpaneMap: function(schedTypeWpaneMapList, sched_type) {
				// get wpanemap corresponding to sched_type
				return arrayUtil.filter(schedTypeWpaneMapList,
					function(item) {
						return item.sched_type == sched_type;
					}
				)[0]
			},
			getselectedWpaneMap: function(schedTypeWpaneMapList) {
				// get wpanemap corresponding to sched_type
				var selectedMap = arrayUtil.filter(schedTypeWpaneMapList,
					function(item) {
						return item.selected ==true;
					}
				)
				if (selectedMap.length > 0)
					return selectedMap[0]
				else
					return null;
			},
			generateWpaneGroup: function(wpaneMap, sched_type) {
				// generate group of wpane's corresponding to current
				// sched type
				var wpaneGenFuncList = wpaneMap.wpaneGenFuncList;
				var wpaneList = wpaneMap.wpaneList;
				if (wpaneList.length > 0)
					this.errormgr_obj.emit_error(
						ErrorManager.constant.software_error_mask,
						"Wizard Pane List shnould be empty");
				arrayUtil.forEach(wpaneGenFuncList, function(wpaneFunc) {
					// generate wizard pane and attach to overall wizard
					// controller
					wpane = wpaneFunc(sched_type);
					this.wizard_reg.addChild(wpane);
					// save generated wpane
					wpaneList.push(wpane);
				}, this)
				wpaneMap.generated = true;
				wpaneMap.selected = true;
				this.wizard_reg.startup();
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
				this.wizard_reg = new Wizard({
					title:"Scheduling Wizard/Start Here",
					// style below should have size that will be greater or equal
					// than child WizardPanes
					class:'allauto',
					//style:"width:600px; height:500px",
					nextButtonLabel:"Next Configuration"
				});
				container_cpane.addChild(this.wizard_reg);

				//--------------------//
				// Create informational starting pane
				var content_str = "<p style='font-size:larger'>User/Organization ID: <strong>"+this.userid_name+"</strong></p>";
				content_str += "Welcome to the YukonTR League Scheduler.  The main purpose of this scheduler is to not only generate schedules for large leagues, but to also accomodate constraints and/or preferences with scheduling.<br><br>To take maximum advantage use of the tool, make sure you understand what you are trying to accomplish through your scheduling efforts.  In addition, division and field data about your League will need to be entered:<br><br>This wizard will take you through six steps of configuration before you generate your schedule:<ul><li><strong>Division Information</strong> - Number of Teams, how many games they play in a season, length of season, length of games, and how often they play</li><br><li><strong>Field Information</strong> - Field labels, which divisions play on the field, availability of fields (date and times).  There is an optional separate calendar UI to enter exceptions and special restrictions on availability - for example temporary field closures or one-time availability of fields</li><br><li><strong>Team Information</strong> - (Optional) For each team, assign team name and also any fields that are designated as home field(s) for that team (both assignments are optional)</li><br><li><strong>Preference Information</strong> - (Optional) If any team has time preferences on when games should be scheduled, the scheduler will attempt to meet those requests.  Configured priorities will guide the scheduler in how aggressively it will disrupt the fairness of the schedule to meet the preference.</li><br><li><strong>Team Conflict Information</strong> - (Optional) If any two teams are recognized to have time conflicts throughout the season (for example coaches coaching multiple teams), the conflicting teams can be specified so that the scheduler attempts to avoid scheduling matches at the same time.  As an administrator, you will need to assign priorities to each confict specification.</li><br><li><strong>Schedule Generation</strong> - In the final step, choose the configured division/field/preference lists that are needed to generate the Schedule.  Generation is done with a single button press; Results are generated under additional tabs that are created.  Both web-based and hardcopy (.xls) output of the schedules are supported.</li></ul><br><b>Begin</b> by pressing 'Next Configuration' button in the bottom-right of the Pane"
				var intro_wpane = new WizardPane({
					content:content_str,
					//class:'allonehundred'
					//style:"width:100px; height:100px"
				})
				this.wizard_reg.addChild(intro_wpane);
				//---------------------//
				//---- Page for Schedule Type Selection -----//
				var topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>Define the Schedule Type - League Round Robin or Tournament Schedule</i><br><br>";
				// Generate rest of wpanes for current sched type
				// define sequence of wizard panes for each schedule type
				// First define wpane generation functions for each sched type
				var schedTypeWpaneMapList = [
					{sched_type:"L", wpaneGenFuncList:[
						lang.hitch(this, this.createDivWpane),
						lang.hitch(this, this.createFieldWpane),
						lang.hitch(this, this.createTeamWpane),
						lang.hitch(this, this.createPrefWpane),
						lang.hitch(this, this.createConflictWpane),
						lang.hitch(this, this.createNewSchedWpane)],
						generated:false,
						wpaneList:[], selected:false},
					{sched_type:"T", wpaneGenFuncList:[
						lang.hitch(this, this.createTournDivWpane),
						lang.hitch(this, this.createFieldWpane),
						lang.hitch(this, this.createNewSchedWpane)],
						generated:false,
						wpaneList:[], selected:false}
				];
				// create schedule type selection radio button widgets
				// Note we are passing in the wpane func mapping list so that
				// the callback can generate or reassign the wpanes based on the
				// selected sched type
				this.widgetgen_obj.create_schedtype_radiobtn(topdiv_node,
					constant.divradio1_id, constant.divradio2_id, "L",
					this, this.rr_sched_callback, this.tourn_sched_callback,
					schedTypeWpaneMapList);
				var select_schedtype_wpane = new WizardPane({
					content:topdiv_node,
				})
				this.wizard_reg.addChild(select_schedtype_wpane);
				// -------------------------------
				// get mapping for current sched_type
				var initschedTypeWpaneMap = this.getschedTypeWpaneMap(
					schedTypeWpaneMapList, this.sched_type);
				var generated = initschedTypeWpaneMap.generated;
				// call wpane generating functions
				if (!generated) {
					this.generateWpaneGroup(initschedTypeWpaneMap, this.sched_type);
				}
				this.wizard_reg.resize();
				container_cpane.resize();
				return container_cpane;
			},
			//-----------------------//
			// --- Generate DIVISION INFO-----//
			createDivWpane: function(sched_type) {
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Division-relation information.  A division is defined as the group of teams that will interplay with each other.  Define name, # of teams, # of games in season, length of each game, and minimum/maximum days that should lapse between games for each team.</i><br><br>";
				this.generate_divwpane(sched_type, topdiv_node);
				var divinfo_wpane = new WizardPane({
					content:topdiv_node,
				})
				return divinfo_wpane
			},
			// --- Generate Tourn DIVISION INFO-----//
			createTournDivWpane: function(sched_type) {
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Tournament Division-relation information.  A division is defined as the group of teams that will interplay with each other in the tournament bracket.  Define name, # of teams in division.</i><br><br>";
				this.generate_divwpane(sched_type, topdiv_node);
				var tourndivinfo_wpane = new WizardPane({
					content:topdiv_node,
				})
				return tourndivinfo_wpane
			},
			// Field Config Pane
			createFieldWpane: function(sched_type) {
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Field-availability -relation information.  Specify name of the field, dates/times available, and the divisions that will be using the fields.  Note for detailed date/time configuration or to specify exceptions, click 'Detailed Config' to bring up calendar UI to specify dates/times.</i><br><br>";
				var fieldinfo_obj = new fieldinfo({
					server_interface:this.server_interface,
					uistackmgr_type:this.wizuistackmgr,
					storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
					schedutil_obj:this.schedutil_obj, op_type:"wizard",
					sched_type:sched_type});
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
				return fieldinfo_wpane
			},
			createTeamWpane: function(sched_type) {
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
					schedutil_obj:this.schedutil_obj, op_type:"wizard",
					sched_type:sched_type});
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
				return teaminfo_wpane;
			},
			createPrefWpane: function(sched_type) {
				//-------------------------------------------//
				// Preference Config Pane
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Scheduling Preferences that concern teams.  The league administrator has the disgression to grant prioritized scheduling to teams. Use the table to grant time scheduling priorities.  Note that satisfying scheduling preferences is a best-effort feature and is not guaranteed.  Raising the priority level increases probability that preference will be satisfied.</i><br><br>";
				var prefinfo_obj = new preferenceinfo({
					server_interface:this.server_interface,
					uistackmgr_type:this.wizuistackmgr,
					storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
					schedutil_obj:this.schedutil_obj, op_type:"wizard",
					sched_type:sched_type});
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
				return prefinfo_wpane;
			},
			createConflictWpane: function(sched_type) {
				//----------------------------------------------//
				// Conflicts Config Pane
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Specify any requests for avoiding time conflicts between teams.  Example use cases may include coaches coaching multiple teams, a coach that coaches one team and plays on another, or trying to ease the burden for certain parents that have many children playing the league.  The league administrator can try to accomodate these requests by specifying these conflicts.  However, priorities must be assigned to each of the specified conflicts.  As with the Preference feature in the previous pane, avoiding the time conflicts is a best-effort feature and results are not guaranteed.  Raising the priority level increases probability that the time conflict will be avoid, but the administrator also needs to be cognizant that fairness for other teams could be compromised depending on the prioritiy level assigned.</i><br><br>";
				var conflictinfo_obj = new conflictinfo({
					server_interface:this.server_interface,
					uistackmgr_type:this.wizuistackmgr,
					storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
					schedutil_obj:this.schedutil_obj, op_type:"wizard",
					sched_type:sched_type});
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
				return conflictinfo_wpane;
			},
			createNewSchedWpane: function(sched_type) {
				//----------------------------------------------//
				// Schedule Generation
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Select Parameters - Divsion List (required), Field List (required), and Preference List (optional) and name the Schedule.  After the parameters are selected using the dropdown element, press the 'Generate' button.  Additional tabs will be created after the schedule is generated, each with a different view into the schedule - by division, by team, by field.  Fairness metrics are also displayed in a separate tab.</i><br><br>";
				var newschedinfo_obj = new newschedulerbase({
					server_interface:this.server_interface,
					uistackmgr_type:this.wizuistackmgr,
					storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
					schedutil_obj:this.schedutil_obj, op_type:"wizard",
					sched_type:sched_type});
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
				return newschedinfo_wpane;
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
			generateswitchWPaneGroup: function(wpaneMapList, sched_type) {
				this.sched_type = sched_type;
				// switch references to wizuistack object to point to
				// the one with the new sched_type property
				this.storeutil_obj.switchWizUIStackMgr(sched_type);
				this.switchWizUIStackMgr(sched_type);
				// get new wizard id list
				this.wizardid_list = idmgrSingleton.get_idmgr_list(
					{op_type:'wizard', sched_type:sched_type});
				var wpaneMap = this.getschedTypeWpaneMap(wpaneMapList,
					sched_type);
				if (!wpaneMap.selected) {
					var currentMap = this.getselectedWpaneMap(wpaneMapList);
					if (currentMap !== null) {
						// first remove the current active wpanes
						// from the wizard controller; note the wpanes for the
						// de-selected sched_type are not destroyed and preserved
						// so that it can be attached again to the controller
						// when sched_type is selected.
						arrayUtil.forEach(currentMap.wpaneList,
							function(wpane) {
								this.wizard_reg.removeChild(wpane);
							}, this
						)
						currentMap.selected = false;
					} else {
						this.errormgr_obj.emit_error(
							ErrorManager.constant.software_error_mask,
							"Current Selected Wizard Pane cannot be found");
					}
					if (wpaneMap.generated) {
						// add the new selected wpanes to the
						// wizard controller
						arrayUtil.forEach(wpaneMap.wpaneList,
							function(wpane) {
								this.wizard_reg.addChild(wpane)
							}, this
						)
						wpaneMap.selected = true;
					} else {
						// need to generate the wpanes for the selecte sched
						// type
						this.generateWpaneGroup(wpaneMap, sched_type);
						currentMap.selected = false;
					}
				} else if (!wpanemap.generated) {
					// if target wpane is already selected, then we don't
					// need to do anything, but make sure there is no
					// erroneous state with generated flag
					this.errormgr_obj.emit_error(
						ErrorManager.constant.software_error_mask,
						"Wizard Pane Generation and Selection inconsistency")
				}
			},
			rr_sched_callback: function(wpaneMapList, event) {
				if (event) {
					this.generateswitchWPaneGroup(wpaneMapList, "L");
				}
			},
			tourn_sched_callback: function(wpaneMapList, event) {
				if (event) {
					this.generateswitchWPaneGroup(wpaneMapList, "T");
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
			generate_divwpane: function(sched_type, topdiv_node) {
				var divinfo_obj = null;
				var idproperty = null;
				// create default divinfo or tourninfo obj
				if (sched_type == 'L') {
					divinfo_obj = new divinfo({
						server_interface:this.server_interface,
						uistackmgr_type:this.wizuistackmgr,
						storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
						schedutil_obj:this.schedutil_obj, op_type:"wizard",
						sched_type:sched_type});
					idproperty ="div_id";
				} else {
					divinfo_obj = new tourndivinfo({
						server_interface:this.server_interface,
						uistackmgr_type:this.wizuistackmgr,
						storeutil_obj:this.storeutil_obj, userid_name:this.userid_name,
						schedutil_obj:this.schedutil_obj, op_type:"wizard",
						sched_type:sched_type});
					idproperty = "tourndiv_id";
				}
				// create default menubar and attached ddown menu widgets
				var menubar_node = put(topdiv_node, "div");
				//var edit_ddownmenu_widget = new DropDownMenu();
				//var del_ddownmenu_widget = new DropDownMenu();
				this.storeutil_obj.create_menubar(idproperty, divinfo_obj, true,
					menubar_node);
				var pcontainerdiv_node = put(topdiv_node, "div")
				var gcontainerdiv_node = put(topdiv_node, "div")
				divinfo_obj.create_wizardcontrol(pcontainerdiv_node,
					gcontainerdiv_node);
				return divinfo_obj;
			},
			switchWizUIStackMgr: function(sched_type) {
				// switch wizuistackmgr when sched_type changes
				this.wizuistackmgr = arrayUtil.filter(this.wizuistackmgr_list,
					function(item) {
						return item.sched_type == sched_type;
					}
				)[0].wizuistackmgr;
			}
		})
	}
);
