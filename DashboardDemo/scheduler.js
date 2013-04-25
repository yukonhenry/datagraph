/**
 * @author Henry
 */
require(["dojo/dom", "dojo/on", "dojo/parser", "dijit/registry","dojo/ready", 
		"dojo/request","dojo/request/script",
        "dojo/json", "dgrid/Grid", "dojo/store/Memory", "dojo/domReady!", "dijit/form/NumberTextBox"],
	function(dom, on, parser, registry, ready, request, script, JSON, Grid, Memory) {
		var game_listP = null;
		var numTeams = 0;
		var numVenues = 0;
		var divnum = "";
		var divisionData = [
		];
		//var numTeams = registry.byId("numberTeams").get("value");
		//var numVenues = registry.byId("numberVenues").get("value");
		//var divnum = registry.byId("playdivisionSelect").get("value");
		function setDivTeams(div_num, nt, nv) {
			console.log("dn, nt, nv="+div_num+" "+nt+" "+nv);
			
			var divdata = [
				{dnum:div_num, nteams:nt, nvenues:nv}
			];
			var grid = new Grid({
				columns: {
					dnum: "Division", nteams: "Number Teams", nvenues: "Number Venues"
				}
			}, "divisionInfoGrid");
			grid.renderArray(divdata);

		}
		var setNumberTeams = function(evt) {
			numTeams = registry.byId("numberTeams").get("value");
			setDivTeams(divnum, numTeams, numVenues);
		}
		var setNumberVenues = function(evt) {
			numVenues = registry.byId("numberVenues").get("value");
			setDivTeams(divnum, numTeams, numVenues);
		}
		var setPlayDivSelect = function(evt) {
			divnum = registry.byId("playdivisionSelect").get("value");
			setDivTeams(divnum, numTeams, numVenues);
		}
		var getSchedule = function(evt) {

			var schedulerDiv = dom.byId("schedulerDiv");

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
		ready(function() {
 			parser.parse();
			on(registry.byId("schedule_btn"), "click", getSchedule);
			on(registry.byId("numberTeams"), "change", setNumberTeams);
			on(registry.byId("numberVenues"), "change", setNumberVenues);
			on(registry.byId("playdivisionSelect"), "change", setPlayDivSelect);			
 		}); 
	}
);