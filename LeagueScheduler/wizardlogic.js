// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dojox/widget/Wizard", "dojox/widget/WizardPane",
	"dijit/DropDownMenu", "dijit/form/DropDownButton", "dijit/form/Button",
	"dijit/layout/ContentPane",
	"LeagueScheduler/baseinfoSingleton", "LeagueScheduler/widgetgen",
	"LeagueScheduler/wizuistackmanager",
	"put-selector/put", "dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry, Wizard, WizardPane,
		DropDownMenu, DropDownButton, Button, ContentPane,
		baseinfoSingleton, WidgetGen, WizUIStackManager, put) {
		var constant = {
			divradio1_id:'wizdivradio1_id', divradio2_id:'wizdivradio2_id',
			divselect_id:'wizdivselect_id',
			fradio1_id:'wizfradio1_id', fradio2_id:'wizfradio2_id',
			fselect_id:'wizfselect_id',
			prefradio1_id:'wizprefradio1_id', prefradio2_id:'wizprefradio2_id',
			prefselect_id:'wizprefselect_id',
		};
		return declare(null, {
			storeutil_obj:null, server_interface:null, widgetgen_obj:null,
			newdivbtn_widget:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			create: function() {
				// tabconatiner examples:
				// http://dojotoolkit.org/reference-guide/1.9/dijit/layout/TabContainer-examples.html
				//wizard documentation:
				// http://archive.dojotoolkit.org/nightly/dojotoolkit/dojox/widget/tests/test_Wizard.html
				//https://github.com/dojo/dojox/blob/master/widget/tests/test_Wizard.html
				var wizuistackmgr = new WizUIStackManager();
				this.storeutil_obj.wizuistackmgr = wizuistackmgr;
				var tabcontainer = registry.byId("tabcontainer_id");
				var container_cpane = new ContentPane({title:"Scheduling Wizard", class:'allauto', id:"wiztop_cpane_id"});
				tabcontainer.addChild(container_cpane, 0);
				//tabcontainer.selectChild(container_cpane);
				//container_cpane.resize();
				// ref http://archive.dojotoolkit.org/nightly/checkout/dijit/tests/layout/test_TabContainer_noLayout.html
				// for doLayout:false effects
				var wizard_reg = new Wizard({
					title:"Scheduling Wizard/Start Here",
					// style below should have size that will be greater or equal
					// than child WizardPanes
					//class:'allauto'
					style:"width:600px; height:500px",
					//nextButtonLabel:"Configure Divisions"
				});
				container_cpane.addChild(wizard_reg);

				//--------------------//
				// Create informational starting pane
				var content_str = "Gather Information for the League:<br>Get basic information for the league such as the number of divisions, number of teams in each division."
				var intro_wpane = new WizardPane({
					content:content_str,
					//class:'allauto'
					//style:"width:100px; height:100px"
				})
				wizard_reg.addChild(intro_wpane);
				//---------------------//
				var topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Division-relation information.  A division is defined as the group of teams that will interplay with each other.  Define name, # of teams, # of games in season, length of each game, and minimum/maximum days that should lapse between games for each team.</i><br><br>";
				// get/create widgetgen obj
				if (!this.widgetgen_obj) {
					this.widgetgen_obj = new WidgetGen({
						storeutil_obj:this.storeutil_obj,
						server_interface:this.server_interface
					});
				}
				this.widgetgen_obj.create_dbtype_radiobtn(topdiv_node,
					constant.divradio1_id, constant.divradio2_id, "rrdb",
					this, this.radio1_callback, this.radio2_callback,
					constant.divselect_id);
				var divinfo_obj = baseinfoSingleton.get_obj('div_id');
				var menubar_node = put(topdiv_node, "div");
				this.storeutil_obj.create_menubar('div_id', divinfo_obj, true, menubar_node, wizuistackmgr);
				var pcontainerdiv_node = put(topdiv_node, "div")
				var gcontainerdiv_node = put(topdiv_node, "div")
				divinfo_obj.create_wizardcontrol(pcontainerdiv_node,
					gcontainerdiv_node, wizuistackmgr);
				//this.wizuistackmgr.initstacks('div_id');
				var divinfo_wpane = new WizardPane({
					content:topdiv_node,
					//class:'allauto'
					//style:"width:500px; height:400px; border:1px solid red"
				})
				wizard_reg.addChild(divinfo_wpane);
				//-------------------------//
				// Field Config Pane
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Field-availability -relation information.  Specify name of the field, dates/times available, and the divisions that will be using the fields.  Note for detailed date/time configuration or to specify exceptions, click 'Detailed Config' to bring up calendar UI to specify dates/times.</i><br><br>";
				this.widgetgen_obj.create_dbtype_radiobtn(topdiv_node,
					constant.fradio1_id, constant.fradio2_id, "rrdb",
					this, this.radio1_callback, this.radio2_callback,
					constant.fselect_id);
				var fieldinfo_obj = baseinfoSingleton.get_obj('field_id');
				menubar_node = put(topdiv_node, "div");
				this.storeutil_obj.create_menubar('field_id', fieldinfo_obj, true, menubar_node, wizuistackmgr);
				var fieldinfo_wpane = new WizardPane({
					content:topdiv_node,
					//class:'allauto'
					//style:"width:500px; height:400px; border:1px solid red"
				})
				wizard_reg.addChild(fieldinfo_wpane);
				//-------------------------//
				topdiv_node = put("div");
				topdiv_node.innerHTML = "<i>In this Pane, Create or Edit Scheduling Preferences that concern teams.  The league administrator has the disgression to grant prioritized scheduling to teams. Use the table to grant time scheduling priorities.  Note that satisfying scheduling preferences is a best-effort feature and is not guaranteed.  Raising the priority level increases probability that preference will be satisfied.</i><br><br>";
				var prefinfo_obj = baseinfoSingleton.get_obj('pref_id');
				menubar_node = put(topdiv_node, "div");
				this.storeutil_obj.create_menubar('pref_id', fieldinfo_obj, true, menubar_node, wizuistackmgr);
				var prefinfo_wpane = new WizardPane({
					content:topdiv_node,
					//class:'allauto'
					//style:"width:500px; height:400px; border:1px solid red"
				})
				wizard_reg.addChild(prefinfo_wpane);
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

			}
		})
	}
);
