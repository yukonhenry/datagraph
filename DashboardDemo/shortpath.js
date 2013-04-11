require(["dojo/dom", "dojo/on", "dojo/parser", "dijit/registry","dojo/ready", "dojo/request/script",
        "dojo/json", "dojo/domReady!", "dijit/form/Select"],
    function(dom, on, parser, registry, ready, script, JSON) {
    	var shortDiv = dom.byId("shortestPathDiv");
		var w = 500;
		var h = 500;
	    var svg = d3.select(shortDiv).append("svg")
	        		.attr("width",w)
	        		.attr("height",h);
		var circstart, circend = null;
		var click_startnode = true;
		// ref http://knowledgestockpile.blogspot.com/2012/01/drawing-svg-path-using-d3js.html
		// and https://github.com/mbostock/d3/wiki/SVG-Shapes#wiki-_area
		var linearline = svg.line()
							.x(function(d) { return d.x; })
							.y(function(d) { return d.y; })
							.interpolate("linear");
	    var setDrawMode = function(evt) {

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
	        	//shortDiv.innerHTML = "<b>Data Creation time is "+data.creation_time+"</b><br>";
	        	//Width and height

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

	        	//d3.select("svg")
	        	var obs_startnode_flag = true;
	        	svg.on("click", function() {
	        		var point = d3.mouse(this);
	        		console.log("coord x="+point[0]+" y="+point[1]);
	        		switch(drawmode) {
	        		case 'sg':
	        			// click_startnode variable controls whether we are drawing start or end node
						if (click_startnode) {
							if (circstart) {
								// delete note by reducing radius attribute to zero and then removing DOM node
								// see example http://bl.ocks.org/benzguo/4370043
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
						break;
					case 'obs':
						// draw obstacle
						if (obs_startnode_flag) {
							var obsnode = svg.append("circle");
	        				obsnode.attr("cx",point[0]).attr("cy",point[1]).attr("r",10).attr("stroke",strokeColor).attr("fill","red")
	        					.on("click", function(d) {
	        						console.log("obsnode ="+obsnode);
	        					});
	        				obs_startnode_flag = false;
	        			} else {
	        				
	        			} 
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
			on(registry.byId("drawingMode"), "change", setDrawMode);
			//on(dom.byId("National"), "click", myClick);
 		});
    }
);        		
