/* manage UI content pane structure, especially switching stack container panes */
define(["dbootstrap",  "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array", "dijit/registry", "dojo/domReady!"],
	function(dbootstrap, declare, lang, arrayUtil, registry) {
		var constant = {
			// param stack id's
			pstackcontainer_id:"paramStackContainer_id",
			nfcpane_id:"numfieldcpane_id",
			tcpane_id:"textbtncpane_id",
			ndcpane_id:"numdivcpane_id",
			sdcpane_id:"scheddivcpane_id",
			nscpane_id:"newschedcpane_id",
			sccpane_id:"seasoncalendar_input",
			// grid stack id's
			gstackcontainer_id:"gridContainer_id",
			divcpane_id:"divinfocpane_id",
			schedcpane_id:"schedinfocpane_id",
			fieldcpane_id:"fieldinfocpane_id",
			blankcpane_id:"blankcpane_id"
		};
		return declare(null, {
			pstackcontainer_reg:null, pstackmap_list:null,
			gstackcontainer_reg:null, gstackmap_list:null,
			cpanestate_list:null, updatebtn_widget:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.pstackcontainer_reg = registry.byId(constant.pstackcontainer_id);
				// define param stack mapping that maps tuple (id_property, config stage)->
				// param content pane
				this.pstackmap_list = new Array();
				this.pstackmap_list.push({id:'field_id', stage:'preconfig',
					pane_id:constant.nfcpane_id});
				this.pstackmap_list.push({id:'field_id', stage:'config',
					pane_id:constant.tcpane_id});
				this.pstackmap_list.push({id:'div_id', stage:'preconfig',
					pane_id:constant.ndcpane_id});
				this.pstackmap_list.push({id:'div_id', stage:'config',
					pane_id:constant.tcpane_id});
				this.pstackmap_list.push({id:'sched_id', stage:'preconfig',
					pane_id:constant.sdcpane_id})
				this.pstackmap_list.push({id:'sched_id', stage:'config',
					pane_id:constant.tcpane_id});
				this.pstackmap_list.push({id:'newsched_id', stage:'preconfig',
					pane_id:constant.nscpane_id});
				this.pstackmap_list.push({id:'newsched_id', stage:'config',
					pane_id:constant.sccpane_id});
				// define mapping object for the grid content pane
				this.gstackcontainer_reg = registry.byId(constant.gstackcontainer_id);
				var id_list = ['newsched_id', 'div_id', 'sched_id',
					'field_id'];
				var cpane_list = [constant.blankcpane_id,
					constant.divcpane_id,
					constant.schedcpane_id,
					constant.fieldcpane_id];
				this.gstackmap_list = new Array();
				this.cpanestate_list = new Array();
				arrayUtil.forEach(id_list, function(item, index) {
					this.gstackmap_list.push({id:item,
					pane_id:cpane_list[index]});
					this.cpanestate_list.push({id:item,
						p_pane:null, p_stage:null,
						g_pane:null, text_str:"", btn_callback:null,
						active_flag:false})
				}, this);
			},
			switch_pstackcpane: function(id, stage, text_str, btn_callback) {
				var idmatch_list = arrayUtil.filter(this.pstackmap_list,
					function(item, index) {
						return item.id == id && item.stage == stage;
					});
				var select_pane = idmatch_list[0].pane_id;
				this.pstackcontainer_reg.selectChild(select_pane);
				// retrieve actual obj and find index
				var state_obj = this.get_cpanestate(id);
				var match_obj = state_obj.match_obj;
				var index = state_obj.index;
				// modify matched obj
				match_obj.p_pane = select_pane;
				match_obj.p_stage = stage;
				match_obj.text_str = text_str || "";
				match_obj.btn_callback = btn_callback;
				this.setreset_cpanestate_active(match_obj);
				this.cpanestate_list[index] = match_obj;
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
			setreset_cpanestate_active: function(match_obj) {
				var active_state = this.get_cpanestate_active();
				if (active_state) {
					var oldmatch_obj = active_state.match_obj;
					oldmatch_obj.active_flag = false;
				}
				match_obj.active_flag = true;
			},
			switch_gstackcpane: function(id) {
				var idmatch_list = arrayUtil.filter(this.gstackmap_list,
					function(item, index) {
						return item.id == id;
					});
				var select_pane = idmatch_list[0].pane_id;
				this.gstackcontainer_reg.selectChild(select_pane);
				// update cpane list state
				var state_obj = this.get_cpanestate(id);
				var match_obj = state_obj.match_obj;
				var index = state_obj.index;
				// modify matched obj
				match_obj.g_pane = select_pane;
				this.setreset_cpanestate_active(match_obj);
				this.cpanestate_list[index] = match_obj;
			},
			check_initialize: function(info_obj, event) {
				var state_obj = this.get_cpanestate(info_obj.idproperty);
				var match_obj = state_obj.match_obj;
				var p_pane = match_obj.p_pane;
				if (p_pane) {
					this.pstackcontainer_reg.selectChild(p_pane);
					info_obj.text_node.innerHTML = match_obj.text_str;
					var idproperty = info_obj.idproperty;
					if ((idproperty == 'div_id' || idproperty == 'field_id') &&
						match_obj.p_stage =='config') {
						// only if conditions where update_btn widget is relevant
						if (!this.updatebtn_widget)
							this.updatebtn_widget = registry.byId("infoBtnNode_id");
						this.updatebtn_widget.set('label', info_obj.updatebtn_str);
						this.updatebtn_widget.set('info_type', info_obj.idproperty);
						this.updatebtn_widget.set("onClick",
							match_obj.btn_callback);
					}
					var g_pane = match_obj.g_pane;
					if (g_pane) {
						this.gstackcontainer_reg.selectChild(g_pane);
					}
				} else {
					info_obj.initialize();
				}
			},
			check_getServerDBInfo: function(options_obj) {
				var info_obj = options_obj.info_obj;
				// get incoming idproperty
				var new_idproperty = info_obj.idproperty;
				var state_obj = this.get_cpanestate(new_idproperty);
				var match_obj = state_obj.match_obj;
				// first check if the idproperty-specific logic requires that
				// server data is needed.
				// idproperty-specific logic is applicable whether selected
				// match_obj has already been active
				var req_flag = info_obj.is_serverdata_required(options_obj);
				if (req_flag) {
					// if cpane is already active for the current idproperty
					// then new grid only has to have store swapped out
					if (match_obj.active_flag)
						options_obj.gridstoreswap_flag = true;
					else:
						// if flag is false create new grid
						options_obj.gridstoreswap_flag = false;
					// server data is required, call it
					info_obj.getServerDBInfo(options_obj);
				} else {
					// if idproperty-specific logic determined that server data
					// is not required, there is still some follow-up actions that
					// are required. Note if the incoming match is already active
					// there is nothing to do
					if (!match_obj.active_flag) {
						// switch panes
						this.setreset_cpanestate_active(match_obj);
						// if incoming idproperty is not active
						// then get corresponding cpane and switch to it
						// if cpane does not exist, get data from server
						var p_pane = match_obj.p_pane;
						if (p_pane) {
							this.setreset_cpanestate_active(match_obj);
							// if panes for incoming idproperty is not active
							// but a pane already exists,
							// then switch to that pane
							this.pstackcontainer_reg.selectChild(p_pane);
							if (new_idproperty != 'sched_id') {
								info_obj.text_node.innerHTML = match_obj.text_str;
								if (!this.updatebtn_widget)
									this.updatebtn_widget = registry.byId("infoBtnNode_id");
								this.updatebtn_widget.set('label', info_obj.updatebtn_str);
								this.updatebtn_widget.set('info_type', new_idproperty);
								this.updatebtn_widget.set("onClick", match_obj.btn_callback);
							}
							var g_pane = match_obj.g_pane;
							if (g_pane) {
								this.gstackcontainer_reg.selectChild(g_pane);
							}
						} else {
							// this case should not happen when cpane is
							// already active, but leave in
							options_obj.gridstoreswap_flag = false;
							info_obj.getServerDBInfo(options_obj);
						}
					} else
						alert("Displayed grid selected, no action");
				}
			}
		});
	}
);
