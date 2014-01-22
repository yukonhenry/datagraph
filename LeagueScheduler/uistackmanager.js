/* manage UI content pane structure, especially switching stack container panes */
define(["dbootstrap",  "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array", "dijit/registry", "dojo/domReady!"],
	function(dbootstrap, declare, lang, arrayUtil, registry) {
		var constant = {
			// param stack id's
			pstackcontainer_id:"paramStackContainer_id",
			nfcpane_id:"numfieldcpane_id",
			tcpane_id:"textbtncpane_id",
			ndcpane_id:"numdivcpane_id",
			// grid stack id's
			gstackcontainer_id:"gridContainer_id",
			divcpane_id:"divinfocpane_id",
			schedcpane_id:"schedinfocpane_id",
			fieldcpane_id:"fieldinfocpane_id"
		};
		return declare(null, {
			pstackcontainer_reg:null, pstackmap_list:null,
			gstackcontainer_reg:null, gstackmap_list:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.pstackcontainer_reg = registry.byId(constant.pstackcontainer_id);
				this.pstackmap_list = new Array();
				this.pstackmap_list.push({stage:'fpreconfig_stage',
					pane_id:constant.nfcpane_id});
				this.pstackmap_list.push({stage:'config_stage',
					pane_id:constant.tcpane_id});
				this.pstackmap_list.push({stage:'dpreconfig_stage',
					pane_id:constant.ndcpane_id});
				this.gstackcontainer_reg = registry.byId("gstackcontainer_id");
				this.gstackmap_list = new Array();
				this.gstackmap_list.push({id:'div_id',
					pane_id:constant.divcpane_id});
				this.gstackmap_list.push({id:'match_id',
					pane_id:constant.schedcpane_id});
				this.gstackmap_list.push({id:'field_id',
					pane_id:constant.fieldcpane_id});
			},
			switch_pstackcpane: function(stage_id) {
				var idmatch_list = arrayUtil.filter(this.pstackmap_list,
					function(item, index) {
						return item.stage == stage_id;
					});
				this.pstackcontainer_reg.selectChild(idmatch_list[0].pane_id);
			},
			switch_gstackcpane: function(id) {
				var idmatch_list = arrayUtil.filter(this.gstackmap_list,
					function(item, index) {
						return item.id == id;
					});
				var matchpane_id = idmatch_list[0].pane_id;
				this.gstackcontainer_reg.selectChild(matchpane_id);
				baseinfoSingleton.enable_gridcpanestate(this.cpane_id);
			}
		});
	}
);
