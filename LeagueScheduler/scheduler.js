/**
 * @author Henry
 */
// small note, if there are issues with garbage characters in the jsonp script get request,
// ensure http://bugs.dojotoolkit.org/ticket/16408 has been resolved in the branch/release
// that is being used.
require(["dojo/dom", "dojo/on", "dojo/parser", "dijit/registry","dojo/ready", 
		"dojo/_base/declare", "dgrid/Grid", "dgrid/Selection",
		"dojo/request/script", "dojo/_base/array",
		"dijit/form/NumberTextBox","dijit/form/Button",
		"dojo/domReady!"],
	function(dom, on, parser, registry, ready, declare, Grid, Selection, script, arrayUtil) {
		var playdivSelectId, numberTeamsId, numberVenuesId;
		var numTeams = 0; numVenues =0; divnum = "U5";
		var gamesGrid = null;
		var CustomGrid = declare([ Grid, Selection ]);
		var grid = new CustomGrid({
			columns: {
				agediv:"Age Group",
				gender:"Boy/Girl",
				totalteams:"Total#",
				fields:"Fields",
				gamedaysperweek:"Weekly Games#",
				gameinterval:"Game Interval(min)"				
			},
			selectionMode: "single"		
		}, "divisionInfoGrid");
		
		script.get("http://127.0.0.1:8080/leaguedivinfo", {
			jsonp:"callback"
		}).then(function(ldata){
			ldata_array = ldata.leaguedivinfo;
			grid.renderArray(ldata_array);

		});
		grid.on("dgrid-select", function(event){
    	// Report the item from the selected row to the console.
    		var idnum = event.rows[0].data._id;
    		console.log("Row selected: ", idnum);
    		script.get("http://127.0.0.1:8080/leaguedivinfo/"+idnum,{
    			jsonp:"callback"
    		}).then(function(sdata){
				var numFields = sdata.numFields;
				// create columns dictionary
				var slot_key_CONST = 'slot';
				var game_columns = {};
				game_columns[slot_key_CONST] = 'GameTime';
				for (var i = 0; i < numFields; i++) {
					var field_i = i+1;  // field names are 1-indexed
					game_columns[field_i] = 'field '+field_i;
				}
				
				var game_array = sdata.game_list;				
				var game_grid_object = new Array();
				arrayUtil.forEach(game_array, function(item,index) {
					/*
					if (index == 0) {
						// create columns object required for dgrid
						arrayUtil.forEach(item, function(it, i) {
							var field_i = i+1;
							game_columns[field_i] = 'field '+field_i;
						});
					};
					*/
					var game_grid_row = {};
					arrayUtil.forEach(item, function(item2, index2) {
						game_grid_row[index2+1] = item2;
					});
					game_grid_object[index] = game_grid_row; 
				});
				// this will define number of columns (games per day)
				if (gamesGrid) {
					// clear grid by clearing dom node
					dom.byId("scheduleInfoGrid").innerHTML = "";
				}
    			gamesGrid = new CustomGrid({
    				columns:game_columns,
    			},"scheduleInfoGrid");
    			gamesGrid.renderArray(game_grid_object);
    			/*
    			arrayUtil.forEach(sdata.game_list, function(item, index) {
    				console.log("item="+item+" ind="+index);
    			}); */
    			
    		});
		});
		grid.on("dgrid-deselect", function(event){
    		console.log("Row de-selected: ", event.rows[0].data);
		});
/*		
		var getSchedule = function(evt) {

	        script.get("http://127.0.0.1:8080/getschedule", {
	        	jsonp:"callback", query: {num_teams:numTeams, num_venues:numVenues}
	        }).then(function(data) {
	        	if (game_listP) {
	        		d3.select(schedulerDiv).selectAll("p").remove();
	        	}
	        	// data returned from server is an array of tuples, with each tuple
	        	// representing two teams in a match
	        	// ref https://github.com/mbostock/d3/wiki/Selections#wiki-exit
	        	// on how to assign variable before enter() so that a check
	        	// can be made later (above) to see if added paragraphs need to be deleted.
	        	game_listP = d3.select(schedulerDiv).selectAll("p")
	        						.data(data.game_list);
	        	game_listP.enter()
					.append("p")
					.text(function(d,i) {
						var matchstr = "slot "+i+": ";
						for (var j =0; j < d.length; j++) {
							var match = d[j];
							matchstr += match[0]+"vs"+match[1]+" ";
						}
						return matchstr;
					});
			});
		}
*/
		ready(function() {
 			parser.parse();	
			//on(registry.byId("schedule_btn"), "click", getSchedule);
 		}); 
	}
);