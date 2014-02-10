define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dijit/form/Button", "LeagueScheduler/editgrid",
	"dojo/domReady!"],
	function(dbootstrap, dom, declare, lang, arrayUtil, registry, Button,
		EditGrid) {
		var constant = {
			infobtn_id:"infoBtnNode_id",
			fielddb_type:"fielddb"
		};
		return declare(null, {
			server_interface:null, editgrid:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			createEditGrid: function(server_data, options_obj) {
				// don't create grid if a grid already exists and it points to the same schedule db col
				// if grid needs to be generated, make sure to clean up prior to recreating editGrid
				var colname = options_obj.item;
				var columnsdef_obj = options_obj.columnsdef_obj;
				var idproperty = options_obj.idproperty;
				var server_key = options_obj.server_key;
				// if server data is fielddb information, then we need to do
				// some data conversion (convert to date obj) before passing onto grid
				// Note server_key is key for outgoing request
				// serverdata_key is for incoming data
				var data_list = server_data[options_obj.serverdata_key];
				if (server_key == constant.fielddb_type) {
					if (idproperty == 'field_id') {
						arrayUtil.forEach(data_list, function(item, index) {
							// save date str to pass into start and end time calc
							// (though it can be a dummy date)
							var start_str = item.start_date;
							var end_str = item.end_date;
							item.start_date = new Date(start_str);
							item.end_date = new Date(end_str);
							item.start_time = new Date(start_str+' '+item.start_time);
							item.end_time = new Date(end_str+' '+item.end_time);
						})
					} else {
						alert('check db_type and idproperty consistency');
					}
				}
				if (!this.server_interface) {
					console.log("no server interface");
					alert("no server interface, check if service running");
				}
				if (options_obj.newgrid_flag) {
					this.editgrid = new EditGrid({griddata_list:data_list,
						colname:colname,
						server_interface:this.server_interface,
						grid_id:options_obj.grid_id,
						error_node:dom.byId("divisionInfoInputGridErrorNode"),
						idproperty:idproperty,
						server_path:options_obj.server_path,
						server_key:options_obj.server_key,
						cellselect_flag:options_obj.cellselect_flag,
						info_obj:options_obj.info_obj,
						uistackmgr:options_obj.uistackmgr,
						storeutil_obj:options_obj.storeutil_obj});
					this.editgrid.recreateSchedInfoGrid(columnsdef_obj);
					//baseinfoSingleton.set_active_grid(this.editgrid);
					//baseinfoSingleton.set_active_grid_name(colname);
				} else {
					this.editgrid.replace_store(data_list);
				}
				// need to rethink structure of setting up and maintaining
				// updatebtn_widget
				if (idproperty != 'sched_id') {
					var text_str = options_obj.text_node_str + ": <b>"+colname+"</b>";
					options_obj.text_node.innerHTML = text_str;
					var updatebtn_widget = this.getInfoBtn_widget(
						options_obj.updatebtn_str, idproperty);
					updatebtn_widget.set("onClick", lang.hitch(this.editgrid,
						this.editgrid.sendDivInfoToServer));
					var btn_callback = lang.hitch(this.editgrid, this.editgrid.sendDivInfoToServer);
				}
				if (options_obj.swapcpane_flag) {
					options_obj.uistackmgr.switch_pstackcpane(idproperty, "config",
						text_str, btn_callback);
					if (!options_obj.newgrid_flag) {
						// also swap grid if we are not generating a new one
						options_obj.uistackmgr.switch_gstackcpane(idproperty);
					}
				}
			},
			getInfoBtn_widget: function(label_str, idproperty_str) {
				var infobtn_widget = registry.byId(constant.infobtn_id);
				if (infobtn_widget) {
					var info_type = infobtn_widget.get('info_type');
					if (info_type != idproperty_str) {
						infobtn_widget.set('label', label_str);
						infobtn_widget.set('info_type', idproperty_str);
					}
				} else {
					infobtn_widget = new Button({
						label:label_str,
						type:"button",
						class:"primary",
						info_type:idproperty_str
					}, constant.infobtn_id);
					infobtn_widget.startup();
				}
				return infobtn_widget;
			},
			is_serverdata_required: function(options_obj) {
				return (options_obj.item != this.colname)?true:false;
			},
			is_newgrid_required: function() {
				if (!this.editgrid)
					return true;
				else
					return (this.editgrid.schedInfoGrid)?false:true;
			}
		})
	}
);
