/* manage UI content pane structure, especially switching stack container panes */
define(["dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array", "dojo/dom",
	"dijit/registry", "dijit/layout/StackContainer", "dijit/layout/ContentPane",
	"dijit/layout/BorderContainer", "dijit/form/Form", "put-selector/put", "dojo/domReady!"],
	function(declare, lang, arrayUtil, dom, registry, StackContainer, ContentPane,
		BorderContainer, Form, put) {
		var constant = {
			// parameter stack container id's
			divparamcontainer_id:"divparamcontainer_id",
			fieldparamcontainer_id:"fieldparamcontainer_id",
			tourndivparamcontainer_id:"tourndivparamcontainer_id",
			newschedparamcontainer_id:"newschedparamcontainer_id",
			prefparamcontainer_id:"prefparamcontainer_id",
			// grid stack container id's
			divgridcontainer_id:"divgridcontainer_id",
			fieldgridcontainer_id:"fieldgridcontainer_id",
			tourndivgridcontainer_id:"tourndivgridcontainer_id",
			newschedgridcontainer_id:"newschedgridcontainer_id",
			prefgridcontainer_id:"prefgridcontainer_id",
			// param stack  cpaneid's
			dummy_id:"wizdummy_id",
			nfcpane_id:"wiznumfieldcpane_id",
			tcpane_id:"wiztextbtncpane_id",
			ndcpane_id:"wiznumdivcpane_id",
			ntcpane_id:"wiznumtourndivcpane_id",
			nscpane_id:"wiznewschedcpane_id",
			sccpane_id:"wizseasoncalendar_input",
			ppcpane_id:"wizprefparamcpane_id",
			// grid stack id's
			gstackcontainer_id:"wizgridContainer_id",
			divcpane_id:"wizdivinfocpane_id",
			tourndivcpane_id:"wiztourndivinfocpane_id",
			fieldbcontainer_id:"wizfieldinfobcontainer_id",
			fieldcpane_id:"wizfieldinfocpane_id",
			blankcpane_id:"wizblankcpane_id",
			prefcpane_id:"wizprefinfocpane_id",
			// entry_pt id's
			init:"init", fromdb:"fromdb", fromdel:"fromdel",
			// form and span id's
			nscform_id:"wiznewsched_form_id",
			nsctxt_id:"wiznewschedtxt_id",
			infotxt_id:"wizinfotxt_id",
			infobtn_id:"wizinfobtn_id",
			fform_id:"wizfield_form_id",
			dform_id:"wizdiv_form_id",
			tdform_id:"wiztourndiv_form_id",
			pform_id:"wizpref_form_id",
			// grid hosting div id's
			divgrid_id:"wizdivinfogrid_id",
			tourndivgrid_id:"wiztourndivinfogrid_id",
			prefgrid_id:"wizprefinfogrid_id",
			fieldgrid_id:"wizfieldinfogrid_id"
		};
		return declare(null, {
			pstackcontainer_list:null, pstackmap_list:null,
			gstackcontainer_list:null, gstackmap_list:null,
			cpanestate_list:null, updatebtn_widget:null,
			current_grid:null, null_cpanestate:null,
			constructor: function(args) {
				lang.mixin(this, args);
				// For the wizard page, there will be stack container
				// per wizard pane (wizard page); control for switching
				// panes will be limited to switching cpanes within the wizard
				// pane.
				this.pstackcontainer_list = new Array();
				this.pstackcontainer_list.push({id:'field_id',
					container_id:constant.fieldparamcontainer_id});
				this.pstackcontainer_list.push({id:'div_id',
					container_id:constant.divparamcontainer_id});
				this.pstackcontainer_list.push({id:'tourndiv_id',
					container_id:constant.tourndivparamcontainer_id});
				this.pstackcontainer_list.push({id:'newsched_id',
					container_id:constant.newschedparamcontainer_id});
				this.pstackcontainer_list.push({id:'pref_id',
					container_id:constant.prefparamcontainer_id});
				// initialized grid stack container list
				this.gstackcontainer_list = new Array();
				this.gstackcontainer_list.push({id:'field_id',
					container_id:constant.fieldgridcontainer_id});
				this.gstackcontainer_list.push({id:'div_id',
					container_id:constant.divgridcontainer_id});
				this.gstackcontainer_list.push({id:'tourndiv_id',
					container_id:constant.tourndivgridcontainer_id});
				this.gstackcontainer_list.push({id:'newsched_id',
					container_id:constant.newschedgridcontainer_id});
				this.gstackcontainer_list.push({id:'pref_id',
					container_id:constant.prefgridcontainer_id});
				// define param stack mapping that maps tuple (idproperty, config stage)->
				// param content pane
				this.pstackmap_list = new Array();
				this.pstackmap_list.push({id:'field_id', p_stage:'preconfig',
					pane_id:constant.nfcpane_id});
				this.pstackmap_list.push({id:'field_id', p_stage:'config',
					pane_id:constant.tcpane_id});
				this.pstackmap_list.push({id:'div_id', p_stage:'preconfig',
					pane_id:constant.ndcpane_id});
				this.pstackmap_list.push({id:'div_id', p_stage:'config',
					pane_id:constant.tcpane_id});
				this.pstackmap_list.push({id:'tourndiv_id', p_stage:'preconfig',
					pane_id:constant.ntcpane_id});
				this.pstackmap_list.push({id:'tourndiv_id', p_stage:'config',
					pane_id:constant.tcpane_id});
				this.pstackmap_list.push({id:'newsched_id', p_stage:'preconfig',
					pane_id:constant.nscpane_id});
				this.pstackmap_list.push({id:'newsched_id', p_stage:'config',
					pane_id:constant.sccpane_id});
				this.pstackmap_list.push({id:'pref_id', p_stage:'preconfig',
					pane_id:constant.ppcpane_id});
				this.pstackmap_list.push({id:'pref_id', p_stage:'config',
					pane_id:constant.tcpane_id});
				// define mapping object for the grid content pane
				// gstackmap_list maps from id to corresponding grid name
				// note idprop newsched_id has no grid the cpane is blank.
				this.gstackmap_list = [{id:'newsched_id', pane_id:constant.blankcpane_id},
					{id:'div_id', pane_id:constant.divcpane_id},
					{id:'tourndiv_id', pane_id:constant.tourndivcpane_id},
					{id:'field_id', pane_id:constant.fieldbcontainer_id},
					{id:'pref_id', pane_id:constant.prefcpane_id}];
				this.cpanestate_list = new Array();
				this.null_cpanestate = {
						p_pane:null, p_stage:null, entry_pt:null,
						g_pane:constant.blankcpane_id,
						text_str:"", btn_callback:null, updatebtn_str:"",
						active_flag:false};
				arrayUtil.forEach(this.gstackmap_list, function(item, index) {
					/* cpanestate_list tracks current configuration state for each
					idproperty: p_pane: parameter pane name, p_stage: parameter p_stage state, entry_pt: who called - init or getserverdb,
					g_pane: grid name, text_str, btn_callback: send server button
					parameters, active_flag:boolean whether idprop is currently
					active or not.
					*/
					this.cpanestate_list.push({id:item.id,
						p_pane:null, p_stage:null, entry_pt:null,
						g_pane:constant.blankcpane_id,
						text_str:"", btn_callback:null, updatebtn_str:"",
						active_flag:false});
				}, this);
			},
			getmatch_obj: function(list, key, value) {
				var match_list = arrayUtil.filter(list,
					function(item) {
						return item[key] == value;
					});
				return match_list[0];
			},
			initstacks: function(id, container_node) {
				var match_obj = this.getmatch_obj(
					this.pstackcontainer_list, 'id', id);
				var container_id = match_obj.containter_id;
				var pstackcontainer = new StackContainer({
					id:container_id,
					doLayout:false,
					style:"float:left; width:80%"
				}, container_node);
				var dummy_cpane = new ContentPane({
					id:id+constant.dummy_id
				})
				pstackcontainer.addChild(dummy_cpane)
				var pane_id = this.getp_pane(id, 'preconfig');

			},
			switch_pstackcpane: function(args_obj) {
				id = args_obj.idproperty;
				p_stage = args_obj.p_stage;
				var select_pane = this.getp_pane(id, p_stage);
				this.pstackcontainer_reg.selectChild(select_pane);
				// retrieve actual obj and find index
				var state_obj = this.get_cpanestate(id);
				var match_obj = state_obj.match_obj;
				//var index = state_obj.index;
				// http://dojotoolkit.org/documentation/tutorials/1.9/augmenting_objects/
				lang.mixin(match_obj, args_obj);
				match_obj.p_pane = select_pane;
				this.setreset_cpanestate_active(match_obj);
				// not necessary to reassign as the list index already points
				// to match_obj
				//this.cpanestate_list[index] = match_obj;
			},
			reset_cpane: function(idproperty) {
				// reset pstackcpane for idproperty to quiscent/initial state
				this.pstackcontainer_reg.selectChild(constant.dummy_id);
				var match_obj = this.get_cpanestate(idproperty).match_obj;
				lang.mixin(match_obj, this.null_cpanestate);
				this.gstackcontainer_reg.selectChild(constant.blankcpane_id);
				this.reset_cpanestate_active();
			},
			swapactive_pgstackcpane: function(match_obj) {
				this.pstackcontainer_reg.selectChild(match_obj.p_pane);
				this.gstackcontainer_reg.selectChild(match_obj.g_pane);
				this.setreset_cpanestate_active(match_obj);
			},
			get_cpanestate: function(id) {
				var idmatch_list = arrayUtil.filter(this.cpanestate_list,
					function(item, index) {
						return item.id == id;
					})
				if (idmatch_list.length > 0) {
					// retrieve actual obj and find index
					var match_obj = idmatch_list[0];  // there should only be one elem
					var index = this.cpanestate_list.indexOf(match_obj);
					return {match_obj:match_obj, index:index};
				} else
					return null;
			},
			// find the cpanestate that was last active
			get_cpanestate_active: function() {
				var idmatch_list = arrayUtil.filter(this.cpanestate_list,
					function(item, index) {
						return item.active_flag == true;
					})
				if (idmatch_list.length > 0) {
					// retrieve actual obj and find index
					var match_obj = idmatch_list[0];  // there should only be one elem
					var index = this.cpanestate_list.indexOf(match_obj);
					return {match_obj:match_obj, index:index};
				} else
					return null;
			},
			getp_pane: function(id, p_stage) {
				// get parameter pane corresponding to id and p_stage
				// ('config' or 'preconfig')
				var idmatch_list = arrayUtil.filter(this.pstackmap_list,
					function(item, index) {
						return item.id == id && item.p_stage == p_stage;
					});
				return idmatch_list[0].pane_id;
			},
			setreset_cpanestate_active: function(match_obj) {
				this.reset_cpanestate_active();
				match_obj.active_flag = true;
			},
			reset_cpanestate_active: function() {
				var active_state = this.get_cpanestate_active();
				if (active_state) {
					var oldmatch_obj = active_state.match_obj;
					oldmatch_obj.active_flag = false;
				}
			},
			switch_gstackcpane: function(id, blankcpane_flag, current_grid) {
				var blankcpane_flag = (typeof blankcpane_flag === "undefined") ? false:blankcpane_flag;
				var select_pane = "";
				if (blankcpane_flag) {
					select_pane = constant.blankcpane_id;
				} else {
					var idmatch_list = arrayUtil.filter(this.gstackmap_list,
						function(item, index) {
							return item.id == id;
						});
					select_pane = idmatch_list[0].pane_id;
					this.current_grid = current_grid;
					//this.current_grid.resize();
				}
				this.gstackcontainer_reg.selectChild(select_pane);
				// update cpane list state
				var state_obj = this.get_cpanestate(id);
				var match_obj = state_obj.match_obj;
				var index = state_obj.index;
				// modify matched obj
				match_obj.g_pane = select_pane;
				// assign db collection name to match_obj property
				this.setreset_cpanestate_active(match_obj);
				this.cpanestate_list[index] = match_obj;
				// do the reisze after the pane has been selected
				if (this.current_grid)
					this.current_grid.resize();
				this.scrollTopEditPane()
			},
			check_initialize: function(info_obj, event) {
				/* initialization UI is selected; manage pane change to initialization UI
				Scenarios to consider:
				a) switch within same idproperty - config to preconfig
				b) switch between different idproperty - grid to preconfig
				c) switch between different idproperty - preconfig to preconfig
				d) swith with same id - preconfig to preconfig - (do nothing)
				e) no switch - previous pane does not exist - init preconfig
				f) switch within same idprop - config to config

				Note we don't need to get data from server for any scenario
				*/
				var new_idproperty = info_obj.idproperty;
				var newgrid_flag = info_obj.is_newgrid_required();
				var state_obj = this.get_cpanestate(new_idproperty);
				var match_obj = state_obj.match_obj;
				var lastp_stage = match_obj.p_stage;
				if (match_obj.active_flag) {
					// this is going to be scenario a or d
					// get the last stage for idproperty
					if (lastp_stage) {
						if (lastp_stage == 'preconfig') {
							// scenario d), do nothing
							return;
						} else {
							// remaining pstage is 'config', switch to preconfig
							// get the preconfig pane
							info_obj.initialize(newgrid_flag);
						}
					} else {
						// this should not happen since active_flag was on
						console.log("check_initialize - logic error");
						alert("initialization logic error");
						return;
					}
				} else {
					// scenarios b, c, or e
					if (match_obj.p_stage) {
						if (match_obj.entry_pt == constant.init) {
							// if previous match for idprop was also an init
							// then just swap into that
							this.swapactive_pgstackcpane(match_obj);
							if (new_idproperty != 'newsched_id')
								// newsched_id does not have reconfig... method
								info_obj.reconfig_infobtn_fromuistack(match_obj);
						} else {
							// else if previous match for idprop was from server
							// then call init
							info_obj.initialize(newgrid_flag);
						}
					} else {
						// if no p_stage with matched obj, then initialize
						info_obj.initialize(newgrid_flag);
					}
				}
			},
			check_getServerDBInfo: function(options_obj) {
				/* scenarios:
				a)switch within same idprop: one grid to another grid - grid doesn't exist
				b)switch within same idprop: incomplete preconfig to different grid that already exists
				c)switch within same idprop: incomplete preconfig to different grid
				that doesn't exist yet
				d)switch between different idprop: one grid to another grid
				e)switch between different idprop: one incomplete preconfig to
				different id grid
				f)switch within same idprop: one grid to same grid (do nothing)
				g)no switch - directly call new grid
				h)switch within same idprop: incomplete preconfig to different grid - grid exists for different data, needs to be swapped out
				i)switch within same idprop: one grid to another grid -
				grid exists but needs to be swapped out
				For each of the scenarios above, we need to decide if we need to get
				data from the server and/or switch content panes; we also need to
				determine if grid needs to be swapped or created*/
				var info_obj = options_obj.info_obj;
				// get incoming idproperty
				var new_idproperty = info_obj.idproperty;
				var state_obj = this.get_cpanestate(new_idproperty);
				var match_obj = state_obj.match_obj;
				var lastp_stage = match_obj.p_stage;
				var newgrid_flag = info_obj.is_newgrid_required();
				if (match_obj.active_flag) {
					// same idprop: scenarios a,b,c,h
					if (lastp_stage) {
						if (lastp_stage == 'preconfig') {
							// we need to swap cpane from preconfig to config
							// even though we are in the same idprop
							// scenarios b,c,h
							// Note if we are in the same idprop we are always going to a config state in this scenario (only one preconfig state per idprop)
							options_obj.swapcpane_flag = true;
							// find if idprop-specific logic requires a new grid to be generated.
							options_obj.newgrid_flag = newgrid_flag;
							if (newgrid_flag) {
								// if new grid is required, set flag  and get server data. this is scenario c)
								info_obj.getServerDBInfo(options_obj);
							} else {
								/* grid already exists; determine if grid name
								matches name of incoming g_pane_colname, or if we need to get server data to swap out grid contents */
								if (info_obj.is_serverdata_required(options_obj)) {
									// scenario h
									info_obj.getServerDBInfo(options_obj);
								} else {
									if (new_idproperty != 'newsched_id') {
										/* Not relevant for newsched_id which doesn't have an infobtn.
										Otherwise, scenario b, but see if there is an exception
										situation to regenerate grid (i.e. for fieldinfo when there is a divinfo colname) */
										var args_obj = {
											colname:options_obj.item,
											text_node_str:options_obj.text_node_str,
											text_node:options_obj.text_node,
											updatebtn_str:options_obj.updatebtn_str,
											idproperty:new_idproperty,
											swapcpane_flag:true,
											newgrid_flag:false,
											entry_pt:constant.fromdb
										}
										info_obj.reconfig_infobtn(args_obj);
									} else {
										// if it newsched_id, we still have to switch cpane
										var args_obj = {
											idproperty:'newsched_id',
											p_stage:'config',
											entry_pt:constant.fromdb
										}
										this.switch_pstackcpane(args_obj);
										// 'true' argument indicates we are switching to a
										// state where no grid is required
										this.switch_gstackcpane('newsched_id', true);
									}
								}
							}
						} else {
							/* p_stage is config
							scenarios a, f, i */
							options_obj.swapcpane_flag = false;
							options_obj.newgrid_flag = newgrid_flag;
							if (newgrid_flag) {
								// scenario a
								info_obj.getServerDBInfo(options_obj);
							} else {
								// scenario f and i.
								// don't need to do anything for scenario f
								if (info_obj.is_serverdata_required(options_obj)) {
									// scenario i
									info_obj.getServerDBInfo(options_obj);
								}
							}
						}
					} else {
						// this should not happen since active_flag was on
						console.log("Error code 2: check_getServerDBInfo - logic error");
						alert("Error Code 2");
						return;
					}
				} else {
					// idprop is switching
					options_obj.swapcpane_flag = true;
					options_obj.newgrid_flag = newgrid_flag;
					if (newgrid_flag) {
						// if new grid is required, set flag  and get server data.
						info_obj.getServerDBInfo(options_obj);
					} else {
						/* grid already exists; determine if grid name
						matches name of incoming g_pane_colname, or if we need to get server data to swap out grid contents */
						if (info_obj.is_serverdata_required(options_obj)) {
							info_obj.getServerDBInfo(options_obj);
						} else {
							if (new_idproperty != 'newsched_id') {
								var args_obj = {
									colname:options_obj.item,
									text_node_str:options_obj.text_node_str,
									text_node:options_obj.text_node,
									updatebtn_str:options_obj.updatebtn_str,
									idproperty:new_idproperty,
									swapcpane_flag:true,
									newgrid_flag:false,
									entry_pt:constant.fromdb
								}
								info_obj.reconfig_infobtn(args_obj);
							} else {
								// if it newsched_id, we still have to switch cpane
								var args_obj = {
									idproperty:'newsched_id',
									p_stage:'config', entry_pt:constant.fromdb
								}
								this.switch_pstackcpane(args_obj);
								// 'true' argument indicates we are switching to a
								// state where no grid is required
								this.switch_gstackcpane('newsched_id', true);
							}
						}
					}
				}
			},
			scrollTopEditPane: function() {
				console.log("scroll to top");
				//http://dojo-toolkit.33424.n3.nabble.com/Force-ContentPane-to-scroll-to-top-when-showing-td158406.html
				// ensure edit pane scroll resets to top
				// seems like scrolling to top only works if it works off of onLoad and not onShow
				var pane_dom = dom.byId("editPane");
				pane_dom.scrollTop = 0;
			},
			create_paramcpane_stack: function(container_cpane) {
				// programmatically create parameter config cpane stack
				// reference on use of different kinds of id's:
				// http://dojotoolkit.org/reference-guide/1.9/dijit/registry.html#data-dojo-id-jsid-before-dojo-1-6
				// http://stackoverflow.com/questions/12469140/difference-between-id-and-data-dojo-id
				var param_scontainer = new StackContainer({
					id:constant.pstackcontainer_id,
					doLayout:false,
					style:"float:left; width:80%"
				})
				this.pstackcontainer_reg = param_scontainer;
				container_cpane.addChild(param_scontainer);
				// create dummy blank pane
				var dummy_cpane = new ContentPane({
					id:constant.dummy_id
				})
				param_scontainer.addChild(dummy_cpane);
				// add newscheduler config cpane
				var newsched_cpane = new ContentPane({
					id:constant.nscpane_id
				})
				var newsched_form = new Form({
					id:constant.nscform_id
				});
				newsched_cpane.addChild(newsched_form);
				param_scontainer.addChild(newsched_cpane)
				// add season calendar input cpane
				var scinput_cpane = new ContentPane({
					id:constant.sccpane_id
				})
				put(scinput_cpane.containerNode, "span[id=$]",constant.nsctxt_id)
				param_scontainer.addChild(scinput_cpane)
				// add txt + button cpane
				var txtbtn_cpane = new ContentPane({
					id:constant.tcpane_id
				})
				put(txtbtn_cpane.containerNode, "span[id=$]", constant.infotxt_id);
				put(txtbtn_cpane.containerNode, "div[id=$]", constant.infobtn_id);
				param_scontainer.addChild(txtbtn_cpane);
				// add field config (number) cpane
				var field_cpane = new ContentPane({
					id:constant.nfcpane_id
				});
				var field_form = new Form({
					id:constant.fform_id
				})
				field_cpane.addChild(field_form);
				param_scontainer.addChild(field_cpane);
				// add div config (number) cpane
				var div_cpane = new ContentPane({
					id:constant.ndcpane_id
				})
				var div_form = new Form({
					id:constant.dform_id
				})
				div_cpane.addChild(div_form);
				param_scontainer.addChild(div_cpane);
				// add tourndiv config (number) cpane
				var tdiv_cpane = new ContentPane({
					id:constant.ntcpane_id
				})
				var tdiv_form = new Form({
					id:constant.tdform_id
				})
				tdiv_cpane.addChild(tdiv_form);
				param_scontainer.addChild(tdiv_cpane);
				// add preference config
				var pref_cpane = new ContentPane({
					id:constant.ppcpane_id
				})
				var pref_form = new Form({
					id:constant.pform_id
				})
				pref_cpane.addChild(pref_form);
				param_scontainer.addChild(pref_cpane)
			},
			create_grid_stack: function(container_cpane) {
				// programmatically create grid stack
				// manage switching between grids by using content panes embedded in stack container
				// note http://dojotoolkit.org/reference-guide/1.9/dijit/layout/StackContainer.html for layout guidance
				// http://css.maxdesign.com.au/floatutorial/
				var grid_scontainer = new StackContainer({
					id:constant.gstackcontainer_id,
					doLayout:false,
					style:"clear:left"
				})
				this.gstackcontainer_reg = grid_scontainer;
				container_cpane.addChild(grid_scontainer);
				// add blank pane (for resetting)
				var blank_cpane = new ContentPane({
					id:constant.blankcpane_id
				})
				grid_scontainer.addChild(blank_cpane);
				// add divinfo cpane and grid div
				var div_cpane = new ContentPane({
					id:constant.divcpane_id
				})
				put(div_cpane.containerNode, "div[id=$]", constant.divgrid_id);
				grid_scontainer.addChild(div_cpane);
				// add tournament divinfo cpane and grid div
				var tdiv_cpane = new ContentPane({
					id:constant.tourndivcpane_id
				})
				put(tdiv_cpane.containerNode, "div[id=$]", constant.tourndivgrid_id);
				grid_scontainer.addChild(tdiv_cpane);
				// add preference info cpane and grid div
				var pdiv_cpane = new ContentPane({
					id:constant.prefcpane_id
				})
				put(pdiv_cpane.containerNode, "div[id=$]", constant.prefgrid_id);
				grid_scontainer.addChild(pdiv_cpane);
				// add field info border container, inside cpane and grid div
				var field_bcontainer = new BorderContainer({
					id:constant.fieldbcontainer_id,
					design:'headline', gutters:true, liveSplitters:true,
					style:"height:800px; width:100%"
				})
				var field_cpane = new ContentPane({
					id:constant.fieldcpane_id,
					region:'top',
					style:"height:300px; width:100%"
				})
				put(field_cpane.containerNode, "div[id=$]",
					constant.fieldgrid_id);
				field_bcontainer.addChild(field_cpane);
				grid_scontainer.addChild(field_bcontainer);
			}
		});
	}
);