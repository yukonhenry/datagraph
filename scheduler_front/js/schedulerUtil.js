/* look at examples in http://dojotoolkit.org/documentation/tutorials/1.9/modules/
for loadable module design and syntax  also ref
http://dojotoolkit.org/documentation/tutorials/1.9/declare/ and
http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html for class constructor syntax
http://dojotoolkit.org/documentation/tutorials/1.9/augmenting_objects/
				// ref http://stackoverflow.com/questions/13932225/dojo-and-dynamically-added-options-to-dijit-form-select
				// for closure http://stackoverflow.com/questions/4726611/function-used-from-within-javascript-dojo-closure-using-this-notation-is-undef
				// without 3rd argument for  forEach, scope is global
				// http://stackoverflow.com/questions/148901/is-there-a-better-way-to-do-optional-function-parameters-in-javascript
*/
define(["dojo/dom", "dojo/dom-construct", "dojo/_base/declare",
	"dojo/_base/lang", "dojo/dom-class", "dojo/date",
	"dojo/_base/array","dijit/registry", "dojo/domReady!"],
	function(dom, domConstruct, declare, lang, domClass, date,
		arrayUtil, registry){
		return declare(null, {
			server_interface:null,
			constructor: function(args) {
				//declare.safeMixin(this, args);
				// augmenting object tutorial referenced above says lang.mixin is a better choise
				// than declare.safeMixin
				lang.mixin(this, args);
			},
			updateDBstatus_node: function(dbstatus, node) {
				if (dbstatus) {
					node.innerHTML = "Schedule in database, Ready.  See generated tabs above to see various views into schedule"
					node.style.color = 'green';
				} else {
					node.innerHTML = "Schedule Computing, Not Ready";
					node.style.color = 'red';
				}
			},
			detect_arrayduplicate: function(arry) {
				// detect duplicate elements in array
				// ref http://stackoverflow.com/questions/840781/easiest-way-to-find-duplicate-values-in-a-javascript-array
				var sorted_arry = arry.sort();
				var results = [];
				for (var i = 0; i < arry.length - 1; i++) {
					if (sorted_arry[i + 1] == sorted_arry[i]) {
						results.push(sorted_arry[i]);
					}
				}
				return results;
			},
			range: function(start, stop, step){
				// reference http://stackoverflow.com/questions/8273047/javascript-function-similar-to-python-range
				// similar to python range function
			    if (typeof stop==='undefined'){
			        // one param defined
			        stop = start;
			        start = 0;
			    };
			    if (typeof step==='undefined'){
			        step = 1;
			    };
			    if ((step>0 && start>=stop) || (step<0 && start<=stop)){
			        return [];
			    };
			    var result = [];
			    for (var i=start; step>0 ? i<stop : i>stop; i+=step){
			        result.push(i);
			    };
			    return result;
			},
			intersect: function(array1, array2) {
				//Intersection of two arrays to find common eleemnts
				//http://stackoverflow.com/questions/1885557/simplest-code-for-array-intersection-in-javascript
				// make sure arrays are sorted, as intersection depends on it
				array1.sort(function(a, b){return a-b});
				array2.sort(function(a, b){return a-b});
				var result = [];
				// Don't destroy the original arrays
				var a = array1.slice(0);
				var b = array2.slice(0);
				var aLast = a.length - 1;
				var bLast = b.length - 1;
				while (aLast >= 0 && bLast >= 0) {
					if (a[aLast] > b[bLast] ) {
						a.pop();
						aLast--;
					} else if (a[aLast] < b[bLast] ){
						b.pop();
						bLast--;
					} else /* they're equal */ {
						result.push(a.pop());
						b.pop();
						aLast--;
						bLast--;
					}
				}
				return result;
			},
			getcalendarmap_list: function(args_obj) {
				// get list that maps fieldday_id to calendar date
				// note logic is similar to getcalendarmap_list used in py
				// but the input/output is different as this function combines some
				// of the functionality that is done in modifyserver_data with the
				// py getcalendarmap_list code
				// this function only intended to be called when a new grid is
				// created and not when data is retrieved from server
				var dayweek_list = args_obj.dayweek_list;
				var start_date = args_obj.start_date;
				var totalfielddays = args_obj.tfd;
				var start_time_str = args_obj.start_time_str;
				var end_time_str = args_obj.end_time_str;
				var start_day = start_date.getDay();
				var fielddaymapdate_list = new Array();
				var dayweek_len = dayweek_list.length;
        		var firststart_day = -1;
        		var firststart_dwindex = -1;
        		// find first actual start day by finding the first day from
        		// the dayweek_list that is past the start_date which is
        		// selected from the calendar drop-down.
        		if (!arrayUtil.some(dayweek_list, function(item, index) {
        			// for every iteration tentatively assign the first start
        			// date to the current iteration day of the dayweek_list
        			// if the iteration day is greater than start_day, .some
        			// loop will exit
        			firststart_day = item;
        			// firststart_index corresponds to index in dayweek_list that
        			// maps to first_date
        			firststart_dwindex = index;
        			return item >= start_day;
        		})) {
        			// if the .some exited with a false value, then the first
        			// start day is the first element in the dayweek_list
        			firststart_day = dayweek_list[0]
        			firststart_dwindex = 0;
        		}
        		var firststart_diff = firststart_day - start_day;
        		if (firststart_diff < 0) {
        			// do modulo addition if start_day (0-6 range) is larger than
        			// firststart_day
        			firststart_diff += 7;
        		}
        		var first_date = date.add(start_date, 'day', firststart_diff);
        		// create list that maps fieldday to actual calendar date
        		// Represented with list, with position in list corresponding to
        		// fieldday_id
        		// first create list whose elements are the # days gap with the
        		// previous dayweek element
        		var dwgap_list = new Array();
        		// get the last element, but offset it by 7 (length of week)
        		// do this as the gap calculation for the first element should
        		// be first_gap = first_elem +7 - last_elem
        		//              = first_elem - (last_elem - 7)
        		var prev_elem = dayweek_list[dayweek_len-1]-7;
        		arrayUtil.forEach(dayweek_list, function(item, index) {
        			dwgap_list[index] = item - prev_elem;
        			prev_elem = item;
        		})
        		var next_date = first_date;
        		var next_dwindex = firststart_dwindex;
        		// generate list that maps fieldday_id (represented as position in
        		// list) to calendar date string
        		for (var id = 1; id < totalfielddays+1; id++) {
        			var next_date_str = next_date.toLocaleDateString();
        			fielddaymapdate_list.push({
        				fieldday_id:id,
        				start_time:new Date(next_date_str+' '+start_time_str),
        				end_time: new Date(next_date_str+' '+end_time_str)
        				//date:next_date.toLocaleDateString()
        			});
        			// get the next index into the gap list
        			// if index is length of list, then roll over to 0
        			if (++next_dwindex == dayweek_len)
        				next_dwindex = 0
        			next_date = date.add(next_date, 'day',
        				dwgap_list[next_dwindex]);
        		}
        		return fielddaymapdate_list
			}
		})
	}
);
