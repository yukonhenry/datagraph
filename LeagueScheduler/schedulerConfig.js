define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dojo/store/Memory","dgrid/OnDemandGrid","dojo/domReady!"], 
	function(dom, declare, lang, arrayUtil, Memory, OnDemandGrid){
		return declare(null, {
			div_id: 0, schedutil_obj: null, numteams:0,
			team_seed_list:[], seedGrid: null, seedStore:null,
			constructor: function(args) {
				//declare.safeMixin(this, args);
				// augmenting object tutorial referenced above says lang.mixin is a better choise
				// than declare.safeMixin
				lang.mixin(this, args);
				this.numteams = this.schedutil_obj.getNumberTeams(this.div_id);
				for (var i = 1; i < this.numteams+1; i++) {
					this.team_seed_list.push({team_id:i, seed_id:i});
				}
			},
			createSeedGrid: function(grid_name) {
				if (this.seedGrid) {
					dom.byId(grid_name).innerHTML = "";
					delete this.seedGrid;
				}
				if (this.seedStore)
					this.seedStore.remove();
				this.seedStore = new Memory({data:this.team_seed_list, idProperty:'team_id'});
				this.seedGrid = new OnDemandGrid({
            		store: this.seedStore,
            		columns: {
                		team_id: "Team ID",
                		seed_id: "Seed"
            		}
        		}, grid_name);
        		this.seedGrid.startup();
        		return this.seedGrid;
			}
		});
	}
);