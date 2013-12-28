define(["dbootstrap", "dojo/dom", "dojo/dom-style", "dojo/_base/declare","dojo/_base/lang", "dojo/date", "dojo/store/Observable","dojo/store/Memory", "dijit/registry","dgrid/editor", "LeagueScheduler/baseinfoSingleton", "dijit/form/TimeTextBox", "dijit/form/DateTextBox", "dijit/form/Button", "put-selector/put", "dojox/calendar/Calendar", "dojo/domReady!"],
       function(dbootstrap, dom, domStyle, declare, lang, date, Observable, Memory, registry, editor, baseinfoSingleton, TimeTextBox, DateTextBox, Button, put, Calendar){
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
			fieldnum:0, calendar_id:0, storeobj_list:null, calendar_store:null,
			fieldevent_reg:null, eventdate_reg:null,
			starttime_reg:null, endtime_reg:null,
			datetimeset_handle:null, datetimedel_handle:null,
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
				var form_dom = baseinfoSingleton.get_visible_form_dom();
				if (form_dom) {
					baseinfoSingleton.reset_visible_form_dom();
					this.schedutil_obj.makeInvisible(form_dom);
				}
				this.server_interface.getServerData("get_fieldcol/"+item,
					lang.hitch(this.schedutil_obj, this.schedutil_obj.createEditGrid), null, options_obj);
			},
			getInitialList: function(fieldnum) {
				// http://dojo-toolkit.33424.n3.nabble.com/1-9-dijit-form-TimeTextBox-visibleRange-bug-td3997566.html
				this.fieldnum = fieldnum;
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
					                    start_time:"", end_time:"", dates:"Config Field "+i});
//					                    start_time: today_9am.toLocaleTimeString(),
//					                    end_time:today_5pm.toLocaleTimeString()});
				}
				return fieldinfo_list;
			},
			processcell_click: function(object) {
				console.log('processcell');
			},
			// ref http://dojotoolkit.org/reference-guide/1.9/dojox/calendar.html
			// for dojox calendar specifics
			// also check api for for dojox/calendar/Calendar
			edit_calendar: function(row_id) {
				// technically the form_dom covers the parent Container that encloses both the form and the calendar div
				// to make border container use visibility property instead of display
				// property, as usage of latter (inline, block, any other property)
				// makes panes under the bordercontainer overlap when the second pane is a dynamically created widget (like the dojox calendar)
				dom.byId("borderContainer").style.visibility = 'visible';
				// create drop down to select (either) field
				var fieldselect_reg = registry.byId("fieldselect_id");
				var fieldselect_list = new Array();
				for (var i = 1; i < this.fieldnum+1; i++) {
					fieldselect_list.push({label:'Field '+i, value:i, selected:false});
				}
				fieldselect_list[row_id-1].selected = true;
				fieldselect_reg.addOption(fieldselect_list);
				// set registers for field time parameters entry
				this.fieldevent_reg = registry.byId("fieldevent_id");
				this.eventdate_reg = registry.byId("eventdate_id");
				this.starttime_reg = registry.byId("starttime_id");
				this.endtime_reg = registry.byId("endtime_id");

				var datetimeset_reg = registry.byId("datetimeset_btn");
				// note use of third parameter (optional arg to event handler) to lang.hitch
				if (this.datetimeset_handle) {
					this.datetimeset_handle.remove();
				}
				this.datetimeset_handle = datetimeset_reg.on("click",
					lang.hitch(this, this.datetimeset_submit, row_id));
				var today = new Date();
				var data_obj = null;
				/*
				if (this.newschedulerbase_obj) {
					data_obj = {id:0, summary:"Calendar 1",
						startTime:this.newschedulerbase_obj.seasonstart_date,
						endTime:this.newschedulerbase_obj.seasonend_date,
						calendar: "Calendar2"}
				} else {
					data_obj = {id:0, summary:"Calendar 1",
						startTime:date.add(today,"month",-1),
						endTime:date.add(today,"year",1),
						calendar: "Calendar2"}
				}
				*/
				this.storeobj_list = new Array();
				this.calendar_store = new Observable(new Memory({data:this.storeobj_list}));
				var calendar = new Calendar({
					dateInterval: "day",
					date: today,
					store: this.calendar_store,
					style: "position:inherit;width:600px;height:600px",
					cssClassFunc: function(item) {
						return item.calendar;
					}
				}, "calendarGrid_id");
				calendar.startup();
				calendar.set("createOnGridClick", true);
				calendar.set("createItemFunc", this.createItem);
				calendar.on("itemClick", lang.hitch(this,this.itemProcess));
			},
			createItem: function(view, date, event) {
				console.log('ok item');
			},
			datetimeset_submit: function(row_id, event) {
				var fieldevent_str = this.fieldevent_reg.get("value");
				/*
				var startdate_reg = registry.byId("startdate_id");
				var enddate_reg = registry.byId("enddate_id");
				// get respective Date objects
				var startdate = startdate_reg.get("value");
				var enddate = enddate_reg.get("value");
				*/
				// get respective Date/Time strings
				var eventdate_str = this.eventdate_reg.get("value").toDateString();
				var starttime_str = this.starttime_reg.get("value").toTimeString();
				var endtime_str = this.endtime_reg.get("value").toTimeString();
				var start_datetime_obj = new Date(eventdate_str+' '+
					starttime_str);
				var end_datetime_obj = new Date(eventdate_str+' '+
					endtime_str);
				if (date.compare(end_datetime_obj, start_datetime_obj) > 0) {
					// after checking end date is later than start time
					var overlapped_list = this.calendar_store.query(function(object){
						return date.compare(start_datetime_obj,
							object.startTime, "date") == 0 &&
							date.compare(end_datetime_obj,
							object.endTime, "date") == 0;
					}).filter(function(object) {
						//ref http://stackoverflow.com/questions/325933/determine-whether-two-date-ranges-overlap
						// http://stackoverflow.com/questions/13387490/determining-if-two-time-ranges-overlap-at-any-point
						// overlap happens when
						// (StartA <= EndB) and (EndA >= StartB)
						// 'A'suffix comes from start_datetime_obj and end_datetime_obj function variables
						// 'B'suffix is from object
						return date.compare(start_datetime_obj,
							object.endTime,"time") < 0 &&
							date.compare(end_datetime_obj, object.startTime,
								"time") > 0;
					})
					if (!overlapped_list.length) {
						// no time overlap detected
						var data_obj = {id:this.calendar_id,
							// tried to put in newline to break the string below,
							// but it appears that text in calendar item doesn't
							// accept newline char
							fieldevent_str:fieldevent_str,
							summary:"Evt"+row_id+':'+fieldevent_str+' '+
								"Block:"+this.calendar_id,
							startTime:start_datetime_obj, endTime:end_datetime_obj,
							calendar:"Calendar"+row_id};
						this.calendar_store.add(data_obj);
						this.calendar_id++;
					} else {
						alert("time overlap, reselect time, or change event");
					}
				} else {
					alert("end time must be later than start timse");
				}
			},
			itemProcess: function(event) {
				var select_id = event.item.id;
				this.calendar_store.query({id:select_id}
					).forEach(lang.hitch(this,function(obj) {
						var start_datetime = obj.startTime;
						var end_datetime = obj.endTime;
						this.fieldevent_reg.set('value', obj.fieldevent_str);
						this.eventdate_reg.set('value', start_datetime);
						this.starttime_reg.set('value', start_datetime);
						this.endtime_reg.set('value', end_datetime);
						var datetimedel_reg = registry.byId("datetimedel_btn");
						// note use of third parameter (optional arg to event handler) to lang.hitch
						if (this.datetimedel_handle) {
							this.datetimedel_handle.remove();
						}
						this.datetimedel_handle = datetimedel_reg.on("click",
							lang.hitch(this, this.datetimedel_submit, obj.id));
					}));
			},
			datetimedel_submit: function(id, event) {
				this.calendar_store.remove(id);
			}
		});
});
