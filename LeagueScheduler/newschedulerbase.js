define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/_base/array", "dojo/keys", "dojo/store/Memory", "dijit/registry",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection", "LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, keys, Memory,
		registry, OnDemandGrid, editor, Keyboard, Selection, EditGrid,
		baseinfoSingleton) {
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			newsched_dom:"", schedutil_obj:null,
			form_name:"", form_dom:null,
			info_obj:null, idproperty:"", server_path:"", server_key:"",
			cellselect_flag:false,
			seasoncalendar_input_dom:null,seasondates_btn_reg:null,
			callback:null, text_node_str:null,
			seasonstart_date:null, seasonend_date:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			initialize: function(arg_obj) {
				this.form_name = "newsched_form_id";
				this.form_reg = registry.byId(this.form_name);
				this.form_dom = dom.byId(this.form_name);
				this.dbname_reg = registry.byId("newsched_input_id");
				this.seasoncalendar_input_dom = dom.byId("seasoncalendar_input");
				this.seasondates_btn_reg = registry.byId("seasondates_btn");
				this.newsched_dom = dom.byId("newsched_text");
				this.showConfig();
			},
			set_schedutil_obj: function(obj) {
				this.schedutil_obj = obj;
			},
			showConfig: function() {
				var active_grid = baseinfoSingleton.get_active_grid();
				if (active_grid) {
					active_grid.cleanup();
					baseinfoSingleton.reset_active_grid();
				}
				this.schedutil_obj.makeVisible(this.form_dom);
				baseinfoSingleton.set_visible_form_dom(this.form_dom);
				if (this.keyup_handle)
					this.keyup_handle.remove();
				this.keyup_handle = this.dbname_reg.on("keyup", lang.hitch(this, this.processdivinfo_input));
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(event) {
				if (event.keyCode == keys.ENTER) {
					if (this.form_reg.validate()) {
						confirm('Input format is Valid, creating new Schedule DB');
						this.newsched_name = this.dbname_reg.get("value");
						if (!this.nodupname_validate(this.newsched_name)) {
							alert("Selected sched name already exists, choose another");
							return;
						}
						// disable schedule name form
						this.schedutil_obj.makeInvisible(this.form_dom);
						if (this.keyup_handle)
							this.keyup_handle.remove();
						//enable season start/end date input datetime textbox and button
						this.schedutil_obj.makeVisible(this.seasoncalendar_input_dom);
						baseinfoSingleton.set_visible_form_dom(this.seasoncalendar_input_dom);
						this.newsched_dom.innerHTML = "Schedule Name: "+this.newsched_name;
						if (this.sdates_handle)
							this.sdates_handle.remove();
						this.sdates_handle = this.seasondates_btn_reg.on("click",
					lang.hitch(this, this.getSeasonDatesFromInput));
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
			getSeasonDatesFromInput: function(event) {
				this.seasonstart_date = registry.byId("seasonstart_date").get("value");
				this.seasonend_date = registry.byId("seasonend_date").get("value");
				console.log("start end="+seasonstart_date+" "+seasonend_date);
			},
		});
	})
