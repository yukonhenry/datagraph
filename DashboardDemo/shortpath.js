require(["dojo/dom", "dojo/on", "dojo/parser", "dijit/registry","dojo/ready", "dojo/request/script",
        "dojo/json", "dojo/domReady!", "dijit/form/Select"],
    function(dom, on, parser, registry, ready, script, JSON) {
    	var setDrawMode = function(evt) {
        	var shortDiv = dom.byId("shortestPathDiv");
        	var drawmode = registry.byId("drawingMode").get("value");
        	var strokeColor;
	        if (drawmode == 'sg') {
	        	strokeColor = "red";
	        } else if (drawmode == 'obs') {
	        	strokeColor = "blue";
	        } else {
	        	strokeColor = "yellow";
	        }
	    	script.get("http://127.0.0.1:8080/getpathdata", {
	        	jsonp:"callback"
	        }).then(function(data) {
	        	shortDiv.innerHTML = "<b>Data Creation time is "+data.creation_time+"</b><br>";
	        	//Width and height
				var w = 500;
				var h = 500;
	        	var svg = d3.select(shortDiv).append("svg")
	        				.attr("width",w)
	        				.attr("height",h);
	        	var circles = svg.selectAll("circle")
	        					.data(data.pathdata)
	        					.enter()
	        					.append("circle");
	        	circles
	        		.attr("cx", function(d) {
	        		return d[0];
	        	})
	        		.attr("cy", function(d) {
	        		return d[1];
	        	})
	        		.attr("r",10);
	        		
	        	d3.select(shortDiv)
	        		.selectAll("p")
	        		.data(data.pathdata)
	        		.enter()
	        		.append("p")
	        		.text(function(d) {return d;});

	        	// reference on null/undefined handling
	     		// http://saladwithsteve.com/2008/02/javascript-undefined-vs-null.html
				var circstart, circend = null;
				var click_startnode = true;
	        	//d3.select("svg")
	        	svg.on("click", function() {
	        		var point = d3.mouse(this);
	        		console.log("coord x="+point[0]+" y="+point[1]);
					if (click_startnode) {
						if (circstart) {
							circstart.attr("r",0);
							circstart.transition().remove();
						}							
	        			circstart = svg.append("circle");
	        			circstart.attr("cx",point[0]).attr("cy",point[1]).attr("r",10).attr("stroke",strokeColor).attr("fill","green");
						click_startnode = false;
					} else {
						if (circend) {
							circend.attr("r",0);
							circend.transition().remove();
						}
						circend = svg.append("circle");
	        			circend.attr("cx",point[0]).attr("cy",point[1]).attr("r",10).attr("stroke",strokeColor).attr("fill","yellow");
						click_startnode = true;
					}
				});
			}, function(error){
                  // Display the error returned
                    console.log('error response is ' + error);
            });				
 		};  /* setDrawMode */
 		ready(function() {
 			parser.parse();
 			console.log("parsing");
			on(registry.byId("drawingMode"), "change", setDrawMode);
			//on(dom.byId("National"), "click", myClick);
 		});
    }
);        		
