define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare",
	"dojo/_base/lang", "dojo/date", "dojo/Stateful",
	"dojo/_base/array", "dojo/keys", "dojo/store/Memory",
	"dijit/registry", "dijit/Tooltip", "dijit/form/ValidationTextBox", "dijit/form/Select", "dijit/form/Button",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection", "LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, date, Stateful, arrayUtil, keys,
		Memory,registry, Tooltip, ValidationTextBox, Select, Button,
		OnDemandGrid, editor, Keyboard, Selection, EditGrid,
		baseinfoSingleton, put) {
		var constant = {
			weekoffset:12,
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
			seasonstart_reg:null, seasonend_reg:null, seasonlength_reg:null,
			seasonstart_handle:null, seasonend_handle:null,
			seasonlength_handle:null, league_select:null, fg_select:null,
			eventsrc_flag:false, uistackmgr:null, newschedwatch_obj:null,
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
						this.seasonstart_reg = registry.byId("seasonstart_date");
						this.seasonend_reg = registry.byId("seasonend_date");
						this.seasonlength_reg = registry.byId("seasonlength_spinner");
						var today = new Date();
						this.seasonstart_reg.set('value', today);
						this.seasonend_reg.set('value',
							date.add(today, 'week', constant.weekoffset));
						this.seasonlength_reg.set('value', constant.weekoffset);
						if (this.seasonstart_handle)
							this.seasonstart_handle.remove();
						// note pausable/resume handler does not work trying to control changes made to textbox's programmatically
						// just use manual eventsrc_flag to control double/cascading event firing
						this.seasonstart_handle = on(this.seasonstart_reg,
							"change",
							lang.hitch(this, function(event) {
								if (!this.eventsrc_flag) {
									var enddate = this.seasonend_reg.get('value');
									var numweeks = date.difference(event, enddate,'week');
									if (numweeks < 1) {
										alert("end date needs to be at least one week after start date");
										// reset the date to an arbitrary default
										numweeks = this.seasonlength_reg.get('value');
										//this.seasonstart_handle.pause();
										this.seasonstart_reg.set('value',
											date.add(enddate, 'week', -numweeks));
										//this.seasonstart_handle.resume();
									} else {
										this.eventsrc_flag = true;
										//this.seasonlength_handle.pause();
										this.seasonlength_reg.set('value', numweeks);
										//this.seasonlength_handle.resume();
									}
								} else {
									this.eventsrc_flag = false;
								}
							})
						);
						if (this.seasonend_handle)
							this.seasonend_handle.remove();
						this.seasonend_handle = on(this.seasonend_reg,
							"change",
							lang.hitch(this, function(event) {
								if (!this.eventsrc_flag) {
									var startdate = this.seasonstart_reg.get('value');
									var numweeks = date.difference(startdate, event,'week');
									if (numweeks < 1) {
										alert("end date needs to be at least one week after start date");
										numweeks = this.seasonlength_reg.get('value');
										//this.seasonend_handle.pause();
										this.seasonend_reg.set('value',
											date.add(startdate, 'week', numweeks));
										//this.seasonend_handle.resume();
									} else {
										this.eventsrc_flag = true;
										//this.seasonlength_handle.pause();
										this.seasonlength_reg.set('value', numweeks);
										//this.seasonlength_handle.resume();
									}
								} else {
									this.eventsrc_flag = false;
								}
							})
						);
						if (this.seasonlength_handle)
							this.seasonlength_handle.remove();
						this.seasonlength_handle = on(this.seasonlength_reg,
							"change",
							lang.hitch(this, function(event) {
								if (!this.eventsrc_flag) {
									var startdate = this.seasonstart_reg.get('value');
									var enddate = date.add(startdate, 'week', event);
									//this.seasonend_handle.pause();
									this.eventsrc_flag = true;
									this.seasonend_reg.set('value', enddate);
									//this.seasonend_handle.resume();
								} else {
									this.eventsrc_flag = false;
								}
							})
						);
						/*
						if (this.sdates_handle)
							this.sdates_handle.remove();
						this.sdates_handle = this.seasondates_btn_reg.on("click",
							lang.hitch(this, this.getSeasonDatesFromInput)); */
						var scinput_dom = dom.byId(constant.scinput_div);
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
						var select_div = dom.byId("league_select_id");
						if (!select_div) {
							// get parent dom and generate dropdown selects
							put(scinput_dom,
								"label.label_box[for=league_select_id]",
								"Select League");
							select_div = put(scinput_dom,
								"select#league_select_id[name=league_select]");
							this.league_select = new Select({
								name:'league_select',
								onChange: lang.hitch(this, function(evt) {
									// copy event (value of option) to watched obj
									this.newschedwatch_obj.set('leagueselect_val',
										evt);
									this.newschedwatch_obj.set('leagueselect_flag',evt>0);
								})
							}, select_div);
							this.newschedwatch_obj.watch('leagueselect_flag',
								lang.hitch(this,
									function(name, oldValue, value) {
										this.newschedwatch_obj.set('league_fg_flag',
											this.newschedwatch_obj.get('fgselect_flag') && value);
									}
								)
							)
							var option_array = this.generateLabelDropDown('db',
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
							this.league_select = registry.byNode(select_div);
						}
						var fg_select_div = dom.byId("fg_select_id");
						if (!fg_select_div) {
							put(scinput_dom,
								"label.label_box[for=fg_select_id]",
								"Select Field Group");
							fg_select_div = put(scinput_dom,
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
							}, fg_select_div);
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
							this.fg_select = registry.byNode(fg_select_div);
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
				if (db_type == 'db') {
					this.league_select.removeOption(index);
				} else if (db_type == 'fielddb') {
					this.fg_slect.removeOption(index)
				}
			},
			addto_select: function(db_type, label, insertIndex) {
				var soption_obj = {label:label, value:insertIndex+1,
					selected:false};
				if (db_type == 'db') {
					this.league_select.addOption(soption_obj);
				} else if (db_type == 'fielddb') {
					this.fg_slect.addOption(soption_obj);
				}
			},
			getSeasonDatesFromInput: function(event) {
				var seasonstart_date = this.seasonstart_reg.get("value");
				var seasonend_date = this.seasonend_reg.get("value");
				var season_len = this.seasonlength_reg.get("value");
				console.log("start end="+seasonstart_date+" "+seasonend_date);
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
				var label_list = this.storeutil_obj.getfromdb_store_value(db_type,
					'label');
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
