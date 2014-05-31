// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dojox/widget/Wizard", "dojox/widget/WizardPane",
	"dijit/layout/ContentPane", "dijit/DropDownMenu", "dijit/form/DropDownButton",
	"LeagueScheduler/baseinfoSingleton","put-selector/put",
	"dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry, Wizard, WizardPane,
		ContentPane, DropDownMenu, DropDownButton, baseinfoSingleton, put) {
		var constant = {
		};
		return declare(null, {
			storeutil_obj:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			create: function() {
				var tabcontainer = registry.byId("tabcontainer_id");
				/*
				var wizard_cpane = new ContentPane({
					title:"Start Here",
					selected:true
				})
				tabcontainer.addChild(wizard_cpane, 0);
				var wizard_cpane = registry.byId("wizard_cpane");
				*/
				var wizard_reg = new Wizard({
					title:"Start Here",
					//nextButtonLabel:"Configure Divisions"
					style:"width:300px; height:800px"
				});
				//wizard_cpane.addChild(wizard_reg);
				tabcontainer.addChild(wizard_reg, 0);
				var content_str = "Gather Information for the League:<br>Get basic information for the league such as the number of divisions, number of teams in each division."
				var wizard_pane = new WizardPane({
					content:content_str,
				})
				wizard_reg.addChild(wizard_pane);
				var wizardcontent_node = put("div#wizardcontent_id");
				var divinfo_ddownmenu = new DropDownMenu({
					title:"Select Division Configuration",
				});
				var divinfo_obj = baseinfoSingleton.get_obj('div_id');
				this.storeutil_obj.create_menu('div_id', divinfo_obj, true, divinfo_ddownmenu)
				var ddown_btn = new DropDownButton({
					label: "hello!",
					class:"primary",
					dropDown:divinfo_ddownmenu,
				}, wizardcontent_node);
				var wizard_pane2 = new WizardPane({
					content:ddown_btn.domNode
				})
				wizard_reg.addChild(wizard_pane2);
				wizard_reg.startup();

			}
		})
	}
);
