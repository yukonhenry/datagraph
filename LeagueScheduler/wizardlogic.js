// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dojox/widget/Wizard", "dojox/widget/WizardPane",
	"dijit/layout/ContentPane",
	"LeagueScheduler/baseinfoSingleton","put-selector/put",
	"dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry, Wizard, WizardPane,
		ContentPane, baseinfoSingleton, put) {
		var constant = {
		};
		return declare(null, {
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
				var wizard_pane2 = new WizardPane({
					content:'test2 ads',
				})
				wizard_reg.addChild(wizard_pane2);
				wizard_reg.startup();

			}
		})
	}
);
