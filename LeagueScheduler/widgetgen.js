/* Utility functions to generate widgets and widget features
*/
define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
    "dojo/_base/array", "dojo/Stateful", "dijit/registry",
    "dijit/form/RadioButton", "dijit/form/Select",
    "put-selector/put","dojo/domReady!"],
    function(dbootstrap, dom, declare, lang, arrayUtil, Stateful, registry, RadioButton, Select, put) {
        var Watch_class = declare([Stateful], {
            db_type:null
        })
        return declare(null, {
            storeutil_obj:null, radio_db_type:null, watch_obj:null,
            constructor: function(args) {
                lang.mixin(this, args);
                this.watch_obj = new Watch_class();
                this.watch_obj.watch("db_type",
                    lang.hitch(this, function(name, oldValue, value) {
                        console.log('new dbtype='+value);
                    })
                )
            },
            // function to create radio button selects for  db_type
            // ref https://github.com/kriszyp/put-selector for put selector
            create_dbtype_radiobtn: function(topdiv_node, div1_radio_id, div2_radio_id) {
                put(topdiv_node, "span", "Select Schedule Type:")
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
                        checked:true,
                        style:"margin-left:5px",
                        onChange: lang.hitch(this, function(evt) {
                            if (evt) {
                                this.watch_obj.set('db_type', 'rrdb');
                            }
                        })
                    }, div1_radio_node);
                    div1_radio.startup();
                } else {
                    div1_radio = registry.byNode(div1_radio_node);
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
                            this.watch_obj.set('db_type', 'tourndb');
                        })
                    }, div2_radio_node);
                    div2_radio.startup();
                } else {
                    div2_radio = registry.byNode(div2_radio_node);
                }
                // initialize watch_obj db_type value
                if (div1_radio.get("checked")) {
                    this.watch_obj.set('db_type', div1_radio.get('value'));
                } else if (div2_radio.get("checked")) {
                    this.watch_obj.set('db_type', div2_radio.get('value'));
                }
            },
            create_league_select: function(topdiv_node, lselect_id, db_type) {
                var league_select = null;
                var select_node = dom.byId(lselect_id);
                if (!select_node) {
                    put(topdiv_node,
                        "label.label_box[for=$][style=margin-left:50px]", lselect_id, "Select League");
                    select_node = put(topdiv_node,
                        "select[id=$][name=league_select]", lselect_id);
                    var dbselect_store = this.storeutil_obj.getselect_store(db_type);
                    var league_select = new Select({
                        name:'league_select',
                        store:dbselect_store,
                        labelAttr:"name",
                        onChange: function(evt) {

                        }
                    }, select_node);
                } else {
                    league_select = registry.byNode(select_node);
                }

            },
        })
    })
