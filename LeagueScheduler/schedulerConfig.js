define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array",
	"dojo/store/Memory","dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", 
	"dgrid/Selection", "dojo/domReady!"], 
	function(dom, declare, lang, arrayUtil, Memory, OnDemandGrid, editor, Keyboard, Selection){
		return declare(null, {
			div_id: 0, schedutil_obj: null, numteams:0,
			team_seed_list:null, seedGrid: null, seedStore:null,
			constructor: function(args) {
				// declare.safeMixin(this, args);
				// augmenting object tutorial referenced above says lang.mixin is a better choise
				// than declare.safeMixin
				lang.mixin(this, args);
				this.numteams = this.schedutil_obj.getNumberTeams(this.div_id);
				this.team_seed_list = new Array();
				for (var i = 1; i < this.numteams+1; i++) {
					this.team_seed_list.push({team_id:i, seed_id:i});
				}
			},
			createSeedGrid: function(grid_name) {
				this.seedStore = new Memory({data:this.team_seed_list, idProperty:"team_id"});

				this.seedGrid = new (declare([OnDemandGrid, Keyboard, Selection]))({
            		store: this.seedStore,
            		columns: {
                		team_id: "Team ID",
                		seed_id: editor({label:"Seed", field:"seed_id"},"text","dblclick")
                	/*	editor({
                			label: "Seed",
                			field: "seed_id",
                			editor: "text",
                			editOn: "dblclick" }); */
            		}
        		}, grid_name);
        		this.seedGrid.startup();
                return this.seedGrid;
            },        		
            editSeedGrid: function(event) {
        			var val = event.value;
        			console.log("val="+val+' replace='+event.oldValue+ ' cell row='+event.rowId +
        				'col='+event.cell.column.field);
                    this.testValue(event.rowId);
                    /*
                    this.seedGrid.updateDirty(2,'seed_id', 989);
                    this.seedGrid.save().then(function(results) {
                        this.seedGrid.refresh();
                        console.log("save finished");
                    });
                    var entry = this.seedStore.get(2);
                    entry.seed_id = 989;
                    this.seedStore.put(entry);

                    //console.log('updated');
        			//saved = this.seedGrid.save();
                    //saved.then(function(results) {
                    console.log("save finished");
                    this.seedGrid.refresh();
                    //})
                    //this.seedGrid.refresh();
                    */
        	},
            testValue: function(rid) {
                console.log("store value"+this.seedStore.get(rid).seed_id);
            }
		});
	}
);