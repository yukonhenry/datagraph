define(["dojo/_base/declare","dojo/_base/lang", "dgrid/editor", "LeagueScheduler/baseinfoSingleton", "dijit/form/TimeTextBox",
       "put-selector/put", "dojo/domReady!"], function(declare, lang, editor, baseinfoSingleton, TimeTextBox, put){
		return declare(null, {
			columnsdef_obj : {
				field_id: "Field ID",
				field_name: editor({label:"Name", field:"field_name", autoSave:true},"text","dblclick"),
				primaryuse_str: editor({label:"Used by", field:"primaryuse_str", autoSave:true}, "text", "dblclick"),
				start_time: editor({label:"Start Time", field:"start_time", autoSave:true,
					editorArgs:{ value: new Date(),
						constraints: {
							timePattern: 'HH:mm:ss',
							clickableIncrement: 'T00:15:00',
							visibleIncrement: 'T00:15:00',
							visibleRange: 'T01:00:00'
							//min: 'T08:00:00',
							//max:'T18:00:00'
						},
					}, /*
					get:function(item) {
						console.log("getitem="+item);
						var new_date = new Date(item.start_time);
						var new_time = new_date.toTimeString();
						return new_time;
					}, */
					renderCell: function(object, value) {
						console.log("renderCell="+object+" "+value);
						return put("div", value?value.toLocaleTimeString():"T08:00:00");
					}
				}, TimeTextBox, "dblclick"),
				end_time: editor({label:"End Time", field:"end_time", autoSave:true}, "text", "dblclick")
			}, server_interface:null, schedutil_obj:null,
			early_time:null, late_time:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			getServerDBFieldInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				var item = options_obj.item;
				options_obj.serverdata_key = 'fieldinfo_list';
				options_obj.idproperty = 'field_id';
				options_obj.server_key = 'fieldinfo_data';
				options_obj.server_path = "create_newfieldcol/";
				if (baseinfoSingleton.get_select_reg()) {
					this.schedutil_obj.makeInvisible(baseinfoSingleton.get_select_dom());
				}
				this.server_interface.getServerData("get_fieldcol/"+item,
					lang.hitch(this.schedutil_obj, this.schedutil_obj.createEditGrid), null, options_obj);
			},
			getInitialList: function(fieldnum) {
				// http://dojo-toolkit.33424.n3.nabble.com/1-9-dijit-form-TimeTextBox-visibleRange-bug-td3997566.html
				var fieldinfo_list = new Array();
				var current_date = new Date();
				var today = new Date();
				var today_9am = new Date(
					today.getYear(), today.getMonth(), today.getDay(),
					9, 0, 0);
				var today_5pm = new Date(
					today.getYear(), today.getMonth(), today.getDay(),
					17, 0, 0);
				for (var i = 1; i < fieldnum+1; i++) {
					fieldinfo_list.push({field_id:i, field_name:"",
					                    primaryuse_str:"",
					                    start_time:"", end_time:""});
//					                    start_time: today_9am.toLocaleTimeString(),
//					                    end_time:today_5pm.toLocaleTimeString()});
				}
				return fieldinfo_list;
			}
		});
});
