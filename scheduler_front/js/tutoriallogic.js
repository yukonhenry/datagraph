// define observable store-related utility functions
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
    "dojo/keys",
    "dijit/registry", "dojox/widget/Wizard", "dojox/widget/WizardPane",
    "dijit/DropDownMenu", "dijit/layout/ContentPane", "dijit/Tooltip",
    "scheduler_front/baseinfoSingleton",
    "scheduler_front/divinfo",
    "scheduler_front/tourndivinfo", "scheduler_front/fieldinfo",
    "scheduler_front/preferenceinfo", "scheduler_front/newschedulerbase",
    "scheduler_front/teaminfo", "scheduler_front/conflictinfo",
    "scheduler_front/idmgrSingleton",
    "put-selector/put", "dojo/domReady!"],
    function(dom, declare, lang, arrayUtil, keys, registry, Wizard, WizardPane,
        DropDownMenu, ContentPane, Tooltip,
        baseinfoSingleton, divinfo, tourndivinfo,
        fieldinfo, preferenceinfo, newschedulerbase, teaminfo, conflictinfo,
        idmgrSingleton,
        put) {
        var constant = {
            //divradio1_id:'wizdivradio1_id', divradio2_id:'wizdivradio2_id',
            //divselect_id:'wizdivselect_id', init_db_type:"rrdb",
            top_cpane_id:'tutorial_cpane_id',
            schedform_id:'schedform_id', schedname_id:'schedname_id',
            schedbtn_id:'schedbtn_id',
        };
        return declare(null, {
            storeutil_obj:null, server_interface:null, widgetgen_obj:null,
            schedutil_obj:null, tutorialid_list:null, keyup_handle:null,
            userid_name:"",
            constructor: function(args) {
                lang.mixin(this, args);
                this.tutorialid_list = idmgrSingleton.get_idmgr_list('op_type', 'tutorial');
            },
            create: function() {
                var tabcontainer = registry.byId("tabcontainer_id");
                var container_cpane = registry.byId(constant.top_cpane_id);
                if (container_cpane) {
                    container_cpane.resize();
                    return
                }
                container_cpane = new ContentPane({title:"Tutorial", class:'allauto', id:constant.top_cpane_id,
                    tooltip:"If using the Scheduler for the first time, start here"
                });
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
                    nextButtonLabel:"Next Step",
                });
                container_cpane.addChild(wizard_reg);

                //--------------------//
                // Create informational starting pane
                var content_str = "<p style='font-size:larger'>User/Organization ID: <strong>"+this.userid_name+"</strong></p>";
                content_str += "Welcome to the YukonTR League Scheduler.  The main purpose of this scheduler is to not only generate schedules for large leagues, but to also accomodate complex constraints/conflicts/preferences that you would like reflected in the schedule.<br><br><b>Begin</b> the tutorial configuration guide by pressing the 'Next Step' button in the bottom-right of the Pane"
                var intro_wpane = new WizardPane({
                    content:content_str,
                })
                wizard_reg.addChild(intro_wpane);
                //---------------------//
                // ---Schedule Name Input -----//
                var schedname_wpane = new WizardPane({
                    content:"<i>Please specify a name for this schedule:</i><br><br>",
                    //class:'allauto'
                    //style:"width:500px; height:400px; border:1px solid red"
                })
                args_obj = {
                    form_id:constant.schedform_id,
                    name_id:constant.schedname_id,
                    initialname_value:this.userid_name,
                    btn_id:constant.schedbtn_id,
                    form_str:"Enter Schedule Name:",
                    tooltip_str:"Specify Schedule Name and press Enter key",
                    cpane:schedname_wpane,
                    callback_func: this.process_input,
                    callback_context: this,
                }
                this.widgetgen_obj.create_forminput(args_obj);
                wizard_reg.addChild(schedname_wpane);
                //---------------------//
                // ---Schedule Name Input -----//
                var divnumber_wpane = new WizardPane({
                    content:"<i>How many divisions are there in your league? (A division is defined as a set of teams that will play against each other):</i><br><br>",
                })
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
            process_input: function(args_obj, event) {
                if (event.type == "click" ||
                    (event.type == "keyup" && event.keyCode == keys.ENTER)) {
                    var schedform_widget = args_obj.form_widget;
                    var schedname_widget = args_obj.name_widget;
                    if (schedform_widget.validate()) {
                        //confirm("ID Format is Valid, Creating or Retrieving Entry")
                        var schedname_id = schedname_widget.get("value");
                        console.log("schedname="+schedname_id);
                    }
                    /*
                    if (this.keyup_handle)
                        this.keyup_handle.remove(); */
                }
            }
        })
    }
);
