/**
 * @author Henry
 */
require(["dojo/on", "dojo/parser", "dijit/registry","dojo/ready", "dgrid/Grid",
		"dojo/store/JsonRest",
		"dijit/form/Select", "dijit/form/NumberTextBox","dijit/form/Button",
		"dojo/domReady!"],
	function(on, parser, registry, ready, Grid, JsonRest) {
		var playdivSelectId, numberTeamsId, numberVenuesId;
		var numTeams = 0; numVenues =0; divnum = "U5";
		
		function setDivTeams() {
			console.log("dn, nt, nv="+divnum+" "+numTeams+" "+numVenues);
			
			var divdata = [
				{dnum:divnum, nteams:numTeams, nvenues:numVenues}
			];
			var grid = new Grid({
				columns: {
					dnum: "Division", nteams: "Number Teams", nvenues: "Number Venues"
				}
			}, "divisionInfoGrid");
			grid.renderArray(divdata);

		}

		var setPlayDivSelect = function(evt) {
			divnum = playdivSelectId.get("value");
			setDivTeams();
		};

		var setNumberTeams = function(evt) {
			numTeams = numberTeamsId.get("value");
			setDivTeams();
		}
		var setNumberVenues = function(evt) {
			numVenues = numberVenuesId.get("value");
			setDivTeams();
		}
		ready(function() {
 			parser.parse();	
			playdivSelectId = registry.byId("playdivisionSelect");
 			on(playdivSelectId, "change", setPlayDivSelect);
 			numberTeamsId = registry.byId("numberTeams");
 			on(numberTeamsId, "change", setNumberTeams);
 			numberVenuesId = registry.byId("numberVenues");
 			on(numberVenuesId, "change", setNumberVenues);
 		}); 
	}
);