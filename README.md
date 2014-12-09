Sports League Scheduling Application:
-------------------------
This production level software implements round-robin league and tournament scheduler software for amateur sports leagues.  There are distinct characterizations with operating amateur sports leagues compared to professional or upper-tier semi-pro leagues, which is driven by scarcity of resources and an abundance of constraints, preferences, and conflicts.  In addition, there is a much larger need to maximize fairness and convenience for the former, in place of maximizing profit, competitiveness, and entertainment value for the latter.  The operational task for match scheduling for amateur leagues has complexities that, compared to their professional counterparts, are accentuated by a)large number of teams/players in a league competing for limited access to resources, and especially what are considered quality resources (i.e. desirable fields, desirable time of day to play, qualified coaches, etc.); b) evaluators and benefactors of the quality of generated schedule is much larger and diverse - i.e. administrators, coaches, players, and families all have a large influence into providing requirements for the quality of a schedule.  These factors contribute to the demand that generated schedules maximize fairness and convenience while satisfying and avoiding a large number of constraints and conflicts.

### Algorithm

This software creates the schedule by first generating round robin matches and then making venue and time slot allocations.  The latter is accomplished by formulating the scheduling problem as a discrete optimization problem with defined cost functions.  Cost function components represent:
* Attaining fairness for venue distribution and undesirable time slot distribution
* Meeting target venue distribution when affinity/home fields are specified
* home/away balancing

In addition, scheduling time preferences and constraints represented as soft constraints, weighted by configured priorities. Priority values also determined how aggressive the algorithm should work to meet constraints at the expense of sacrificing fairness for others.  Constraint violation is represented as penalty costs incorporated into the overall cost function.

### Implementation:
Algorithm implmentation in Python on a hosted (cloud) backend server, with storage of schedule and configuration information on a key:value db (mongodb).  Web-based UI implemented in js, utilizing dojo framework.  dojo components such as dgrid and dojox calendar are heavily utiized.  UI<->backend data exchange through http rest interface, with python bottle used as the server-side controller routing.

#### Code Structure:
* bottle_baseball directory includes py code that implements the schduling algorithm.  Entry pt is schedstart.py.  leaguedivprocess.py implements that bottle framework that routes incoming requests from the UI.  xxdbinterface.py implements various db interface requests.  schedmaster.py implements entry point for schedule generation.  matchgenerator.py implements time/place independent match generation, with xxfieldtimescheduler.py implementing time/venue assignments.
* leaguescheduler directory includes js code for UI.  scheduler.js is the main js module loaded from index.hmtl.  UI code follows two separate paths (for wizard, and 'advanced' UI - for content pane creation, but merge together once the per-pane UI components are generated.  Dojo framework provides the infrastructure, with heavy use of dgrid, dodjox calendar, and local dojo store

#### Running code with UI at http://www.yukontr.com/apps/LeagueScheduler/

### Other code in datagraph respository
Note this repository also includes experimental nlp+visualization code utilizing nltk and d3js
####Any questions or comments should be directed to henry@yukontr.com

