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

	        	var clickCount = 0;

	        	//d3.select("svg")
	        	svg.on("click", function() {
	        		var point = d3.mouse(this);
	        		var circstart = svg.append("circle");
	        		var circend = svg.append("circle");
	        		console.log("coord x="+point[0]+" y="+point[1]);
	        		switch (clickCount) {
	        		case 0:
	        			//circstart = svg.append("circle");
	        			circstart.attr("cx",point[0]).attr("cy",point[1]).attr("r",10).attr("stroke",strokeColor).attr("fill","green");
						clickCount = 1;
						break;
					case 1:
	        			circend.attr("cx",point[0]).attr("cy",point[1]).attr("r",10).attr("stroke",strokeColor).attr("fill","yellow");
						clickCount = 2;
						break;
					case 2:
						circstart.remove();
						clickCount = 3;
						break;
					case 3:
						circend.remove();
						clickCount = 0;
						break;
					default:
						break;
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
