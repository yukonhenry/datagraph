// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
    "dijit/registry", "dojox/widget/Wizard", "dojox/widget/WizardPane",
    "dijit/DropDownMenu", "dijit/form/Button", "dijit/layout/ContentPane",
    "LeagueScheduler/baseinfoSingleton", "LeagueScheduler/widgetgen",
    "LeagueScheduler/divinfo",
    "LeagueScheduler/tourndivinfo", "LeagueScheduler/fieldinfo",
    "LeagueScheduler/preferenceinfo", "LeagueScheduler/newschedulerbase",
    "LeagueScheduler/teaminfo", "LeagueScheduler/conflictinfo",
    "LeagueScheduler/idmgrSingleton",
    "put-selector/put", "dojo/domReady!"],
    function(dom, declare, lang, arrayUtil, registry, Wizard, WizardPane,
        DropDownMenu, Button, ContentPane,
        baseinfoSingleton, WidgetGen, divinfo, tourndivinfo,
        fieldinfo, preferenceinfo, newschedulerbase, teaminfo, conflictinfo,
        idmgrSingleton,
        put) {
        var constant = {
            //divradio1_id:'wizdivradio1_id', divradio2_id:'wizdivradio2_id',
            //divselect_id:'wizdivselect_id', init_db_type:"rrdb",
            top_cpane_id:'tutorial_cpane_id',
            schedform_id:'schedform_id'
        };
        return declare(null, {
            storeutil_obj:null, server_interface:null, widgetgen_obj:null,
            schedutil_obj:null, tutorialid_list:null,
            userid_name:"",
            constructor: function(args) {
                lang.mixin(this, args);
                this.tutorialid_list = idmgrSingleton.get_idmgr_list('op_type', 'tutorial');
            },
            create: function() {
                // tabconatiner examples:
                // http://dojotoolkit.org/reference-guide/1.9/dijit/layout/TabContainer-examples.html
                //wizard documentation:
                // http://archive.dojotoolkit.org/nightly/dojotoolkit/dojox/widget/tests/test_Wizard.html
                //https://github.com/dojo/dojox/blob/master/widget/tests/test_Wizard.html
                //var wizuistackmgr = new WizUIStackManager();
                //this.wizuistackmgr = wizuistackmgr;
                var tabcontainer = registry.byId("tabcontainer_id");
                var container_cpane = registry.byId(constant.top_cpane_id);
                if (container_cpane) {
                    container_cpane.resize();
                    return
                }
                container_cpane = new ContentPane({title:"Scheduling Tutorial", class:'allauto', id:constant.top_cpane_id});
                container_cpane.on("show", lang.hitch(this, function(evt) {
                    console.log("tutorial onshow");
                    container_cpane.domNode.scrollTop = 0;
                }))
                tabcontainer.addChild(container_cpane);
                // ref http://archive.dojotoolkit.org/nightly/checkout/dijit/tests/layout/test_TabContainer_noLayout.html
                // for doLayout:false effects
                var wizard_reg = new Wizard({
                    title:"Scheduling Tutorial/Start Here",
                    // style below should have size that will be greater or equal
                    // than child WizardPanes
                    class:'allauto',
                    //style:"width:600px; height:500px",
                    nextButtonLabel:"Next Step"
                });
                container_cpane.addChild(wizard_reg);

                //--------------------//
                // Create informational starting pane
                var content_str = "<p style='font-size:larger'>User/Organization ID: <strong>"+this.userid_name+"</strong></p>";
                content_str += "Welcome to the YukonTR League Scheduler.  The main purpose of this scheduler is to not only generate schedules for large leagues, but to also accomodate complex constraints/conflicts/preferences that you would like reflected in the schedule.<br><br><b>Begin</b> the step-by-step tutorial by pressing the 'Next Step' button in the bottom-right of the Pane"
                var intro_wpane = new WizardPane({
                    content:content_str,
                    //class:'allonehundred'
                    //style:"width:100px; height:100px"
                })
                wizard_reg.addChild(intro_wpane);
                //---------------------//
                // --- DIVISION INFO-----//
                var topdiv_node = put("div");
                topdiv_node.innerHTML = "<i>Please specify an identifier for the schedule:</i><br><br>";
                var schedform_id = constant.schedform_id;
                var schedform_widget = registry.byId(schedform_id);
                if (!schedform_widget) {
                    schedform_widget = new Form({
                        id:schedform_id
                    })
                }
                var schedname_wpane = new WizardPane({
                    content:topdiv_node,
                    //class:'allauto'
                    //style:"width:500px; height:400px; border:1px solid red"
                })
                wizard_reg.addChild(schedname_wpane);
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
                return container_cpane;
            },
            get_idstr_obj: function(id) {
                var idmgr_obj = this.getuniquematch_obj(this.tutorialid_list,
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
