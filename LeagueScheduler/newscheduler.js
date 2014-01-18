define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/_base/array", "dojo/keys", "dijit/registry",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection", "LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, keys,
		registry, OnDemandGrid, editor, Keyboard, Selection, EditGrid,
		baseinfoSingleton) {
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			entrynum_reg: null, error_node:null, text_node:null,
			newcol_name:"", schedutil_obj:null, form_dom:null, editgrid:null,
			info_obj:null, idproperty:"", server_path:"", server_key:"",
			cellselect_flag:false,
			callback:null, text_node_str:"",
			updatebtn_widget:null,
			grid_id:"", cpane_id:"",
			constructor: function(args) {
				lang.mixin(this, args);
			},
			showConfig: function() {
				this.cleanup();
				this.schedutil_obj.makeVisible(this.form_dom);
				baseinfoSingleton.set_visible_form_dom(this.form_dom);
				/* this.updatebtn_reg = registry.byId(this.updatebtn_id);
				if (this.updatebtn_str)
					this.updatebtn_reg.set('label', this.updatebtn_str);
				*/
				if (this.keyup_handle)
					this.keyup_handle.remove();
				this.keyup_handle = this.entrynum_reg.on("keyup", lang.hitch(this, this.processdivinfo_input));
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(event) {
				if (event.keyCode == keys.ENTER) {
					if (this.form_reg.validate()) {
						confirm('Input format is Valid, creating new Schedule DB');
						this.newcol_name = this.dbname_reg.get("value");
						if (!this.nodupname_validate(this.newcol_name)) {
							alert("Selected sched name already exists, choose another");
							return;
						}
						//var divinfo_obj = this.info_obj;
						//divnum is the total # of divisions or other entity like fields
						var divnum = this.entrynum_reg.get("value");
						var divinfo_list = this.info_obj.getInitialList(divnum);
						this.schedutil_obj.makeInvisible(this.form_dom);
						baseinfoSingleton.reset_visible_form_dom();
						if (this.keyup_handle)
							this.keyup_handle.remove();
						this.editgrid = new EditGrid({griddata_list:divinfo_list,
							colname:this.newcol_name,
							server_interface:this.server_interface,
							grid_id:this.grid_id,
							cpane_id:this.cpane_id,
							textcpane_id:this.textcpane_id,
							error_node:dom.byId("divisionInfoInputGridErrorNode"),
							text_node:this.text_node,
							updatebtn_widget:this.updatebtn_widget,
							idproperty:this.idproperty,
							server_callback:this.callback,
							server_path:this.server_path,
							server_key:this.server_key,
							cellselect_flag:this.cellselect_flag,
							info_obj:this.info_obj,
							text_node_str:this.text_node_str});
						var columnsdef_obj = this.info_obj.getcolumnsdef_obj();
						this.editgrid.recreateSchedInfoGrid(columnsdef_obj,
							registry.byId("gridContainer_id"),
							registry.byId("gridparamContainer_id"));
						baseinfoSingleton.set_active_grid(this.editgrid);
						baseinfoSingleton.set_active_grid_name(this.newcol_name);
					} else {
						alert('Input name is Invalid, please correct');
					}
				}
			},
			nodupname_validate: function(col_name) {
				// if name exists in the current list (index > -1) then
				// return false (test failed)
				// currently dbname_list includes list of all db names
				// and doesn't distinguish between various field/div db's
				var dbname_list = baseinfoSingleton.get_dbname_list();
				if (dbname_list.indexOf(col_name) > -1)
					return false;
				else
					return true;
			},
			cleanup: function() {
				// cleanup here is cleaning up what is left over from other
				// forms and grids
				var active_grid = baseinfoSingleton.get_active_grid();
				if (active_grid) {
					active_grid.cleanup();
					baseinfoSingleton.reset_active_grid();
				}
				var form_dom = baseinfoSingleton.get_visible_form_dom();
				if (form_dom) {
					baseinfoSingleton.reset_visible_form_dom();
					this.schedutil_obj.makeInvisible(form_dom);
				}
			}

		});
	})
