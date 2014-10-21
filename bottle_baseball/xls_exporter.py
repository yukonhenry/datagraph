from tablib import Dataset, Databook
from datetime import datetime
from dateutil import parser
from schedule_util import mkdir_p
from singletonlite import hostserver
import os

LOCALDIR_PATH = '/home/henry/workspace/datagraph/bottle_baseball/download/xls'
SERVERDIR_PATH = '/home/tominaga/webapps/htdocs/xls'
_reftrust_level = [{'div_id':1, 'cr':1, 'ar':1, 'ment':3},
    {'div_id':2, 'cr':1, 'ar':1, 'ment':3},
    {'div_id':3, 'cr':1, 'ar':1, 'ment':3},
    {'div_id':4, 'cr':1, 'ar':1, 'ment':3},
    {'div_id':5, 'cr':2, 'ar':2, 'ment':3},
    {'div_id':6, 'cr':2, 'ar':2, 'ment':3},
    {'div_id':7, 'cr':3, 'ar':2, 'ment':4},
    {'div_id':8, 'cr':3, 'ar':2, 'ment':4}]
_rindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(_reftrust_level)).get(x)
class XLS_Exporter:
    ''' this class and it's methods will eventually supersede sched_exporter
    class and methods '''
    def __init__(self, schedcol_name, divinfo_tuple, fieldinfo_tuple, sdbInterface):
        self.schedcol_name = schedcol_name
        self.divinfo_list = divinfo_tuple.dict_list
        self.dindexerGet = divinfo_tuple.indexerGet
        self.fieldinfo_list = fieldinfo_tuple.dict_list
        self.findexerGet = fieldinfo_tuple.indexerGet
        self.sdbinterface = sdbInterface
        if hostserver == "local":
            self.dir_path = LOCALDIR_PATH
        else:
            self.dir_path = SERVERDIR_PATH
        mkdir_p(self.dir_path)

    def export(self, genxls_id, db_type):
        div_id_property = 'div_id' if db_type == 'rrdb' else 'tourndiv_id'
        if genxls_id == 'div_id':
            file_list = self.generate_divxls(div_id_property)
        elif genxls_id == 'field_id':
            file_list = self.generate_fieldxls()
        elif genxls_id == 'team_id':
            file_list = self.generate_divteamxls(div_id_property)
        elif genxls_id == 'referee_id':
            file_list = self.generate_refereexls()
        return file_list

    def generate_divxls(self, genxls_id):
        headers = ['Game Date', 'Day', 'Time', 'Division', 'Home',
            'Visitor', 'Venue']
        datasheet_list = list()
        for divinfo in self.divinfo_list:
            div_id = divinfo[genxls_id]
            div_age = divinfo['div_age']
            div_gen = divinfo['div_gen']
            div_str = div_age + div_gen
            datasheet = Dataset(title=div_str)
            datasheet.headers = list(headers)
            match_list = self.sdbinterface.get_schedule(genxls_id, div_age=div_age,
                div_gen=div_gen)
            # note conversions for time from 24-hour to am/pm format
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
        bookname_xls_fullpath = os.path.join(self.dir_path, bookname_xls_relpath)
        with open(bookname_xls_fullpath,'wb') as f:
            f.write(book.xls)
        f.close()
        return [{'path':bookname_xls_relpath}]

    def generate_fieldxls(self):
        headers = ['Game Date', 'Day', 'Time', 'Division', 'Home',
        'Visitor', 'Venue']
        datasheet_list = list()
        for fieldinfo in self.fieldinfo_list:
            field_name = fieldinfo['field_name']
            field_id = fieldinfo['field_id']
            datasheet = Dataset(title=field_name)
            datasheet.headers = list(headers)
            match_list = self.sdbinterface.get_schedule('field_id',
                field_id=field_id)
            tabformat_list = [(x['game_date'],
                parser.parse(x['game_date']).strftime("%a"),
                datetime.strptime(x['start_time'], "%H:%M").strftime("%I:%M%p"),
                x['div_age']+x['div_gen'], x['home'], x['away'], field_name)
                for x in match_list]
            for tabformat in tabformat_list:
                datasheet.append(tabformat)
            datasheet_list.append(datasheet)
        book = Databook(datasheet_list)
        bookname_xls_relpath = self.schedcol_name + "_byField.xls"
        bookname_xls_fullpath = os.path.join(self.dir_path, bookname_xls_relpath)
        with open(bookname_xls_fullpath,'wb') as f:
            f.write(book.xls)
        f.close()
        return [{'path':bookname_xls_relpath}]

    def generate_divteamxls(self, div_id_property):
        headers = ['Game Date', 'Day', 'Time', 'Division', 'Home',
        'Visitor', 'Venue']
        file_list = list()
        for divinfo in self.divinfo_list:
            div_id = divinfo[div_id_property]
            div_age = divinfo['div_age']
            div_gen = divinfo['div_gen']
            div_str = div_age + div_gen
            totalteams = divinfo['totalteams']
            datasheet_list = list()
            if div_id == 2:
                teamrange = range(1,18)+range(19,23)
            else:
                teamrange = range(1,totalteams+1)
            for team_id in teamrange:
                team_str = div_str + str(team_id)
                datasheet = Dataset(title=team_str)
                datasheet.headers = list(headers)
                match_list = self.sdbinterface.get_schedule('team_id',
                    div_age=div_age, div_gen=div_gen, team_id=team_id)
                tabformat_list = [(x['game_date'],
                    parser.parse(x['game_date']).strftime("%a"),
                    datetime.strptime(x['start_time'], "%H:%M").strftime("%I:%M%p"),
                    div_str, x['home'], x['away'],
                    self.fieldinfo_list[self.findexerGet(x['venue'])]['field_name'])
                    for x in match_list]
                for tabformat in tabformat_list:
                    datasheet.append(tabformat)
                datasheet_list.append(datasheet)
            book = Databook(datasheet_list)
            bookname_xls_relpath = self.schedcol_name + div_str+"_byTeam.xls"
            bookname_xls_fullpath = os.path.join(self.dir_path,
                bookname_xls_relpath)
            with open(bookname_xls_fullpath,'wb') as f:
               f.write(book.xls)
            f.close()
            file_list.append({'path':bookname_xls_relpath, 'mdata':div_str})
        return file_list

    def generate_refereexls(self):
        headers = ['Match#','Date', 'Day', 'Time', 'Division', 'Week#', 'Home', 'Visitor', 'Field', 'cr_trust', 'ar_trust', 'm_trust']
        datasheet = Dataset(title="Referee Scheduler Compatible")
        datasheet.headers = list(headers)
        file_list = list()
        return file_list
