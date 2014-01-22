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
			cpanestate_list:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.pstackcontainer_reg = registry.byId(constant.pstackcontainer_id);
				// define param stack mapping that maps tuple (id_property, config stage)->
				// param content pane
				this.pstackmap_list = new Array();
				this.pstackmap_list.push({id:'field_id', stage:'preconfig',
					pane_id:constant.nfcpane_id});
				this.pstackmap_list.push({id:'field_id', stage:'config',
					pane_id:constant.tcpane_id});
				this.pstackmap_list.push({id:'div_id', stage:'preconfig',
					pane_id:constant.ndcpane_id});
				this.pstackmap_list.push({id:'div_id', stage:'config',
					pane_id:constant.tcpane_id});
				this.gstackcontainer_reg = registry.byId(constant.gstackcontainer_id);
				this.gstackmap_list = new Array();
				this.gstackmap_list.push({id:'div_id',
					pane_id:constant.divcpane_id});
				this.gstackmap_list.push({id:'match_id',
					pane_id:constant.schedcpane_id});
				this.gstackmap_list.push({id:'field_id',
					pane_id:constant.fieldcpane_id});
				this.cpanestate_list = new Array();
				var id_list = ['div_id', 'match_id', 'field_id'];
				arrayUtil.forEach(id_list, function(item) {
					this.cpanestate_list.push({id:item, p_state:null, g_state:null})
				}, this);
			},
			switch_pstackcpane: function(id, stage) {
				var idmatch_list = arrayUtil.filter(this.pstackmap_list,
					function(item, index) {
						return item.id == id && item.stage == stage;
					});
				this.pstackcontainer_reg.selectChild(idmatch_list[0].pane_id);
				// update cpanestate_list element
				// first find element obj with id match
				idmatch_list = arrayUtil.filter(this.cpanestate_list,
					function(item, index) {
						return item.id == id;
					})
				// retrieve actual obj and find index
				var match_obj = idmatch_list[0];
				var index = this.cpanestate_list.indexOf(match_obj);
				// modify matched obj
				match_obj.p_state = stage;
				this.cpanestate_list[index] = match_obj;
				console.log("cpanestate="+this.cpanestate_list);
			},
			switch_gstackcpane: function(id) {
				var idmatch_list = arrayUtil.filter(this.gstackmap_list,
					function(item, index) {
						return item.id == id;
					});
				var matchpane_id = idmatch_list[0].pane_id;
				this.gstackcontainer_reg.selectChild(matchpane_id);
				this.gcpanestate_obj.matchpane_id = true;
			}
		});
	}
);
