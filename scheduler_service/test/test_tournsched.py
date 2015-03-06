import pytest
from util.singletonlite import mongoClient, generic_dbInterface
from algorithm.tournschedmaster import TournSchedMaster
from db.userdbinterface import UserDBInterface
from db.dbinterface import DB_Col_Type
from router.router_process import get_dbcollection, select_db_interface
import simplejson as json
from pprint import pprint
from collections import namedtuple

''' run with $py.test from /scheduler_service; run $py.test -s to see print outputs
'''

TESTUSER = "testuser"
TESTCOL = "TESTCOL"
TESTDIV = [{"tourndiv_id":1,"div_age":"U8","div_gen":"B","totalteams":8,"totalgamedays":2,
    "gameinterval":80,"mingap_time":120,"elimination_type":"S","thirdplace_enable":"N"}]
TESTFIELD = [{"pr":"1","end_date":"6/5/2015","tfd":28,"start_time":"8:00:00 AM",
    "field_id":1,"detaileddates":"","end_time":"5:00:00 PM","field_name":"p1",
    "dr":"0,6","start_date":"3/7/2015"}]

@pytest.fixture
def userdbinterface():
    from db.userdbinterface import UserDBInterface
    return UserDBInterface(mongoClient)


@pytest.fixture(scope="module")
def datadbinterface():
    dbtuple = namedtuple('dbtuple', 'div field')
    return dbtuple(select_db_interface(TESTUSER, 'tourndb', TESTCOL),
        select_db_interface(TESTUSER, 'fielddb', TESTCOL))


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
        DB_Col_Type.TournRR, TESTUSER)
    if len(collection_list):
        pprint(collection_list)
    else:
        print "No existing collection"
    assert True

# write div config to db and read it back.
def test_tourndivwriteread(datadbinterface):
    divdbinterface = datadbinterface.div
    testdiv_len = len(TESTDIV[0])
    testdiv_str = json.dumps(TESTDIV)
    divdbinterface.writeDB(testdiv_str, 1)
    read_dict = divdbinterface.readDB().list[0]
    #pprint(read_dict)
    assert len(read_dict)==testdiv_len

# write div config to db and read it back.
def test_tournfieldwriteread(datadbinterface):
    fielddbinterface = datadbinterface.field
    testfield_len = len(TESTFIELD[0])
    testfield_str = json.dumps(TESTFIELD)
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
