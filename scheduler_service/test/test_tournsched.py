import pytest
from util.singletonlite import mongoClient, generic_dbInterface
from algorithm.tournschedmaster import TournSchedMaster
from db.userdbinterface import UserDBInterface
from db.dbinterface import DB_Col_Type
from router.router_process import select_db_interface
import simplejson as json
from pprint import pprint
from collections import namedtuple

''' run with $py.test from /scheduler_service; run $py.test -s to see print outputs
'''

TESTUSER = "testuser"
TESTCOL = "TESTCOL"
TESTDIV_list = [{"tourndiv_id":1,"div_age":"U8","div_gen":"B","totalteams":23,
    "totalgamedays":2,
    "gameinterval":30,"mingap_time":90,"elimination_type":"S","thirdplace_enable":"Y"},
    {"tourndiv_id":2,"div_age":"U8","div_gen":"G","totalteams":14,
    "totalgamedays":2,
    "gameinterval":30,"mingap_time":90,"elimination_type":"D","thirdplace_enable":"Y"}]
tdindexerGet = lambda x: dict((p['tourndiv_id'],i) for i,p in enumerate(TESTDIV_list)).get(x)
TESTFIELD_list = [{"pr":"1,2","end_date":"6/12/2015","tfd":28,
    "start_time":"8:00:00 AM",
    "field_id":1,"detaileddates":"","end_time":"5:00:00 PM","field_name":"p1",
    "dr":"0,6","start_date":"3/14/2015"},
    {"pr":"1,2","end_date":"6/12/2015","tfd":28,"start_time":"8:00:00 AM",
    "field_id":2,"detaileddates":"","end_time":"5:00:00 PM","field_name":"p2",
    "dr":"0,6","start_date":"3/14/2015"}]

@pytest.fixture(scope="module")
def userdbinterface():
    from db.userdbinterface import UserDBInterface
    return UserDBInterface(mongoClient)


@pytest.fixture(scope="module")
def datadbinterface():
    dbtuple = namedtuple('dbtuple', 'div field')
    return dbtuple(select_db_interface(TESTUSER, 'tourndb', TESTCOL, "T"),
        select_db_interface(TESTUSER, 'fielddb', TESTCOL, "T"))

''' calculate total number of matches in generated match list
'''
def calculate_actual_numtotalmatches(match_list):
    return sum(len(x['gameday_data']) for x in match_list)

''' calculate expected total number of matches based on totalteams
    (in one playing division), tournament type, and 3rd place match flag.
    Single Elimination: #matches = #teams - 1 (+1 is 3rd place flag enabled)
    Double Elimination: #matches = 2*(#teams - 1) = 2*#teams - 2
    Consolation (modified double elim): #matches = 2(#teams-1)- 1 =
        2*#teams - 3  (can either derived as one less than Double Elim or the aggregate of two single elim brackes, one with N teams, second with N-1
            teams #teams-1+(#teams-1-1) = 2*#teams - 3)
'''
def calculate_expected_numtotalmatches(totalteams, elim_type,
    thirdplace_enable):
    if elim_type == 'S':
        numgames = totalteams - 1 if thirdplace_enable=='N' else totalteams
    elif elim_type == 'D':
        numgames = 2*totalteams - 2
    elif elim_type == 'C':
        numgames = 2*totalteams - 3
    else:
        assert False
    return numgames

# check default userinfo assignment can be read and if n
def test_tournuser(userdbinterface):
    result = userdbinterface.check_user(TESTUSER)
    if result == 0:
        status = userdbinterface.writeDB(TESTUSER)
    else:
        status = True
    assert status

def test_existingcollections():
    collection_list = generic_dbInterface.getScheduleCollection(
        DB_Col_Type.TournRR, TESTUSER, "T")
    if len(collection_list):
        pprint(collection_list)
    else:
        print "No existing collection"
    assert True

# write div config to db and read it back.
def test_tourndivwriteread(datadbinterface):
    divdbinterface = datadbinterface.div
    testdiv_len = len(TESTDIV_list[0])
    testdiv_str = json.dumps(TESTDIV_list)
    divdbinterface.writeDB(testdiv_str, 1)
    read_dict = divdbinterface.readDB().list[0]
    #pprint(read_dict)
    assert len(read_dict)==testdiv_len

# write div config to db and read it back.
def test_tournfieldwriteread(datadbinterface):
    fielddbinterface = datadbinterface.field
    testfield_len = len(TESTFIELD_list[0])
    testfield_str = json.dumps(TESTFIELD_list)
    fielddbinterface.writeDB(testfield_str, 1, divstr_colname=TESTCOL,
        divstr_db_type="tourndb")
    read_dict = fielddbinterface.readDB().list[0]
    #pprint(read_dict)
    # length of db read dict is one longer as fielddaymap field is calculated
    # and stored
    assert len(read_dict)==testfield_len+1

def test_elimtourngenerate():
    schedMaster = TournSchedMaster(mongoClient, TESTUSER, TESTCOL, TESTCOL,
        TESTCOL, "elimination")
    if schedMaster.error_code:
        print "TournSchedMaster error code=", schedMaster.error_code
        assert 0
    else:
        dbstatus = schedMaster.schedGenerate()
        assert dbstatus
        for tourndiv_id in (1,2):
            divsched_list = schedMaster.get_schedule('tourndiv_id', tourndiv_id)
            pprint(divsched_list)
            actual = calculate_actual_numtotalmatches(divsched_list['game_list'])
            divinfo = TESTDIV_list[tdindexerGet(tourndiv_id)]
            expected = calculate_expected_numtotalmatches(divinfo['totalteams'],
                divinfo['elimination_type'], divinfo['thirdplace_enable'])
            print "actual #games=", actual, "expected games=", expected
            assert actual == expected
