from tablib import Dataset, Databook
from leaguedivprep import getLeagueDivInfo, mapGamedayIdToCalendar, getFieldInfo,tournMapGamedayIdToCalendar, tournMapGamedayIdToDate
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

class ScheduleExporter:
    def __init__(self, dbinterface, divinfotuple=None,fieldtuple=None):
        self.dbinterface = dbinterface
        if divinfotuple is None:
            divinfotuple = getLeagueDivInfo()
        self.leaguedivinfo = divinfotuple.dict_list
        self.lindexerGet = divinfotuple.indexerGet
        if fieldtuple is None:
            fieldtuple = getFieldInfo()
        self.fieldinfo = fieldtuple.dict_list
        self.findexerGet = fieldtuple.indexerGet

    def exportDivTeamSchedules(self, div_id, age, gen, numteams, prefix=""):
        headers = ['Gameday#', 'Game Date', 'Start Time', 'Venue', 'Home Team', 'Away Team']
        datasheet_list = []
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
    def exportDivSchedules(self, div_id):
        pass

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

    def exportDivSchedulesRefFormat(self, prefix=""):
        headers = ['Date', 'Day', 'Time', 'Division', 'Home', 'Visitor', 'Field']
        datasheet = Dataset(title=prefix+'RefschedulerFormat2013')
        datasheet.headers = list(headers)

        schedule_list = self.dbinterface.findDivisionSchedulePHMSARefFormat()
        tabformat_list = [(tournMapGamedayIdToCalendar(x[gameday_id_CONST]), tournMapGamedayIdToDate(x[gameday_id_CONST]),
            datetime.strptime(x[start_time_CONST],"%H:%M").strftime("%I:%M %p"),
            x[age_CONST]+x[gen_CONST],
            x[home_CONST], x[away_CONST],
            self.fieldinfo[self.findexerGet(x[venue_CONST])]['name'])
            for x in schedule_list] if prefix else [(mapGamedayIdToCalendar(x[gameday_id_CONST],format=1), 'Saturday',
                datetime.strptime(x[start_time_CONST],"%H:%M").strftime("%I:%M %p"),
                x[age_CONST]+x[gen_CONST],
                x[home_CONST], x[away_CONST],
                self.fieldinfo[self.findexerGet(x[venue_CONST])]['name'])
                for x in schedule_list]
        for tabformat in tabformat_list:
            datasheet.append(tabformat)
        sheet_xls_relpath = prefix+'2013PHMSAFall_schedule_RefFormat.xls'
        sheet_xls_abspath = os.path.join('/home/henry/workspace/datagraph/bottle_baseball/download/xls',
                                         sheet_xls_relpath)
        with open(sheet_xls_abspath,'wb') as f:
            f.write(datasheet.xls)
        f.close()
