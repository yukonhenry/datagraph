/**
 * @author Henry
 */
require(["dojo/dom", "dojo/on", "dojo/parser", "dijit/registry","dojo/ready", 
		"dojo/request","dojo/request/script",
        "dojo/json", "dojo/domReady!", "dijit/form/NumberTextBox"],
	function(dom, on, parser, registry, ready, request, script, JSON) {

		var getSchedule = function(evt) {
			var numTeams = registry.byId("numberTeams").get("value");
			var numVenues = registry.byId("numberVenues").get("value");
			var schedulerDiv = dom.byId("schedulerDiv");
	        script.get("http://127.0.0.1:8080/getschedule", {
	        	jsonp:"callback", query: {num_teams:numTeams, num_venues:numVenues}
	        }).then(function(data) {
	        	// data returned from server is an array of tuples, with each tuple
	        	// representing two teams in a match
	        	d3.select(schedulerDiv).selectAll("p")
					.data(data.game_list).enter()
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
 		}); 
	}
);