/**
 * Copyright (c) 2013 YukonTR *
 * @author Henry
 */
// small note, if there are issues with garbage characters in the jsonp script get request,
// ensure http://bugs.dojotoolkit.org/ticket/16408 has been resolved in the branch/release
// that is being used.
// dbootstrap reference: https://github.com/thesociable/dbootstrap
require(["dbootstrap", "dojo/dom", "dojo/dom-construct", "dojo/on", "dojo/parser", "dijit/registry","dojo/ready", 
		"dojo/_base/declare", "dojo/_base/lang", "dgrid/Grid", "dgrid/Selection",
		"dojo/request/script", "dojo/_base/array",
		"dojo/request", 
		"LeagueScheduler/schedulerUtil", "LeagueScheduler/schedulerConfig",
		"LeagueScheduler/newscheduler", "LeagueScheduler/serverinterface",
		"dijit/form/Button",
		"dojo/domReady!"],
	function(dbootstrap, dom, domConstruct, on, parser, registry, ready, declare, lang, Grid, Selection, 
		script, arrayUtil, request, schedulerUtil, schedulerConfig, newscheduler, serverinterface) {
		var constant = {'SERVER_PREFIX':"http://localhost:8080/"};
		var team_id_CONST = 'TEAM_ID';
		var homeratio_CONST = 'HOMERATIO';
		var earliest_count_CONST = 'EARLIEST_COUNT';
		var latest_count_CONST = 'LATEST_COUNT';
		var totalgames_CONST = 'TOTALGAMES'
		var playdivSelectId, numberTeamsId, numberVenuesId;
		var numTeams = 0; numVenues =0; divnum = "U5";
		var gamesGrid = divisionGrid = teamDataGrid = fieldScheduleGrid = metricsGrid = null;
		var seedGrid = null;
		var divisionGridHandle = null;
		var ldata_array = null;
		var schedUtil = null;
		var serverInterface = new serverinterface({hostURL:constant.SERVER_PREFIX});
		var CustomGrid = declare([ Grid, Selection ]);
		var grid = new CustomGrid({
			columns: {
				agediv:"Age Group",
				gender:"Boy/Girl",
				totalteams:"Total#Teams",
				fields:"Fields (ID)",
				gameinterval:"Game Interval(min)",
				gamesperseason:"Games in Season"				
			},
			selectionMode: "single"		
		}, "divisionInfoGrid");
		
		var fieldInfoGrid = new CustomGrid({
			columns: {
				field_id:"Field ID",
				name:"Name"
			},
			selectionMode:"single"
		}, "fieldInfoGrid");    // div ID
		//script.get(constant.SERVER_PREFIX+"leaguedivinfo", {
		//	jsonp:"callback"
		//}).then(function(ldata){
		var leaguediv_func = function(ldata) {
			ldata_array = ldata.leaguedivinfo;
			fdata_array = ldata.field_info;
			grid.renderArray(ldata_array);
			fieldInfoGrid.renderArray(fdata_array);
			dbstatus = ldata.dbstatus;
			schedUtil = new schedulerUtil({leaguedata:ldata_array});
			schedUtil.updateDBstatusline(dbstatus);
			// generate division selection drop-down menus
			schedUtil.generateDivSelectDropDown(registry.byId("divisionSelect"));
			schedUtil.generateDivSelectDropDown(registry.byId("divisionSelectForMetrics"));
			//schedUtil.generateDivSelectDropDown(registry.byId("divSelectForEdit"));
			schedUtil.createSchedLinks(ldata_array, "divScheduleLinks");
			// generate links for individual team schedules
			schedUtil.createTeamSchedLinks(ldata_array, "teamScheduleLinks");
			dbcollection_list = ldata.dbcollection_list;
			dbcollection_submenu_dom = registry.byId("dbcollection_submenu");
			schedUtil.generateDBCollection_smenu(dbcollection_submenu_dom,
				dbcollection_list);
		}
		//});
		serverInterface.getServerData("leaguedivinfo", leaguediv_func);
		
		grid.on("dgrid-select", function(event){
    	// Report the item from the selected row to the console.
    		var idnum = event.rows[0].data.div_id;
    		script.get(constant.SERVER_PREFIX+"leaguedivinfo/"+idnum,{
    			jsonp:"callback"
    		}).then(function(sdata){
				var field_array = sdata.fields;
				// create columns dictionary
				var time_column_key_CONST = 'time';
				var gameday_column_key_CONST = 'cycle';
				var game_columns = {};
				game_columns[gameday_column_key_CONST] = 'Game Date'
				game_columns[time_column_key_CONST] = 'GameTime';
				arrayUtil.forEach(field_array, function(item, index) {
					// fields names are keys to the column dictionary
					game_columns[item] = schedUtil.getFieldMap(item);
				});

				var game_array = sdata.game_list;				
				var game_grid_list = new Array();
				var listindex = 0;
				arrayUtil.forEach(game_array, function(item,index) {
					var gameday_id = item.GAMEDAY_ID;
					var gameday_data = item.GAMEDAY_DATA;
					var start_time = item.START_TIME; 
					var game_grid_row = {};
					// fill in the game day number and start time
					game_grid_row[gameday_column_key_CONST] = schedUtil.getCalendarMap(gameday_id);
					game_grid_row[time_column_key_CONST] = schedUtil.tConvert(start_time);
					arrayUtil.forEach(gameday_data, function(item2, index2) {
						game_grid_row[item2.VENUE] = item2.HOME + 'v' + item2.AWAY;
					});
					game_grid_list[listindex] = game_grid_row;
					listindex++;
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
    		//console.log("Row de-selected: ", event.rows[0].data);
		});
		
		fieldInfoGrid.on("dgrid-select", function(event){
    	// Report the item from the selected row to the console.
    		var fidnum = event.rows[0].data.field_id;
			if (fieldScheduleGrid) {
				// clear grid by clearing dom node
				dom.byId("fieldScheduleGrid").innerHTML = "";
				delete fieldScheduleGrid;
			}
    		fieldScheduleGrid = new CustomGrid({
    			columns:{
    				GAMEDAY_ID:'Game Date',
    				START_TIME:'Start Time',
    				AGE:'Age Group',
    				GEN:'Boy/Girl',
    				HOME:'Home Team#',
    				AWAY:'Away Team#'
    			}
    		},"fieldScheduleGrid");
    		script.get(constant.SERVER_PREFIX+"fieldschedule/"+fidnum,{
    			jsonp:"callback"
    		}).then(function(fdata){
    			fieldschedule_array = fdata.fieldschedule_list;
    			arrayUtil.forEach(fieldschedule_array, function(item, index) {
					// fields names are keys to the column dictionary
					gameday_id = item.GAMEDAY_ID;
					item.GAMEDAY_ID = schedUtil.getCalendarMap(gameday_id);
					item.START_TIME = schedUtil.tConvert(item.START_TIME)
				});    		
    			fieldScheduleGrid.renderArray(fieldschedule_array);
    		});
		});
		var getAllDivSchedule = function(evt) {
			schedUtil.updateDBstatusline(0);
	        script.get(constant.SERVER_PREFIX+"getalldivschedule", {
	        	jsonp:"callback"
	        }).then(function(adata) {
				schedUtil.updateDBstatusline(adata.dbstatus);
/*				
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
*/
			});
		}
		var exportSchedule = function(evt) {
			//dom.byId("status").innerHTML = "";
	        script.get(constant.SERVER_PREFIX+"exportschedule", {
	        	jsonp:"callback"
	        }).then(function(adata) {
	        	//console.log("getalldiv schedule status"+adata.status);
			});			
		}
		var getCupSchedule = function(evt) {
	        script.get(constant.SERVER_PREFIX+"getcupschedule", {
	        	jsonp:"callback"
	        }).then(function(adata) {
	        	//console.log("getalldiv schedule status"+adata.status);
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
    			if (teamDataGrid) {
					dom.byId("teamDataGrid").innerHTML = "";
					// delete reference to obj
					delete teamDataGrid;    				
    			}
    			teamDataGrid = new CustomGrid({
    				columns: {
    					GAMEDAY_ID:'Game Date',
    					START_TIME:'Start Time',
    					VENUE:'Venue',
    					HOME:'Home',
    					AWAY:'Away'
    				}
    			},"teamDataGrid");
    			script.get(constant.SERVER_PREFIX+"teamdata/"+rowid,{
    				jsonp:"callback",
    				query:{division_code:divisioncode}
    			}).then(function(tdata){
    				tdata_array = tdata.teamdata_list;
					arrayUtil.forEach(tdata_array, function(item, index) {
						// fields names are keys to the column dictionary						console.log("tdata "+item);
						gameday_id = item.GAMEDAY_ID;
						item.GAMEDAY_ID = schedUtil.getCalendarMap(gameday_id);
						venue = item.VENUE;
						item.VENUE = schedUtil.getFieldMap(venue);
						item.START_TIME = schedUtil.tConvert(item.START_TIME);
					});    		
    				teamDataGrid.renderArray(tdata_array);
    			});
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
		var editSeedGrid = function(evt) {
			if (seedGrid) {
				dom.byId("seedGrid").innerHTML = "";
				delete seedGrid;
			}
			var schedConfig = new schedulerConfig({div_id:registry.byId("divSelectForEdit").get("value"),
				schedutil_obj:schedUtil});
			seedGrid = schedConfig.createSeedGrid("seedGrid");
			// Note there are several ways to invoke event handler; see this file
			// and ref http://dojotoolkit.org/documentation/tutorials/1.9/events/
			// see http://dojotoolkit.org/documentation/tutorials/1.9/hitch/
			// for usage of hitch to mitigate against js scope rules around execution context
			on(seedGrid, "dgrid-datachange", lang.hitch(schedConfig, schedConfig.editSeedGrid));
			schedConfig.testValue(1);
		}
		var initNewSchedule = function(evt) {
			form_reg = registry.byId("newsched_form_id");
			input_reg = registry.byId("newsched_input_id");
			divnum_reg = registry.byId("divnum_input_id");
			submitbtn_reg = registry.byId("submit_btn");
			newScheduler = new newscheduler({dbname_reg:input_reg, form_reg:form_reg,
				divnum_reg:divnum_reg, server_interface:serverInterface,
				divInfoGridName:"divisionInfoInputGrid"});
			newScheduler.makeVisible("newsched_form_id");
			on(submitbtn_reg, "click", lang.hitch(newScheduler, newScheduler.processdbname_input));
			console.log("after on");
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
		var resizeEditPaneGrids = function(evt) {
			if (seedGrid)
				seedGrid.resize();
		}

		// events for widgets should be in one file; trying to split it up into two or more modules
		// does not work - registry.byId cannot find the widget
		ready(function() {
 			parser.parse();	
			on(registry.byId("schedule_btn"), "click", getAllDivSchedule);
			on(registry.byId("export_btn"), "click", exportSchedule);
			on(registry.byId("cup_btn"), "click", getCupSchedule);
			on(registry.byId("divisionSelect"), "change", getDivisionTeamData);
			on(registry.byId("divisionSelectForMetrics"),"change", getTeamMetrics);
			//on(registry.byId("divSelectForEdit"),"change", editSeedGrid);
			on(registry.byId("divisionPane"),"show",resizeDivisionPaneGrids);
			on(registry.byId("teamsPane"),"show",resizeTeamsPaneGrids);
			on(registry.byId("fieldsPane"),"show",resizeFieldsPaneGrids);
			on(registry.byId("metricsPane"),"show",resizeMetricsPaneGrids);
			on(registry.byId("editPane"),"show",resizeEditPaneGrids);
			on(registry.byId("newsched_item"), "click", initNewSchedule);
 		}); 
	}
);