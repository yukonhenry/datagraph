define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/_base/array", "dojo/keys",
	"dijit/registry", "dijit/Tooltip",
	"LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, arrayUtil, keys,
		registry, Tooltip, EditGrid,
		baseinfoSingleton) {
		var constant = {
			infobtn_id:"infoBtnNode_id"
		};
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			entrynum_reg: null, error_node:null, text_node:null,
			newcol_name:"", editgrid:null,
			info_obj:null, idproperty:"", server_path:"", server_key:"",
			cellselect_flag:false,
			text_node_str:"",
			updatebtn_str:"", storeutil_obj:null,
			grid_id:"", uistackmgr:null, tooltip_list:null,
			constructor: function(args) {
				lang.mixin(this, args)
				this.tooltip_list = new Array();
			},
			showConfig: function(tooltipconfig_list, newgrid_flag) {
				// ref http://stackoverflow.com/questions/11743392/check-if-array-is-empty-or-exists
				// to check if array exists and is non-empty
				if (typeof tooltipconfig_list !== 'undefined' && this.tooltip_list.length == 0) {
					arrayUtil.forEach(tooltipconfig_list, function(item) {
						this.tooltip_list.push(new Tooltip(item));
					}, this);
				}
				this.uistackmgr.switch_pstackcpane(this.idproperty, "preconfig");
				this.uistackmgr.switch_gstackcpane(this.idproperty, true);
				if (this.keyup_handle)
					this.keyup_handle.remove();
				this.keyup_handle = this.entrynum_reg.on("keyup", lang.hitch(this, this.processdivinfo_input, newgrid_flag));
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(newgrid_flag, event) {
				if (event.keyCode == keys.ENTER) {
					if (this.form_reg.validate()) {
						confirm('Input format is Valid, creating new DB');
						this.newcol_name = this.dbname_reg.get("value");
						if (!this.storeutil_obj.nodupdb_validate(this.newcol_name,
							this.idproperty)) {
							alert("Selected sched name already exists, choose another");
							return;
						}
						//var divinfo_obj = this.info_obj;
						//divnum is the total # of divisions or other entity like fields
						var divnum = this.entrynum_reg.get("value");
						var divinfo_list = this.info_obj.getInitialList(divnum);
						if (this.keyup_handle)
							this.keyup_handle.remove();
						if (newgrid_flag) {
							var columnsdef_obj = this.info_obj.getcolumnsdef_obj();
							this.editgrid = new EditGrid({griddata_list:divinfo_list,
								colname:this.newcol_name,
								server_interface:this.server_interface,
								grid_id:this.grid_id,
								error_node:dom.byId("divisionInfoInputGridErrorNode"),
								idproperty:this.idproperty,
								server_path:this.server_path,
								server_key:this.server_key,
								cellselect_flag:this.cellselect_flag,
								info_obj:this.info_obj,
								uistackmgr:this.uistackmgr,
								storeutil_obj:this.storeutil_obj});
							this.editgrid.recreateSchedInfoGrid(columnsdef_obj);
							// assign editgrid created by newscheduler back to the
							// info_obj (or its prototype defined by superclass)
							// editgrid so that isgrid_required function returns
							// correct value
							this.info_obj.editgrid = this.editgrid;
						} else {
							this.editgrid.replace_store(divinfo_list);
						}
						var args_obj = {
							colname:this.newcol_name,
							text_node_str:this.text_node_str,
							text_node:this.text_node,
							updatebtn_str:this.updatebtn_str,
							idproperty:this.idproperty,
							swapcpane_flag:true,
							newgrid_flag:true
						}
						this.info_obj.reconfig_infobtn(args_obj);
						baseinfoSingleton.set_active_grid(this.editgrid);
						baseinfoSingleton.set_active_grid_name(this.newcol_name);
					} else {
						alert('Input name is Invalid, please correct');
					}
				}
			},
			cleanup: function() {
				// cleanup here is cleaning up what is left over from other
				// forms and grids
				var active_grid = baseinfoSingleton.get_active_grid();
				if (active_grid) {
					active_grid.cleanup();
					baseinfoSingleton.reset_active_grid();
				}
				arrayUtil.forEach(this.tooltip_list, function(item) {
					item.destroyRecursive();
				});
			}

		});
	})
