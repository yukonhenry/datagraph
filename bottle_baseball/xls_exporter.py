from tablib import Dataset, Databook
from datetime import datetime
from dateutil import parser
import os

class XLS_Exporter:
    def __init__(self, schedcol_name, divinfo_tuple, fieldinfo_tuple, sdbInterface):
        self.schedcol_name = schedcol_name
        self.divinfo_list = divinfo_tuple.dict_list
        self.dindexerGet = divinfo_tuple.indexerGet
        self.fieldinfo_list = fieldinfo_tuple.dict_list
        self.findexerGet = fieldinfo_tuple.indexerGet
        self.sdbinterface = sdbInterface

    def export(self, genxls_id):
        if genxls_id == 'div_id':
            self.generate_divxls()
        elif genxls_id == 'field_id':
            self.generate_fieldxls()
        elif genxls_id == 'team_id':
            self.generate_teamxls()

    def generate_divxls(self):
        headers = ['Match ID', 'Game Date', 'Day', 'Time', 'Division', 'Home',
            'Away', 'Field']
        div_id_list = [x['div_id'] for x in self.divinfo_list]
        datasheet_list = list()
        for div_id in div_id_list:
            divinfo = self.divinfo_list[self.dindexerGet(div_id)]
            totalteams = divinfo['totalteams']

    def generate_fieldxls(self):
        pass

    def generate_teamxls(self):
        pass

