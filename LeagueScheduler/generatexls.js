/**
 * Copyright (c) 2014 YukonTR *
 * @author Henry
 */
// define class for creating pane(s) to host links to xls hardcopy files for the
// generated schedule
define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/_base/array", "dijit/registry", "dijit/DropDownMenu", "dijit/MenuItem",
	"dijit/form/DropDownButton", "dijit/layout/ContentPane",
	"LeagueScheduler/idmgrSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(dbootstrap, dom, declare, lang, arrayUtil, registry,
		DropDownMenu, MenuItem, DropDownButton, ContentPane, idmgrSingleton, put) {
		var constant = {
			idproperty_str:'xls_id',
		};
		var idconstant = {
			ddown_btn_id:"xlscpane_ddown_btn_id"
		}
		return declare(null, {
			idproperty:constant.idproperty_str, idmgr_obj:null, op_type:"",
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
					var label_id_list = [
						{label:"by Division", genxls_id:'div_id'},
						{label:"by Field", genxls_id:'field_id'},
						{label:"by Team", genxls_id:'team_id'}];
					arrayUtil.forEach(label_id_list, function(item) {
						var menuitem_widget = new MenuItem({
							label:item.label,
						})
					})
				}

			}
		})
	}
);
