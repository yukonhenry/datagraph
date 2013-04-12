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
		// http://www.dashingd3js.com/svg-paths-and-d3js
		var obs_startnode_flag = true;
		var linearline = d3.svg.line()
							.x(function(d) { return d.x; })
							.y(function(d) { return d.y; })
							.interpolate("linear");
		var line_startpos = {x:0, y:0};
		var line_endpos = {x:0, y:0};

		var linearline_closed = d3.svg.line()
							.x(function(d) { return d.x; })
							.y(function(d) { return d.y; })
							.interpolate("linear-closed");
		
		function computePath(sgnodes, obs_polyline) {
			script.get("http://127.0.0.1:8080/getpathdata", {
	        	jsonp:"callback", query:{sg_nodes:sgnodes, obs_poly:obs_polyline}
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
	        	// will most likely delete text printout of nodes
	        	d3.select(shortDiv)
	        		.selectAll("p")
	        		.data(data.pathdata)
	        		.enter()
	        		.append("p")
	        		.text(function(d) {return d;});
			}, function(error){
                  // Display the error returned
                    console.log('error response is ' + error);
            });
		};  //computePath	

	    var setDrawMode = function(evt) {
        	var drawmode = registry.byId("drawingMode").get("value");
        	var strokeColor;
        	var sgnodes = [{x:0,y:0},{x:0,y:0}];
			var obs_polyline = new Array();        	
        	switch(drawmode) {
        	case 'sg':
	        	strokeColor = "red";
	        	svg.on("click", function() {
	        		var point = d3.mouse(this);
	        		console.log("coord x="+point[0]+" y="+point[1]);
	        		// click_startnode variable controls whether we are drawing start or end node
					if (click_startnode) {
						if (circstart) {
							// delete note by reducing radius attribute to zero and then removing DOM node
							// see example http://bl.ocks.org/benzguo/4370043
							//circstart.attr("r",0);  // we don't really need to do this where we decrease r to 0
							circstart.remove();
						}							
	        			circstart = svg.append("circle");
	        			circstart.attr("cx",point[0]).attr("cy",point[1]).attr("r",10).attr("stroke",strokeColor).attr("fill","green");
	        			sgnodes[0].x = point[0];
	        			sgnodes[0].y = point[1];
						click_startnode = false;
					} else {
						if (circend) {
							//circend.attr("r",0);
							circend.remove();
						}
						circend = svg.append("circle");
	        			circend.attr("cx",point[0]).attr("cy",point[1]).attr("r",10).attr("stroke",strokeColor).attr("fill","yellow");
	        			sgnodes[1].x = point[0];
	        			sgnodes[1].y = point[1];
						click_startnode = true;
					}
				});
				break;
	        case 'obs':
	        	strokeColor = "blue";
	        	var line_drawing_mode = false;  // controls obstacle drawing
				// create array that will hold point coordinates of polyline rep of obstacle

				var obs_pathobj_array = new Array();  // for holding the individual path line segments
	        	svg.on("click", function() {
	        		var point = d3.mouse(this);
	        		console.log("coord x="+point[0]+" y="+point[1]);
					// draw obstacle
					if (obs_startnode_flag) {
						var obsnode = svg.append("circle");
						line_drawing_mode = true;
	        			obsnode.attr("cx",point[0]).attr("cy",point[1]).attr("r",10).attr("stroke",strokeColor).attr("fill","red")
	        				.on("click", function(d) {
	        					console.log("obsnode ="+obsnode);
	        					line_drawing_mode = false;
	        					// first remove the temporary line segments created during
	        					// drawing of individual segments
	        					while (obs_pathobj_array.length) {
	        						pathelem = obs_pathobj_array.pop();
	        						pathelem.remove();
	        					}
	        					svg.append("path")
									.attr("d", linearline_closed(obs_polyline))
									.style("stroke-width", 2)
									.style("stroke", "navy")
									.style("fill", "orange");
								obsnode.remove();	        						
	        				});
	        			line_startpos.x = point[0];
	        			line_startpos.y = point[1];
	        			obs_polyline.push({x:line_startpos.x, y:line_startpos.y});
	        			obs_startnode_flag = false;
	        		} else {
	        			if (line_drawing_mode) {
	        				line_endpos.x = point[0];
	        				line_endpos.y = point[1];
	        				obs_polyline.push({x:line_endpos.x, y:line_endpos.y});
	        				// draw temporary line segments
	        				var lineseg = svg.append("path")
												.attr("d", linearline([line_startpos, line_endpos]))
												.style("stroke-width", 2)
												.style("stroke", "steelblue")
												.style("fill", "none");
							obs_pathobj_array.push(lineseg);
							line_startpos.x = line_endpos.x;
							line_startpos.y = line_endpos.y;
						}
	        		}
	      		});
				break;
			case 'comp':
				computePath(sgnodes, obs_polyline);
				break;
			}
 		};  /* setDrawMode */
 		ready(function() {
 			parser.parse();
			on(registry.byId("drawingMode"), "change", setDrawMode);
			//on(dom.byId("National"), "click", myClick);
 		});
    }
);        		
