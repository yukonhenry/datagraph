/* Utility functions to generate widgets and widget features
*/
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
    "dojo/_base/array", "dojo/Stateful", "dojo/date",
    "dijit/registry", "dijit/Dialog", "dijit/form/Button", "dijit/form/RadioButton",
    "dijit/form/Select", "dijit/form/NumberSpinner", "dijit/form/DateTextBox",
    "dijit/form/Form", "dijit/form/ValidationTextBox",
    "dijit/Tooltip",
    "put-selector/put", "scheduler_front/baseinfoSingleton", "dojo/domReady!"],
    function(dom, declare, lang, arrayUtil, Stateful, date,
        registry, Dialog, Button, RadioButton, Select, NumberSpinner, DateTextBox,
        Form, ValidationTextBox,
        Tooltip, put, baseinfoSingleton) {
        var Watch_class = declare([Stateful], {
            db_type:null
        });
        var constant = {
            default_db_type:'rrdb',
            oddnum_dialog_id:"oddnum_dialog_id",
            oddnum_radio1_id:"oddnum_radio1_id",
            oddnum_radio2_id:"oddnum_radio2_id",
            oddnum_radio_name:"oddnum_radio_name", oddnum_btn_id:"oddnum_btn_id"
        }
        return declare(null, {
            storeutil_obj:null, radio_db_type:null, watch_obj:null,
            start_dtbox:null, end_dtbox:null, sl_spinner:null,
            server_interface:null, event_flag:false, tooltip_list:null,
            constructor: function(args) {
                lang.mixin(this, args);
                this.watch_obj = new Watch_class();
                this.watch_obj.watch("db_type",
                    lang.hitch(this, function(name, oldValue, value) {
                        this.swap_league_select_db('league_select_id', value);
                    })
                );
                this.tooltip_list = new Array();
            },
            // function to create radio button selects for  db_type
            // ref https://github.com/kriszyp/put-selector for put selector
            // also reference
            // http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
            // http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
            create_dbtype_radiobtn: function(topdiv_node, div1_radio_id,
                div2_radio_id, init_db_type, callback_context, radio1_callback,
                radio2_callback, league_select_id) {
                // first figure out which radio button is initially enabled
                var radio1_flag = false;
                if (init_db_type) {
                    // if an init_db_type is specified
                    radio1_flag = (init_db_type == 'rrdb')?true:false;
                } else {
                    // if no init_db_type, then use default for initial
                    // radiobtn selection
                    radio1_flag = (constant.default_db_type == 'rrdb')?true:false;
                }
                // NOTE: dom.byID after the widget does not recover the
                // widget's domNode. In this example, the widget's domNode is a
                // HTML div element, but the dom.byId after the widget is created
                // gets an HTML Input element.
                // affects how to get widget later is dom.byId succeeds - use
                // registry.byId and Not registry.byNode(dom.byId()) if the
                // enclosing domnode type is not the same between the node and the
                // widget (in this case one is Div and the widget is an Input)
                var div1_radio_node = dom.byId(div1_radio_id);
                var div1_radio = null;
                if (!div1_radio_node) {
                    put(topdiv_node, "span", "Select Schedule Type:");
                    div1_radio_node = put(topdiv_node,
                        "div[id=$]", div1_radio_id);
                    put(topdiv_node,
                        "label.label_box[for=$]", div1_radio_id,
                        "League/Round Robin");
                    div1_radio = new RadioButton({
                        name:'db_type',
                        value:'rrdb',
                        checked:radio1_flag,
                        style:"margin-left:5px",
                        // ok to include league_select_id as a third parameter to
                        // hitch as league_select_id is a fixed dom id that gets
                        // determined when the callback is defined.
                        // If the third parameter is determined run-time, do Not
                        // define it as the 3rd parameter of hitch and instead get
                        // the variable from within the callback function during
                        // runtime.
                        onChange: lang.hitch(callback_context, radio1_callback, league_select_id)
                    }, div1_radio_node);
                    div1_radio.startup();
                } else {
                    // see comment above on why byId is used instead of
                    // byNode
                    div1_radio = registry.byId(div1_radio_id);
                }
                var div2_radio_node = dom.byId(div2_radio_id);
                var div2_radio = null;
                if (!div2_radio_node) {
                    div2_radio_node = put(topdiv_node,
                        "div[id=$]", div2_radio_id);
                    put(topdiv_node,
                        "label.label_box[for=$]", div2_radio_id,
                        "Tournament");
                    div2_radio = new RadioButton({
                        name:'db_type',
                        value:'tourndb',
                        style:"margin-left:10px",
                        checked:!radio1_flag,
                        onChange: lang.hitch(callback_context, radio2_callback, league_select_id)
                    }, div2_radio_node);
                    div2_radio.startup();
                    put(topdiv_node, "br, br");
                } else {
                    // see comment above on why byId is used instead of
                    // byNode
                    div2_radio = registry.byId(div2_radio_id);
                }
            },
            // reload already-created radio buttons with different default selections
            reload_dbytpe_radiobtn: function(div1_radio_id, div2_radio_id, init_db_type) {
                var radio1_flag = (init_db_type == 'rrdb')?true:false;
                var div1_radio = registry.byId(div1_radio_id);
                div1_radio.set("checked", radio1_flag);
                var div2_radio = registry.byId(div2_radio_id);
                div2_radio.set("checked", !radio1_flag);
            },
            // create select dropdown
            // programmatic creation of enclosing node and then widget itself
            create_select: function(args_obj) {
                var topdiv_node = args_obj.topdiv_node;
                var lselect_id = args_obj.select_id;
                var init_db_type = args_obj.init_db_type;
                var init_colname = args_obj.init_colname;
                var onchange_callback = args_obj.onchange_callback;
                var name_str = args_obj.name_str;
                var label_str = args_obj.label_str;
                var put_trail_spacing = args_obj.put_trail_spacing;

                var db_type = (init_db_type == "") ?
                    constant.default_db_type:init_db_type;
                var league_select = null;
                var select_node = dom.byId(lselect_id);
                if (!select_node) {
                    put(topdiv_node,
                        //"label.label_box[for=$][style=margin-left:50px]",
                        "label.label_box[for=$]",
                        lselect_id, label_str);
                    select_node = put(topdiv_node,
                        "select[id=$][name=$]", lselect_id, name_str);
                    var league_select = new Select({
                        name:name_str,
                        //store:dbselect_store,
                        //labelAttr:"name",
                        onChange:onchange_callback
                    }, select_node);
                    var args_obj = {db_type:db_type, label_str:label_str,
                        config_status:true, init_colname:init_colname};
                    // data necessary to create option list is in local store-
                    // created during initialization with initial query of
                    // collection list
                    var option_list = this.storeutil_obj.getLabelDropDown_list(args_obj);
                    league_select.addOption(option_list);
                    league_select.startup();
                    if (option_list.length < 2) {
                        var ls_tooltipconfig = {
                            connectId:[lselect_id],
                            label:"If Empty Make Selection First",
                            position:['above','after']};
                        var ls_tooltip = new Tooltip(ls_tooltipconfig);
                    }
                    // NOTE: the spaces below might not be appropriate for
                    // fieldinfo - double check
                    put(topdiv_node, put_trail_spacing);  // add space
                } else {
                    // we can use by Node here as both node and widget are selects
                    league_select = registry.byNode(select_node);
                    // reset options and callback based on passed in parameters
                    var args_obj = {db_type:db_type, label_str:label_str,
                        config_status:true, init_colname:init_colname};
                    var option_list = this.storeutil_obj.getLabelDropDown_list(args_obj);
                    league_select.set("options", option_list);
                    league_select.set("onChange", onchange_callback);
                    league_select.startup();
                }
                return league_select;
            },
            reload_select: function(args_obj) {
                // reset/reload select dropdown
                var select_reg = args_obj.select_reg;
                var init_db_type = args_obj.init_db_type;
                var init_colname = args_obj.init_colname;
                var label_str = args_obj.label_str;

                args_obj = {db_type:init_db_type, label_str:label_str,
                    config_status:true, init_colname:init_colname};
                var option_list = this.storeutil_obj.getLabelDropDown_list(args_obj);
                select_reg.set("options", option_list);
                select_reg.startup();
            },
            // get list of items in db specified by db_type from server
            // collection name is the event of calling onChange event handler
            // ordering of parameters is important, as get_leagueparam_list is an event
            // handler - colname is passed as the event value - calling event handler
            // is specified as lang.hitch(this, this.getname, db_type, info_obj)
            // event comes in as the last parameter (empirically determined, should)
            // get confirmation.
            get_leagueparam_frommenu_list: function(info_obj, event) {
                // callback from a menuitem click - callback from menus are different
                // than callbacks from select's as for the latter the event will
                // be the value of the select entry; however, the event for a menu
                // click is a click related object and the pertinent value must
                // be extracted from the object.  Here we are using the label -
                // we could have also used info_obj.item (see calling function)
                this.get_leagueparam_list(info_obj, info_obj.item);
                if (info_obj.idproperty == 'team_id') {
                    // if idprop is team_id, then activegrid_colname for the grid is
                    // league param collection (not just the distr_colname like for
                    // other idproperties)
                    info_obj.activegrid_colname = info_obj.item;
                }
            },
            get_leagueparam_list: function(info_obj, colname) {
                // note {colname:colname} is the options_obj obj passed directly
                // to the callback function create_divstr_list
                // we want to pass the colname back to the callback so that the colname
                // can be attached to the fieldinfo data when it is saved to the
                // local store and also sent back to the server
                // ref http://stackoverflow.com/questions/154059/how-do-you-check-for-an-empty-string-in-javascript
                // for checking for empty string
                // if db_type is still null, assign default
                var divstr_db_type = info_obj.divstr_db_type;
                var db_type = (divstr_db_type == "") ?
                    constant.default_db_type:divstr_db_type;
                var idproperty_str = (db_type == 'rrdb')?'div_id':'tourndiv_id'
                if (colname) {
                    // first check to see whether data is in a current grid store
                    // Note info_obj points to where the divstr_list will eventually
                    // be applied to - not where it is coming from, which will
                    // always be from a 'div_id' idproperty db - rrdb or tourndb
                    // Reference w newschedulerbase/getdivselect_dropdown; info_obj
                    // is Not necessarily divinfo
                    // NOTE 'div_id' for get_obj should be a passed parameter as the obj might be tourndiv_id idprop object
                    var divinfo_obj = baseinfoSingleton.get_obj(idproperty_str,
                        info_obj.op_type);
                    var options_obj = {colname:colname, info_obj:info_obj,
                        db_type:db_type};
                    if (divinfo_obj && divinfo_obj.infogrid_store &&
                        divinfo_obj.activegrid_colname == colname) {
                        var data_obj = new Object();
                        divinfo_obj.infogrid_store.fetch().then(
                            function(info_list) {
                                data_obj.info_list = info_list;
                            })
                        data_obj.config_status = divinfo_obj.config_status;
                        this.create_divstr_list(data_obj, options_obj)
                    } else {
                        // not in local divinfo store, so get from server
                        // db_type is a divstr_db_type - which means it should always
                        // be rrdb or tourndb
                        var userid_name = baseinfoSingleton.get_userid_name();
                        this.server_interface.getServerData(
                            'get_dbcol/'+userid_name+'/'+db_type+'/'+colname,
                            lang.hitch(this, this.create_divstr_list), null,
                            options_obj);
                    }
                }
            },
            // swap the store for the league select widget
            // usually driven by radio button db type selection
            swap_league_select_db: function(lselect_id, db_type) {
                args_obj = {db_type:db_type, label_str:'Select League',
                            config_status:true};
                var option_list = this.storeutil_obj.getLabelDropDown_list(args_obj);
                var league_select = registry.byId(lselect_id);
                // ref http://dojotoolkit.org/documentation/tutorials/1.9/selects_using_stores/ (section of using select without stores)
                league_select.set("options", option_list);
                league_select.startup();
            },
            create_divstr_list: function(server_data, options_obj) {
                // call after getting league param divstr informaton from server
                var data_list = server_data.info_list;
                var config_status = server_data.config_status;
                var colname = options_obj.colname; // collection name for divinfo
                var db_type = options_obj.db_type; // db_type for divstr
                var info_obj = options_obj.info_obj; // where to return colname and db_type info
                // config_status below should always be 1 as the db's are selected
                // from a list that includes only fully complete configurations
                if (config_status) {
                    var idproperty_str = (db_type == "rrdb")?'div_id':'tourndiv_id';
                    var divstr_list = arrayUtil.map(data_list,
                        function(item, index) {
                            // return both the divstr (string) and div_id value
                            // value used as the value for the checkbox in the fieldinfo grid dropdown
                            // save other fields that will be useful for various
                            // infoobj grid fields
                            // divfield_list and fieldcol_name can be undefined
                            // if field list has not been configured and divfield_list
                            // calculated.
                            var return_obj = {divstr:item.div_age + item.div_gen,
                                //div_id:item.div_id,
                                totalteams:item.totalteams,
                                divfield_list:item.divfield_list
                                //'divfield_list':item.divfield_list,
                                //'fieldcol_name':item.fieldcol_name
                            };
                            return_obj[idproperty_str] = item[idproperty_str];
                            return return_obj;
                    })
                    // save divinfo obj information that is attached to the current
                    // fieldinfo obj
                    info_obj.setdivstr_obj(colname, db_type);
                    baseinfoSingleton.set_watch_obj('divstr_list', divstr_list,
                        info_obj.op_type, info_obj.idproperty);
                }
            },
            // create calendar inputs for season start/end dates
            /* note pausable/resume handler does not work trying to control changes made to textbox's programmatically
            just use manual event_flag to control double/cascading event firing; set event_flag to true anytime another start/end/length register is set from within a similar handler.  The flag will be used to prevent cascading event handling which will be unnecessary.
            NOTE a boolean event flag only works if a handler sets only one other register.  If multiple registers are set in the
            handler than the event_flag needs to be turned into a counter. */
            create_calendarspinner_input: function(args_obj) {
                var topdiv_node = args_obj.topdiv_node;
                var start_datebox_id = args_obj.start_datebox_id;
                var end_datebox_id = args_obj.end_datebox_id;
                var sl_spinner_id = args_obj.spinner_id;
                var default_numweeks = args_obj.numweeks;
                var sdbtn_id = args_obj.seasondates_btn_id;
                var op_type = args_obj.op_type;
                var today = new Date();
                var start_dtbox_node = dom.byId(start_datebox_id);
                if (!start_dtbox_node) {
                    put(topdiv_node,
                        "label.label_box[for=$]", start_datebox_id,
                        "Season Start Date");
                    start_dtbox_node = put(topdiv_node,
                        "input[id=$]", start_datebox_id);
                    this.start_dtbox = new DateTextBox({
                        value: today,
                        style:'width:120px; margin-right:40px',
                        onChange: lang.hitch(this, function(event) {
                            if (!this.event_flag) {
                                var enddate = this.end_dtbox.get('value');
                                var numweeks = date.difference(event, enddate,'week');
                                if (numweeks < 1) {
                                    alert("end date needs to be at least one week after start date");
                                    // reset the date to an arbitrary default
                                    numweeks = this.sl_spinner.get('value');
                                    this.start_dtbox.set('value',
                                        date.add(enddate, 'week', -numweeks));
                                } else {
                                    this.sl_spinner.set('value', numweeks);
                                }
                                this.event_flag = true;
                            } else {
                                this.event_flag = false;
                            }
                        })
                    }, start_dtbox_node);
                    this.start_dtbox.startup();
                } else {
                    if (!this.start_dtbox)
                        // registry.byNode is not returning widget, use byId
                        this.start_dtbox = registry.byId(start_datebox_id);
                    //this.start_dtbox = registry.byNode(start_dtbox_node);
                }
                // create season end date entry
                var end_dtbox_node = dom.byId(end_datebox_id);
                if (!end_dtbox_node) {
                    put(topdiv_node,
                        "label.label_box[for=$]", end_datebox_id,
                        "Season End Date");
                    end_dtbox_node = put(topdiv_node,
                        "input[id=$]", end_datebox_id);
                    this.end_dtbox = new DateTextBox({
                        value: date.add(today, 'week', default_numweeks),
                        style:'width:120px; margin-right:40px',
                        onChange: lang.hitch(this, function(event) {
                            if (!this.event_flag) {
                                var startdate = this.start_dtbox.get('value');
                                var numweeks = date.difference(startdate, event,'week');
                                if (numweeks < 1) {
                                    alert("end date needs to be at least one week after start date");
                                    numweeks = this.sl_spinner.get('value');
                                    //this.seasonend_handle.pause();
                                    this.end_dtbox.set('value',
                                        date.add(startdate, 'week', numweeks));
                                    //this.seasonend_handle.resume();
                                } else {
                                    //this.seasonlength_handle.pause();
                                    this.sl_spinner.set('value', numweeks);
                                    //this.seasonlength_handle.resume();
                                }
                                this.event_flag = true;
                            } else {
                                this.event_flag = false;
                            }
                        })
                    }, end_dtbox_node);
                    this.end_dtbox.startup();
                } else {
                    if (!this.end_dtbox)
                        this.end_dtbox = registry.byId(end_datebox_id);
                }
                // create season length spinner
                var sl_spinner_node = dom.byId(sl_spinner_id);
                if (!sl_spinner_node) {
                    put(topdiv_node,
                        "label.label_box[for=$]", sl_spinner_id,
                        "Season Length (weeks)");
                    sl_spinner_node = put(topdiv_node,
                        "input[id=$][name=$]", sl_spinner_id, sl_spinner_id);
                    this.sl_spinner = new NumberSpinner({
                        value:default_numweeks,
                        smallDelta:1,
                        constraints:{min:1, max:50, places:0},
                        style:'width:80px',
                        onChange: lang.hitch(this, function(event) {
                            if (!this.event_flag) {
                                var startdate = this.start_dtbox.get('value');
                                var enddate = date.add(startdate, 'week', event);
                                //this.seasonend_handle.pause();
                                this.event_flag = true;
                                this.end_dtbox.set('value', enddate);
                                //this.seasonend_handle.resume();
                            } else {
                                this.event_flag = false;
                            }
                        })
                    }, sl_spinner_node);
                    this.sl_spinner.startup();
                    //put(topdiv_node, "br");
                } else {
                    if (!this.sl_spinner)
                        this.sl_spinner = registry.byId(sl_spinner_id);
                }
                // create button to save season start/end/length
                var sdbtn_node = dom.byId(sdbtn_id);
                var sdbtn = null;
                if (!sdbtn_node) {
                    sdbtn_node = put(topdiv_node,
                        "button.dijitButton[id=$][type=button]", sdbtn_id);
                    var sdbtn_status_span = put(sdbtn_node,"+span.empty_smallgap_color");
                    sdbtn = new Button({
                        label:"Transfer Dates Info",
                        title:"Click to Calculate # weeks in season and transfer to Grid",
                        class:"primary",
                        onClick: lang.hitch(this, this.getSeasonDatesFromInput,
                            op_type)
                    }, sdbtn_node);
                    sdbtn.startup();
                    put(topdiv_node, "br, br");
                } else {
                    sdbtn = registry.byId(sdbtn_id);
                }
            },
            getSeasonDatesFromInput: function(op_type, event) {
                var seasonstart_date = this.start_dtbox.get("value");
                var seasonend_date = this.end_dtbox.get("value");
                var season_len = this.sl_spinner.get("value");
                // season dates spinners are only for div_id panel at the moment
                baseinfoSingleton.set_watch_obj('numweeks', season_len, op_type, 'div_id');
            },
            create_forminput: function(args_obj) {
                var form_id = args_obj.form_id;
                var name_id = args_obj.name_id;
                var input_type = args_obj.input_type;
                var btn_id = args_obj.btn_id;
                var cpane = args_obj.cpane;
                var form_str = args_obj.form_str;
                var tooltip_str = args_obj.tooltip_str;
                var callback_func = args_obj.callback_func;
                var callback_context = args_obj.callback_context;
                var initialname_value = args_obj.initialname_value;
                var form_widget = registry.byId(form_id)
                if (!form_widget) {
                    // create all elements under the form
                    form_widget = new Form({
                        id:form_id
                    })
                    cpane.addChild(form_widget);
                    var form_node = form_widget.domNode;
                    put(form_node, "label.label_box[for=$]",
                        name_id, form_str);
                    put(form_node, "span.empty_tinygap");
                    var name_node = put(form_node,
                        "input[id=$][type=text][required=true]",
                        name_id)
                    var name_widget = new ValidationTextBox({
                        value:initialname_value,
                        regExp:'\\D[\\w]+',
                        style:'width:12em',
                        promptMessage:form_str + '-start with letter or _, followed by alphanumeric or _',
                        invalidMessage:'start with letter or _, followed by alphanumeric characters and _, no spaces',
                        missingMessage:form_str,
                    }, name_node);
                    var tooltipconfig = {connectId:[name_id],
                        label:tooltip_str,
                        position:['below','above']};
                    this.tooltip_list.push(new Tooltip(tooltipconfig));
                    put(form_node, "span.empty_tinygap");
                    var callback_args_obj = {
                        form_widget:form_widget,
                        name_widget:name_widget
                    }
                    var btn_node = put(form_node,
                        "button.dijitButton[id=$][type=submit]", btn_id);
                    var btn_widget = new Button({
                        label:"Submit",
                        disabled:false,
                        class:"success",
                        onClick: lang.hitch(callback_context, callback_func,
                            callback_args_obj)
                    }, btn_node);
                    btn_widget.startup();
                    name_widget.on("keyup",
                        lang.hitch(callback_context, callback_func,
                            callback_args_obj));
                }
            },
            get_radiobtn_dialog: function(args_obj) {
                var init_radio_value = args_obj.init_radio_value;
                var context = args_obj.context;
                var radio1_callback = args_obj.radio1_callback;
                var radio2_callback = args_obj.radio2_callback;
                var submit_callback = args_obj.submit_callback;
                var deferred_obj = args_obj.deferred_obj;
                var raw_result = args_obj.raw_result;
                var radio1_id = constant.oddnum_radio1_id;
                var radio2_id = constant.oddnum_radio2_id;
                var btn_id = constant.oddnum_btn_id;
                var radio1_flag = (init_radio_value == 'BYE')?true:false;
                var oddnum_dialog = registry.byId(constant.oddnum_dialog_id);
                if (!oddnum_dialog) {
                   oddnum_dialog = new Dialog({
                        id:constant.oddnum_dialog_id,
                        class:"dijitDialog", title:"<p style='color:blue'>BYE or PLAY</p>",
                        style:"width:300px",
                        content:"Div has odd # of teams; Select Model"
                    })
                    var oddnum_form = new Form();
                    var form_node = oddnum_form.domNode;
                    put(form_node, "span", "Select one:");
                    var radio1_node = put(form_node, "div[id=$]", radio1_id);
                    put(form_node, "label.label_box[for=$]", radio1_id, "Bye");
                    var radio2_node = put(form_node, "div[id=$]", radio2_id);
                    put(form_node, "label.label_box[for=$]", radio2_id, "Play");
                    new RadioButton({
                        name:constant.oddnum_radio_name,
                        value:"bye", checked:radio1_flag,
                        style:"margin-left:5px",
                        onChange: lang.hitch(context, radio1_callback)
                    }, radio1_node)
                    new RadioButton({
                        name:constant.oddnum_radio_name,
                        value:"play", checked:!radio1_flag,
                        style:"margin-left:10px",
                        onChange: lang.hitch(context, radio2_callback)
                    }, radio2_node);
                    var btn_node = put(form_node,
                        "button.dijitButton[id=$][type=submit]", btn_id);
                    var btn_widget = new Button({
                        label:"Submit",
                        class:"success",
                        onClick: lang.hitch(context, submit_callback,
                            deferred_obj, raw_result)
                    }, btn_node);
                    var tooltipconfig = {
                        connectId:[constant.oddnum_dialog_id],
                        label:"BYE Model: One Team has Bye; PLAY Model: One team plays twice on a game date so that no team has a BYE",
                        position:['before','after']};
                    new Tooltip(tooltipconfig);
                    oddnum_dialog.addChild(oddnum_form);
                } else {
                    var radio1_widget = registry.byId(radio1_id);
                    radio1_widget.set("checked", radio1_flag);
                    var radio2_widget = registry.byId(radio2_id);
                    radio2_widget.set("checked", !radio1_flag);
                    var btn_widget = registry.byId(btn_id);
                    btn_widget.set("onClick", lang.hitch(context, submit_callback,
                        deferred_obj, raw_result))
                }
                oddnum_dialog.startup();
                return oddnum_dialog
            },
        })
    })
