/**
 * Copyright (c) 2014 YukonTR *
 * @author Henry
 */
// define class for creating pane(s) to host links to xls hardcopy files for the
// generated schedule
define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/_base/array", "dijit/registry", "dijit/DropDownMenu", "dijit/MenuItem",
	"dijit/form/DropDownButton", "dijit/layout/ContentPane",
	"dijit/layout/StackContainer"
	"LeagueScheduler/idmgrSingleton", "LeagueScheduler/baseinfoSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(dbootstrap, dom, declare, lang, arrayUtil, registry,
		DropDownMenu, MenuItem, DropDownButton, ContentPane, StackContainer,
		idmgrSingleton,
		baseinfoSingleton, put) {
		var constant = {
			idproperty_str:'xls_id',
			label_id_list:[{label:"by Division", genxls_id:'div_id'},
						{label:"by Field", genxls_id:'field_id'},
						{label:"by Team", genxls_id:'team_id'}],
		};
		var idconstant = {
			ddown_btn_id:"xlscpane_ddown_btn_id"
			div_cpane_id:"xlsdiv_cpane_id",
			field_cpane_id:"xlsfield_cpane_id",
			team_cpane_id:"xlsteam_cpane_id"
		}
		return declare(null, {
			idproperty:constant.idproperty_str, idmgr_obj:null, op_type:"",
			server_interface:null, schedcol_name:"",
			stackcpane_list:null, stackcontainer_widget:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
					id:this.idproperty, op_type:this.op_type});
				// create id's that are not managed by idmgr_obj
				var op_prefix = this.op_type.substring(0,3);
				this.opconstant_obj = new Object();
				for (var key in idconstant) {
					this.opconstant_obj[key] = op_prefix+idconstant[key]
				}
				this.stackcontainer_widget = new StackContainer({
					doLayout:false,
					style:"float:left; width:80%"
				})
				this.stackcpane_list = [{id:'div_id',
					cpane_id:this.opconstant_obj.div_cpane_id},
					{id:'field_id', cpane_id:this.opconstant_obj.field_cpane_id},
					{id.'team_id', cpane_id:this.opconstant_obj.team_cpane_id}
				];
				this.columnsdef_obj_list = [{genxls_id:'div_id',
					columsndef_obj:{}}
				]
			},
			get_cpane_id: function(id) {
				var idmatch_list = arrayUtil.filter(this.stackcpane_list,
				function(item) {
					return item.id == id;
				})
				return idmatch_list[0].cpane_id;
			},
			generate_xlscpane_widgets: function(xls_cpane) {
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
					arrayUtil.forEach(constant.label_id_list, function(item) {
						var menuitem_widget = new MenuItem({
							label:item.label,
							onClick:lang.hitch(this, this.switch_xlsstack_cpane,
								item.genxls_id, xls_cpane)
						})
						ddown_menu.addChild(menuitem_widget);
					}, this)
				}
			},
			switch_xlsstack_cpane: function(genxls_id, xls_cpane, event) {

			},
			get_xlsdata: function(genxls_id, xls_cpane, event) {
				this.server_interface.getServerData(
					'get_xls/'+this.schedcol_name+'/'+genxls_id,
					lang.hitch(this, this.create_links));
			},
			create_links: function(adata) {
				var file_list = adata.file_list;
				var host_path = baseinfoSingleton.get_xlsdownload_path();
				var file_num = file_list.length;
				if (file_num == 1) {
					var file_path = host_path+file;
				}
				arrayUtil.forEach(file_list, function(file) {

				})
			}
		})
	}
);
