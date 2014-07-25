from tablib import Dataset, Databook
from leaguedivprep import getLeagueDivInfo, mapGamedayIdToCalendar, getFieldInfo,tournMapGamedayIdToCalendar, tournMapGamedayIdToDate, getTournDivID
from datetime import datetime
from dateutil import parser
import os
venue_CONST = 'VENUE'
gameday_id_CONST = 'GAMEDAY_ID'
start_time_CONST = 'START_TIME'
home_CONST = 'HOME'
away_CONST = 'AWAY'
age_CONST = 'AGE'
gen_CONST = 'GEN'
match_id_CONST = 'MATCH_ID'
gameday_data_CONST = 'GAMEDAY_DATA'
comment_CONST = 'COMMENT'
round_CONST = 'ROUND'
_reftrust_level = [{'div_id':1, 'cr':2, 'ar':2, 'ment':3}, {'div_id':2, 'cr':2, 'ar':2, 'ment':3}, {'div_id':3, 'cr':3, 'ar':2, 'ment':4}, {'div_id':4, 'cr':3, 'ar':2, 'ment':4}, {'div_id':5, 'cr':4, 'ar':3, 'ment':5}, {'div_id':6, 'cr':3, 'ar':3, 'ment':5}]
_rindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(_reftrust_level)).get(x)
_offset = 32000

class ScheduleExporter:
    def __init__(self, dbinterface, divinfo_tuple=None,fieldtuple=None):
        self.dbinterface = dbinterface
        if divinfo_tuple is None:
            divinfo_tuple = getLeagueDivInfo()
        self.leaguedivinfo = divinfo_tuple.dict_list
        self.lindexerGet = divinfo_tuple.indexerGet
        if fieldtuple is None:
            fieldtuple = getFieldInfo()
        self.fieldinfo = fieldtuple.dict_list
        self.findexerGet = fieldtuple.indexerGet

    def exportDivTeamSchedules(self, div_id, age, gen, numteams, prefix=""):
        headers = ['Gameday#', 'Game Date', 'Day', 'Start Time', 'Venue', 'Home Team', 'Away Team']
        datasheet_list = []
        for team_id in range(1, numteams+1):
            team_str = age+gen+str(team_id)
            datasheet = Dataset(title=team_str)
            datasheet.headers = list(headers)
            teamdata_list = self.dbinterface.findTeamSchedule(age, gen, team_id)
            tabformat_list = [(x[gameday_id_CONST], tournMapGamedayIdToCalendar(x[gameday_id_CONST]), tournMapGamedayIdToDate(x[gameday_id_CONST]),
                               datetime.strptime(x[start_time_CONST],"%H:%M").strftime("%I:%M %p"),
                               self.fieldinfo[self.findexerGet(x[venue_CONST])]['name'],
                               x[home_CONST], x[away_CONST]) for x in teamdata_list]
            for tabformat in tabformat_list:
                datasheet.append(tabformat)
            datasheet_list.append(datasheet)
        book = Databook(datasheet_list)
        cdir = os.path.dirname(__file__)
        bookname_xls = prefix+age + gen +'_schedule.xls'
        bookname_html = prefix+age + gen +'_schedule.html'
        booknamefull_xls = os.path.join('/home/henry/workspace/datagraph/bottle_baseball/download/xls', bookname_xls)
        booknamefull_html = os.path.join('~/workspace/datagraph/bottle_baseball/download/html', bookname_html)
        with open(booknamefull_xls,'wb') as f:
            f.write(book.xls)
        f.close()
        '''
        with open(bookname_html,'wb') as f:
            f.write(book.html)
        f.close()
        '''
    def exportDivSchedules(self, startgameday, prefix=""):
        headers = ['Match ID', 'Gameday#', 'Game Date', 'Day', 'Time', 'Division', 'Home', 'Away', 'Field', '', 'Comment']
        datasheet_list = []
        for division in self.leaguedivinfo:
            div_id = division['div_id']
            div_age = division['div_age']
            div_gen = division['div_gen']
            div_str =  div_age + div_gen
            datasheet = Dataset(title=div_str)
            datasheet.headers = list(headers)
            divdata_list = self.dbinterface.findElimTournDivisionSchedule(div_age, div_gen, min_game_id=startgameday)
            tabformat_list = [(y[match_id_CONST], x[gameday_id_CONST], tournMapGamedayIdToCalendar(x[gameday_id_CONST]), tournMapGamedayIdToDate(x[gameday_id_CONST]), datetime.strptime(x[start_time_CONST],"%H:%M").strftime("%I:%M %p"), div_str, y[home_CONST], y[away_CONST], self.fieldinfo[self.findexerGet(y[venue_CONST])]['name'], '', y[comment_CONST]) for x in divdata_list for y in x[gameday_data_CONST]]
            for tabformat in tabformat_list:
                datasheet.append(tabformat)
            datasheet.append_separator("Prefix Legend: 'S'-Seeded Team#, 'W'-Winning Team (See Match ID), 'L'-Losing Team)")
            datasheet_list.append(datasheet)
        book = Databook(datasheet_list)
        cdir = os.path.dirname(__file__)
        bookname_xls = prefix+'.xls'
        bookname_html = prefix+'.html'
        booknamefull_xls = os.path.join('/home/henry/workspace/datagraph/bottle_baseball/download/xls', bookname_xls)
        booknamefull_html = os.path.join('~/workspace/datagraph/bottle_baseball/download/html', bookname_html)
        with open(booknamefull_xls,'wb') as f:
            f.write(book.xls)
        f.close()

    def exportFieldSchedule(self, startgameday, prefix=""):
        headers = ['Game#', 'Date', 'Day', 'Time', 'Division', 'Round', 'Home', 'Visitor']
        datasheet_list = []
        for field in self.fieldinfo:
            field_name = field['name']
            field_id = field['field_id']
            datasheet = Dataset(title=field_name)
            datasheet.headers = list(headers)
            fielddata_list = self.dbinterface.findFieldSchedule(field_id, min_game_id=startgameday, tourntype='E')
            tabformat_list = [(x[match_id_CONST], tournMapGamedayIdToCalendar(x[gameday_id_CONST]), tournMapGamedayIdToDate(x[gameday_id_CONST]), datetime.strptime(x[start_time_CONST],"%H:%M").strftime("%I:%M %p"), x[age_CONST]+x[gen_CONST], x[round_CONST], x[home_CONST], x[away_CONST]) for x in fielddata_list]
            for tabformat in tabformat_list:
                datasheet.append(tabformat)
            #datasheet.append_separator("Prefix Legend: 'S'-Seeded Team#, 'W'-Winning Team (See Match ID), 'L'-Losing Team)")
            datasheet_list.append(datasheet)
        book = Databook(datasheet_list)
        cdir = os.path.dirname(__file__)
        bookname_xls = prefix+'_byField.xls'
        bookname_html = prefix+'byField.html'
        booknamefull_xls = os.path.join('/home/henry/workspace/datagraph/bottle_baseball/download/xls', bookname_xls)
        booknamefull_html = os.path.join('~/workspace/datagraph/bottle_baseball/download/html', bookname_html)
        with open(booknamefull_xls,'wb') as f:
            f.write(book.xls)
        f.close()

    def exportFieldScheduleOld(self, prefix=""):
        headers = ['Game#', 'Date', 'Day', 'Time', 'Division', 'Home', 'Visitor']
        datasheet_list = []
        for field in self.fieldinfo:
            field_name = field['name']
            field_id = field['field_id']
            datasheet = Dataset(title=field_name)
            datasheet.headers = list(headers)
            fielddata_list = self.dbinterface.findFieldSchedule(field_id)
            tabformat_list = [(x[gameday_id_CONST], tournMapGamedayIdToCalendar(x[gameday_id_CONST]), tournMapGamedayIdToDate(x[gameday_id_CONST]), datetime.strptime(x[start_time_CONST],"%H:%M").strftime("%I:%M %p"), x[age_CONST]+x[gen_CONST], x[home_CONST], x[away_CONST]) for x in fielddata_list]
            for tabformat in tabformat_list:
                datasheet.append(tabformat)
            #datasheet.append_separator("Prefix Legend: 'S'-Seeded Team#, 'W'-Winning Team (See Match ID), 'L'-Losing Team)")
            datasheet_list.append(datasheet)
        book = Databook(datasheet_list)
        cdir = os.path.dirname(__file__)
        bookname_xls = prefix+'_byField.xls'
        bookname_html = prefix+'byField.html'
        booknamefull_xls = os.path.join('/home/henry/workspace/datagraph/bottle_baseball/download/xls', bookname_xls)
        booknamefull_html = os.path.join('~/workspace/datagraph/bottle_baseball/download/html', bookname_html)
        with open(booknamefull_xls,'wb') as f:
            f.write(book.xls)
        f.close()

    def exportTeamSchedules(self, div_id, age, gen, numteams, prefix=""):
        headers = ['Gameday#', 'Game Date', 'Start Time', 'Venue', 'Home Team', 'Away Team']
        cdir = os.path.dirname(__file__)
        for team_id in range(1, numteams+1):
            team_str = age+gen+str(team_id)
            datasheet = Dataset(title=team_str)
            datasheet.headers = list(headers)
            teamdata_list = self.dbinterface.findTeamSchedule(age, gen, team_id)
            tabformat_list = [(x[gameday_id_CONST], mapGamedayIdToCalendar(x[gameday_id_CONST]),
                               datetime.strptime(x[start_time_CONST],"%H:%M").strftime("%I:%M %p"),
                               self.fieldinfo[self.findexerGet(x[venue_CONST])]['name'],
                               x[home_CONST], x[away_CONST]) for x in teamdata_list]
            for tabformat in tabformat_list:
                datasheet.append(tabformat)
            if team_id < 10:
                team_id_str = '0'+str(team_id)
            else:
                team_id_str = str(team_id)
            sheet_xls_relpath = prefix+age + gen + team_id_str+ '_schedule.xls'
            sheet_xls_abspath = os.path.join('/home/henry/workspace/datagraph/bottle_baseball/download/xls',
                                             sheet_xls_relpath)
            with open(sheet_xls_abspath,'wb') as f:
                f.write(datasheet.xls)
            f.close()



    def exportDivSchedulesRefFormat(self, startgameday, prefix=""):
        headers = ['Game#', 'Game#', 'Tourn Match#','Date', 'Day', 'Time', 'Division', 'Round', 'Home', 'Visitor', 'Field', 'cr_trust', 'ar_trust', 'm_trust']
        datasheet = Dataset(title=prefix)
        datasheet.headers = list(headers)

        schedule_list = self.dbinterface.findDivisionSchedulePHMSARefFormat(startgameday)
        tabformat_list = [(_offset+x[match_id_CONST], x[match_id_CONST], tournMapGamedayIdToCalendar(x[gameday_id_CONST]), tournMapGamedayIdToDate(x[gameday_id_CONST]),
            datetime.strptime(x[start_time_CONST],"%H:%M").strftime("%I:%M %p"),
            x[age_CONST]+x[gen_CONST], x[round_CONST],
            x[home_CONST], x[away_CONST],
            self.fieldinfo[self.findexerGet(x[venue_CONST])]['name'],
            _reftrust_level[_rindexerGet(getTournDivID(x[age_CONST], x[gen_CONST]))]['cr'],
            _reftrust_level[_rindexerGet(getTournDivID(x[age_CONST], x[gen_CONST]))]['ar'],
            _reftrust_level[_rindexerGet(getTournDivID(x[age_CONST], x[gen_CONST]))]['ment'])
            for x in schedule_list] if prefix else [(mapGamedayIdToCalendar(x[gameday_id_CONST],format=1), 'Saturday',
                datetime.strptime(x[start_time_CONST],"%H:%M").strftime("%I:%M %p"),
                x[age_CONST]+x[gen_CONST],
                x[home_CONST], x[away_CONST],
                self.fieldinfo[self.findexerGet(x[venue_CONST])]['name'])
                for x in schedule_list]
        if prefix:
            atabformat_list = [(_offset+i, j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9], j[10], j[11], j[12]) for i,j in enumerate(tabformat_list)]
        else:
            atabformat_list = tabformat_list
        for tabformat in atabformat_list:
            datasheet.append(tabformat)
        sheet_xls_relpath = prefix+'_RefFormat.xls'
        sheet_xls_abspath = os.path.join('/home/henry/workspace/datagraph/bottle_baseball/download/xls',
                                         sheet_xls_relpath)
        with open(sheet_xls_abspath,'wb') as f:
            f.write(datasheet.xls)
        f.close()


