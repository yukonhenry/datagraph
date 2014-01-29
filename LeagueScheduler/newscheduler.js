define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/_base/array", "dojo/keys",
	"dijit/registry", "dijit/Tooltip",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection",
	"LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, keys,
		registry, Tooltip, OnDemandGrid, editor, Keyboard, Selection, EditGrid,
		baseinfoSingleton) {
		var constant = {
			infobtn_id:"infoBtnNode_id"
		};
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			entrynum_reg: null, error_node:null, text_node:null,
			newcol_name:"", schedutil_obj:null, editgrid:null,
			info_obj:null, idproperty:"", server_path:"", server_key:"",
			cellselect_flag:false,
			text_node_str:"",
			updatebtn_str:"", storeutil_obj:null,
			grid_id:"", uistackmgr:null, tooltip_list:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.tooltip_list = new Array();
			},
			showConfig: function(tooltipconfig_list) {
				// ref http://stackoverflow.com/questions/11743392/check-if-array-is-empty-or-exists
				// to check if array exists and is non-empty
				if (typeof tooltipconfig_list !== 'undefined' && this.tooltip_list.length == 0) {
					arrayUtil.forEach(tooltipconfig_list, function(item) {
						this.tooltip_list.push(new Tooltip(item));
					}, this);
				}
				this.uistackmgr.switch_pstackcpane(this.idproperty, "preconfig");
				this.uistackmgr.switch_gstackcpane(this.idproperty);
				if (this.keyup_handle)
					this.keyup_handle.remove();
				this.keyup_handle = this.entrynum_reg.on("keyup", lang.hitch(this, this.processdivinfo_input));
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(event) {
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
						var text_str = this.text_node_str + ": <b>"+this.newcol_name+"</b>";
						this.text_node.innerHTML = text_str;
						var updatebtn_widget = this.schedutil_obj.getInfoBtn_widget(
							this.updatebtn_str, this.idproperty);
						// do straight overrride on button onclick event handler
						// so that we don't have to worry about handler clean-up
						updatebtn_widget.set("onClick",
							lang.hitch(this.editgrid,
								this.editgrid.sendDivInfoToServer));
						var btn_callback = lang.hitch(this.editgrid, this.editgrid.sendDivInfoToServer);
						this.uistackmgr.switch_pstackcpane(this.idproperty, "config", text_str, btn_callback);

						var columnsdef_obj = this.info_obj.getcolumnsdef_obj();
						this.editgrid.recreateSchedInfoGrid(columnsdef_obj);
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
