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

		};
		return declare(null, {
			pstackcontainer_reg:null, pstackmap_list:null,
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
			},
			switch_pstackcpane: function(stage_id) {
				var idmatch_list = arrayUtil.filter(this.pstackmap_list,
					function(item, index) {
						return item.stage == stage_id;
					});
				this.pstackcontainer_reg.selectChild(idmatch_list[0].pane_id);
			}
		});
	}
);
