define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/_base/array", "dojo/keys", "dojo/store/Memory", "dijit/registry",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection", "LeagueScheduler/divinfo", "LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, keys, Memory,
		registry, OnDemandGrid, editor, Keyboard, Selection, divinfo, EditGrid,
		baseinfoSingleton) {
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			divnum_reg: null, divinfo_store:null, divinfo_grid:null,
			divinfogrid_name:"", error_node:null, newcol_name:"",
			schedutil_obj:null, form_name:"", editgrid:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			showConfig: function() {
				var active_grid = baseinfoSingleton.get_active_grid();
				if (active_grid) {
					active_grid.cleanup();
				}
				this.schedutil_obj.makeVisible(this.form_name);
				if (this.keyup_handle)
					this.keyup_handle.remove();
				this.keyup_handle = this.divnum_reg.on("keyup", lang.hitch(this, this.processdivinfo_input));
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
						//divnum is the total # of divisions
						var divnum = this.divnum_reg.get("value");
						var divInfo_list = new Array();
						for (var i = 1; i < divnum+1; i++) {
							divInfo_list.push({div_id:i, div_age:"", div_gen:"",
							totalteams:1, totalbrackets:1, elimination_num:1,
							elimination_type:"",
							field_id_str:"", gameinterval:1, rr_gamedays:1});
						}
						this.schedutil_obj.makeInvisible(this.form_name);
						if (this.keyup_handle)
							this.keyup_handle.remove();
						this.editgrid = new EditGrid({griddata_list:divInfo_list,
							colname:this.newcol_name,
							server_interface:this.server_interface,
							grid_name:"divisionInfoInputGrid",
							error_node:dom.byId("divisionInfoInputGridErrorNode"),
							text_node:dom.byId("divisionInfoNodeText"),
							submitbtn_reg:registry.byId("updatesubmit_btn"),
							updatebtn_node:dom.byId("divisionInfoUpdateBtnText"),
							idproperty:'div_id',
							schedutil_obj:this.schedutil_obj,
							server_callback:lang.hitch(this.schedutil_obj,this.schedutil_obj.regenAddDBCollection_smenu)});
						var divinfo_obj = new divinfo;
						var columnsdef_obj = divinfo_obj.columnsdef_obj;
						this.editgrid.recreateSchedInfoGrid(columnsdef_obj);
						baseinfoSingleton.set_active_grid(this.editgrid);
						//on(this.divInfoGrid, "dgrid-datachange",
						//	lang.hitch(this, this.editDivInfoGrid));
					} else {
						alert('Input name is Invalid, please correct');
					}
				}
			},
			nodupname_validate: function(col_name) {
				// if name exists in the current list (index > -1) then
				// return false (test failed)
				var dbname_list = baseinfoSingleton.get_dbname_list();
				if (dbname_list.indexOf(col_name) > -1)
					return false;
				else
					return true;
			}
		});
	})
