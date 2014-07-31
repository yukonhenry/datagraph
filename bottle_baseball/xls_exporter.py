from tablib import Dataset, Databook
from datetime import datetime
from dateutil import parser
from schedule_util import mkdir_p
from singletonlite import hostserver
import os

LOCALDIR_PATH = '/home/henry/workspace/datagraph/bottle_baseball/download/xls'
class XLS_Exporter:
    def __init__(self, schedcol_name, divinfo_tuple, fieldinfo_tuple, sdbInterface):
        self.schedcol_name = schedcol_name
        self.divinfo_list = divinfo_tuple.dict_list
        self.dindexerGet = divinfo_tuple.indexerGet
        self.fieldinfo_list = fieldinfo_tuple.dict_list
        self.findexerGet = fieldinfo_tuple.indexerGet
        self.sdbinterface = sdbInterface
        mkdir_p(LOCALDIR_PATH)

    def export(self, genxls_id):
        if genxls_id == 'div_id':
            self.generate_divxls()
        elif genxls_id == 'field_id':
            self.generate_fieldxls()
        elif genxls_id == 'team_id':
            self.generate_teamxls()

    def generate_divxls(self):
        headers = ['Game Date', 'Day', 'Time', 'Division', 'Home',
            'Away', 'Field']
        div_id_list = [x['div_id'] for x in self.divinfo_list]
        datasheet_list = list()
        for div_id in div_id_list:
            divinfo = self.divinfo_list[self.dindexerGet(div_id)]
            div_age = divinfo['div_age']
            div_gen = divinfo['div_gen']
            div_str = div_age + div_gen
            datasheet = Dataset(title=div_str)
            datasheet.headers = list(headers)
            match_list = self.sdbinterface.get_schedule('div_id', div_age=div_age,
                div_gen=div_gen)
            tabformat_list = [(x['game_date'],
                parser.parse(x['game_date']).strftime("%a"),
                datetime.strptime(x['start_time'], "%H:%M").strftime("%I:%M%p"),
                div_str, y['home'], y['away'],
                self.fieldinfo_list[self.findexerGet(y['venue'])]['field_name']) for x in match_list for y in x['gameday_data']]
            for tabformat in tabformat_list:
                datasheet.append(tabformat)
            datasheet_list.append(datasheet)
        book = Databook(datasheet_list)
        bookname_xls_relpath = self.schedcol_name + "_byDiv.xls"
        bookname_xls_fullpath = os.path.join(LOCALDIR_PATH, bookname_xls_relpath)
        with open(bookname_xls_fullpath,'wb') as f:
            f.write(book.xls)
        f.close()

    def generate_fieldxls(self):
        pass

    def generate_teamxls(self):
        pass

