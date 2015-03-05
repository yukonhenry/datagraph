import pytest
from util.singletonlite import mongoClient
from algorithm.schedmaster import SchedMaster
from db.userdbinterface import UserDBInterface

@pytest.fixture
def dbinterface():
	from db.userdbinterface import UserDBInterface
	return UserDBInterface(mongoClient)

def test_tournuser(dbinterface):
	userid = "demo"
	result = dbinterface.check_user("demo")
	if result == 0:
		status = dbinterface.writeDB("demo")
	else:
		status = True
	assert status