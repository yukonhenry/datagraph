/**
 * Copyright (c) 2014 YukonTR *
 * @author Henry
 */
// define class for creating pane(s) to host links to xls hardcopy files for the
// generated schedule
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/_base/array", "dijit/registry", "dijit/DropDownMenu", "dijit/MenuItem",
	"dijit/form/DropDownButton", "dijit/layout/ContentPane",
	"dijit/layout/StackContainer",
	"scheduler_front/idmgrSingleton", "scheduler_front/baseinfoSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry,
		DropDownMenu, MenuItem, DropDownButton, ContentPane, StackContainer,
		idmgrSingleton,
		baseinfoSingleton, put) {
		var constant = {
			idproperty_str:'xls_id',
		};
		var idconstant = {
			// id for the dropdown btn
			ddown_btn_id:"xlscpane_ddown_btn_id",
			// id for the various cpane, each (except) blank hosting a xls ouput
			// type link
			div_cpane_id:"xlsdiv_cpane_id",
			field_cpane_id:"xlsfield_cpane_id",
			team_cpane_id:"xlsteam_cpane_id",
			//referee_cpane_id:"xlsreferee_cpane_id",
			blank_cpane_id:"xlsblank_cpane_id"
		}
		return declare(null, {
			idproperty:constant.idproperty_str, idmgr_obj:null, op_type:"",
			server_interface:null, schedcol_name:"",
			stackcpane_list:null, stackcontainer_widget:null, userid_name:"",
			db_type:null, label_id_list:null, sched_type:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
					id:this.idproperty, op_type:this.op_type,
					sched_type:this.sched_type});
				// create id's that are not managed by idmgr_obj
				var op_prefix = this.op_type.substring(0,3);
				this.opconstant_obj = new Object();
				for (var key in idconstant) {
					this.opconstant_obj[key] = op_prefix+idconstant[key]
				}
				this.stackcpane_list = [
					{genxls_id:'blank_id', cpane_id:this.opconstant_obj.blank_id, descrip_str:"default"},
					{genxls_id:'div_id', cpane_id:this.opconstant_obj.div_cpane_id,
						descrip_str:"by Division"},
					{genxls_id:'field_id',
						cpane_id:this.opconstant_obj.field_cpane_id,
						descrip_str:"by Field"}
				];
				this.label_id_list = [{label:"by Division", genxls_id:'div_id'},
					{label:"by Field", genxls_id:'field_id'}];
				if (this.db_type == "rrdb") {
					// per team_id info only relevant for RoundRobin league as elimination tournament
					// schedule dependent on seeding and win/loss results for each match
					this.stackcpane_list.push({genxls_id:'team_id',
						cpane_id:this.opconstant_obj.team_cpane_id,
						descrip_str:"by Team"});
					this.label_id_list.push({label:"by Team", genxls_id:'team_id'});
				}
				this.columnsdef_obj_list = [{genxls_id:'div_id',
					columsndef_obj:{}}
				]
			},
			get_cpane_id: function(genxls_id) {
				var idmatch_list = arrayUtil.filter(this.stackcpane_list,
				function(item) {
					return item.genxls_id == genxls_id;
				})
				return idmatch_list[0].cpane_id;
			},
			generate_xlscpane_widgets: function(xls_cpane) {
				// called from callback fun after send_generate returns w data
				var server_key_obj = null;
				var ddown_btn = registry.byId(this.opconstant_obj.ddown_btn_id);
				if (!ddown_btn) {
					// create widgets only if they don't already exist
					var ddown_menu = new DropDownMenu({
					})
					var ddown_btn = new DropDownButton({
						class:"info editsched",
						label:"Select XLS Output",
						dropDown:ddown_menu,
						id:this.opconstant_obj.ddown_btn_id
					})
					xls_cpane.addChild(ddown_btn);
					arrayUtil.forEach(this.label_id_list, function(item) {
						var menuitem_widget = new MenuItem({
							label:item.label,
							onClick:lang.hitch(this, this.switch_xlsstack_cpane,
								item.genxls_id)
						})
						ddown_menu.addChild(menuitem_widget);
					}, this)
					// create stackcontainer and child content panes, one each
					// for the different types of xls file links
					this.stackcontainer_widget = new StackContainer({
						doLayout:false,
						style:"float:left; width:80%"
					})
					// add statckcontainer to cpane
					xls_cpane.addChild(this.stackcontainer_widget);
					arrayUtil.forEach(this.stackcpane_list, function(item) {
						var cpane_id = item.cpane_id;
						var stack_cpane = new ContentPane({id:cpane_id});
						this.stackcontainer_widget.addChild(stack_cpane);
						if (cpane_id != this.opconstant_obj.blank_id) {
							// as long as the cpane is not the default blank cpane,
							// get all links and populate
							var descrip_str = item.descrip_str;
							// NOTE: this is a hack for elimination tourn
							// type
							if (this.db_type == 'tourndb') {
								server_key_obj = {tourn_type:"elimination"}
							}
							this.server_interface.getServerData(
								'get_xls/'+this.userid_name+'/'+
								this.schedcol_name+'/'+this.db_type+'/'+
								item.genxls_id+'/'+this.sched_type,
								lang.hitch(this, this.create_links), server_key_obj,
								{cpane:stack_cpane, descrip_str:descrip_str});
						}
					}, this)
					xls_cpane.startup();
					//this.stackcontainer_widget.selectChild(
					//	this.opconstant_obj.blank_cpane_id)
				} else {
					// widget environment already exists, but regenerate links
					arrayUtil.forEach(this.stackcpane_list, function(item) {
						var cpane_id = item.cpane_id;
						var stack_cpane = registry.byId(cpane_id);
						if (cpane_id != this.opconstant_obj.blank_id) {
							// as long as the cpane is not the default blank cpane,
							// get all links and populate
							var descrip_str = item.descrip_str;
							if (this.db_type == 'tourndb') {
								server_key_obj = {tourn_type:"elimination"}
							}
							this.server_interface.getServerData(
								'get_xls/'+this.userid_name+'/'+
								this.schedcol_name+'/'+this.db_type+'/'+
								item.genxls_id+'/'+this.sched_type,
								lang.hitch(this, this.create_links), server_key_obj,
								{cpane:stack_cpane, descrip_str:descrip_str});
						}
					}, this)
				}
			},
			switch_xlsstack_cpane: function(genxls_id, event) {
				var cpane_id = this.get_cpane_id(genxls_id);
				this.stackcontainer_widget.selectChild(cpane_id)
			},
			create_links: function(adata, options_obj) {
				var cpane = options_obj.cpane;
				var descrip_str = options_obj.descrip_str;
				var file_list = adata.file_list;
				var host_path = baseinfoSingleton.get_xlsdownload_path();
				var content_str = "<p>Click on Links below</p>";
				arrayUtil.forEach(file_list, function(item) {
					var file_url = host_path+item.path;
					var link_str = "";
					if ('mdata' in item) {
						link_str = "<a href='"+file_url+"'>"+this.schedcol_name+
							item.mdata+" Schedule,"+descrip_str+"</a><br>";
					} else {
						link_str = "<a href='"+file_url+"'>"+this.schedcol_name+
							" Schedule,"+descrip_str+"</a><br>";
					}
					content_str += link_str
					cpane.set("content", content_str)
				}, this)
			}
		})
	}
);
