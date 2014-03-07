/* Utility functions to generate widgets and widget features
*/
define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
    "dojo/_base/array", "dojo/Stateful", "dojo/store/Memory", "dijit/registry",
    "dijit/form/RadioButton", "dijit/form/Select",
    "put-selector/put", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
    function(dbootstrap, dom, declare, lang, arrayUtil, Stateful, Memory,
        registry, RadioButton, Select, put, baseinfoSingleton) {
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
            server_interface:null,
            constructor: function(args) {
                lang.mixin(this, args);
                this.watch_obj = new Watch_class();
                this.watch_obj.watch("db_type",
                    lang.hitch(this, function(name, oldValue, value) {
                        this.swap_league_select_db('leagueselect_id', value);
                    })
                );
            },
            // function to create radio button selects for  db_type
            // ref https://github.com/kriszyp/put-selector for put selector
            // also reference
            // http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
            // http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
            create_dbtype_radiobtn: function(topdiv_node, div1_radio_id, div2_radio_id) {
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
                        style:"margin-left:5px",
                        onChange: lang.hitch(this, function(evt) {
                            if (evt) {
                                this.watch_obj.set('db_type', 'rrdb');
                            }
                        })
                    }, div1_radio_node);
                    div1_radio.startup();
                } else {
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
                        onChange: lang.hitch(this, function(evt) {
                            if (evt) {
                                this.watch_obj.set('db_type', 'tourndb');
                            }
                        })
                    }, div2_radio_node);
                    div2_radio.startup();
                } else {
                    div2_radio = registry.byId(div2_radio_id);
                }
                if (constant.default_db_type == 'rrdb') {
                    div1_radio.set("checked", true);
                    //this.watch_obj.set('db_type', 'rrdb');
                } else {
                    div2_radio.set("checked", true);
                    //this.watch_obj.set('db_type', 'tourndb');
                }
            },
            // create select dropdown
            // programmatic creation of enclosing node and then widget itself
            create_league_select: function(topdiv_node, lselect_id, db_type) {
                var db_type = (db_type == 'default') ?
                    constant.default_db_type:db_type;
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
                            var name_list = this.getname_list(evt, db_type);
                        })
                    }, select_node);
                    args_obj = {db_type:db_type, label_str:'Select League',
                                config_status:true};
                    var option_list = this.storeutil_obj.getLabelDropDown_list(args_obj);
                    league_select.addOption(option_list);
                    league_select.startup();
                } else {
                    // we can use by Node here as both node and widget are selects
                    league_select = registry.byNode(select_node);
                }
            },
            // get list of items in db specified by db_type from server
            getname_list: function(colname, db_type) {
                var query_obj = {db_type:db_type};
                this.server_interface.getServerData('get_dbcol/'+colname,
                    lang.hitch(this, this.create_divstr_list), query_obj);
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
            create_divstr_list: function(server_data) {
                var data_list = server_data[constant.serverdata_key];
                var config_status = server_data[constant.serverstatus_key];
                // config_status below should always be 1 as the db's are selected
                // from a list that includes only fully complete configurations
                if (config_status) {
                    var divstr_list = arrayUtil.map(data_list,
                        function(item, index) {
                            return item.div_age + item.div_gen;
                        })
                    baseinfoSingleton.watch_obj.set('divstr_list', divstr_list);
                }
            }
        })
    })
