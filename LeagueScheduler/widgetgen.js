/* Utility functions to generate widgets and widget features
*/
define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
    "dojo/_base/array", "dojo/Stateful", "dojo/store/Memory", "dojo/date",
    "dijit/registry", "dijit/form/Button", "dijit/form/RadioButton",
    "dijit/form/Select", "dijit/form/NumberSpinner", "dijit/form/DateTextBox",
    "put-selector/put", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
    function(dbootstrap, dom, declare, lang, arrayUtil, Stateful, Memory, date,
        registry, Button, RadioButton, Select, NumberSpinner, DateTextBox,
        put, baseinfoSingleton) {
        var Watch_class = declare([Stateful], {
            db_type:null
        });
        var constant = {
            default_db_type:'rrdb',
            serverdata_key:'info_list',
            serverstatus_key:'config_status'
        }
        return declare(null, {
            storeutil_obj:null, radio_db_type:null, watch_obj:null,
            start_dtbox:null, end_dtbox:null, sl_spinner:null,
            server_interface:null, event_flag:false,
            constructor: function(args) {
                lang.mixin(this, args);
                this.watch_obj = new Watch_class();
                this.watch_obj.watch("db_type",
                    lang.hitch(this, function(name, oldValue, value) {
                        this.swap_league_select_db('league_select_id', value);
                    })
                );
            },
            // function to create radio button selects for  db_type
            // ref https://github.com/kriszyp/put-selector for put selector
            // also reference
            // http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
            // http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
            create_dbtype_radiobtn: function(topdiv_node, div1_radio_id, div2_radio_id, init_db_type, callback_context, radio1_callback, radio2_callback, league_select_id) {
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
                put(topdiv_node, "span", "Select Schedule Type:");
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
                    div1_radio_node = put(topdiv_node,
                        "div[id=$]", div1_radio_id);
                    put(topdiv_node,
                        "label.label_box[for=$]", div1_radio_id,
                        "Round Robin");
                    div1_radio = new RadioButton({
                        name:'db_type',
                        value:'rrdb',
                        checked:radio1_flag,
                        style:"margin-left:5px",
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
                } else {
                    // see comment above on why byId is used instead of
                    // byNode
                    div2_radio = registry.byId(div2_radio_id);
                }
            },
            // create select dropdown
            // programmatic creation of enclosing node and then widget itself
            create_league_select: function(topdiv_node, lselect_id, info_obj, init_db_type, init_colname) {
                var db_type = (init_db_type == "") ?
                    constant.default_db_type:init_db_type;
                var league_select = null;
                var select_node = dom.byId(lselect_id);
                if (!select_node) {
                    put(topdiv_node,
                        "label.label_box[for=$][style=margin-left:50px]", lselect_id, "Select League");
                    select_node = put(topdiv_node,
                        "select[id=$][name=league_select]", lselect_id);
                    var league_select = new Select({
                        name:'league_select',
                        //store:dbselect_store,
                        //labelAttr:"name",
                        onChange: lang.hitch(this, function(evt) {
                            this.getname_list(evt, db_type, info_obj);
                        })
                    }, select_node);
                    args_obj = {db_type:db_type, label_str:'Select League',
                                config_status:true, init_colname:init_colname};
                    var option_list = this.storeutil_obj.getLabelDropDown_list(args_obj);
                    league_select.addOption(option_list);
                    league_select.startup();
                } else {
                    // we can use by Node here as both node and widget are selects
                    league_select = registry.byNode(select_node);
                }
            },
            // get list of items in db specified by db_type from server
            // collection name is the event of calling onChange event handler
            getname_list: function(colname, db_type, info_obj) {
                var query_obj = {db_type:db_type};
                // note {colname:colname} is the options_obj obj passed directly
                // to the callback function create_divstr_list
                // we want to pass the colname back to the callback so that the colname
                // can be attached to the fieldinfo data when it is saved to the
                // local store and also sent back to the server
                var options_obj = {colname:colname, info_obj:info_obj};
                this.server_interface.getServerData(
                    'get_dbcol/'+db_type+'/'+colname,
                    lang.hitch(this, this.create_divstr_list), query_obj,
                    options_obj);
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
                var data_list = server_data[constant.serverdata_key];
                var config_status = server_data[constant.serverstatus_key];
                var colname = options_obj.colname; // collection name for divinfo
                var db_type = options_obj.db_type; // db_type for divstr
                var info_obj = options_obj.info_obj; // where to return colname and db_type info
                // config_status below should always be 1 as the db's are selected
                // from a list that includes only fully complete configurations
                if (config_status) {
                    var divstr_list = arrayUtil.map(data_list,
                        function(item, index) {
                            // return both the divstr (string) and div_id value
                            // value used as the value for the checkbox in the fieldinfo grid dropdown
                            return {'divstr':item.div_age + item.div_gen,
                                'div_id':item.div_id};
                        })
                    // save divinfo obj information that is attached to the current
                    // fieldinfo obj
                    info_obj.setdivstr_obj(colname, db_type);
                    baseinfoSingleton.watch_obj.set('divstr_list', divstr_list);
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
                    this.start_dtbox = registry.byNode(start_dtbox_node);
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
                    this.end_dtbox = registry.byNode(end_dtbox_node);
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
                    this.sl_spinner = registry.byNode(sl_spinner_node);
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
                        class:"primary",
                        onClick: lang.hitch(this, function(evt) {
                            //sdbtn_status_span.innerHTML = "Season Dates Saved";
                            this.getSeasonDatesFromInput(evt);
                        })
                    }, sdbtn_node);
                    sdbtn.startup();
                    put(topdiv_node, "br, br");
                } else {
                    sdbtn = registry.byNode(sdbtn_node);
                }
            },
            getSeasonDatesFromInput: function(event) {
                var seasonstart_date = this.start_dtbox.get("value");
                var seasonend_date = this.end_dtbox.get("value");
                var season_len = this.sl_spinner.get("value");
                baseinfoSingleton.watch_obj.set('numweeks', season_len);
            },
        })
    })
