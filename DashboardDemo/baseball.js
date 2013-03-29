 		//references for handling radio button
		//javascript: http://homepage.ntlworld.com/kayseycarvey/jss3p11.html
		//dojo:
		//http://dojotoolkit.org/reference-guide/1.8/dijit/form/RadioButton.html#dijit-form-radiobutton
		//http://dojotoolkit.org/documentation/tutorials/1.8/checkboxes/
 		function findRadioButton(dom) {
			var len = dom.byId("radio_select").radio_sel.length;
			var radio_val;
			for (var i=0; i < len; i++) {
				with (dom.byId("radio_select")) {
					if (radio_sel[i].checked)
						radio_val = radio_sel[i].value;
				}
			}
			return radio_val;			
 		}
        require(["dojo/dom", "dojo/on", "dojo/request","dojo/parser", "dijit/registry","dojo/ready",
        			"dojo/keys", "dojo/request/script","dojo/json","dojox/gfx", "dojo/domReady!",
        			"dijit/form/Select","dijit/form/SimpleTextarea", "dijit/form/TextBox",
        			"dijit/form/RadioButton", "dijit/form/Button", "dijit/layout/TabContainer","dijit/layout/ContentPane"],
   		function(dom, on, request, parser, registry, ready, keys, script, JSON, gfx) {
   			// keep order of parameters the same as order of modules declared in require function
			// reference below on difference dom.byId and registry.byId 
			// http://dojotoolkit.org/reference-guide/1.8/dijit/registry.html#dijit-registry
			surface = gfx.createSurface("surfaceElement", 600, 600);

			var sendTeam = function(evt) {
				// review js scope rules as resultDiv and textDiv variables need to be declared
				// under function declaration and not above
				var resultDiv = dom.byId("resultDiv");
	        	var textDiv = dom.byId("textarea1");
				var teamcode = registry.byId("teamSelect").get("value");
				var radio_val = findRadioButton(dom);
				//alert("scopehandler = "+this.id + teamcode);
	        	script.get("http://127.0.0.1:8080/hello", {
	        		jsonp:"callback", query: {team_code:teamcode, ret_type:radio_val}
	        	}).then(function(data) {
                   	console.log('text file response is here'+JSON.stringify(data));
                   	//resultDiv.innerHTML = "<pre>"+data.team+" "+data.team_tweets+"</pre>";
                   	if (radio_val == 'team_relation') {
                   		textDiv.value = JSON.stringify(data.team_search);
 
var diameter = 960;

var tree = d3.layout.tree()
    .size([360, diameter / 2 - 120])
    .separation(function(a, b) { return (a.parent == b.parent ? 1 : 2) / a.depth; });
/*
var tree = d3.layout.tree()
    .sort(null)
    .size([100, 80])
    .children(function(d)
    {
        return (!d.children || d.children.length === 0) ? null : d.children;
    });
*/
var diagonal = d3.svg.diagonal.radial()
    .projection(function(d) { return [d.y, d.x / 180 * Math.PI]; });

var svg = d3.select("body").append("svg")
    .attr("width", diameter)
    .attr("height", diameter - 150)
  .append("g")
    .attr("transform", "translate(" + diameter / 2 + "," + diameter / 2 + ")");
testnodes = {name:"parent", contents:[{name:"child1", contents:[]},{name:"child2",contents:[]}]};
  var nodes = tree.nodes(data.team_search);
  var links = tree.links(nodes);
console.log("nodes "+nodes);
console.log("links "+links.length+links);
  var link = svg.selectAll(".link")
      .data(links)
    .enter().append("path")
      .attr("class", "link")
      .attr("d", diagonal);

  var node = svg.selectAll(".node")
      .data(nodes)
    .enter().append("g")
      .attr("class", "node")
      .attr("transform", function(d) { return "rotate(" + (d.x - 90) + ")translate(" + d.y + ")"; })

  node.append("circle")
      .attr("r", 4.5);

  node.append("text")
      .attr("dy", ".31em")
      .attr("text-anchor", function(d) { return d.x < 180 ? "start" : "end"; })
      .attr("transform", function(d) { return d.x < 180 ? "translate(8)" : "rotate(180)translate(-8)"; })
      .text(function(d) { return d.id; });
  d3.select(self.frameElement).style("height", diameter - 150 + "px");
                   	} else {
	                   	textDiv.value = data.team_search;
                   	}
				}, function(error){
                   	// Display the error returned
                    console.log('error response is here');
                    resultDiv.innerHTML = "<div class=\"error\">"+error+"<div>";
                });
			};
			var sendSearchTerm = function(evt) {
				var resultDiv = dom.byId("resultDiv");
	        	var textDiv = dom.byId("textarea1");
	        	if (evt.keyCode == keys.ENTER) {
					var term = registry.byId("searchterm").get("value");
					var radio_val = findRadioButton(dom);
					console.log("search term here "+term+" radio="+radio_val);
	        		script.get("http://127.0.0.1:8080/hello", {
	        			jsonp:"callback", query: {general:term, ret_type:radio_val}
	        		}).then(function(data) {
                   		//console.log('text file response is here'+JSON.stringify(data));
	                   	textDiv.value = data.tweet_list;
					}, function(error){
                   		// Display the error returned
                    	console.log('error response is here');
                    	resultDiv.innerHTML = "<div class=\"error\">"+error+"<div>";
                	});
				}
			};
			var getDesign = function(evt) {
				//d3.json("http://127.0.0.1:8080/getdesign1", draw);
	        	script.get("http://127.0.0.1:8080/getdesign", {
	        		jsonp:"callback"
	        	}).then(function(data) {
	        		draw(data);
	        		var stencil_array = data.stencil_id;
	        		var len = stencil_array.length;
	        		if (len > 0) {
	        			// clear surface as design may have changed
	        			surface.clear();		
						//surface = gfx.createSurface("surfaceElement", 600, 600);
						var base_x = 50, base_y=50;    			
	        			for (var i = 0; i < len; i++) {
	        				var id = stencil_array[i];
	        				console.log("basex, y="+base_x+" "+base_y+" id="+id);
	        				switch (id) {
	        				case 1:
								surface.createRect({ x: base_x, y: base_y, width: 30, height: 30 })
									.setFill("yellow").setStroke("blue");
								base_x += 50;
	        					base_y += 50;
	        					break;
	        				case 2:
	        					surface.createRect({ x: base_x, y: base_y, width: 30, height: 30, r:3 })
									.setFill("yellow").setStroke("blue");
								base_x += 50;
	        					base_y += 50;
	        					break;
	        				case 3:
								surface.createRect({ x: base_x, y: base_y, width: 30, height: 30, r:10 })
									.setFill("yellow").setStroke("blue");
								base_x += 50;
	        					base_y += 50;
	        					break;	        				
	        				case 4:
	        					surface.createCircle({ cx: base_x, cy: base_y, r:12 })
    								.setFill("green").setStroke("pink");
    							base_x += 50;
    							base_y += 50;
    							break;
    						default:
    							alert("unrecognized stencil id =" + id);
    							break;
	        				}
	        			}
	        		}
					//alert("stencil ="+stencil_array.toString());
				}, function(error){
                   	// Display the error returned
                    console.log('error response is ' + error);
                });
  			};              
			var getMLBStoveInfo = function(evt) {
				//d3.json("http://127.0.0.1:8080/getdesign1", draw);
	        	script.get("http://127.0.0.1:8080/getmlbstoveinfo", {
	        		jsonp:"callback"
	        	}).then(function(data) {
	        		console.log("graph json len="+data.creation_time);
	        		resultDiv.innerHTML = "<p><b>Data Creation time is "+data.creation_time+"</b></p>";
	        		var nodes = data.mlbgraph.nodes;
	        		var links = data.mlbgraph.links;
	        		var links2 = links.slice();  //make a copy
	        		var links2len = links2.length;
	        		// ref http://www.elated.com/articles/manipulating-javascript-arrays/
	        		d3.select("body").selectAll("p")
						.data(nodes).enter()
						.append("p")
						.text(function(d, i) {
							var linkstr = '';
							// loop through list of graph edges (links)
							// method assumes that graph edge description is ordered by 
							// originating node number.  See python library call json_graph.node_link_data(G)
							while (links2len > 0 && links2[0].source == i) {
								linkstr += links2.shift().target + ' ';
								links2len--;
							}
							return d.id+" ind="+i + ' '+linkstr;});
					var width = 1200, height = 1000;

					var color = d3.scale.category20();

					var force = d3.layout.force()
								.charge(-3000)
    							.linkDistance(50)
    							.gravity(1)
    							.size([width, height]);

					var svg = d3.select("body").append("svg")
    							.attr("width", width)
    							.attr("height", height);
					// ref http://bl.ocks.org/MoritzStefaner/1377729 for labeled nodes
					// but modify because we already have a graph to work off of
					// (No need to generate a random one as described in the reference)
					var labelDistance = 0;
					var labelAnchors = [];
 					for (var i = 0; i < nodes.length; i++) {
						labelAnchors.push({node:nodes[i]});
						labelAnchors.push({node:nodes[i]});
					};
					var labelAnchorLinks = [];  
					for (var i = 0; i < nodes.length; i++) {
						labelAnchorLinks.push({
							source : i * 2,
							target : i * 2 + 1,
							weight : 1
						});
					};


					// Add the data
					force.nodes(nodes)
					.links(links)
					.linkStrength(function(x) {
						return x.weight*0.5;  // experiment w. weighting scaling factor - 0.5 seems to work
						// for link weights < 10.
					}).start();	
 
 					var force2 = d3.layout.force().nodes(labelAnchors).links(labelAnchorLinks)
 									.gravity(0).linkDistance(0).linkStrength(8)
 									.charge(-100).size([width, height]);
					force2.start();
					// Draw the links

					var link = svg.selectAll(".link").data(links)
	    						.enter().append("line")
      							.attr("class", "link")
      							.style("stroke", "#CCC")
      							.style("stroke-width", function(d) { return Math.sqrt(d.weight); });

					// Draw the nodes
					// ref http://stackoverflow.com/questions/11102795/d3-node-labeling
					var node = svg.selectAll(".node").data(nodes)
    							.enter().append("g")
      							.attr("class", "node");
 
				 	node.append("circle")
					 	.attr("r", 5)
      					.style("fill", function(d) { return color(d.group); })
      					.style("stroke-width", 3);
      				node.call(force.drag);
      				/*
					node.append("text")
						.attr("dx", 12)
						.attr("dy", ".35em")
						.text(function(d) { return d.id });
					*/
					var anchorLink = svg.selectAll(".anchorLink")
										.data(labelAnchorLinks)//.enter().append("svg:line").attr("class", "anchorLink").style("stroke", "#999");

					var anchorNode = svg.selectAll(".anchorNode")
										.data(force2.nodes()).enter()
										.append("g")
										.attr("class", "anchorNode");
					anchorNode.append("circle").attr("r", 0).style("fill", "#FFF");
					anchorNode.append("text")
								.text(function(d, i) {
									return i % 2 == 0 ? "" : d.node.id
								})
								.style("fill", "#555").style("font-family", "Arial").style("font-size", 12);

					var updateLink = function() {
						this.attr("x1", function(d) {
							return d.source.x;
						}).attr("y1", function(d) {
							return d.source.y;
						}).attr("x2", function(d) {
							return d.target.x;
						}).attr("y2", function(d) {
							return d.target.y;
						});
					}

					var updateNode = function() {
						this.attr("transform", function(d) {
							return "translate(" + d.x + "," + d.y + ")";
						});

					}
					force.on("tick", function() {
						force2.start();
						node.call(updateNode);
						anchorNode.each(function(d, i) {
							if (i % 2 == 0) {
								d.x = d.node.x;
								d.y = d.node.y;
							} else {
								var b = this.childNodes[1].getBBox();
								var diffX = d.x - d.node.x;
								var diffY = d.y - d.node.y;
								var dist = Math.sqrt(diffX * diffX + diffY * diffY);
								var shiftX = b.width * (diffX - dist) / (dist * 2);
								shiftX = Math.max(-b.width, Math.min(0, shiftX));
								var shiftY = 5;
								this.childNodes[1]
									.setAttribute("transform", "translate(" + shiftX + "," + shiftY + ")");
							}
						});
						anchorNode.call(updateNode);
						link.call(updateLink);
						anchorLink.call(updateLink);
					});
	//node.append("title")
    //  .text(function(d) { console.log("node ="宮市 剛+d.id);return d.id; });
/*
  force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });
node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
    //node.attr("cx", function(d) { return d.x; })
        //.attr("cy", function(d) { return d.y; });
  });
*/										
				}, function(error){
                   	// Display the error returned
                    console.log('error response is ' + error);
                });
			};
        	// Results will be displayed in resultDiv
        	//http://stackoverflow.com/questions/1850050/how-to-get-the-value-of-a-filteringselect-select-in-dojo
        	//dijit.byId is deprecated
 			ready(function() {
 				console.log("in ready function"); 
 				parser.parse();
				on(registry.byId("teamSelect"), "change", sendTeam);
				on(registry.byId("searchterm"), "keydown", sendSearchTerm);
				on(registry.byId("startbtn"), "click", getDesign);
				on(registry.byId("mlbstove_btn"), "click", getMLBStoveInfo);
				//on(dom.byId("National"), "click", myClick);
 			}); 
    	});