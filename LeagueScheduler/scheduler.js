/**
 * Copyright (c) 2013 YukonTR *
 * @author Henry
 */
// small note, if there are issues with garbage characters in the jsonp script get request,
// ensure http://bugs.dojotoolkit.org/ticket/16408 has been resolved in the branch/release
// that is being used.
// dbootstrap reference: https://github.com/thesociable/dbootstrap
require(["dbootstrap", "dojo/dom", "dojo/on", "dojo/parser", "dijit/registry","dojo/ready",
		"dojo/_base/declare", "dojo/_base/lang",
		"dojo/request/script", "dojo/_base/array", "dojo/request",
		"LeagueScheduler/schedulerUtil", "LeagueScheduler/serverinterface",
		"LeagueScheduler/baseinfoSingleton",
		"LeagueScheduler/storeutil", "LeagueScheduler/userinfo",
		"dojo/domReady!"],
	function(dbootstrap, dom, on, parser, registry, ready, declare, lang, script, arrayUtil, request, schedulerUtil,
		serverinterface, baseinfoSingleton, storeUtil,
		UserInfo) {
		var constant = {SERVER_PREFIX:"http://localhost:8080/"};
		var serverInterface = new serverinterface({hostURL:constant.SERVER_PREFIX});
		var schedutil_obj = new schedulerUtil({server_interface:serverInterface});
		// storeutil_obj has separate member variables for uistackmgr and
		// wizuistackmgr
		var storeutil_obj = new storeUtil({schedutil_obj:schedutil_obj,
			server_interface:serverInterface});
		var userinfo_obj = new UserInfo({server_interface:serverInterface,
			storeutil_obj:storeutil_obj});
		var server_process = function(adata) {
			var greeting_node = dom.byId("versiongreeting");
			greeting_node.innerHTML += " running since "+adata.creation_time;
			baseinfoSingleton.set_hostserver(adata.hostserver);
			userinfo_obj.create();
			console.log("load userinfo pane complete");
		}
/*
		var elimination2013 = function(evt) {
		    script.get(constant.SERVER_PREFIX+"elimination2013/phmsacup2013", {
	        	jsonp:"callback"
	        }).then(function(adata) {
	        	//console.log("getalldiv schedule status"+adata.status);
			});
		}
		var export_elim2013 = function(evt) {
			//dom.byId("status").innerHTML = "";
	        script.get(constant.SERVER_PREFIX+"export_elim2013/phmsacup2013", {
	        	jsonp:"callback"
	        }).then(function(adata) {exp
	        	//console.log("getalldiv schedule status"+adata.status);
			});
		}
		*/
		var resizeEditPaneGrids = function(evt) {
			console.log("show edit pane");
			if (uiStackManager && uiStackManager.current_grid) {
				uiStackManager.current_grid.resize();
			}
			var pane_dom = dom.byId("editPane");
			pane_dom.scrollTop = 0;
			//to resize bracket info grid also
		}
		var scrollTopEditPane = function(evt) {
			console.log("load edit pane");
			//http://dojo-toolkit.33424.n3.nabble.com/Force-ContentPane-to-scroll-to-top-when-showing-td158406.html
			// ensure edit pane scroll resets to top
			// seems like scrolling to top only works if it works off of onLoad and not onShow
			var pane_dom = dom.byId("editPane");
			pane_dom.scrollTop = 0;
		}
		var resizeTournamentPaneGrids = function(evt) {
			// todo
		}
		// make sure global variables/objects have full context by the time callback functions to events defined below are assFigned
		ready(function() {
 			parser.parse();
 			// UI Stack Manager obj can only be created after html has been parsed
			// as UIStackManager constructor needs to identify widgets
			serverInterface.getServerData("get_hostserver", server_process);
 		});
	}
);
