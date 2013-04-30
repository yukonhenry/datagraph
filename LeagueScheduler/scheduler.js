/**
 * @author Henry
 */
// small note, if there are issues with garbage characters in the jsonp script get request,
// ensure http://bugs.dojotoolkit.org/ticket/16408 has been resolved in the branch/release
// that is being used.
require(["dojo/on", "dojo/parser", "dijit/registry","dojo/ready", 
		"dojo/_base/declare", "dgrid/Grid", "dgrid/Selection",
		"dojo/request/script", 
		"dijit/form/Select", "dijit/form/NumberTextBox","dijit/form/Button",
		"dojo/domReady!"],
	function(on, parser, registry, ready, declare, Grid, Selection, script) {
		var playdivSelectId, numberTeamsId, numberVenuesId;
		var numTeams = 0; numVenues =0; divnum = "U5";
		
		var CustomGrid = declare([ Grid, Selection ]);
		var grid = new CustomGrid({
			columns: {
				agediv:"Age Group",
				gender:"Boy/Girl",
				totalteams:"Total#",
				totalfields:"Field#",
				gamedaysperweek:"Weekly Games#"
			},
			selectionMode: "single"		
		}, "divisionInfoGrid");
		
		script.get("http://127.0.0.1:8080/leaguedivinfo", {
			jsonp:"callback"
		}).then(function(ldata){
			ldata_array = ldata.leaguedivinfo;
			grid.renderArray(ldata_array);
			grid.on("dgrid-select", function(event){
    // Report the item from the selected row to the console.
    console.log("Row selected: ", event.rows[0].data);
});
grid.on("dgrid-deselect", function(event){
    console.log("Row de-selected: ", event.rows[0].data);
});
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