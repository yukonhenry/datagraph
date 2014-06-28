datagraph
=========

Data Graph experiments - this repository includes the league scheduler software, along with some experimentation code for d3js and nltk.

Code Structure:
bottle_baseball directory includes py code that implements the schduling algorithm.  Entry pt is schedstart.py.  leaguedivprocess.py implements that bottle framework that routes incoming requests from the UI.  xxdbinterface.py implements various db interface requests.  schedmaster.py implements entry point for schedule generation.  matchgenerator.py implements time/place independent match generation, with xxfieldtimescheduler.py implementing time/venue assignments.

leaguescheduler directory includes js code for UI.  scheduler.js is the main js module loaded from index.hmtl.  UI code follows two separate paths (for wizard, and 'advanced' UI - for content pane creation, but merge together once the per-pane UI components are generated.  Dojo framework provides the infrastructure, with heavy use of dgrid, dodjox calendar, and local dojo store

------------

Dev Installation:
1)Dbootstrap install: ref https://github.com/thesociable/dbootstrap (install from workspace project dir)

2)Node.js installation: http://stackoverflow.com/questions/7214474/how-to-keep-up-with-the-latest-versions-of-nodejs-in-ubuntu-ppa-compiling

3)CPM install: ref https://github.com/kriszyp/cpm  (precede sh with sudo) curl https://raw.github.com/kriszyp/cpm/master/install | sudo sh

4)Java installation - https://help.ubuntu.com/community/Java  (get openjdk-7 from software center)

5)Put selector: https://github.com/kriszyp/put-selector (install from workspace project dir)

6)Install node_modules/stylus with global option (sudo npm install stylus -g)

7)git clone --recursive git://github.com/thesociable/dbootstrap.git (from workspace dir)

