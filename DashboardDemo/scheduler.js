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
			var textarea = dom.byId("schedule_textarea");
	        script.get("http://127.0.0.1:8080/getschedule", {
	        	jsonp:"callback", query: {num_teams:numTeams, num_venues:numVenues}
	        }).then(function(data) {
	        	textarea.value = data.game_list;
			});
		}
		ready(function() {
 			parser.parse();
			on(registry.byId("schedule_btn"), "click", getSchedule);
 		}); 
	}
);