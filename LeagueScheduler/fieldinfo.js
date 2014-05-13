define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare",
	"dojo/_base/lang", "dojo/date", "dojo/store/Observable","dojo/store/Memory",
	"dojo/_base/array",
	"dijit/registry","dgrid/editor", "LeagueScheduler/baseinfo",
	"LeagueScheduler/baseinfoSingleton", "LeagueScheduler/widgetgen",
	"dijit/form/TimeTextBox", "dijit/form/DateTextBox", "dijit/form/Select",
	"dijit/form/DropDownButton", "dijit/TooltipDialog", "dijit/form/CheckBox",
	"dijit/form/Button", "dijit/form/Form", "dijit/form/ValidationTextBox",
	"dijit/Tooltip",
	"dijit/layout/BorderContainer", "dijit/layout/ContentPane",
	"dijit/TitlePane",
	"put-selector/put", "dojox/calendar/Calendar", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, date, Observable, Memory,
		arrayUtil, registry, editor, baseinfo, baseinfoSingleton,
		WidgetGen,
		TimeTextBox, DateTextBox, Select, DropDownButton, TooltipDialog,
		CheckBox, Button, Form, ValidationTextBox,
		Tooltip, BorderContainer, ContentPane, TitlePane, put, Calendar){
		var constant = {
			infobtn_id:"infoBtnNode_id",
			idproperty_str:"field_id",
			updatebtn_str:"Update Field Info",
			grid_id:"fieldinfogrid_id",
			text_node_str:'Field List Name',
			db_type:'fielddb',
			day_list:['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
			radiobtn1_id:"radio1_id", radiobtn2_id:"radio2_id",
			league_select_id:"league_select_id",
			default_fieldevent_str:"Sports"
		};
		return declare(baseinfo, {
 			idproperty:constant.idproperty_str,
			calendar_store:null, calendar_id:1,
			fieldselect_widget:null, fieldevent_reg:null, eventdate_reg:null,
			starttime_reg:null, endtime_reg:null,
			starttime_handle:null, tooltip:null,
			datetimeset_handle:null,
			calendar:null, db_type:constant.db_type,
			field_id:0, old_field_id:-1,
			dupfieldselect_reg:null,
			rendercell_flag:true, today:null, widgetgen:null,
			divstr_colname:"", divstr_db_type:"rrdb",
			infogrid_store:null, calendarmapobj_list:null,
			tpform_btn_widget:null, tpform_delbtn_widget:null,
			tpform_savebtn_widget:null, tpform_cancelbtn_widget:null,
			delta_store:null,
			constructor: function(args) {
				// reference http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html#arrays-and-objects-as-member-variables
				// on the importance of initializing object in the constructor'
				// (non-objects can be initialized in member var declaration)
				lang.mixin(this, args);
				this.today = new Date();
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
					field_id: "Field ID",
					field_name: editor({label:"Name", autoSave:true},"text","dblclick"),
					primaryuse_str: {label:"Primary Use",
						renderCell: lang.hitch(this, this.primaryuse_actionRenderCell)
					},
					start_date: editor({label:"Start Date", autoSave:true,
						columntype:false,
						editorArgs:{
							style:'width:120px',
						},
					}, DateTextBox),
					end_date: editor({label:"End Date", autoSave:true,
						columntype:false,
						editorArgs:{
							style:'width:120px',
						},
					}, DateTextBox),
					start_time: editor({label:"Start Time", field:"start_time", autoSave:true, columntype:false,
						// note adding editorArgs w constraints timePattern
						// HH:MM:ss turns time display into 24-hr format
						// do not use if 12 hour am/pm format is desired
						// set function def not needed as we are going to just
						// store date object.  Using str representation of time
						// is not effective for initial display if initial store
						// does not have date object and only has str representation
						/*
						editorArgs:{
							constraints: {
								timePattern: 'HH:mm:ss',
								clickableIncrement: 'T00:15:00',
								visibleIncrement: 'T00:15:00',
								visibleRange: 'T01:00:00'
							},
						}, */
						/*
						set: function(item) {
							if (this.columntype) {
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
						} */
					}, TimeTextBox),
					end_time: editor({label:"End Time", field:"end_time",
					                 autoSave:true, columntype:false,
					                 /*
						editorArgs:{
							constraints: {
								timePattern: 'HH:mm:ss',
								clickableIncrement: 'T00:15:00',
								visibleIncrement: 'T00:15:00',
								visibleRange: 'T01:00:00'
							},
						}, */
						/*
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
						}, */
					}, TimeTextBox),
					dayweek_str:{label:"Days of Week",
						renderCell: lang.hitch(this, this.dayweek_actionRenderCell)},
					detaileddates: {label:"Detailed Config",
						renderCell: lang.hitch(this, this.dates_actionRenderCell)},
					totalfielddays: {label:"# Open Field Days",
						set:lang.hitch(this, this.calc_totalfielddays)
					}
				};
				return columnsdef_obj;
			},
			getfixedcolumnsdef_obj: function () {
				var columnsdef_obj = {
					field_id:"Field ID",
					field_name:"Field Name"
				};
				return columnsdef_obj;
			},
			initialize: function(newgrid_flag) {
				var form_name = "fieldconfig_form_id";
				var form_reg = registry.byId(form_name);
				//var form_dom = dom.byId(form_name);
				var input_name = "fieldlistname_input_id";
				var input_reg = registry.byId(input_name);
				var fieldnum_reg = registry.byId("fieldnum_input_id");
				var tooltipconfig_list = [{connectId:['fieldnum_input_id'],
					label:"Specify Number of Fields and press ENTER",
					position:['below','after']},
					{connectId:['fieldlistname_input_id'],
					label:"Specify Field List Name",
					position:['below','after']}];
				var args_obj = {
					dbname_reg:input_reg,
					form_reg:form_reg,
					entrynum_reg:fieldnum_reg,
					server_path:"create_newdbcol/",
					server_key:'info_data',
					text_node_str: constant.text_node_str,
					grid_id:constant.grid_id,
					updatebtn_str:constant.updatebtn_str,
					tooltipconfig_list:tooltipconfig_list,
					newgrid_flag:newgrid_flag,
					cellselect_flag:true
				}
				this.showConfig(args_obj);
				// delete old calendarmapobj_list if this is the subsequent time
				// we are coming through initialize()
				if (this.calendarmapobj_list)
					delete this.calendarmapobj_list;
			},
			getServerDBInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				options_obj.idproperty = constant.idproperty_str;
				options_obj.server_path = "create_newdbcol/";
				options_obj.server_key = 'info_data';
				options_obj.cellselect_flag = true;
				options_obj.text_node_str = constant.text_node_str;
				// key for response object from server
				options_obj.serverdata_key = 'info_list';
				options_obj.grid_id = constant.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.getserver_path = 'get_dbcol/';
				options_obj.db_type = constant.db_type;
				this.inherited(arguments);
			},
			getInitialList: function(fieldnum) {
				// return value defines structure for store for grid
				// http://dojo-toolkit.33424.n3.nabble.com/1-9-dijit-form-TimeTextBox-visibleRange-bug-td3997566.html
				var later_date = date.add(this.today, 'month', 3);
				var info_list = new Array();
				// assign default values for grid
				for (var i = 1; i < fieldnum+1; i++) {
					info_list.push({field_id:i, field_name:"",
						primaryuse_str:"",
						start_date:this.today, end_date:later_date,
						start_time:new Date(2014,0,1,8,0,0),
						end_time:new Date(2014,0,1,17,0,0),
						dayweek_str:"", detaileddates:"", totalfielddays:0});
				}
				return info_list;
			},
			// main entry point for creating dojox calendar inst
			// ref http://dojotoolkit.org/reference-guide/1.9/dojox/calendar.html
			// for dojox calendar specifics
			// also check api for for dojox/calendar/Calendar
			edit_calendar: function(field_id) {
				this.old_field_id = this.field_id;
				this.field_id = field_id;
				// see if we can get the 1st level bordercontainer which should be
				// below the top-level cpane which also happens to be a border
				// container.
				var detailed_bordercontainer = registry.byId("detailed_bordercontainer_id");
				if (!detailed_bordercontainer) {
					// if it doesn't exist, then we need to create it
					// first get the top-level cpane widget (which is also a
					// bordercontainer)
					var fieldinfocpane = registry.byId("fieldinfocpane_id");
					// created border container
					var detailed_bordercontainer = new BorderContainer({
						region:'center', design:'sidebar', gutters:true,
						liveSplitters:true, class:'allonehundred',
						id:'detailed_bordercontainer_id'
					});
					var detailed_leftcpane = new ContentPane({
						splitter:true, region:'leading',
						id:'detailed_leftcpane_id'
					})
					// start defining timepane content
					var tpcontent_node = put("div#title_pane_content_id");
					put(tpcontent_node, "label.label_box[for=fieldselect_id]",
						"Select Venue:");
					var fieldselect_node = put(tpcontent_node,
						"select#fieldselect_id[name=fieldselect_id]");
					this.fieldselect_widget = new Select({
						name:"fieldselect_id",
						onChange: lang.hitch(this, function(event) {
							// call edit_calendar with event as field_id
							this.edit_calendar(event);
						})
					}, fieldselect_node);
					var fieldselect_list = new Array();
					// this.rownum is defined in baseinfo
					for (var i = 1; i < this.rownum+1; i++) {
						fieldselect_list.push({label:'Field '+i, value:i, selected:false});
					}
					// initialize selected value with field_id row that selected
					// calendar.
					fieldselect_list[field_id-1].selected = true;
					this.fieldselect_widget.addOption(fieldselect_list);
					put(tpcontent_node, "br, hr");
					//fieldselect_widget.startup();
					// end defining field select widget
					// start defining form under titlepane
					// create domnode for Form
					// reference
					// http://stackoverflow.com/questions/15000249/how-to-make-and-display-a-form-in-a-dijit-dialog-programmatically
					// http://blackcatsolutions.co.uk/blog/programmatic-form-creation-with-dojo
					// However, despite the references above - where the goal was
					// to try to minimize put() statements to create nodes before creating
					// a widget, and because of the label elements that did not have
					// and equivalent dojo widget, we went back to the methodology
					// of creating nodes using put() first, and then creating widgets
					// on top of the created nodes.  See also baseinfo.js with use
					// of dbname widgets etc.
					// create dojo form widget
					var tpform_node = put(tpcontent_node, "form#tpform_id");
					var tpform_widget = new Form({}, tpform_node);
					var tpform_domnode = tpform_widget.domNode;
					// Note tpform_domnode does not equal tpform_node, but confirm
					// create elements that fall under form
					put(tpform_domnode,
						"label.label_box[for=tpform_input_id]", "Event Name:");
					var tpform_input_node = put(tpform_domnode,
						"input#tpform_input_id");
					this.tpform_input_widget = new ValidationTextBox({
						value:constant.default_fieldevent_str, required:true, regExp:'[\\w]+',
						promptMessage:'Enter Event Name - only alphanumeric characters and _',
						invalidMessage:'only alphanumeric characters and _',
						missingMessage:'enter event name',
						type:'text', style:'width:150px'
					}, tpform_input_node);
					put(tpform_domnode,"br, br");
					// create date input
					put(tpform_domnode,
						"label.label_box[for=tpform_date_id]", "Event Date:");
					var tpform_date_node = put(tpform_domnode,
						"input#tpform_date_id");
					this.tpform_date_widget = new DateTextBox({
						value:this.today, style:'width:150px'
					}, tpform_date_node);
					put(tpform_domnode,"br, br");
					// create time input
					put(tpform_domnode,
						"label.label_box[for=tpform_starttime_id]", "Start:");
					var tpform_starttime_node = put(tpform_domnode,
						"input#tpform_starttime_id");
					this.tpform_starttime_widget = new TimeTextBox({
						value:"T08:00:00", style:'width:110px'
					}, tpform_starttime_node);
					put(tpform_domnode,"br");
					put(tpform_domnode,
						"label.label_box[for=tpform_endtime_id]", "End:");
					var tpform_endtime_node = put(tpform_domnode,
						"input#tpform_endtime_id");
					this.tpform_endtime_widget = new TimeTextBox({
						value:"T09:00:00", style:'width:110px'
					}, tpform_endtime_node);
					put(tpform_domnode,"br, br");
					// create buttons
					var tpform_btn_node = put(tpform_domnode,
						"button.dijitButton#tpform_btn_id[type=button]");
					this.tpform_btn_widget = new Button({
						label:"Change Event", class:"primary", disabled:true
					}, tpform_btn_node);
					var tpform_delbtn_node = put(tpform_domnode,
						"button.dijitButton#tpform_delbtn_id[type=button]");
					this.tpform_delbtn_widget = new Button({
						label:"Delete Event", class:"info", disabled:true,
					}, tpform_delbtn_node);
					put(tpform_domnode, "br, br");
					// save to server button
					var tpform_savebtn_node = put(tpform_domnode,
						"button.dijitButton#tpform_savebtn_id[type=button]");
					this.tpform_savebtn_widget = new Button({
						label:"Save Changes", class:"success", disabled:true
					}, tpform_savebtn_node);
					// cancel changes button
					var tpform_cancelbtn_node = put(tpform_domnode,
						"button.dijitButton#tpform_cancelbtn_id[type=button]");
					this.tpform_cancelbtn_widget = new Button({
						label:"Cancel Changes", class:"warning", disabled:true
					}, tpform_cancelbtn_node);
					// attach all of the above form and its widgets to the title
					// pane
					var title_pane = new TitlePane({
						title:'Select Dates', content:tpcontent_node
					})

					detailed_leftcpane.addChild(title_pane);
					// underneath the above bordercontainer we have another
					// cpane which itself has a div underneath it.
					// that div will hold the dojox calendar.
					var calendargrid_node = put("div#calendargrid_id");
					var detailed_rightcpane = new ContentPane({
						splitter:true, region:'center', class:'allauto',
						content:calendargrid_node
					})
					detailed_bordercontainer.addChild(detailed_leftcpane);
					detailed_bordercontainer.addChild(detailed_rightcpane);
					detailed_bordercontainer.startup();
					fieldinfocpane.addChild(detailed_bordercontainer);
					// create store that feeds the dojox calendar
					if (this.calendar_store) {
						// reset calendar store and id
						delete this.calendar_store
						this.calendar_id = 1;
					}
					this.calendar_store = new Observable(new Memory({data:new Array()}));
					if (this.delta_store)
						delete this.delta_store
					this.delta_store = new Memory({data:new Array()});
					if (this.calendarmapobj_list) {
						// copy fieldinfo data originally returned from server to
						// create fieldinfo grid, to dojox calendar store
						//
						// use the current grid/db name as the 'fieldevent'
						// for now - reevaluate
						// read in entire calendarmapobj_list - note that doing a setData for every field_id request does not work as setData
						// does not work for observable stores (setData is a function for Memory store, not the Observable wrapper)
						// http://dojo-toolkit.33424.n3.nabble.com/dojo-store-Observable-Change-Request-td3286606.html
						arrayUtil.forEach(this.calendarmapobj_list, function(item) {
							var fieldevent_str = constant.default_fieldevent_str;
							/*
							var closed_list = null;
							if ('closed_list' in item) {
								closed_list = item.closed_list;
							} */
							this.populate_calendar_store(item.calendarmap_list,
								item.field_id, fieldevent_str);
								/*
								if (closed_list && closed_list.indexOf(fieldday_id) > -1) {
									// if fieldday_id falls in a closed_list, then
									// add to delta store instead of calendar store
									this.delta_store.add({action:'remove',
										data_obj:data_obj,
										id:this. calendar_id, field_id:field_id});
								} else {
									this.calendar_store.add(data_obj);
								} */
						}, this);
					} else {
						// if this.calendarmapobj_list does not exist, then no data
						// has been returned from the server.  Instead, retrieve
						// data from the current store
						var item = this.editgrid.schedInfoStore.get(field_id);
						var args_obj = {dayweek_list:item.dayweek_str.split(','),
							start_date:item.start_date,
							totalfielddays:item.totalfielddays,
							start_time_str:item.start_time.toLocaleTimeString(),
							end_time_str:item.end_time.toLocaleTimeString()};
						// get calendarmap list that maps fieldday_id to calendar
						// date, for each field
						var calendarmap_list = this.schedutil_obj.getcalendarmap_list(args_obj);
						var fieldevent_str = constant.default_fieldevent_str;
						this.populate_calendar_store(calendarmap_list,
							item.field_id, fieldevent_str);
					}
					// create dojox calendar - note we create a (blank) calendar
					// even if there is no calendarmap_obj_list data
					this.calendar = new Calendar({
						dateInterval: "day",
						date: this.today,
						startTimeAttr:"starttime",
						endTimeAttr:"endtime",
						store: this.calendar_store,
						style: "position:inherit;width:100%;height:600px",
						cssClassFunc: function(item) {
							return item.calendar;
						},
						query:{field_id:field_id}
					}, calendargrid_node);
					this.calendar.startup();
					this.calendar.on("itemClick",
						lang.hitch(this,this.process_clickedCalendarItem));
					//this.calendar.resize();
				} else {
					// if border container has already been created, then the
					// calendar store should already have been created, along
					// with the dojox calendar.
					// Here we will see if there is a different field_id, and if
					// there is, display the configured field-specific config
					this.calendar.set("query", {field_id:field_id});
					// ref http://stackoverflow.com/questions/12585051/dojox-calendar-and-jsonrest-how-to-update
					// unlike dgrid, set("store",) must be explicitly called
					// for the new store query to take effect
					this.calendar.set("store", this.calendar_store);
					// http://stackoverflow.com/questions/7869805/programmatically-set-the-selected-value-of-a-dijit-select-widget
					// autochange fieldselect drop-down selection in titlepane
					this.fieldselect_widget.set('value', field_id);
					this.tpform_btn_widget.set('disabled', true);
					this.tpform_delbtn_widget.set('disabled', true);
					this.tpform_savebtn_widget.set('disabled', true);
					this.tpform_cancelbtn_widget.set('disabled', true);
				}
				this.calendar.resize();
				// update callback with current field_id
				this.tpform_cancelbtn_widget.set("onClick",
					lang.hitch(this, this.restore_delta, field_id));
				this.tpform_savebtn_widget.set("onClick",
					lang.hitch(this, this.send_delta, field_id));
				/*
				// create drop down to select (either) field
				if (this.fieldselect_reg) {

				} else {
					// if field select widget does not exist, create one.
					this.fieldselect_reg = registry.byId("fieldselect_id");
					var fieldselect_list = new Array();
					for (var i = 1; i < this.rownum+1; i++) {
						fieldselect_list.push({label:'Field '+i, value:i, selected:false});
					}
					fieldselect_list[field_index].selected = true;
					this.fieldselect_reg.addOption(fieldselect_list);
					// add field list for schedule duplication select drop-down
					var dupfieldselect_list = lang.clone(fieldselect_list);
					dupfieldselect_list.push({label:'All Fields', value:this.rownum+1, selected:false});
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
					this.fieldevent_reg = registry.byId("tpform_input_id");
					this.eventdate_reg = registry.byId("tpform_date_id");
					this.starttime_reg = registry.byId("tpform_starttime_id");
					if (this.starttime_handle) {
						this.starttime_handle.remove();
					}
					this.starttime_handle = this.starttime_reg.on("change",
						lang.hitch(this, function (event) {
							this.endtime_reg.set('value',
								date.add(event, 'hour', 1));
						}));
					this.endtime_reg = registry.byId("tpform_endtime_id");
					var datetimeset_reg = registry.byId("datetimeset_btn");
					if (this.datetimeset_handle) {
						this.datetimeset_handle.remove();
					}
					this.datetimeset_handle = datetimeset_reg.on("click",
						lang.hitch(this, this.datetimeset_submit));
					var tooltipconfig = {connectId:['tpform_input_id'],
						label:"Enter Event Type and Name",
						position:['below','after']};
					this.tooltip = new Tooltip(tooltipconfig);
					this.eventdate_reg.set('value', this.today);
					this.eventdate_reg.startup();
					// setup titlepane widget to generate event when it opens
					var duptitlepane_reg = registry.byId("duptitlepane_id");
					duptitlepane_reg.on("show", function(event){
						console.log("dupfield");
					});
					this.calendar_store = new Observable(new Memory({data:new Array()}));
					this.calendar = new Calendar({
						dateInterval: "day",
						date: this.today,
						store: this.calendar_store,
						style: "position:inherit;width:600px;height:600px",
						cssClassFunc: function(item) {
							return item.calendar;
						}
					}, "calendarGrid_id");
					this.calendar.startup();
					this.calendar.set("createOnGridClick", true);
					this.calendar.set("createItemFunc", this.createItem);
				} */
			},
			populate_calendar_store: function(calendarmap_list, field_id, fieldevent_str) {
				// populate calendar_store with entries from calendarmap_list
				// which holds field dates, and fieldevent and field_id
				// parameters
				arrayUtil.forEach(calendarmap_list, function(item) {
					var fieldday_id = item.fieldday_id;
					var data_obj = {
						id:this.calendar_id,
						fieldevent_str:fieldevent_str,
						field_id:field_id,
						summary:"Field"+field_id+':'+fieldevent_str+' '+"Block:"+this.calendar_id,
						// start and end times have dates embedded
						// in them
						starttime:item.start_time,
						endtime:item.end_time,
						fieldday_id:fieldday_id,
						calendar:'Calendar'+field_id
					}
					this.calendar_store.add(data_obj);
					this.calendar_id++;
				}, this);
			},
			createItem: function(view, date, event) {
				console.log('ok item');
			},
			// handler for datetime update btn in left title pane
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
					// ref https://www.sitepen.com/blog/2011/02/15/dojo-object-stores/
					// on making complex queries
					var overlapped_list = this.calendar_store.query(lang.hitch(this, function(object){
						return date.compare(start_datetime_obj,
							object.starttime, "date") == 0 &&
							date.compare(end_datetime_obj,
							object.endtime, "date") == 0 &&
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
							object.endtime,"time") < 0 &&
							date.compare(end_datetime_obj, object.starttime,
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
							starttime:start_datetime_obj, endtime:end_datetime_obj,
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
			process_clickedCalendarItem: function(event) {
				var item = event.item;
				var calendar_id = item.id;
				// get store object with id==select_id
				//var match_obj = this.calendar_store.get(calendar_id);
				// http://stackoverflow.com/questions/7869805/programmatically-set-the-selected-value-of-a-dijit-select-widget
				this.tpform_delbtn_widget.set('disabled', false);
				this.tpform_delbtn_widget.set("onClick",
					lang.hitch(this, this.delete_calevent, calendar_id));
				// enable change event button
				this.tpform_btn_widget.set('disabled', false);
				this.tpform_btn_widget.set("onClick",
					lang.hitch(this, this.change_calevent, calendar_id));
				this.tpform_input_widget.set('value', item.fieldevent_str)
				this.tpform_date_widget.set('value', item.starttime);
				this.tpform_starttime_widget.set('value', item.starttime);
				this.tpform_endtime_widget.set('value', item.endtime);
			},
			delete_calevent: function(calendar_id, event) {
				var data_obj = this.calendar_store.get(calendar_id);
				// re-use calendar_id as id for delta_store also.
				// should not be a problem as calendar_id is unique
				// calendar_id should be same as data_obj.id
				this.delta_store.add({action:'remove', data_obj:data_obj,
					id:calendar_id, field_id:data_obj.field_id});
				this.calendar_store.remove(calendar_id);
				this.enable_savecancel_widgets();
			},
			change_calevent: function(calendar_id, event) {
				var data_obj = this.calendar_store.get(calendar_id);
				// make a copy to store in delta_store as data_obj will be overwritten
				var clonedata_obj = lang.clone(data_obj);
				if (this.delta_store.get(calendar_id)) {
					// if there is already a delta change already in the delta_store
					// remove it, as the latest one will have priority
					this.delta_store.remove(calendar_id);
				}
				this.delta_store.add({action:'change', data_obj:clonedata_obj,
					id:calendar_id, field_id:data_obj.field_id});
				var fieldevent_str = this.tpform_input_widget.get('value');
				var date_str = this.tpform_date_widget.get('value').toLocaleDateString();
				data_obj.fieldevent_str = fieldevent_str;
				data_obj.summary = "Field"+data_obj.field_id+':'+fieldevent_str+' '+"Block:"+calendar_id;
				var starttime = new Date(date_str+' '+
					this.tpform_starttime_widget.get('value').toLocaleTimeString());
				var endtime = new Date(date_str+' '+
					this.tpform_endtime_widget.get('value').toLocaleTimeString());
				if (date.compare(endtime, starttime) > 0) {
					data_obj.starttime = starttime;
					data_obj.endtime = endtime;
					this.calendar_store.put(data_obj);
				} else {
					alert("end time must be later than start timse");
				}
				this.enable_savecancel_widgets();
			},
			enable_savecancel_widgets:function() {
				if (this.tpform_cancelbtn_widget.get('disabled'))
					this.tpform_cancelbtn_widget.set('disabled', false);
				if (this.tpform_savebtn_widget.get('disabled'))
					this.tpform_savebtn_widget.set('disabled', false);
			},
			// restore calendar changes defined in the delta_store
			restore_delta: function(field_id, evt) {
				this.delta_store.query({field_id:field_id})
					.forEach(function(item) {
					if (item.action == 'remove') {
						// if action was 'remove', add element back to
						// calendar store
						this.calendar_store.add(item.data_obj)
					} else if (item.action == 'change') {
						this.calendar_store.put(item.data_obj);
					}
					// delete action item from delta_store
					this.delta_store.remove(item.id);
				}, this);
			},
			send_delta: function(field_id, evt) {
				// send contents of delta_store to server, except instead
				// sending each entry separately, we will aggregate changes
				// and removals into separate lists and send them as separate
				// commands (gets).  We need to send the changes first as
				// there may be some calendar id's that were changed first and then
				// removed.
				if (this.config_status) {
					var change_list = new Array();
					var remove_list = new Array();
					this.delta_store.query({field_id:field_id})
						.forEach(function(item) {
						if (item.action == 'remove') {
							remove_list.push(item.data_obj.fieldday_id);
						} else if (item.action == 'change') {
							// don't use delta_store object for sending to server
							// as that has the pre-change info necessary to restore
							// original when a cancel button is clicked; instead
							// get from calendar_store
							var data_obj = this.calendar_store.get(item.id)
							// we only need a subset of the original calendar_store
							// data_obj for the server
							change_list.push({
								fieldday_id:data_obj.fieldday_id,
								starttime:data_obj.starttime.toLocaleTimeString(),
								endtime:data_obj.endtime.toLocaleTimeString()
							});
						}
					}, this);
					var server_key_obj = null;
					if (change_list.length > 0) {
						// make sure to convert list of objects to json string
						server_key_obj = {change_str:JSON.stringify(change_list)};
						this.server_interface.getServerData(
							"send_delta/change/"+field_id, function(data) {

							}, server_key_obj)
					}
					if (remove_list.length > 0) {
						server_key_obj = {remove_str:remove_list.join(',')};
						this.server_interface.getServerData(
							"send_delta/remove/"+field_id, function(data) {

							}, server_key_obj)
					}
				} else {
					alert("Re-Save after basic configuration is saved");
				}
			},
			primaryuse_actionRenderCell: function(object, data, node) {
				if (this.rendercell_flag) {
					var TDialog = null;
					var tdialogprop_obj = null;
					var field_id = object.field_id;
					// get data to create the possible check list items
					// which is the all the divinfo items
					// Data for actually entering the checks will come later
					// if data is already in the store (when selecting a fieldinfo grid that has been stored in the server)
					// the 'data' field (alternatively object.primaryuse_str) will
					// have the passed data originating from the server
					// through local data store.
					var divstr_list = baseinfoSingleton.watch_obj.get('divstr_list')
					if (divstr_list && divstr_list.length > 0) {
						var primaryuse_obj = this.create_primaryuse_dialog(divstr_list,field_id);
						tdialogprop_obj = primaryuse_obj.tdialogprop_obj;
						TDialog = primaryuse_obj.tdialog;
						//http://stackoverflow.com/questions/13444162/widgets-inside-dojo-dgrid
			    	} else {
			    		TDialog = new TooltipDialog({
			    			content:"Select Database using Select Config->Division Info"
			    		});
			    	}
					//myDialog.startup();
					var dropdown_btn = registry.byId('fielddropdownbtn'+field_id+'_id');
					if (!dropdown_btn) {
						var dropdown_btn = new DropDownButton({
							label:"Config",
							dropDown:TDialog,
							id:'fielddropdownbtn'+field_id+'_id'
						});
						dropdown_btn.startup();
					} else {
						dropdown_btn.set('dropDown', TDialog);
					}
					// fill in checkboxes if store already has checkbox info
					// this has to be called after dropdown_btn is created
		    		if (divstr_list && divstr_list.length > 0 && object.primaryuse_str) {
		    			// index_offset is 1 (-1) as check_str is a list of
		    			// div_id's, which need to be decremented to be an index
		    			// into the display_list
		    			var args_obj = {dialogprop_obj:tdialogprop_obj,
		    				check_str:object.primaryuse_str,
		    				display_list:tdialogprop_obj.div_list,
		    				dropdownbtn_prefix:"fielddropdownbtn",
		    				index_offset:1}
		    			this.init_checkbox(args_obj);
		    		}
				} else {
					// retrieve widget that had already been instantiated
					var field_id = object.field_id;
					var dropdown_btn = registry.byId('fielddropdownbtn'+field_id+'_id');
				}
				node.appendChild(dropdown_btn.domNode);
				//dropdown_btn.startup();
				return dropdown_btn;
			},
			create_primaryuse_dialog: function(divstr_list, field_id) {
				//http://stackoverflow.com/questions/13444162/widgets-inside-dojo-dgrid
				var content_str = "";
				var checkboxid_list = new Array();
				var div_list = new Array();
				arrayUtil.forEach(divstr_list, function(divstr_obj) {
					var divstr = divstr_obj.divstr;
					div_list.push(divstr);
					var idstr = "checkbox"+divstr+field_id+"_id";
					content_str += '<input type="checkbox" data-dojo-type="dijit/form/CheckBox" style="color:green" id="'+idstr+
					'" value="'+divstr_obj.div_id+'"><label for="'+idstr+'">'+divstr+'</label><br>';
					checkboxid_list.push(idstr);
				});
				var button_id = 'tdialogbtn'+field_id+'_id';
				content_str += '<button data-dojo-type="dijit/form/Button" type="submit" id="'+button_id+'">Save</button>'
				var TDialog = registry.byId('tooltip'+field_id);
				if (TDialog) {
					TDialog.set('content', content_str);
				} else {
					TDialog = new TooltipDialog({
						id:"tooltip"+field_id,
						content: content_str
	    			});
				}
	    		var tdialogprop_obj = {field_id:field_id,
	    			checkboxid_list:checkboxid_list,
	    			div_list:div_list};
	    		//this.tdialogprop_list.push({field_id:field_id,
	    		//	checkboxid_list:checkboxid_list});
	    		var button_reg = registry.byId(button_id);
	    		button_reg.set("onClick",
	    			lang.hitch(this,this.dialogbtn_process, tdialogprop_obj));
	    		return {tdialog:TDialog, tdialogprop_obj:tdialogprop_obj};
			},
			// below function called after divstr_list changed externally
			set_primaryuse_dialog_dropdown: function(divstr_list) {
				for (var field_id = 1; field_id < this.rownum+1; field_id++) {
					var primaryuse_obj = this.create_primaryuse_dialog(divstr_list, field_id);
					var TDialog = primaryuse_obj.tdialog;
					var dropdown_btn = registry.byId('fielddropdownbtn'+field_id+'_id');
					if (dropdown_btn) {
						dropdown_btn.set('dropDown', TDialog);
					}
				}
			},
			// handler for primary use dialog btn
			dialogbtn_process: function(tdialogprop_obj, event) {
				var field_id = tdialogprop_obj.field_id;
				var checkboxid_list = tdialogprop_obj.checkboxid_list;
				var div_list = tdialogprop_obj.div_list;
				var display_str = "";
				var value_str = "";
				arrayUtil.forEach(checkboxid_list, function(checkbox_id, index) {
					var checkbox_reg = registry.byId(checkbox_id);
					if (checkbox_reg.get("checked")) {
						// create str to display in buttone
						display_str += div_list[index]+',';
						// create str to store (str of integer id elements)
						value_str += checkbox_reg.get("value")+',';
					}
				}, this);
				// trim off last comma
				// http://stackoverflow.com/questions/952924/javascript-chop-slice-trim-off-last-character-in-string
				display_str = display_str.substring(0, display_str.length-1);
				value_str = value_str.substring(0, value_str.length-1);
				if (this.editgrid) {
					var store_elem = this.editgrid.schedInfoStore.get(field_id);
					store_elem.primaryuse_str = value_str;
					this.editgrid.schedInfoStore.put(store_elem);
					// because of trouble using dgrid w observable store, directly update dropdownbtn instead of dgrid cell with checkbox info
					var dropdownbtn_reg = registry.byId("fielddropdownbtn"+field_id+"_id");
					dropdownbtn_reg.set('label', display_str);
				}
			},
			dates_actionRenderCell: function(object, data, node) {
				if (this.rendercell_flag) {
					var field_id = object.field_id;
					var config_btn = registry.byId("fielddatesbtn"+field_id+"_id");
					if (!config_btn) {
						config_btn = new Button({
							label:"Config Venue"+field_id,
							id:"fielddatesbtn"+field_id+"_id",
							onClick: lang.hitch(this, function() {
								this.edit_calendar(field_id);
							})
						});
						config_btn.startup();
					}
				} else {
					// retrieve widget that had already been instantiated
					var field_id = object.field_id;
					var config_btn = registry.byId("fielddatesbtn"+field_id+"_id");
				}
				node.appendChild(config_btn.domNode);
				return config_btn;
			},
			dayweek_actionRenderCell: function(object, data, node) {
				if (this.rendercell_flag) {
					var field_id = object.field_id;
					//http://stackoverflow.com/questions/13444162/widgets-inside-dojo-dgrid
					var content_str = "";
					var checkboxid_list = new Array();
					arrayUtil.forEach(constant.day_list, function(day, index) {
						var idstr = day+field_id+"_id";
						content_str += '<input type="checkbox" data-dojo-type="dijit/form/CheckBox" style="color:green" id="'+idstr+
						'" value='+index+'><label for="'+idstr+'">'+day+'</label> ';
						if (index%2)
							content_str += '<br>'
						checkboxid_list.push(idstr);
					});
					var button_id = 'dwdialogbtn'+field_id+'_id';
					content_str += '<br><button data-dojo-type="dijit/form/Button" type="submit" id="'+button_id+'">Save</button>'
					var dwdialog = registry.byId("dwtooltip"+field_id);
					if (!dwdialog) {
						dwdialog = new TooltipDialog({
							id:"dwtooltip"+field_id,
							content: content_str
			    		});
					} else {
						dwdialog.set('content', content_str);
					}
		    		var dwdialogprop_obj = {field_id:field_id,
		    			checkboxid_list:checkboxid_list,
		    			day_list:constant.day_list};
		    		var button_reg = registry.byId(button_id);
		    		button_reg.on("click",
		    			lang.hitch(this,this.dwdialogbtn_process, dwdialogprop_obj));
		    		var dropdown_btn = registry.byId('dwfielddropdownbtn'+field_id+'_id');
		    		if (!dropdown_btn) {
						dropdown_btn = new DropDownButton({
							label:"Config",
							dropDown:dwdialog,
							id:'dwfielddropdownbtn'+field_id+'_id'
						});
						dropdown_btn.startup();
		    		} else {
		    			dropdown_btn.set('dropDown', dwdialog);
		    		}
		    		if (object.dayweek_str) {
		    			// note index_offset is 0 as dayweek_str is already
		    			// a list of indices into the day_list string list
		    			var args_obj = {dialogprop_obj:dwdialogprop_obj,
		    				check_str:object.dayweek_str,
		    				display_list:dwdialogprop_obj.day_list,
		    				dropdownbtn_prefix:"dwfielddropdownbtn",
		    				index_offset:0}
		    			this.init_checkbox(args_obj);
		    		}
				} else {
					var field_id = object.field_id;
					var dropdown_btn = registry.byId('dwfielddropdownbtn'+field_id+'_id');
				}
				node.appendChild(dropdown_btn.domNode);
				//dropdown_btn.startup();
				return dropdown_btn;
			},
			// handler for days week dialog btn
			dwdialogbtn_process: function(dwdialogprop_obj, event) {
				var field_id = dwdialogprop_obj.field_id;
				var checkboxid_list = dwdialogprop_obj.checkboxid_list;
				var day_list = dwdialogprop_obj.day_list;
				var display_str = "";
				var value_str = "";
				//var numdays = 0;
				arrayUtil.forEach(checkboxid_list, function(checkbox_id, index) {
					var checkbox_reg = registry.byId(checkbox_id);
					if (checkbox_reg.get("checked")) {
						// create str to display in buttone
						display_str += day_list[index]+',';
						// create str to store (str of integer id elements)
						value_str += checkbox_reg.get("value")+',';
						//numdays++;  // numdays counts num days per week
					}
				})
				// trim off last comma
				// http://stackoverflow.com/questions/952924/javascript-chop-slice-trim-off-last-character-in-string
				display_str = display_str.substring(0, display_str.length-1);
				value_str = value_str.substring(0, value_str.length-1);
				if (this.editgrid) {
					var store_elem = this.editgrid.schedInfoStore.get(field_id);
					store_elem.dayweek_str = value_str;
					store_elem.totalfielddays = this.calc_totalfielddays(store_elem);
					//store_elem.dayweek_num = numdays;
					this.editgrid.schedInfoStore.put(store_elem);
					// because of trouble using dgrid w observable store, directly update dropdownbtn instead of dgrid cell with checkbox info
					var dwdropdownbtn_reg = registry.byId("dwfielddropdownbtn"+field_id+"_id");
					dwdropdownbtn_reg.set('label', display_str);
				}
			},
			// mark checkboxes depending on state of store
			init_checkbox: function(args_obj) {
				var dialogprop_obj = args_obj.dialogprop_obj;
				var check_str = args_obj.check_str;
				var display_list = args_obj.display_list;
				var dropdownbtn_prefix = args_obj.dropdownbtn_prefix;
				var index_offset = args_obj.index_offset;
				var field_id = dialogprop_obj.field_id;
				var checkboxid_list = dialogprop_obj.checkboxid_list;
				var display_str = "";
				arrayUtil.forEach(check_str.split(','), function(item) {
					// note index is computed from item
					// (Not index of function(item, index))
					var index = parseInt(item)-index_offset;
					var checkbox_reg = registry.byId(checkboxid_list[index]);
					checkbox_reg.set("checked", true);
					display_str += display_list[index]+',';
				});
				display_str = display_str.substring(0, display_str.length-1);
				var dropdownbtn_reg = registry.byId(dropdownbtn_prefix+field_id+"_id");
				dropdownbtn_reg.set('label', display_str);
			},
			create_dbselect_radiobtnselect: function(radio1_id, radio2_id, select_id, init_db_type, init_colname) {
				// passed in init_db_type and init_colname are typicall
				// for divinfo(divstr) db_type and colname even though it
				// is used for fieldinfo grid
				var init_db_type = init_db_type || "";
				var init_colname = init_colname || "";
				//For field grids, create radio button pair to select
				// schedule type - rr or tourn
				var fieldinfogrid_node = dom.byId(constant.grid_id);
				var topdiv_node = put(fieldinfogrid_node, "-div");
				if (!this.widgetgen) {
					this.widgetgen = new WidgetGen({
						storeutil_obj:this.storeutil_obj,
						server_interface:this.server_interface
					});
				}
				this.widgetgen.create_dbtype_radiobtn(topdiv_node,
					radio1_id, radio2_id, init_db_type,
					this, this.radio1_callback, this.radio2_callback, select_id);
				//for callback function, additional parameters after the first two
				// are passed to the callback as extra parameters.
				var args_obj = {
					topdiv_node:topdiv_node, select_id:select_id,
					init_db_type:init_db_type,
					init_colname:init_colname,
					onchange_callback:lang.hitch(this.widgetgen, this.widgetgen.getname_list, this),
					name_str:"league select",
					label_str:"Select League",
					put_trail_spacing:"br"}
				this.widgetgen.create_select(args_obj);
			},
			// callback function when dbtype radiobutton is changed
			radio1_callback: function(select_id, event) {
				if (event) {
					this.widgetgen.swap_league_select_db(select_id, 'rrdb');
					this.divstr_db_type = 'rrdb';
				}
			},
			radio2_callback: function(select_id, event) {
				if (event) {
					this.widgetgen.swap_league_select_db(select_id, 'tourndb');
					this.divstr_db_type = 'tourndb';
				}
			},
			// set and get divinfo  obj information that is attached to the current
			// fieldinfo obj
			setdivstr_obj: function(colname, db_type) {
				this.divstr_colname = colname;
				this.divstr_db_type = db_type;
			},
			getdivstr_obj: function() {
				return {colname:this.divstr_colname, db_type:this.divstr_db_type};
			},
			checkconfig_status: function(raw_result){
				// do check to make sure all fields have been filled.
				// note construct of using arrayUtil.some works better than
				// query.filter() as loop will exit immediately if .some() returns
				// true.
				// config_status is an integer type as booleans cannot be directly
				// be transmitted to server (sent as 'true'/'false' string)
				var config_status = 0;
				if (arrayUtil.some(raw_result, function(item, index) {
					// ref http://stackoverflow.com/questions/8312459/iterate-through-object-properties
					// iterate through object's own properties too see if there
					// any unfilled fields.  If so alert and exit without sending
					// data to server
					var break_flag = false;
					for (var prop in item) {
						if (prop=='detaileddates')
							continue;
						if (item[prop] === "") {
							//alert("Not all fields in grid filled out, but saving");
							break_flag = true;
							break;
						}
					}
					return break_flag;
				})) {
					// insert return statement here if plan is to prevent saving.
					console.log("Not all fields complete for "+this.idproperty+
						" but saving");
				} else {
					config_status = 1;
				}
				return config_status;
			},
			// modify field_id-specific data returned from server, which consists
			// of converting date/time strings to js date objects needed for dojo
			// widgets.
			// also create (in js) calendarmap_list which maps fieldday_id to date objects
			modifyserver_data: function(data_list, divstr_obj) {
				if (this.calendarmapobj_list)
					delete this.calendarmapobj_list;
				this.calendarmapobj_list = new Array();
				arrayUtil.forEach(data_list, function(item, index) {
					// save date str to pass into start and end time calc
					// (though it can be a dummy date)
					var start_date_str = item.start_date;
					var end_date_str = item.end_date;
					var start_time_str = item.start_time;
					var end_time_str = item.end_time;
					item.start_date = new Date(start_date_str);
					item.end_date = new Date(end_date_str);
					item.start_time = new Date(start_date_str+' '+start_time_str);
					item.end_time = new Date(end_date_str+' '+end_time_str);
					// this.calendarmapobj_list is used by the dojox calendar
					// to set initial date/time configurations based on server
					// data.
					var calendarmap_list = new Array();
					// calendarmap_list includes date string, so concatenate w
					// timestr from above and create date objects for both
					// start and end times
					arrayUtil.forEach(item.calendarmap_list,
						function(item2, index2) {
						var start_time = new Date(item2.date+' '+start_time_str)
						var end_time = new Date(item2.date+' '+end_time_str)
						calendarmap_list.push({
							start_time:start_time,
							end_time:end_time,
							fieldday_id:item2.fieldday_id});
					})
					var obj = {
						field_id:item.field_id,
						field_name:item.field_name,
						calendarmap_list:calendarmap_list
					}
					/*
					if ('closed_list' in item) {
						obj.closed_list = item.closed_list;
					} */
					this.calendarmapobj_list.push(obj)
				}, this);
				// datalist modifications end above. However, there are other
				// field_id-specific processing that needs to be done, concerning
				// divinfo data attached for fieldinfo data
				// extract divinfo obj related parameters from server data
				this.divstr_colname = divstr_obj.colname;
				this.divstr_db_type = divstr_obj.db_type;
				var config_status = divstr_obj.config_status;
				var info_list = divstr_obj.info_list;
				//For field grids, create radio button pair to select
				// schedule type - rr or tourn
				// if divstr parameters were saved with fieldgrid info and returned
				// to the client, use those to set up the radio buttons.  Otherwise
				// use default values.
				if (this.divstr_colname && this.divstr_db_type) {
					this.create_dbselect_radiobtnselect(constant.radiobtn1_id,
						constant.radiobtn2_id, constant.league_select_id,
						this.divstr_db_type, this.divstr_colname);
				} else {
					this.initabovegrid_UI();
				}
				//config_status should always be 1 for as divinfo db's are
				// selected from a list that includes only fully complete configs
				// however, there is a chance that a non-config-complete fieldgrid
				// was saved to the server.
                if (config_status) {
                    var divstr_list = arrayUtil.map(info_list,
                        function(item, index) {
                            // return both the divstr (string) and div_id value
                            // value used as the value for the checkbox in the fieldinfo grid dropdown
                            return {'divstr':item.div_age + item.div_gen,
                                'div_id':item.div_id};
                        })
                    // save divinfo obj information that is attached to the current
                    // fieldinfo obj
                    baseinfoSingleton.watch_obj.set('divstr_list', divstr_list);
                }
				return data_list;
			},
			modify_toserver_data: function(raw_result) {
				// modify store data before sending data to server
				var newlist = new Array();
				// for the field grid data convert Data objects to str
				// note we want to keep it as data objects inside of store to
				// maintain direct compatibility with Date and TimeTextBox's
				// and associated picker widgets.
				raw_result.map(function(item) {
					var newobj = lang.clone(item);
					newobj.start_date = newobj.start_date.toLocaleDateString();
					newobj.end_date = newobj.end_date.toLocaleDateString();
					newobj.start_time = newobj.start_time.toLocaleTimeString();
					newobj.end_time = newobj.end_time.toLocaleTimeString();
					return newobj;
				}).forEach(function(obj) {
					newlist.push(obj);
				});
				return newlist;
			},
			initabovegrid_UI: function() {
				this.create_dbselect_radiobtnselect(
					constant.radiobtn1_id, constant.radiobtn2_id,
					constant.league_select_id);
			},
			calc_totalfielddays: function(item) {
				// calculate # of totalfielddays based on current grid
				// cell values
				// Current calculation is independent of closed day list calculation
				var start_date = item.start_date;
				// get day of week
				var start_day = start_date.getDay();
				var end_date = item.end_date;
				var end_day = end_date.getDay();
        		// create list of available dates during last week
        		//calc # days between start and end dates
        		// http://dojotoolkit.org/reference-guide/1.9/dojo/date.html
        		var diffdays_num = date.difference(start_date, end_date);
        		var diffweeks_num = date.difference(start_date, end_date,
        			'week');
        		// get current configuration for days-of-week and it's length
        		// i.e. number of days in week
        		var dayweek_list = item.dayweek_str.split(',')
        		var dayweekint_list = arrayUtil.map(dayweek_list, function(item){
        			return parseInt(item);
        		})
        		var dayweek_len = dayweek_list.length;
        		// calc baseline # of fielddays based on full weeks
        		var totalfielddays = dayweek_len * diffweeks_num;
        		// calc num days in last week (can be partial week)
        		var lastwkdays_num = diffdays_num % diffweeks_num;
        		var lw_list = 0;
        		if (lastwkdays_num > 0) {
        			if (end_day >= start_day) {
        				lw_list = this.schedutil_obj.range(start_day,
        					end_day+1);
        			} else {
                		//days of week are numbered as a circular list so take care
                		//of case where start day is later than end day wrt day num
                		//i.e. start = Fri and end = Mon
                		lw_list = this.schedutil_obj.range(start_day, 7).concat(
                			this.schedutil_obj.range(end_day+1));
        			}
        			totalfielddays += this.schedutil_obj.intersect(
        				lw_list, dayweekint_list).length;
        		}
        		return totalfielddays;
			},
			cleanup: function() {
				if (this.starttime_handle)
					this.starttime_handle.remove();
				if (this.datetimeset_handle)
					this.datetimeset_handle.remove();
				this.calendar.destroyRecursive();
				//delete this.calendar;
				delete this.calendar_store;
				delete this.delta_store;
				if (this.tooltip)
					this.tooltip.destroyRecursive();
			}
		});
});
