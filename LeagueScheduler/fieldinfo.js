define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare","dojo/_base/lang", "dojo/date", "dojo/store/Observable","dojo/store/Memory",
	"dojo/_base/array",
	"dijit/registry","dgrid/editor",
	"LeagueScheduler/baseinfoSingleton", "LeagueScheduler/newscheduler",
	"dijit/form/TimeTextBox", "dijit/form/DateTextBox", "dijit/form/DropDownButton", "dijit/TooltipDialog", "dijit/form/CheckBox", "dijit/form/Button",
	"put-selector/put", "dojox/calendar/Calendar", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, date, Observable, Memory, arrayUtil,
		registry, editor, baseinfoSingleton, newscheduler,
		TimeTextBox, DateTextBox, DropDownButton, TooltipDialog, CheckBox, button,
		put, Calendar){
		return declare(null, {
 			server_interface:null, schedutil_obj:null, newschedulerbase_obj:null,
 			divinfo_obj:null,
			fieldnum:0, calendar_id:0, calendar_store:null,
			fieldselect_reg:null, fieldevent_reg:null, eventdate_reg:null,
			starttime_reg:null, endtime_reg:null,
			starttime_handle:null,
			datetimeset_handle:null, datetimedel_handle:null,
			calendar:null,
			field_id:0, fieldselect_handle:null,
			dupfieldselect_reg:null,
			divstr_list:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.divstr_list = new Array();
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
					field_id: "Field ID",
					field_name: editor({label:"Name", autoSave:true},"text","dblclick"),
					primaryuse: {label:"Primary Use",
						renderCell: lang.hitch(this, this.actionRenderCell)
					},
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
					dates: {label:"Config Dates"}
				};
				return columnsdef_obj;
			},
			initialize: function(arg_obj) {
				// get divinfo information here
				if (this.divinfo_obj.currentdivinfo_name) {
					this.divinfo_obj.getBasicServerDBDivInfo(this, this.createDivSelectDialog);
				}
				var form_name = "fieldconfig_form_id";
				var form_reg = registry.byId(form_name);
				var form_dom = dom.byId(form_name);
				var input_name = "fieldlistname_input_id";
				var input_reg = registry.byId(input_name);
				var fieldnum_reg = registry.byId("fieldnum_input_id");
				var newFieldGroup = new newscheduler({dbname_reg:input_reg,
					form_dom:form_dom, form_reg:form_reg,
					entrynum_reg:fieldnum_reg,
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					callback: lang.hitch(this.schedutil_obj,this.schedutil_obj.regenAddFieldDBCollection_smenu),
					info_obj:this,
					idproperty:'field_id',
					server_path:"create_newfieldcol/",
					server_key:'fieldinfo_data',
					cellselect_flag:true,
					text_node_str: 'Field List Name',
					updatebtn_str:'Update Field Info'});
				newFieldGroup.showConfig();
			},
			set_schedutil_obj: function(obj) {
				this.schedutil_obj = obj;
			},
			getServerDBFieldInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				var item = options_obj.item;
				options_obj.info_obj = this;
				options_obj.idproperty = 'field_id';
				options_obj.server_path = "create_newfieldcol/";
				options_obj.server_key = 'fieldinfo_data';
				options_obj.cellselect_flag = true;
				options_obj.text_node_str = "Field List Name";
				options_obj.updatebtn_str = 'Update Field Info';
				// key for response object from server
				options_obj.serverdata_key = 'fieldinfo_list';
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
				for (var i = 1; i < fieldnum+1; i++) {
					fieldinfo_list.push({field_id:i, field_name:"",
						primaryuse:"Config primary "+i, start_time:"", end_time:"",
						dates:"Config Venue "+i});
				}
				return fieldinfo_list;
			},
			processcell_click: function(object) {
				console.log('processcell');
			},
			// ref http://dojotoolkit.org/reference-guide/1.9/dojox/calendar.html
			// for dojox calendar specifics
			// also check api for for dojox/calendar/Calendar
			edit_calendar: function(row_id, colname) {
				var field_index = row_id-1;
				var oldfield_index = this.field_id-1;
				this.field_id = row_id;
				// technically the form_dom covers the parent Container that encloses both the form and the calendar div
				// to make border container use visibility property instead of display
				// property, as usage of latter (inline, block, any other property)
				// makes panes under the bordercontainer overlap when the second pane is a dynamically created widget (like the dojox calendar)
				dom.byId("borderContainer").style.visibility = 'visible';
				// create drop down to select (either) field
				if (this.fieldselect_reg) {
					// if select already exists,
					// look at dijit/form/Select api for getOptions, updateOption
					// parameters
					// ref http://dojotoolkit.org/documentation/tutorials/1.9/selects_using_stores/
					// (section without stores) to properly configure select widget
					// programmatically
					// also see same reference - apparently select widget
					// needs to be started up again if options change
					// (just add or delete? or change in value also?)
					var cur_option = this.fieldselect_reg.getOptions(oldfield_index);
					cur_option.selected = false;
					// retrieved option is a pointer to the obtion object in the widget
					// no need to call updateOption (it actually confuses the update)
					// make sure to call widget startup()
					//this.fieldselect_reg.updateOption(cur_option);
					cur_option = this.fieldselect_reg.getOptions(field_index);
					cur_option.selected = true;
					this.fieldselect_reg.startup();
					//this.calendar.currentView.invalidateLayout();
					// send store info to server
					// first make store query and get count
					/*
					if (this.calendar_store) {
						var fieldtime_obj = this.calendar_store.query({});
						if (fieldtime_obj.total > 0) {
							fieldtime_str = JSON.stringify(fieldtime_obj);
							// note REST parameter has to be this.field_id and not row_id as row_id indicates current field_id where paramenters have yet to be entered.
							this.server_interface.getServerData("update_fieldtimes/"+colname,
								this.server_interface.server_ack,
								{fieldtime_str:fieldtime_str});
						}
					}
					*/
				} else {
					// if field select widget does not exist, create one.
					this.fieldselect_reg = registry.byId("fieldselect_id");
					var fieldselect_list = new Array();
					for (var i = 1; i < this.fieldnum+1; i++) {
						fieldselect_list.push({label:'Field '+i, value:i, selected:false});
					}
					fieldselect_list[field_index].selected = true;
					this.fieldselect_reg.addOption(fieldselect_list);
					// add field list for schedule duplication select drop-down
					var dupfieldselect_list = lang.clone(fieldselect_list);
					dupfieldselect_list.push({label:'All Fields', value:this.fieldnum+1, selected:false});
					this.dupfieldselect_reg = registry.byId("dupfieldselect_id");
					this.dupfieldselect_reg.addOption(dupfieldselect_list);
					//this.dupfieldselect_reg.startup();
					if (this.fieldselect_handle)
						this.fieldselect_handle.remove();
					this.fieldselect_handle = this.fieldselect_reg.on("change",
						lang.hitch(this, function(event) {
							this.field_id = event;
						})
					);
					this.fieldselect_reg.startup();
					// set registers for field time parameters entry
					this.fieldevent_reg = registry.byId("fieldevent_id");
					this.eventdate_reg = registry.byId("eventdate_id");
					this.starttime_reg = registry.byId("starttime_id");
					if (this.starttime_handle) {
						this.starttime_handle.remove();
					}
					this.starttime_handle = this.starttime_reg.on("change",
						lang.hitch(this, function (event) {
							this.endtime_reg.set('value',
								date.add(event, 'hour', 1));
						}));
					this.endtime_reg = registry.byId("endtime_id");
					var datetimeset_reg = registry.byId("datetimeset_btn");
					if (this.datetimeset_handle) {
						this.datetimeset_handle.remove();
					}
					this.datetimeset_handle = datetimeset_reg.on("click",
						lang.hitch(this, this.datetimeset_submit));
					var today = new Date();
					this.eventdate_reg.set('value', today);
					this.eventdate_reg.startup();
					// setup titlepane widget to generate event when it opens
					var duptitlepane_reg = registry.byId("duptitlepane_id");
					duptitlepane_reg.on("show", function(event){
						console.log("dupfield");
					});
					this.calendar_store = new Observable(new Memory({data:new Array()}));
					this.calendar = new Calendar({
						dateInterval: "day",
						date: today,
						store: this.calendar_store,
						style: "position:inherit;width:600px;height:600px",
						cssClassFunc: function(item) {
							return item.calendar;
						}
					}, "calendarGrid_id");
					this.calendar.startup();
					this.calendar.set("createOnGridClick", true);
					this.calendar.set("createItemFunc", this.createItem);
					this.calendar.on("itemClick", lang.hitch(this,this.clickedItemProcess));
				}
			},
			createItem: function(view, date, event) {
				console.log('ok item');
			},
			datetimeset_submit: function(event) {
				var fieldevent_str = this.fieldevent_reg.get("value");
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
					// using the store query+filter call below, attempt to find
					// time-overlapped events on the same field.
					var overlapped_list = this.calendar_store.query(lang.hitch(this, function(object){
						return date.compare(start_datetime_obj,
							object.startTime, "date") == 0 &&
							date.compare(end_datetime_obj,
							object.endTime, "date") == 0 &&
							(object.field_id == this.field_id);
					})).filter(function(object) {
						//ref http://stackoverflow.com/questions/325933/determine-whether-two-date-ranges-overlap
						// http://stackoverflow.com/questions/13387490/determining-if-two-time-ranges-overlap-at-any-point
						// overlap happens when
						// (StartA <= EndB) and (EndA >= StartB)
						// 'A'suffix comes from start_datetime_obj and end_datetime_obj function variables
						// 'B'suffix is from object
						// if object field_id is different than selected field id
						// then no need to worry about time overlap
						return (date.compare(start_datetime_obj,
							object.endTime,"time") < 0 &&
							date.compare(end_datetime_obj, object.startTime,
								"time") > 0);
					})
					if (!overlapped_list.length) {
						// no time overlap detected
						var data_obj = {id:this.calendar_id,
							// tried to put in newline to break the string below,
							// but it appears that text in calendar item doesn't
							// accept newline char
							// note we can also use this.field_id in lieu of passed
							// paramemter row_id
							// calendar key needed to cssClassFunc to retrieve style
							// for Calendar element
							fieldevent_str:fieldevent_str,
							summary:"Field"+this.field_id+':'+fieldevent_str+' '+
								"Block:"+this.calendar_id,
							startTime:start_datetime_obj, endTime:end_datetime_obj,
							field_id:this.field_id,
							calendar:'Calendar'+this.field_id};
						this.calendar_store.add(data_obj);
						this.calendar_id++;
					} else {
						alert("time overlap, reselect time, or change event");
					}
				} else {
					alert("end time must be later than start timse");
				}
			},
			clickedItemProcess: function(event) {
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
			},
			actionRenderCell: function(object, data, node) {
				var TDialog = null;
				if (this.divinfo_obj.currentdivinfo_name) {
					//http://stackoverflow.com/questions/13444162/widgets-inside-dojo-dgrid
					var content_str = "";
					var field_id = object.field_id;
					var checkboxid_list = new Array();
					arrayUtil.forEach(this.divstr_list, function(divstr, index) {
						var idstr = "checkbox"+divstr+field_id+"_id";
						content_str += '<input type="checkbox" data-dojo-type="dijit/form/CheckBox" style="color:green" id="'+idstr+
						'" value="'+divstr+'"><label for="'+idstr+'">'+divstr+'</label><br>';
						checkboxid_list.push(idstr);
					});
					var button_id = 'tdialogbtn'+field_id+'_id';
					content_str += '<button data-dojo-type="dijit/form/Button" type="submit" id="'+button_id+'">Save</button>'
					TDialog = new TooltipDialog({
						id:"tooltip"+object.field_id,
						content: content_str
		    		});
		    		var tdialogprop_obj = {field_id:field_id,
		    			checkboxid_list:checkboxid_list};
		    		//this.tdialogprop_list.push({field_id:field_id,
		    		//	checkboxid_list:checkboxid_list});
		    		var button_reg = registry.byId(button_id);
		    		button_reg.on("click",
		    			lang.hitch(this,this.dialogbtn_process, tdialogprop_obj));
		    	} else {
		    		TDialog = new TooltipDialog({
		    			content:"Select Database using Select Config->Division Info"
		    		})
		    	}
				//myDialog.startup();
				var dropdown_btn = new DropDownButton({
					label:"Config",
					dropDown:TDialog,
				});
				node.appendChild(dropdown_btn.domNode);
				//dropdown_btn.startup();
			return dropdown_btn;
			},
			dialogbtn_process: function(tdialogprop_obj, event) {
				var field_id = tdialogprop_obj.field_id;
				var checkboxid_list = tdialogprop_obj.checkboxid_list;
				console.log('field_id='+field_id);
				console.log('idlist='+checkboxid_list);
				arrayUtil.forEach(checkboxid_list, function(checkboxid, index) {

				})

			},
			createDivSelectDialog: function(server_data) {
				arrayUtil.forEach(server_data.divinfo_list, function(item, index) {
					this.divstr_list.push(item.div_age + item.div_gen);
				}, this);
			},
			cleanup: function() {
				if (this.starttime_handle)
					this.starttime_handle.remove();
				if (this.datetimeset_handle)
					this.datetimeset_handle.remove();
				if (this.datetimedel_handle)
					this.datetimedel_handle.remove();
				if (this.fieldselect_handle)
					this.fieldselect_handle.remove();
				this.calendar.destroyRecursive();
				//delete this.calendar;
				delete this.calendar_store;
			}
		});
});
