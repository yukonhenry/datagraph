/* Utility functions to generate widgets and widget features
*/
define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
    "dojo/_base/array", "dijit/registry", "dijit/form/RadioButton",
    "put-selector/put","dojo/domReady!"],
    function(dbootstrap, dom, declare, lang, arrayUtil, registry, RadioButton, put) {
        return declare(null, {
            constructor: function(args) {
                lang.mixin(this, args);
            },
            // function to create radio button selects for  db_type
            // ref https://github.com/kriszyp/put-selector for put selector
            create_dbtype_radiobtn: function(topdiv_node, div1_radio_id, div2_radio_id) {
                put(topdiv_node, "span", "Select Schedule Type:")
                var div1_radio_node = dom.byId(div1_radio_id);
                if (!div1_radio_node) {
                    div1_radio_node = put(topdiv_node,
                        "div[id=$]", div1_radio_id);
                    put(topdiv_node,
                        "label.label_box[for=$]", div1_radio_id,
                        "Round Robin");
                    var div1_radio = new RadioButton({
                        name:'db_type',
                        value:'rrdb',
                        checked:true,
                        style:"margin-left:5px"
                    }, div1_radio_node);
                } else {
                    div1_radio = registry.byNode(div1_radio_node);
                }
                var div2_radio_node = dom.byId(div2_radio_id);
                if (!div2_radio_node) {
                    div2_radio_node = put(topdiv_node,
                        "div[id=$]", div2_radio_id);
                    put(topdiv_node,
                        "label.label_box[for=$]", div2_radio_id,
                        "Tournament");
                    var div2_radio = new RadioButton({
                        name:'db_type',
                        value:'tourndb',
                        style:"margin-left:10px"
                    }, div2_radio_node);
                } else {
                    div2_radio = registry.byNode(div2_radio_node);
                }
                put(topdiv_node, "br, br");
                if (div1_radio.get("checked")) {
                    console.log("radio 1 checked")
                } else if (div2_radio.get("checked")) {
                    console.log("radio2 checked");
                }
            },
            create_league_select: function(topdiv_node, lselect_id, db_type) {
                var select_node = dom.byId(lselect_id);
                if (!select_node) {
                    put(topdiv_node,
                        "label.label_box[for=$]", lselect_id, "Select League");
                    select_node = put(topdiv_node,
                        "select[id=$][name=league_select]", lselect_id);
                    var league_select = new Select({
                        name:'league_select',
                        onChange: function(evt) {

                        }
                    }, select_node);
                } else {
                    select_node = registry.byNode(select_node);
                }
            }
        })
    })
