require(["dojo/dom", "dojo/on", "dojo/request/script",
        "dojo/json", "dojo/domReady!"],
    function(dom, on, script, JSON) {
        var shortDiv = dom.byId("shortestPathDiv");
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
        });
    }
);        		
