/**
 * Copyright (c) 2013 YukonTR *
 * @author Henry
 */
// small note, if there are issues with garbage characters in the jsonp script get request,
// ensure http://bugs.dojotoolkit.org/ticket/16408 has been resolved in the branch/release
// that is being used.
// dbootstrap reference: https://github.com/thesociable/dbootstrap
require(["dbootstrap", "dojo/dom", "dojo/on", "dojo/parser", "dijit/registry","dojo/ready",
		"dojo/_base/declare", "dojo/_base/lang", "dgrid/Grid", "dgrid/Selection",
		"dojo/request/script", "dojo/_base/array",
		"dojo/request",
		"LeagueScheduler/schedulerUtil", "LeagueScheduler/serverinterface",
		"LeagueScheduler/divinfo",
		"LeagueScheduler/fieldinfo", "LeagueScheduler/baseinfoSingleton",
		"LeagueScheduler/newschedulerbase", "LeagueScheduler/preferenceinfo",
		"LeagueScheduler/uistackmanager", "LeagueScheduler/storeutil",
		"LeagueScheduler/tourndivinfo", "LeagueScheduler/wizardlogic",
		"dojo/domReady!"],
	function(dbootstrap, dom, on, parser, registry, ready, declare, lang, Grid,
		Selection, script, arrayUtil, request, schedulerUtil,
		serverinterface, divinfo, FieldInfo, baseinfoSingleton, NewSchedulerBase,
		PreferenceInfo, UIStackManager, storeUtil, tourndivinfo, WizardLogic) {
		var constant = {SERVER_PREFIX:"http://localhost:8080/"};
		var gamesGrid = null; var divisionGrid = null;
		var teamDataGrid = null; var fieldScheduleGrid = null;
		var metricsGrid = null;
		var seedGrid = null;
		var ldata_array = null;
		var schedUtil = null;
		var serverInterface = new serverinterface({hostURL:constant.SERVER_PREFIX});
		var newschedbase_obj = new NewSchedulerBase({server_interface:serverInterface});
		var divinfo_obj = new divinfo({server_interface:serverInterface});
		var tourndivinfo_obj = new tourndivinfo({server_interface:serverInterface});
		var fieldinfo_obj = new FieldInfo({server_interface:serverInterface});
		var preferenceinfo_obj = new PreferenceInfo(
			{server_interface:serverInterface});
		//var schedinfo_obj = new schedinfo({server_interface:serverInterface});
		var uiStackManager = null;
		var CustomGrid = declare([ Grid, Selection ]);
		var leaguediv_func = function(ldata) {
			ldata_array = ldata.leaguedivinfo;
			var fdata_array = ldata.field_info;
			//grid.renderArray(ldata_array);
			//fieldInfoGrid.renderArray(fdata_array);
			//var dbstatus = ldata.dbstatus;
			schedUtil = new schedulerUtil({leaguedata:ldata_array, server_interface:serverInterface});
			var storeutil_obj = new storeUtil({schedutil_obj:schedUtil, uistackmgr:uiStackManager, server_interface:serverInterface});
			newschedbase_obj.set_obj(schedUtil, storeutil_obj);
			fieldinfo_obj.set_obj(schedUtil, storeutil_obj);
			divinfo_obj.set_obj(schedUtil, storeutil_obj);
			tourndivinfo_obj.set_obj(schedUtil, storeutil_obj);
			preferenceinfo_obj.set_obj(schedUtil, storeutil_obj);
			//schedinfo_obj.set_obj(schedUtil, storeutil_obj);
			//schedUtil.createSchedLinks(ldata_array, "divScheduleLinks");
			// generate links for individual team schedules
			//schedUtil.createTeamSchedLinks(ldata_array, "teamScheduleLinks");
			// generate dropdown menu for edit->existing schedules
			var parent_ddown_reg = registry.byId("configmenu_id");
			var rrdbcollection_list = ldata.rrdbcollection_list;
			// fill initial store and create dropdown menu
			storeutil_obj.createdb_store(rrdbcollection_list, 'rrdb');
			//storeutil_obj.create_menu('div_id', divinfo_obj, true, parent_ddown_reg);
			var tourndbcollection_list = ldata.tourndbcollection_list;
			storeutil_obj.createdb_store(tourndbcollection_list, 'tourndb');
			//storeutil_obj.create_menu('tourndiv_id', tourndivinfo_obj, true);
			var args_list = [{id:'div_id', info_obj:divinfo_obj},
				{id:'tourndiv_id', info_obj:tourndivinfo_obj}]
			var args_obj = {parent_ddown_reg:parent_ddown_reg,
				args_list:args_list}
			storeutil_obj.create_divmenu(args_obj);
			// note we need to add delete to the schedule here by passing 'true'
			//storeutil_obj.create_menu('sched_id', schedinfo_obj, false);
			// generate dropdown for 'generate cup schedule'
			/*
			var cupdbcollection_list = ldata.tourndbcollection_list;
			var cupdbcollection_smenu_reg = registry.byId("cupdbcollection_submenu");
			schedUtil.generateDBCollection_smenu(cupdbcollection_smenu_reg,
				cupdbcollection_list, schedUtil, schedUtil.getCupSchedule,
				{db_type:'gen'});
			var exportcupdbcollection_smenu_reg = registry.byId("exportcupdbcollection_submenu")
			schedUtil.generateDBCollection_smenu(exportcupdbcollection_smenu_reg,
				cupdbcollection_list, schedUtil, schedUtil.export_rr2013,
				{db_type:'export'});
			*/
			// create menu for the field collections lists
			var fielddb_list = ldata.fielddb_list;
			storeutil_obj.createdb_store(fielddb_list, 'fielddb');
			storeutil_obj.create_menu('field_id', fieldinfo_obj, true,
				parent_ddown_reg);
			// load initial schedule db's for display under new schedule/generation
			// submenu
			var newscheddb_list = ldata.newscheddb_list;
			storeutil_obj.createdb_store(newscheddb_list, 'newscheddb');
			storeutil_obj.create_menu('newsched_id', newschedbase_obj, true,
				parent_ddown_reg);
			var prefdb_list = ldata.prefdb_list;
			storeutil_obj.createdb_store(prefdb_list, 'prefdb');
			storeutil_obj.create_menu('pref_id', preferenceinfo_obj, true,
				parent_ddown_reg);
			var wizardlogic_obj = new WizardLogic({storeutil_obj:storeutil_obj});
			wizardlogic_obj.create();
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
			/*
			var active_grid = baseinfoSingleton.get_active_grid();
			if (active_grid) {
				active_grid.schedInfoGrid.resize();
			} */
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
		// make sure global variables/objects have full context by the time callback functions to events defined below are assigned
		ready(function() {
 			parser.parse();
 			// UI Stack Manager obj can only be created after html has been parsed
			// as UIStackManager constructor needs to identify widgets
			uiStackManager = new UIStackManager();
			divinfo_obj.uistackmgr = uiStackManager;
			tourndivinfo_obj.uistackmgr = uiStackManager;
			fieldinfo_obj.uistackmgr = uiStackManager;
			//schedinfo_obj.uistackmgr = uiStackManager;
			newschedbase_obj.uistackmgr = uiStackManager;
			preferenceinfo_obj.uistackmgr = uiStackManager;
			serverInterface.getServerData("leaguedivinfo", leaguediv_func);
			//on(registry.byId("divisionPane"),"show",resizeDivisionPaneGrids);
			//on(registry.byId("teamsPane"),"show",resizeTeamsPaneGrids);
			//on(registry.byId("fieldsPane"),"show",resizeFieldsPaneGrids);
			//on(registry.byId("metricsPane"),"show",resizeMetricsPaneGrids);
			on(registry.byId("editPane"),"show",resizeEditPaneGrids);
			on(registry.byId("editPane"),"load",scrollTopEditPane);
			//on(registry.byId("tournamentPane"),"show",resizeTournamentPaneGrids);
			//on(registry.byId("elimination2013"), "click", elimination2013);
			//on(registry.byId("export_elimination2013"), "click", export_elim2013);
 		});
	}
);
