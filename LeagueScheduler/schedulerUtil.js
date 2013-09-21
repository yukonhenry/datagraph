/* look at examples in http://dojotoolkit.org/documentation/tutorials/1.9/modules/
for loadable module design and syntax  also ref
http://dojotoolkit.org/documentation/tutorials/1.9/declare/ and 
http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html for class constructor syntax
http://dojotoolkit.org/documentation/tutorials/1.9/augmenting_objects/*/
define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array", "dojo/domReady!"], 
	function(dom, declare, lang, arrayUtil){
		var calendarMapObj = {1:'Sept 7', 2:'Sept 14', 3:'Sept 21', 4:'Sept 28', 5:'Oct 5',
			6:'Oct 12', 7:'Oct 19', 8:'Oct 26', 9:'Nov 2', 10:'Nov 9', 11:'Nov 16', 12:'Nov 23'};
		var fieldMapObj = {1:'Sequoia Elem 1', 2:'Sequoia Elem 2',3:'Pleasant Hill Elem 1',
			4:'Pleasant Hill Elem 2',
			5:'Pleasant Hill Elem 3', 6:'Golden Hills 1', 7:'Golden Hills 2',
			8:'Mountain View Park', 9:'Pleasant Hill Middle 1', 10:'Pleasant Hill Middle 2',
			11:'Pleasant Hill Middle 3', 12:'Nancy Boyd Park', 13:'Strandwood Elem',
			14:'Sequoia Middle', 15:'Gregory Gardens Elem', 16:'Pleasant Hill Park'};
		var status_dom = dom.byId("dbstatus_txt");
		var status1_dom = dom.byId("dbstatus1_txt");
		return declare(null, {
			leaguedata: null,
			constructor: function(args) {
				//declare.safeMixin(this, args);
				// augmenting object tutorial referenced above says lang.mixin is a better choise
				// than declare.safeMixin
				lang.mixin(this, args);
			},
			getCalendarMap: function(gameday_id) {
				return calendarMapObj[gameday_id];
			},
			getFieldMap: function(field_id) {
				return fieldMapObj[field_id];
			},
			tConvert: function(time) {
				// courtesy http://stackoverflow.com/questions/13898423/javascript-convert-24-hour-time-of-day-string-to-12-hour-time-with-am-pm-and-no
  				// Check correct time format and split into components
  				time = time.toString ().match (/^([01]\d|2[0-3])(:)([0-5]\d)(:[0-5]\d)?$/) || [time];

  				if (time.length > 1) { // If time format correct
    				time = time.slice (1);  // Remove full string match value
    				time[5] = +time[0] < 12 ? ' am' : ' pm'; // Set AM/PM
    				time[0] = +time[0] % 12 || 12; // Adjust hours
  				}
  				return time.join (''); // return adjusted time or original string
			},
			updateDBstatusline: function(dbstatus) {
				arrayUtil.forEach([status_dom, status1_dom], function(item_dom, index) {
					if (dbstatus) {
						item_dom.innerHTML = "Schedule in database, Ready";
						item_dom.style.color = 'green';
					} else {
						item_dom.innerHTML = "Schedule Not Ready";
						item_dom.style.color = 'red';
					}
				});
			},
			generateDivSelectDropDown: function(select_reg) {
				// ref http://stackoverflow.com/questions/13932225/dojo-and-dynamically-added-options-to-dijit-form-select
				option_array = [{label:"Select Division", value:"", selected:true}];
				arrayUtil.forEach(this.leaguedata, function(item, index) {
					divstr = item.agediv + item.gender;
					// division code is 1-index based so increment by 1
					option_array.push({label:divstr, value:index+1, selected:false});
				});
				select_reg.addOption(option_array);
			},
			getNumberTeams: function(div_id) {
				// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/array.html#dojo-base-array
				var result_array = arrayUtil.filter(this.leaguedata, function(item) {
					return item.div_id == div_id;
				});
				return result_array[0].totalteams;
			}
		});
	}
);