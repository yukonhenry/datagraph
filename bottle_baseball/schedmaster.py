''' Copyright YukonTR 2014 '''
import logging

class SchedMaster:
    def __init__(self, mongoClient, db_type, divcol_name, field_colname):
        if db_type == 'rrdb':
            dbInterface = RRDBInterface(mongoClient, getcol_name)
        elif db_type == 'tourndb':
            dbInterface = TournDBInterface(mongoClient, getcol_name)
        elif db_type == 'fielddb':
            dbInterface = FieldDBInterface(mongoClient, getcol_name)
        else:
            raise CodeLogicError("schemaster:init: db_type not recognized db_type=%s" % (db_type,))
        dbtuple = dbInterface.readDB();
        info_list = dbtuple.list
        config_status = dbtuple.config_status
