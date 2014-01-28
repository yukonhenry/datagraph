// define observable store-related utility functions
define(["dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dojo/store/Observable","dojo/store/Memory","dijit/registry",
	"dojo/domReady!"],
	function(declare, lang, arrayUtil, Observable, Memory, registry) {
		return declare(null, {
			dbselect_store:null, schedutil_obj:null, uistackmgr:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.dbselect_store = new Observable(new Memory({data:new Array()}));
			},
			initdb_store: function(db_list, db_type) {
				// follow observable store model followed by
				// https://www.sitepen.com/blog/2011/02/15/dojo-object-stores/
				// http://dojotoolkit.org/reference-guide/1.9/dojo/store/Observable.html#dojo-store-observable
				// note we can't tie the store directly to select since we are
				// using dropdown->menuitem instead of select
				arrayUtil.forEach(db_list, function(item, index) {
					this.dbselect_store.add({id:item+'_'+db_type, label:item,
						db_type:db_type})
				});
				this.schedutil_obj.generateDB_smenu(db_list,
					"editfieldlist_submenu", this.uistackmgr,
					this.uistackmgr.check_getServerDBInfo,
					{db_type:'fielddb', info_obj:this});
				var delfielddb_smenu_reg = registry.byId("delfielddb_submenu");
				this.schedutil_obj.generateDBCollection_smenu(delfielddb_smenu_reg,
					fielddb_list, this.schedutil_obj,
					this.schedutil_obj.delete_dbcollection,
					{db_type:'fielddb', server_path:"delete_fieldcol/"});
			},

		})
	}
);
