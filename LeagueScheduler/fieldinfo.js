define(["dojo/_base/declare","dojo/_base/lang", "dgrid/editor", "LeagueScheduler/baseinfoSingleton", "dijit/form/TimeTextBox", "dijit/form/DateTextBox", "dijit/form/Button", "put-selector/put", "dojox/calendar/Calendar", "dojo/domReady!"],
       function(declare, lang, editor, baseinfoSingleton, TimeTextBox, DateTextBox, Button, put, Calendar){
		return declare(null, {
			columnsdef_obj : {
				field_id: "Field ID",
				field_name: editor({label:"Name", field:"field_name", autoSave:true},"text","dblclick"),
				primaryuse_str: editor({label:"Used by", field:"primaryuse_str", autoSave:true}, "text", "dblclick"),
				start_time: editor({label:"Start Time", field:"start_time", autoSave:true, columntype:false,
					editorArgs:{
						constraints: {
							timePattern: 'HH:mm:ss',
							clickableIncrement: 'T00:15:00',
							visibleIncrement: 'T00:15:00',
							visibleRange: 'T01:00:00'
							//min: 'T08:00:00',
							//max:'T18:00:00'
						},
					},
					/*
					set: function(item) {
						var column_obj = item[this.columntype];
						if (typeof column_obj == "string")
							return column_obj;
						else {
							var time_str = column_obj.toLocaleTimeString();
							console.log("setitem="+time_str);
							return time_str;
						}
					},*/
					set: function(item) {
						if (this.columntype) {
							var column_obj = item.start_time;
							var time_str = column_obj.toLocaleTimeString();
							console.log("setitem="+time_str);
							this.columntype = false;
							return time_str;
						}
					},
					renderCell: function(object, value) {
						if (typeof value == "string")
							return put("div", value);
						else {
							// if the type if a Date object (only type of obj) possible
							// here, extract (local) timestring
							return put("div", value?value.toLocaleTimeString():"");
						}
					}
				}, TimeTextBox, "dblclick"),
				end_time: editor({label:"End Time", field:"end_time",
				                 autoSave:true, columntype:false,
					editorArgs:{
						constraints: {
							timePattern: 'HH:mm:ss',
							clickableIncrement: 'T00:15:00',
							visibleIncrement: 'T00:15:00',
							visibleRange: 'T01:00:00'
						},
					},
					set: function(item) {
						if (this.columntype) {
							var column_obj = item.end_time;
							var time_str = column_obj.toLocaleTimeString();
							console.log("end setitem="+time_str);
							this.columntype = false;
							return time_str;
						}
					},
					renderCell: function(object, value) {
						if (typeof value == "string")
							return put("div", value);
						else {
							// if the type if a Date object (only type of obj) possible
							// here, extract (local) timestring
							return put("div", value?value.toLocaleTimeString():"");
						}
					},
				}, TimeTextBox, "dblclick"),
				// http://stackoverflow.com/questions/13444162/widgets-inside-dojo-dgrid
				/*
				dates: {label:"Select Dates", field:"dates",
					renderCell: function(object, value) {
						var button = new Button({label:"dates",
							onClick: function() {
								var onclick_direct = lang.hitch(this, this.processcell_click);
								onclick_direct(object);
							}
						})
						return button.domNode;
					}
				} */
				dates: {label:"Config Dates", field:"dates"}
			}, server_interface:null, schedutil_obj:null, newschedulerbase_obj:null,
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
				options_obj.cellselect_flag = true;
				options_obj.info_obj = this;
				options_obj.text_node_str = "Field List Name";
				// do some clean-up
				if (baseinfoSingleton.get_select_reg()) {
					this.schedutil_obj.makeInvisible(baseinfoSingleton.get_select_dom());
				}
				var form_name = baseinfoSingleton.get_visible_form_name();
				if (form_name) {
					baseinfoSingleton.reset_visible_form_name();
					this.schedutil_obj.makeInvisible(form_name);
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
					                    start_time:"", end_time:"", dates:"Calendar"});
//					                    start_time: today_9am.toLocaleTimeString(),
//					                    end_time:today_5pm.toLocaleTimeString()});
				}
				return fieldinfo_list;
			},
			processcell_click: function(object) {
				console.log('processcell');
			},
			edit_calendar: function(row_id) {
				var calendar = new Calendar({
					dateInterval: "day",
					date: new Date(),
					style: "position:relative;width:600px;height:600px"
				}, "calendarGrid");
				calendar.startup();
			}
		});
});
