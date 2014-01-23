define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare","dojo/_base/lang", "dojo/date", "dojo/store/Observable","dojo/store/Memory",
	"dojo/_base/array",
	"dijit/registry","dgrid/editor",
	"LeagueScheduler/baseinfoSingleton", "LeagueScheduler/newscheduler",
	"dijit/form/TimeTextBox", "dijit/form/DateTextBox", "dijit/form/DropDownButton", "dijit/TooltipDialog", "dijit/form/CheckBox", "dijit/form/Button",
	"put-selector/put", "dojox/calendar/Calendar", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, date, Observable, Memory, arrayUtil,
		registry, editor, baseinfoSingleton, newscheduler,
		TimeTextBox, DateTextBox, DropDownButton, TooltipDialog, CheckBox, Button,
		put, Calendar){
		var constant = {
			infobtn_id:"infoBtnNode_id",
			text_id:"infoTextNode_id",
			idproperty_str:"field_id",
			updatebtn_str:"Update Field Info",
			grid_id:"fieldinfogrid_id",
			text_node_str:'Field List Name',
		};
		return declare(null, {
 			server_interface:null, schedutil_obj:null,
 			divinfo_obj:null, idproperty:constant.idproperty_str,
			fieldnum:0, calendar_id:0, calendar_store:null,
			fieldselect_reg:null, fieldevent_reg:null, eventdate_reg:null,
			starttime_reg:null, endtime_reg:null,
			starttime_handle:null,
			datetimeset_handle:null, datetimedel_handle:null,
			calendar:null,
			field_id:0, fieldselect_handle:null,
			dupfieldselect_reg:null,
			divstr_list:null,
			editgrid_obj:null,
			text_node:null, text_node_str: constant.text_node_str,
			uistackmgr:null, updatebtn_str: constant.updatebtn_str,
			constructor: function(args) {
				lang.mixin(this, args);
				this.divstr_list = new Array();
				this.text_node = dom.byId(constant.text_id);
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
					field_id: "Field ID",
					field_name: editor({label:"Name", autoSave:true},"text","dblclick"),
					primaryuse: {label:"Primary Use",
						renderCell: lang.hitch(this, this.primaryuse_actionRenderCell)
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
					dayweek:{label:"Days of Week",
						renderCell: lang.hitch(this, this.dayweek_actionRenderCell)},
					dates: {label:"Config Dates",
						renderCell: lang.hitch(this, this.dates_actionRenderCell)}
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
				//var form_dom = dom.byId(form_name);
				var input_name = "fieldlistname_input_id";
				var input_reg = registry.byId(input_name);
				var fieldnum_reg = registry.byId("fieldnum_input_id");
				var newFieldGroup = new newscheduler({dbname_reg:input_reg,
					form_reg:form_reg,
					entrynum_reg:fieldnum_reg,
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					callback: lang.hitch(this.schedutil_obj,this.schedutil_obj.regenAddFieldDBCollection_smenu),
					info_obj:this, idproperty:constant.idproperty_str,
					server_path:"create_newfieldcol/",
					server_key:'fieldinfo_data',
					cellselect_flag:true,
					text_node_str: constant.text_node_str,
					grid_id:constant.grid_id,
					text_node:this.text_node,
					updatebtn_str:constant.updatebtn_str,
					uistackmgr:this.uistackmgr
				});
				newFieldGroup.showConfig();
			},
			set_schedutil_obj: function(obj) {
				this.schedutil_obj = obj;
			},
			getServerDBInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				var item = options_obj.item;
				options_obj.info_obj = this;
				options_obj.idproperty = constant.idproperty_str;
				options_obj.server_path = "create_newfieldcol/";
				options_obj.server_key = 'fieldinfo_data';
				options_obj.cellselect_flag = true;
				options_obj.text_node_str = constant.text_node_str;
				// key for response object from server
				options_obj.serverdata_key = 'fieldinfo_list';
				options_obj.grid_id = constant.grid_id;
				options_obj.text_node = this.text_node;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.uistackmgr = this.uistackmgr;
				// do some clean-up
				if (baseinfoSingleton.get_select_reg()) {
					this.schedutil_obj.makeInvisible(baseinfoSingleton.get_select_dom());
				}
				/*
				var form_dom = baseinfoSingleton.get_visible_form_dom();
				if (form_dom) {
					baseinfoSingleton.reset_visible_form_dom();
					this.schedutil_obj.makeInvisible(form_dom);
				} */
				this.server_interface.getServerData("get_fieldcol/"+item,
					lang.hitch(this.schedutil_obj, this.schedutil_obj.createEditGrid), null, options_obj);
			},
			getInitialList: function(fieldnum) {
				// return value defines structure for store for grid
				// http://dojo-toolkit.33424.n3.nabble.com/1-9-dijit-form-TimeTextBox-visibleRange-bug-td3997566.html
				this.fieldnum = fieldnum;
				var fieldinfo_list = new Array();
				for (var i = 1; i < fieldnum+1; i++) {
					fieldinfo_list.push({field_id:i, field_name:"",
						primaryuse:"Config primary "+i, start_time:"", end_time:"",
						dayweek:"", dates:"Config Venue "+i});
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
			primaryuse_actionRenderCell: function(object, data, node) {
				var TDialog = null;
				var field_id = object.field_id;
				if (this.divinfo_obj.currentdivinfo_name) {
					//http://stackoverflow.com/questions/13444162/widgets-inside-dojo-dgrid
					var content_str = "";
					var checkbox_list = new Array();
					arrayUtil.forEach(this.divstr_list, function(divstr, index) {
						var idstr = "checkbox"+divstr+field_id+"_id";
						content_str += '<input type="checkbox" data-dojo-type="dijit/form/CheckBox" style="color:green" id="'+idstr+
						'" value="'+divstr+'"><label for="'+idstr+'">'+divstr+'</label><br>';
						checkbox_list.push(idstr);
					});
					var button_id = 'tdialogbtn'+field_id+'_id';
					content_str += '<button data-dojo-type="dijit/form/Button" type="submit" id="'+button_id+'">Save</button>'
					TDialog = new TooltipDialog({
						id:"tooltip"+field_id,
						content: content_str
		    		});
		    		var tdialogprop_obj = {field_id:field_id,
		    			checkbox_list:checkbox_list};
		    		//this.tdialogprop_list.push({field_id:field_id,
		    		//	checkbox_list:checkbox_list});
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
					id:'fielddropdownbtn'+field_id+'_id'
				});
				node.appendChild(dropdown_btn.domNode);
				//dropdown_btn.startup();
				return dropdown_btn;
			},
			dialogbtn_process: function(tdialogprop_obj, event) {
				var field_id = tdialogprop_obj.field_id;
				var checkbox_list = tdialogprop_obj.checkbox_list;
				var checkboxvalue_str = "";
				arrayUtil.forEach(checkbox_list, function(checkbox_id, index) {
					var checkbox_reg = registry.byId(checkbox_id);
					if (checkbox_reg.get("checked")) {
						checkboxvalue_str += checkbox_reg.get('value')+',';
					}
				})
				// trim off last comma
				// http://stackoverflow.com/questions/952924/javascript-chop-slice-trim-off-last-character-in-string
				checkboxvalue_str = checkboxvalue_str.substring(0, checkboxvalue_str.length-1);
				if (this.editgrid_obj) {
					var store_elem = this.editgrid_obj.schedInfoStore.get(field_id);
					store_elem.primaryuse = checkboxvalue_str;
					this.editgrid_obj.schedInfoStore.put(store_elem);
					// because of trouble using dgrid w observable store, directly update dropdownbtn instead of dgrid cell with checkbox info
					var dropdownbtn_reg = registry.byId("fielddropdownbtn"+field_id+"_id");
					dropdownbtn_reg.set('label', checkboxvalue_str);
					//this.editgrid_obj.schedInfoStore.refresh();
				}
			},
			createDivSelectDialog: function(server_data) {
				arrayUtil.forEach(server_data.divinfo_list, function(item, index) {
					this.divstr_list.push(item.div_age + item.div_gen);
				}, this);
			},
			dates_actionRenderCell: function(object, data, node) {
				var field_id = object.field_id;
				var config_btn = new Button({
					label:"Config Venue"+field_id,
					id:"fielddatesbtn"+field_id+"_id",
					onClick: lang.hitch(this, function() {
						this.edit_calendar(field_id);
					})
				})
				node.appendChild(config_btn.domNode);
				return config_btn;
			},
			dayweek_actionRenderCell: function(object, data, node) {
				var field_id = object.field_id;
				//http://stackoverflow.com/questions/13444162/widgets-inside-dojo-dgrid
				var content_str = "";
				var day_list = ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
				var checkboxid_list = new Array();
				arrayUtil.forEach(day_list, function(day, index) {
					var idstr = day+field_id+"_id";
					content_str += '<input type="checkbox" data-dojo-type="dijit/form/CheckBox" style="color:green" id="'+idstr+
					'" value='+index+'><label for="'+idstr+'">'+day+'</label> ';
					if (index%2)
						content_str += '<br>'
					checkboxid_list.push(idstr);
				});
				var button_id = 'dwdialogbtn'+field_id+'_id';
				content_str += '<br><button data-dojo-type="dijit/form/Button" type="submit" id="'+button_id+'">Save</button>'
				var dwdialog = new TooltipDialog({
					id:"dwtooltip"+field_id,
					content: content_str
	    		});
	    		var dwdialogprop_obj = {field_id:field_id,
	    			checkboxid_list:checkboxid_list, day_list:day_list};
	    		var button_reg = registry.byId(button_id);
	    		button_reg.on("click",
	    			lang.hitch(this,this.dwdialogbtn_process, dwdialogprop_obj));
				//myDialog.startup();
				var dropdown_btn = new DropDownButton({
					label:"Config",
					dropDown:dwdialog,
					id:'dwfielddropdownbtn'+field_id+'_id'
				});
				node.appendChild(dropdown_btn.domNode);
				//dropdown_btn.startup();
				return dropdown_btn;
			},
			dwdialogbtn_process: function(dwdialogprop_obj, event) {
				var field_id = dwdialogprop_obj.field_id;
				var checkboxid_list = dwdialogprop_obj.checkboxid_list;
				var day_list = dwdialogprop_obj.day_list;
				var display_str = "";
				var value_str = "";
				arrayUtil.forEach(checkboxid_list, function(checkbox_id, index) {
					var checkbox_reg = registry.byId(checkbox_id);
					if (checkbox_reg.get("checked")) {
						// create str to display in buttone
						display_str += day_list[index]+',';
						// create str to store (str of integer id elements)
						value_str += checkbox_reg.get("value")+',';
					}
				})
				// trim off last comma
				// http://stackoverflow.com/questions/952924/javascript-chop-slice-trim-off-last-character-in-string
				display_str = display_str.substring(0, display_str.length-1);
				value_str = value_str.substring(0, value_str.length-1);
				if (this.editgrid_obj) {
					var store_elem = this.editgrid_obj.schedInfoStore.get(field_id);
					store_elem.dayweek = value_str;
					this.editgrid_obj.schedInfoStore.put(store_elem);
					// because of trouble using dgrid w observable store, directly update dropdownbtn instead of dgrid cell with checkbox info
					var dwdropdownbtn_reg = registry.byId("dwfielddropdownbtn"+field_id+"_id");
					dwdropdownbtn_reg.set('label', value_str);
					//this.editgrid_obj.schedInfoStore.refresh();
				}
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
