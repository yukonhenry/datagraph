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
		"dojo/request/script", "dojo/_base/array",
		"dojo/request",
		"LeagueScheduler/schedulerUtil", "LeagueScheduler/serverinterface",
		"LeagueScheduler/divinfo",
		"LeagueScheduler/fieldinfo", "LeagueScheduler/baseinfoSingleton",
		"LeagueScheduler/newschedulerbase", "LeagueScheduler/preferenceinfo",
		"LeagueScheduler/uistackmanager", "LeagueScheduler/storeutil",
		"LeagueScheduler/tourndivinfo", "LeagueScheduler/wizardlogic",
		"LeagueScheduler/teaminfo", "LeagueScheduler/exclusioninfo",
		"dojo/domReady!"],
	function(dbootstrap, dom, on, parser, registry, ready, declare, lang, script, arrayUtil, request, schedulerUtil,
		serverinterface, divinfo, FieldInfo, baseinfoSingleton, NewSchedulerBase,
		PreferenceInfo, UIStackManager, storeUtil, tourndivinfo, WizardLogic,
		TeamInfo, ExclusionInfo) {
		var constant = {SERVER_PREFIX:"http://localhost:8080/"};
		var ldata_array = null;
		var serverInterface = new serverinterface({hostURL:constant.SERVER_PREFIX});
		var schedutil_obj = new schedulerUtil({server_interface:serverInterface});
		var uistackmgr = new UIStackManager();
		// storeutil_obj has separate member variables for uistackmgr and
		// wizuistackmgr
		var storeutil_obj = new storeUtil({schedutil_obj:schedutil_obj,
			server_interface:serverInterface, uistackmgr:uistackmgr});
		var wizardlogic_obj = new WizardLogic({server_interface:serverInterface,
			storeutil_obj:storeutil_obj, schedutil_obj:schedutil_obj});
		var newschedbase_obj = new NewSchedulerBase({
			server_interface:serverInterface, schedutil_obj:schedutil_obj,
			uistackmgr_type:uistackmgr, storeutil_obj:storeutil_obj, op_type:"advance"});
		var divinfo_obj = new divinfo({server_interface:serverInterface,
			schedutil_obj:schedutil_obj, uistackmgr_type:uistackmgr,
			storeutil_obj:storeutil_obj, op_type:"advance"});
		var tourndivinfo_obj = new tourndivinfo({server_interface:serverInterface,
			schedutil_obj:schedutil_obj, uistackmgr_type:uistackmgr,
			storeutil_obj:storeutil_obj, op_type:"advance"});
		var fieldinfo_obj = new FieldInfo({server_interface:serverInterface,
			schedutil_obj:schedutil_obj, uistackmgr_type:uistackmgr,
			storeutil_obj:storeutil_obj, op_type:"advance"});
		var preferenceinfo_obj = new PreferenceInfo(
			{server_interface:serverInterface, schedutil_obj:schedutil_obj,
				uistackmgr_type:uistackmgr, storeutil_obj:storeutil_obj,
				op_type:"advance"});
		var teaminfo_obj = new TeamInfo(
			{server_interface:serverInterface, schedutil_obj:schedutil_obj,
				uistackmgr_type:uistackmgr, storeutil_obj:storeutil_obj,
				op_type:"advance"});
		var exclusioninfo_obj = new ExclusionInfo(
			{server_interface:serverInterface, schedutil_obj:schedutil_obj,
				uistackmgr_type:uistackmgr, storeutil_obj:storeutil_obj,
				op_type:"advance"});
		var leaguediv_func = function(ldata) {
			var ldata_array = ldata.leaguedivinfo;

			//schedUtil.createSchedLinks(ldata_array, "divScheduleLinks");
			// generate links for individual team schedules
			//schedUtil.createTeamSchedLinks(ldata_array, "teamScheduleLinks");
			// generate dropdown menu for edit->existing schedules
			//var parent_ddown_reg = registry.byId("configmenu_id");
			var rrdbcollection_list = ldata.rrdbcollection_list;
			var tourndbcollection_list = ldata.tourndbcollection_list;
			var fielddb_list = ldata.fielddb_list;
			var newscheddb_list = ldata.newscheddb_list;
			var prefdb_list = ldata.prefdb_list;
			var teamdb_list = ldata.teamdb_list;
			var data_list = [
				{db_type:'rrdb', db_list:rrdbcollection_list},
				{db_type:'tourndb', db_list:tourndbcollection_list},
				{db_type:'fielddb', db_list:fielddb_list},
				{db_type:'newscheddb', db_list:newscheddb_list},
				{db_type:'prefdb', db_list:prefdb_list},
				{db_type:'teamdb', db_list:teamdb_list}];
			// store initial data returned from server
			storeutil_obj.store_init_data(data_list)
			// create initial wizard UI
			wizardlogic_obj.create();
			// create advanced UI
			var info_obj_list = [
				{id:'div_id', info_obj:divinfo_obj},
				{id:'tourndiv_id', info_obj:tourndivinfo_obj},
				{id:'field_id', info_obj:fieldinfo_obj},
				{id:'team_id', info_obj:teaminfo_obj},
				{id:'pref_id', info_obj:preferenceinfo_obj},
				{id:'newsched_id', info_obj:newschedbase_obj},
			]
			storeutil_obj.init_advanced_UI(info_obj_list);
			console.log("load basic info complete");
		}
/*
		var exportSchedule = function(evt) {
			//dom.byId("status").innerHTML = "";
	        script.get(constant.SERVER_PREFIX+"exportschedule", {
	        	jsonp:"callback"
	        }).then(function(adata) {
			});
		}
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
			serverInterface.getServerData("leaguedivinfo", leaguediv_func);
			//on(registry.byId("elimination2013"), "click", elimination2013);
			//on(registry.byId("export_elimination2013"), "click", export_elim2013);
 		});
	}
);
