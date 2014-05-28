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
		"LeagueScheduler/tourndivinfo",
		"dojo/domReady!"],
	function(dbootstrap, dom, on, parser, registry, ready, declare, lang, Grid,
		Selection, script, arrayUtil, request, schedulerUtil,
		serverinterface, divinfo, FieldInfo, baseinfoSingleton, NewSchedulerBase,
		PreferenceInfo, UIStackManager, storeUtil, tourndivinfo) {
		var constant = {SERVER_PREFIX:"http://localhost:8080/"};
		var team_id_CONST = 'TEAM_ID';
		var homeratio_CONST = 'HOMERATIO';
		var earliest_count_CONST = 'EARLIEST_COUNT';
		var latest_count_CONST = 'LATEST_COUNT';
		var totalgames_CONST = 'TOTALGAMES'
		var playdivSelectId, numberTeamsId, numberVenuesId;
		var gamesGrid = null; var divisionGrid = null;
		var teamDataGrid = null; var fieldScheduleGrid = null;
		var metricsGrid = null;
		var seedGrid = null;
		var divisionGridHandle = null;
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
			var rrdbcollection_list = ldata.rrdbcollection_list;
			// fill initial store and create dropdown menu
			storeutil_obj.createdb_store(rrdbcollection_list, 'rrdb');
			storeutil_obj.create_menu('div_id', divinfo_obj, true);
			var tourndbcollection_list = ldata.tourndbcollection_list;
			storeutil_obj.createdb_store(tourndbcollection_list, 'tourndb');
			storeutil_obj.create_menu('tourndiv_id', tourndivinfo_obj, true);
			// note we need to add delete to the schedule here by passing 'true'
			//var dbcollection_list = rrdbcollection_list.concat(tourndbcollection_list)
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
			storeutil_obj.create_menu('field_id', fieldinfo_obj, true);
			// load initial schedule db's for display under new schedule/generation
			// submenu
			var newscheddb_list = ldata.newscheddb_list;
			storeutil_obj.createdb_store(newscheddb_list, 'newscheddb');
			storeutil_obj.create_menu('newsched_id', newschedbase_obj, true);
			var prefdb_list = ldata.prefdb_list;
			storeutil_obj.createdb_store(prefdb_list, 'prefdb');
			storeutil_obj.create_menu('pref_id', preferenceinfo_obj, true);
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
		var getTeamMetrics = function(evt) {
			var division_id = registry.byId("divisionSelectForMetrics").get("value");
    		script.get(constant.SERVER_PREFIX+"schedulemetrics/"+division_id,{
    			jsonp:"callback"
    		}).then(function(mdata){
				var field_array = mdata.fields;
				var metrics_array = mdata.metrics;
				var metrics_columns = {};
				metrics_columns[team_id_CONST] = "Team ID";
				metrics_columns[totalgames_CONST] = "Total Games"
				metrics_columns[homeratio_CONST] = "Home ratio";
				arrayUtil.forEach(field_array, function(item, index) {
					// fields names are keys to the column dictionary
					metrics_columns[item] = '# games field '+item;
				});
				metrics_columns[earliest_count_CONST] = '# Earliest Games';
				metrics_columns[latest_count_CONST] = '# Latest Games';

				dom.byId("metricsHeader").innerHTML =
					"Total game slots per team: <b>"+ldata_array[division_id-1].gamesperseason+"</b>";
				// this will define number of columns (games per day)
				if (metricsGrid) {
					// clear grid by clearing dom node
					dom.byId("metricsGrid").innerHTML = "";
					delete metricsGrid;
				}
				var metricsGrid_list = new Array();
				var listindex = 0;
				arrayUtil.forEach(metrics_array, function(item,index) {
					var team_id = item.TEAM_ID;
					var totalgames = item.TOTALGAMES;
					var homeratio = item.HOMERATIO;
					var venue_count_array = item.VENUE_COUNT_LIST;
					var metrics_grid_row = {};
					// fill in the game day number and start time
					metrics_grid_row[team_id_CONST] = team_id;
					metrics_grid_row[totalgames_CONST] = totalgames;
					metrics_grid_row[homeratio_CONST] = homeratio;
					arrayUtil.forEach(venue_count_array, function(item2, index2) {
						metrics_grid_row[item2.VENUE] = item2.VENUE_COUNT;
					});
					metrics_grid_row[earliest_count_CONST] = item.EARLIEST_COUNT;
					metrics_grid_row[latest_count_CONST] = item.LATEST_COUNT;

					metricsGrid_list[listindex] = metrics_grid_row;
					listindex++;
				});
    			metricsGrid = new CustomGrid({
    				columns:metrics_columns,
    			},"metricsGrid");
    			metricsGrid.renderArray(metricsGrid_list);
    		});
		};
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
		// resize dgrid's if there is a show event on the content pane
		// see https://github.com/SitePen/dgrid/issues/63
		var resizeDivisionPaneGrids = function(evt) {
			grid.resize();
			if (gamesGrid)
				gamesGrid.resize();
		}
		var resizeTeamsPaneGrids = function(evt) {
			if (divisionGrid)
				divisionGrid.resize();
			if (teamDataGrid)
				teamDataGrid.resize();
		}
		var resizeFieldsPaneGrids = function(evt) {
			fieldInfoGrid.resize();
			if (fieldScheduleGrid)
				fieldScheduleGrid.resize();
		}
		var resizeMetricsPaneGrids = function(evt) {
			if (metricsGrid)
				metricsGrid.resize();
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
			//			on(registry.byId("newdivinfo_item"), "click",initNewDivInfo
			//	);
			on(registry.byId("newdivinfo_item"), "click",
				lang.hitch(uiStackManager, uiStackManager.check_initialize, divinfo_obj));
			on(registry.byId("tournnewdivinfo_item"), "click",
				lang.hitch(uiStackManager, uiStackManager.check_initialize, tourndivinfo_obj));
			on(registry.byId("newfieldlist_item"), "click",
				lang.hitch(uiStackManager, uiStackManager.check_initialize, fieldinfo_obj));
			on(registry.byId("newsched_item"), "click",
				lang.hitch(uiStackManager, uiStackManager.check_initialize,
					newschedbase_obj));
			on(registry.byId("newpref_item"), "click",
				lang.hitch(uiStackManager, uiStackManager.check_initialize,
					preferenceinfo_obj));
			//on(registry.byId("elimination2013"), "click", elimination2013);
			//on(registry.byId("export_elimination2013"), "click", export_elim2013);
 		});
	}
);
