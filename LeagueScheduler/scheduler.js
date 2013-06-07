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
		var constant = {'SERVER_PREFIX':"http://127.0.0.1:8080/"}
		var playdivSelectId, numberTeamsId, numberVenuesId;
		var numTeams = 0; numVenues =0; divnum = "U5";
		var gamesGrid = null;
		var divisionGrid = null;
		var divisionGridHandle = null;
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
		
		script.get(constant.SERVER_PREFIX+"leaguedivinfo", {
			jsonp:"callback"
		}).then(function(ldata){
			ldata_array = ldata.leaguedivinfo;
			grid.renderArray(ldata_array);

		});
		grid.on("dgrid-select", function(event){
    	// Report the item from the selected row to the console.
    		var idnum = event.rows[0].data._id;
    		console.log("Row selected: ", idnum);
    		script.get(constant.SERVER_PREFIX+"leaguedivinfo/"+idnum,{
    			jsonp:"callback"
    		}).then(function(sdata){
				var field_array = sdata.fields;
				// create columns dictionary
				var time_column_key_CONST = 'time';
				var gameday_column_key_CONST = 'cycle';
				var game_columns = {};
				game_columns[gameday_column_key_CONST] = 'GameDay#'
				game_columns[time_column_key_CONST] = 'GameTime';
				arrayUtil.forEach(field_array, function(item, index) {
					// fields names are keys to the column dictionary
					game_columns[item] = 'field '+item;
				});

				var game_array = sdata.game_list;				
				var game_grid_list = new Array();
				listindex = 0;
				arrayUtil.forEach(game_array, function(item,index) {
					var gameday_id = item.GAMEDAY_ID;
					var gameday_data = item.GAMEDAY_DATA; 
					arrayUtil.forEach(gameday_data, function(item2, index2) {
						var game_grid_row = {};
						// fill in the game day number and start time
						game_grid_row[gameday_column_key_CONST] = gameday_id;
						game_grid_row[time_column_key_CONST] = item2.START_TIME;
						arrayUtil.forEach(item2.VENUE_GAME_LIST, function(item3, index3) {
							// iterate amongst fields and fill in matches
							game_grid_row[item3.VENUE] = item3.GAME_TEAM.HOME + 'v' +
															item3.GAME_TEAM.AWAY;
						})
						game_grid_list[listindex] = game_grid_row;
						listindex++;
					});
				});
				
				// this will define number of columns (games per day)
				if (gamesGrid) {
					// clear grid by clearing dom node
					dom.byId("scheduleInfoGrid").innerHTML = "";
					delete gamesGrid;
					
				}
    			gamesGrid = new CustomGrid({
    				columns:game_columns,
    			},"scheduleInfoGrid");
    			gamesGrid.renderArray(game_grid_list);    			
    		});
		});
		grid.on("dgrid-deselect", function(event){
    		console.log("Row de-selected: ", event.rows[0].data);
		});
		
		var getAllDivSchedule = function(evt) {
	        script.get(constant.SERVER_PREFIX+"getalldivschedule", {
	        	jsonp:"callback"
	        }).then(function(adata) {
/*					        	if (game_listP) {
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
*/
			});
		}
		var getDivisionTeamData = function(evt) {
			var divisioncode = registry.byId("divisionSelect").get("value");
			if (divisionGrid) {
				// clear grid by clearing dom node
				dom.byId("divisionGridLinkTeams").innerHTML = "";
				// delete reference to obj
				delete divisionGrid;
				// remove event listener
				// http://dojotoolkit.org/documentation/tutorials/1.8/events/
				if (divisionGridHandle)
					divisionGridHandle.remove();
			}
			divisionGrid = new CustomGrid({
				columns: {
					team_id:"Team ID",
				},
				selectionMode: "single"		
			}, "divisionGridLinkTeams");
			script.get(constant.SERVER_PREFIX+"divisiondata/"+divisioncode, {
				jsonp:"callback"
			}).then(function(ldata){
				var totalteams = ldata.totalteams;
				var division_list = new Array();
				for (var i=0; i < totalteams; i++) {
					division_list[i] = {'team_id':i+1};
				}
				divisionGrid.renderArray(division_list);
			});
			divisionGridHandle = divisionGrid.on("dgrid-select", function(event){
    			// Report the item from the selected row to the console.
    			// Note the last field is an element of the row.
    			var rowid = event.rows[0].data.team_id;
    			teamDataGrid = new CustomGrid({
    				columns: {
    					GAMEDAY_ID:'Game Day ID',
    					START_TIME:'Start Time',
    					VENUE:'Venue',
    					HOME:'Home',
    					AWAY:'Away'
    				}
    			},"teamDataDiv");
    			script.get(constant.SERVER_PREFIX+"teamdata/"+rowid,{
    				jsonp:"callback",
    				query:{division_code:divisioncode}
    			}).then(function(sdata){
    			});
			});
		}


		// events for widgets should be in one js file; trying to split it up into two or more modules
		// does not work - registry.byId cannot find the widget
		ready(function() {
 			parser.parse();	
			on(registry.byId("schedule_btn"), "click", getAllDivSchedule);
			on(registry.byId("divisionSelect"), "change", getDivisionTeamData);
 		}); 
	}
);