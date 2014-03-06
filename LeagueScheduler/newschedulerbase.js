define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare",
	"dojo/_base/lang", "dojo/date", "dojo/Stateful",
	"dojo/_base/array", "dojo/keys", "dojo/store/Memory",
	"dijit/registry", "dijit/Tooltip",
	"dijit/form/ValidationTextBox","dijit/form/Select", "dijit/form/Button",
	"dijit/form/NumberSpinner", "dijit/form/DateTextBox",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection", "LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, date, Stateful, arrayUtil, keys,
		Memory,registry, Tooltip, ValidationTextBox, Select, Button, NumberSpinner,
		DateTextBox,
		OnDemandGrid, editor, Keyboard, Selection, EditGrid,
		baseinfoSingleton, put) {
		var constant = {
			numweeks:12,
			idproperty_str:'newsched_id',
			form_name:'newsched_form_id',
			scinput_div:'seasoncalendar_input'
		};
		var newschedwatch_class = declare([Stateful],{
			leagueselect_val:-1,
			leagueselect_flag:false,
			fgselect_val:-1,
			fgselect_flag:false,
			league_fg_flag:false
		})
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			newsched_dom:"", schedutil_obj:null, storeutil_obj:null,
			info_obj:null, idproperty:constant.idproperty_str,
			server_path:"", server_key:"",
			seasondates_btn_reg:null,
			callback:null, text_node_str:"", tooltip:null,
			start_dtbox:null, end_dtbox:null, sl_spinner:null,
			seasonstart_handle:null, seasonend_handle:null,
			seasonlength_handle:null, league_select:null, fg_select:null,
			event_flag:false, uistackmgr:null, newschedwatch_obj:null,
			selectexists_flag:false,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
				this.newschedwatch_obj = new newschedwatch_class();
			},
			initialize: function(arg_obj) {
				this.form_reg = registry.byId(constant.form_name);
				//this.dbname_reg = registry.byId("newsched_input_id");
				// put selector documentation
				// http://davidwalsh.name/put-selector
				// https://github.com/kriszyp/put-selector
				// first check to see if the domNode has already been created by
				// seeing the dom node can be retrieved
				var sched_input = dom.byId("newched_input_id");
				if (!sched_input) {
					put(this.form_reg.domNode, "label.label_box[for=newsched_input_id]",
						'New Schedule Name:');
					sched_input = put(this.form_reg.domNode,
						"input#newsched_input_id[type=text][required=true]");
					this.dbname_reg = new ValidationTextBox({
						value:'PHMSA2014',
						regExp:'[\\w]+',
						promptMessage:'Enter New Schedule - only alphanumeric characters and _',
						invalidMessage:'only alphanumeric characters and _',
						missingMessage:'enter schedule name'
					}, sched_input);
				} else {
					// domnode already exists, get widget that should also be there
					this.dbname_reg = registry.byNode(sched_input);
				}

				this.seasondates_btn_reg = registry.byId("seasondates_btn");
				this.newsched_dom = dom.byId("newsched_text");
				this.showConfig();
			},
			set_obj: function(schedutil_obj, storeutil_obj) {
				this.schedutil_obj = schedutil_obj;
				this.storeutil_obj = storeutil_obj;
			},
			showConfig: function() {
				this.uistackmgr.switch_pstackcpane({idproperty:this.idproperty,
					p_stage:"preconfig", entry_pt:"init"});
				this.uistackmgr.switch_gstackcpane(this.idproperty, true);
				var tooltipconfig = {connectId:['newsched_input_id'],
					label:"Enter Schedule Name and press ENTER",
					position:['below','after']};
				this.tooltip = new Tooltip(tooltipconfig);
				if (this.keyup_handle)
					this.keyup_handle.remove();
				this.keyup_handle = this.dbname_reg.on("keyup", lang.hitch(this, this.processdivinfo_input));
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(event) {
				if (event.keyCode == keys.ENTER) {
					if (this.form_reg.validate()) {
						confirm('Input format is Valid, creating new Schedule DB');
						this.newsched_name = this.dbname_reg.get("value");
						if (!this.storeutil_obj.nodupdb_validate(this.newsched_name,
							this.idproperty)) {
							alert("Selected sched name already exists, choose another");
							return;
						}
						// disable schedule name form
						//this.schedutil_obj.makeInvisible(this.form_dom);
						if (this.keyup_handle)
							this.keyup_handle.remove();
						this.newsched_dom.innerHTML = "Schedule Name: "+this.newsched_name;
						// set initial values for seasonstart and end dates
						//this.start_dtbox = registry.byId("seasonstart_date");
						//this.end_dtbox = registry.byId("seasonend_date");
						//this.sl_spinner = registry.byId("seasonlength_spinner");
						var today = new Date();
						//this.start_dtbox.set('value', today);
						//this.end_dtbox.set('value',
						//	date.add(today, 'week', constant.numweeks));
						//this.sl_spinner.set('value', constant.numweeks);
/*
						if (this.seasonstart_handle)
							this.seasonstart_handle.remove();
						this.seasonstart_handle = on(this.start_dtbox,
							"change",
							lang.hitch(this, function(event) {
								console.log('season start handle'+this.event_flag);
								if (!this.event_flag) {
									var enddate = this.end_dtbox.get('value');
									var numweeks = date.difference(event, enddate,'week');
									if (numweeks < 1) {
										alert("end date needs to be at least one week after start date");
										// reset the date to an arbitrary default
										numweeks = this.sl_spinner.get('value');
										//this.seasonstart_handle.pause();
										this.start_dtbox.set('value',
											date.add(enddate, 'week', -numweeks));
										//this.seasonstart_handle.resume();
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
						); */
						/*
						if (this.seasonend_handle)
							this.seasonend_handle.remove();
						this.seasonend_handle = on(this.end_dtbox,
							"change",
							lang.hitch(this, function(event) {
								console.log('season end handle'+this.event_flag);
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
						); */
						/*
						if (this.seasonlength_handle)
							this.seasonlength_handle.remove();
						this.seasonlength_handle = on(this.sl_spinner,
							"change",
							lang.hitch(this, function(event) {
								console.log("season len handle="+this.event_flag)
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
						); */
						/* note pausable/resume handler does not work trying to control changes made to textbox's programmatically
						just use manual event_flag to control double/cascading event firing; set event_flag to true anytime another start/end/length register is set from within a similar handler.  The flag will be used to prevent cascading event handling which will be unnecessary.
						NOTE a boolean event flag only works if a handler sets only one other register.  If multiple registers are set in the
						handler than the event_flag needs to be turned into a counter. */
						var scinput_dom = dom.byId(constant.scinput_div);
						// create season start date entry
						var start_dtbox_node = dom.byId('start_dtbox_id');
						if (!start_dtbox_node) {
							put(scinput_dom,
								"label.label_box[for=start_dtbox_id]",
								"Season Start Date");
							start_dtbox_node = put(scinput_dom,
								"input#start_dtbox_id");
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
											//this.seasonstart_handle.pause();
											this.start_dtbox.set('value',
												date.add(enddate, 'week', -numweeks));
											//this.seasonstart_handle.resume();
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
							}, start_dtbox_node);
						} else {
							this.start_dtbox = registry.byNode(start_dtbox_node);
						}
						// create season end date entry
						var end_dtbox_node = dom.byId('end_dtbox_id');
						if (!end_dtbox_node) {
							put(scinput_dom,
								"label.label_box[for=end_dtbox_id]",
								"Season End Date");
							end_dtbox_node = put(scinput_dom,
								"input#end_dtbox_id");
							this.end_dtbox = new DateTextBox({
								value: date.add(today, 'week', constant.numweeks),
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
						} else {
							this.end_dtbox = registry.byNode(end_dtbox_node);
						}
						// create season length spinner
						var sl_spinner_node = dom.byId('sl_spinner_id');
						if (!sl_spinner_node) {
							put(scinput_dom,
								"label.label_box[for=sl_spinner_id]",
								"Season Length (weeks)");
							sl_spinner_node = put(scinput_dom,
								"input#sl_spinner_id[name=sl_spinner_id]");
							this.sl_spinner = new NumberSpinner({
								value:constant.numweeks,
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
							put(scinput_dom, "br");
						} else {
							this.sl_spinner = registry.byNode(sl_spinner_node);
						}
						// create button to save season start/end/length
						var sdbtn_node = dom.byId("sdbtn_id");
						if (!sdbtn_node) {
							sdbtn_node = put(scinput_dom,
								"button.dijitButton#sdbtn_id[type=button]");
							var sdbtn = new Button({
								label:"Save Season Dates",
								class:"primary",
								onClick: lang.hitch(this,
									this.getSeasonDatesFromInput)
							}, sdbtn_node);
							put(scinput_dom, "br, br");
						}
						// create league info dropdowns
						var select_node = dom.byId("league_select_id");
						if (!select_node) {
							// get parent dom and generate dropdown selects
							put(scinput_dom,
								"label.label_box[for=league_select_id]",
								"Select League");
							select_node = put(scinput_dom,
								"select#league_select_id[name=league_select]");
							this.league_select = new Select({
								name:'league_select',
								onChange: lang.hitch(this, function(evt) {
									// copy event (value of option) to watched obj
									this.newschedwatch_obj.set('leagueselect_val',
										evt);
									this.newschedwatch_obj.set('leagueselect_flag',evt>0);
								})
							}, select_node);
							this.newschedwatch_obj.watch('leagueselect_flag',
								lang.hitch(this,
									function(name, oldValue, value) {
										this.newschedwatch_obj.set('league_fg_flag',
											this.newschedwatch_obj.get('fgselect_flag') && value);
									}
								)
							)
							var option_array = this.generateLabelDropDown('rrdb',
								'Select League');
							this.league_select.addOption(option_array);
							if (option_array.length < 2) {
								var ls_tooltipconfig = {
									connectId:['league_select_id'],
									label:"If Empty Specify League Spec's First",
									position:['above','after']};
								var ls_tooltip = new Tooltip(ls_tooltipconfig);
							}
							put(scinput_dom, "span.empty_gap");  // add space
						} else {
							this.league_select = registry.byNode(select_node);
						}
						// create field group dropdown
						var fg_select_node = dom.byId("fg_select_id");
						if (!fg_select_node) {
							put(scinput_dom,
								"label.label_box[for=fg_select_id]",
								"Select Field Group");
							fg_select_node = put(scinput_dom,
								"select#fg_select_id[name=fg_select]");
							this.fg_select = new Select({
								name:'fg_select',
								onChange: lang.hitch(this, function(evt) {
									// copy event (value of option) to watched obj
									this.newschedwatch_obj.set('fgselect_val',
										evt);
									this.newschedwatch_obj.set('fgselect_flag',
										evt>0);
								})
							}, fg_select_node);
							this.newschedwatch_obj.watch('fgselect_flag',
								lang.hitch(this,
									function(name, oldValue, value) {
										this.newschedwatch_obj.set('league_fg_flag',
											this.newschedwatch_obj.get('leagueselect_flag') && value);
									}
								)
							)
							option_array = this.generateLabelDropDown('fielddb',
								'Select Field Group');
							this.fg_select.addOption(option_array);
							if (option_array.length < 2) {
								var fg_tooltipconfig = {
									connectId:['fg_select_id'],
									label:"If Empty Specify Field Groups First",
									position:['above','after']};
								var fg_tooltip = new Tooltip(fg_tooltipconfig);
							}
							put(scinput_dom, "span.empty_gap");
						} else {
							this.fg_select = registry.byNode(fg_select_node);
						}
						var btn_node = dom.byId("schedparambtn_id");
						if (!btn_node) {
							btn_node = put(scinput_dom,
								"button.dijitButton#schedparambtn_id[type=button]");
							var btn_tooltipconfig = {
								connectId:['schedparambtn_id'],
								label:"Ensure League and Field Group are Selected",
								position:['above','after']};
							var schedule_btn = new Button({
								label:"Generate",
								disabled:true,
								class:"success",
							}, btn_node);
							schedule_btn.startup();
							var btn_tooltip = new Tooltip(btn_tooltipconfig);
							this.newschedwatch_obj.watch('league_fg_flag',
								function(name, oldValue, value) {
									if (value) {
										schedule_btn.set('disabled', false);
										btn_tooltipconfig.set('label',
											'Press to Save Sched Parameters');
									}
								}
							)
						}
						// set flag that is used by observable memory update in
						// storeutl
						this.selectexists_flag = true;
						// need to add btn callbacks here
						this.uistackmgr.switch_pstackcpane({
							idproperty:this.idproperty, p_stage:"config",
							entry_pt:"init"});
					} else {
						alert('Input name is Invalid, please correct');
					}
				}
			},
			removefrom_select: function(db_type, index) {
				// remove entries from the div or field group dropdown
				if (db_type == 'rrdb') {
					this.league_select.removeOption(index);
				} else if (db_type == 'fielddb') {
					this.fg_select.removeOption(index)
				}
			},
			addto_select: function(db_type, label, insertIndex) {
				var soption_obj = {label:label, value:insertIndex+1,
					selected:false};
				if (db_type == 'rrdb') {
					this.league_select.addOption(soption_obj);
				} else if (db_type == 'fielddb') {
					this.fg_select.addOption(soption_obj);
				}
			},
			getSeasonDatesFromInput: function(event) {
				var seasonstart_date = this.start_dtbox.get("value");
				var seasonend_date = this.end_dtbox.get("value");
				var season_len = this.sl_spinner.get("value");
				baseinfoSingleton.watch_obj.set('numweeks', season_len);
			},
			is_serverdata_required: function(options_obj) {
				// follow up on cases where data needs to be queried from server.
				return false;
			},
			is_newgrid_required: function() {
				return false;
			},
			generateLabelDropDown: function(db_type, label_str) {
				// get list of db's from store that have been completed
				var label_list = this.storeutil_obj.getfromdb_store_value(db_type,
					'label', true);
				var option_array = [{label:label_str, value:"",
					selected:true}];
				arrayUtil.forEach(label_list, function(item, index) {
					option_array.push({label:item, value:index+1, selected:false});
				});
				return option_array;
			},
			cleanup: function() {
				if (this.seasonstart_handle)
					this.seasonstart_handle.remove();
				if (this.seasonend_handle)
					this.seasonend_handle.remove();
				if (this.seasonlength_handle)
					this.seasonlength_handle.remove();
				if (this.tooltip)
					this.tooltip.destroyRecursive();
				if (this.dbname_reg)
					this.dbname_reg.destroyRecursive();
			}
		});
	})
