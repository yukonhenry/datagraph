// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dojox/widget/Wizard", "dojox/widget/WizardPane",
	"dijit/DropDownMenu", "dijit/form/DropDownButton",
	"LeagueScheduler/baseinfoSingleton", "LeagueScheduler/widgetgen",
	"put-selector/put", "dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry, Wizard, WizardPane,
		DropDownMenu, DropDownButton,
		baseinfoSingleton, WidgetGen, put) {
		var constant = {
			radio1_id:'wizradio1_id', radio2_id:'wizradio2_id',
			select_id:'wizselect_id'
		};
		return declare(null, {
			storeutil_obj:null, server_interface:null, widgetgen_obj:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			create: function() {
				// tabconatiner examples:
				// http://dojotoolkit.org/reference-guide/1.9/dijit/layout/TabContainer-examples.html
				//wizard documentation:
				// http://archive.dojotoolkit.org/nightly/dojotoolkit/dojox/widget/tests/test_Wizard.html
				//https://github.com/dojo/dojox/blob/master/widget/tests/test_Wizard.html
				var tabcontainer = registry.byId("tabcontainer_id");
				// ref http://archive.dojotoolkit.org/nightly/checkout/dijit/tests/layout/test_TabContainer_noLayout.html
				// for doLayout:false effects
				var wizard_reg = new Wizard({
					title:"Scheduling Wizard",
					// style below should have size that will be greater or equal
					// than child WizardPanes
					style:"width:500px; height:200px"
					//nextButtonLabel:"Configure Divisions"
				});
				//wizard_cpane.addChild(wizard_reg);
				tabcontainer.addChild(wizard_reg, 0);
				//--------------------//
				// Create informational starting pane
				var content_str = "Gather Information for the League:<br>Get basic information for the league such as the number of divisions, number of teams in each division."
				var intro_wpane = new WizardPane({
					content:content_str,
					style:"width:100px; height:100px"
				})
				wizard_reg.addChild(intro_wpane);
				//---------------------//
				var topdiv_node = put("div");
				// get/create widgetgen obj
				if (!this.widgetgen_obj) {
					this.widgetgen_obj = new WidgetGen({
						storeutil_obj:this.storeutil_obj,
						server_interface:this.server_interface
					});
				}
				this.widgetgen_obj.create_dbtype_radiobtn(topdiv_node,
					constant.radio1_id, constant.radio2_id, "rrdb",
					this, this.radio1_callback, this.radio2_callback,
					constant.select_id);
				/*
				var divinfo_ddownmenu = new DropDownMenu({
					title:"Select Division Configuration",
				});
				var divinfo_obj = baseinfoSingleton.get_obj('div_id');
				this.storeutil_obj.create_menu('div_id', divinfo_obj, true, divinfo_ddownmenu)
				var ddown_btn = new DropDownButton({
					label: "hello!",
					class:"primary",
					dropDown:divinfo_ddownmenu,
				}, topdiv_node);
				*/
				var divinfo_wpane = new WizardPane({
					content:topdiv_node,
					style:"width:500px; height:400px; border:1px solid red"

				})
				wizard_reg.addChild(divinfo_wpane);
				wizard_reg.startup();

			},
			radio1_callback: function(select_id, event) {

			},
			radio2_callback: function(select_id, event) {

			}
		})
	}
);
