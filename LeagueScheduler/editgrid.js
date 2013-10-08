define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang", 
	"dojo/dom-class", "dojo/_base/array", "dojo/keys", "dojo/store/Memory",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, keys, Memory, 
		OnDemandGrid, editor, Keyboard, Selection) {
		return declare(null, {
			divinfo_list:null, totaldivs: null, text_node:null,
			server_interface:null, colname:null,
			divInfoStore:null, divInfoGrid:null,
			divInfoGridName:null, error_node:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			makeVisible: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(event) {
				if (event.keyCode == keys.ENTER) {
					if (this.form_reg.validate()) {
						confirm('Input Name is Valid, creating new Schedule DB');
						this.newcol_name = this.dbname_reg.get("value");
						divnum = this.divnum_reg.get("value");
						console.log("newdb="+this.newcol_name+" divnum="+divnum);
						this.createDivInfoGrid(divnum);
						on(this.divInfoGrid, "dgrid-datachange",
							lang.hitch(this, this.editDivInfoGrid));
					} else {
						alert('Input name is Invalid, please correct');
					}
				}	
			},
			recreateDivInfoGrid: function() {
				if (this.divInfoGrid) {
					dom.byId(this.divInfoGridName).innerHTML = "";
					delete this.divInfoGrid;
				}
				this.text_node.innerHTML = "Schedule Name: <b>"+this.colname+"</b>";
				divInfo_list = new Array();
				arrayUtil.forEach(this.divinfo_list, function(item, index) {
					for (var propt in item) {
						console.log("propt item="+propt+" "+item[propt]);
					}
					//divInfo_list.push(item);
				});
				this.divInfoStore = new Memory({data:divInfo_list, idProperty:"div_id"});
				this.divInfoGrid = new (declare([OnDemandGrid, Keyboard, Selection]))({
            		store: this.divInfoStore,
            		columns: {
                		div_id: "Div ID",
                		div_age: editor({label:"Age", field:"div_age", autoSave:true},"text","dblclick"),
                		div_gen: editor({label:"Gender", field:"div_gen", autoSave:true}, "text", "dblclick"),
                		totalteams: editor({label:"Total Teams", field:"totalteams", autoSave:true},
                			"text", "dblclick"),
                		totalbrackets: editor({label:"Total RR Brackets", field:"totalbrackets", autoSave:true},
                			"text", "dblclick"),
                		elimination_num: editor({label:"Elimination #", field:"elimination_num", autoSave:true},
                			"text", "dblclick"),
                		field_id_str: editor({label:"Fields", field:"field_id_str", autoSave:true},
                			"text", "dblclick")
                	}
                }, this.divInfoGridName);
				this.divInfoGrid.startup();
				this.divInfoGrid.on("dgrid-error", function(event) {
					this.error_node.className = "message error";
					this.error_node.innerHTML = event.error.message;
				});
			},
			editDivInfoGrid: function(event) {
				var val = event.value;
        		console.log("gridval="+val+' replace='+event.oldValue+ ' cell row='+event.rowId +
        			'col='+event.cell.column.field);
			},
			sendDivInfoToServer: function(event) {
				if (this.form_reg.validate()) {
					storedata_json = JSON.stringify(this.divInfoStore.query());
					//this.divInfoStore.query().forEach(function(division) {
        			//});
					this.server_interface.getServerData("create_newdbcol/"+this.newcol_name,
						this.server_interface.server_ack, {divinfo_data:storedata_json});					
				}
			}
		});
	})