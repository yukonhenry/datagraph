datagraph
=========

Data Graph - this repository includes the league scheduler software, along with unrelated experimentation nlp processing/visualization code utilizing nltk and d3js.

Sports League Scheduling Software:
-------------------------
This production level software implements league scheduler (both round robin and tournament) software for amateur sports leagues.  There are unique characterizations with amateur sports leagues, mainly driven by scarcity of resources and an abundance of constraints and preferences.  Further adding to the complexity is that the consumer of a schedule has many audiences, and given that, the definition of a 'good' or optimal schedule may have competing interests.  For example, field spaces may be limited and hours restricted, but at the same time must be fairly shared.  Participants in the leagues may have many time and distance constraints.  

This software aims to rigorously solve this as a combinatorial optimization problem with defined cost functions and constraints.

- Cost function:  Defined to maximize fairness - field use and time use fairness.
- Constraints: Limits or irregularity with field/time availability
- Preferences: Best effort attempt to meet prioritized time preferences.

### Demo code continously available on http://www.yukontr.com/apps/LeagueScheduler/

### Implementation:
Algorithm implmentation in Python on a hosted (cloud) backend server, with storage of schedule and configuration information on a key:value db (mongodb).  Web-based UI implemented in js, utilizing dojo framework.  dojo components such as dgrid and dojox calendar are utiized.  UI<->backend data exchange through http rest-like interface.

####Code Structure:
* bottle_baseball directory includes py code that implements the schduling algorithm.  Entry pt is schedstart.py.  leaguedivprocess.py implements that bottle framework that routes incoming requests from the UI.  xxdbinterface.py implements various db interface requests.  schedmaster.py implements entry point for schedule generation.  matchgenerator.py implements time/place independent match generation, with xxfieldtimescheduler.py implementing time/venue assignments.
* leaguescheduler directory includes js code for UI.  scheduler.js is the main js module loaded from index.hmtl.  UI code follows two separate paths (for wizard, and 'advanced' UI - for content pane creation, but merge together once the per-pane UI components are generated.  Dojo framework provides the infrastructure, with heavy use of dgrid, dodjox calendar, and local dojo store


###Dev Installation Notes:
1. Dbootstrap install: ref https://github.com/thesociable/dbootstrap (install from workspace project dir)

2. Node.js installation: http://stackoverflow.com/questions/7214474/how-to-keep-up-with-the-latest-versions-of-nodejs-in-ubuntu-ppa-compiling

3. CPM install: ref https://github.com/kriszyp/cpm  (precede sh with sudo) curl https://raw.github.com/kriszyp/cpm/master/install | sudo sh

4. Java installation - https://help.ubuntu.com/community/Java  (get openjdk-7 from software center)

5. Put selector: https://github.com/kriszyp/put-selector (install from workspace project dir)

6. Install node_modules/stylus with global option (sudo npm install stylus -g)

7. git clone --recursive git://github.com/thesociable/dbootstrap.git (from workspace dir)

##Any questions or comments should be directed to henry@yukontr.com

