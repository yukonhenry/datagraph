/**
 * @author Henry
 */
require(["dojo/dom", "dojo/on", "dojo/parser", "dijit/registry","dojo/ready", 
		"dojo/request","dojo/request/script",
        "dojo/json", "dojo/domReady!", "dijit/form/NumberTextBox"],
	function(dom, on, parser, registry, ready, request, script, JSON) {
		var setNumberTeams = function(evt) {
			var numTeams = registry.byId("numberTeams").get("value");
			console.log("number of teams="+numTeams);
		}
		ready(function() {
 			parser.parse();
			on(registry.byId("numberTeams"), "change", setNumberTeams);
 		}); 
	}
);