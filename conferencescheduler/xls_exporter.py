from tablib import Dataset, Databook
from datetime import datetime
from dateutil import parser
import os, errno

LOCALDIR_PATH = '/home/henry/workspace/datagraph/conferencescheduler/'
class XLS_Exporter:
    ''' this class and it's methods will eventually supersede sched_exporter
    class and methods '''
    def __init__(self):
        self.dir_path = LOCALDIR_PATH
        self.mkdir_p(self.dir_path)

    def generate_studentsched_xls(self, student_schedule_list):
        headers = ['Start Time', 'End Time', 'Location', 'Teacher/Coach']
        datasheet_list = list()
        for student_schedule in student_schedule_list:
            student_name = student_schedule['student_name']
            datasheet = Dataset(title=student_name)
            datasheet.headers = list(headers)
            datasheet.append_separator("Schedule for "+student_name)
            for ssched_slot in student_schedule['schedule_list']:
                start_time = ssched_slot['start_time_dt'].strftime("%I:%M%p")
                end_time = ssched_slot['end_time_dt'].strftime("%I:%M%p")
                room = ssched_slot['room']
                teacher_name = ssched_slot['teacher_name']
                if 'asstcoach_list' in ssched_slot:
                    asstcoach_str = ', '.join(ssched_slot['asstcoach_list'])
                    teacher_name += ', '+ asstcoach_str
                datasheet.append((start_time, end_time, room, teacher_name))
            datasheet_list.append(datasheet)
        book = Databook(datasheet_list)
        bookname_xls_relpath = "2014IndividualConference_byStudent.xls"
        bookname_xls_fullpath = os.path.join(self.dir_path, bookname_xls_relpath)
        with open(bookname_xls_fullpath,'wb') as f:
            f.write(book.xls)
        f.close()

    def generate_teachersched_xls(self, teacher_schedule_list):
        headers = ['Start Time', 'End Time', 'Location', 'Student-Athlete']
        datasheet_list = list()
        for teacher_schedule in teacher_schedule_list:
            teacher_name = teacher_schedule['teacher_name']
            datasheet = Dataset(title=teacher_name)
            datasheet.headers = list(headers)
            datasheet.append_separator("Schedule for "+teacher_name)
            for tsched_slot in teacher_schedule['schedule_list']:
                start_time = tsched_slot['start_time_dt'].strftime("%I:%M%p")
                end_time = tsched_slot['end_time_dt'].strftime("%I:%M%p")
                room = tsched_slot['room']
                student_name = tsched_slot['student_name']
                datasheet.append((start_time, end_time, room, student_name))
            datasheet_list.append(datasheet)
        book = Databook(datasheet_list)
        bookname_xls_relpath = "2014IndividualConference_byStaff.xls"
        bookname_xls_fullpath = os.path.join(self.dir_path, bookname_xls_relpath)
        with open(bookname_xls_fullpath,'wb') as f:
            f.write(book.xls)
        f.close()

    def generate_timesched_xls(self, time_schedule_list, venue_list):
        headers = ['Start Time', 'End Time']
        headers.extend(venue_list)
        datasheet_list = list()
        compressed_list = list()
        cindexerGet = lambda x: dict((p['start_time_dt'],i) for i,p in enumerate(compressed_list)).get(x)
        datasheet = Dataset(title="Individual Conferences")
        datasheet.headers = list(headers)
        for time_schedule in time_schedule_list:
            teacher_name = time_schedule['teacher_name']
            if 'asstcoach_list' in time_schedule:
                asstcoach_str = ', '.join(time_schedule['asstcoach_list'])
                teacher_name += ', '+ asstcoach_str
            student_name = time_schedule['student_name']
            meet_str = student_name+' v '+teacher_name
            start_time_dt = time_schedule['start_time_dt']
            end_time_dt = time_schedule['end_time_dt']
            room = time_schedule['room']
            cindex = cindexerGet(start_time_dt)
            if cindex is None:
                start_time_list = [start_time_dt.strftime("%I:%M%p"),
                    end_time_dt.strftime("%I:%M%p")]
                start_time_list.extend(len(venue_list)*[""])
                hindex = headers.index(room)
                if hindex is None:
                    raise CodeLogicError("room %s not in headers" % (room,))
                else:
                    start_time_list[hindex] = meet_str
                compressed_list.append({'start_time_dt':start_time_dt,
                    'start_time_list':start_time_list})
            else:
                hindex = headers.index(room)
                if hindex is None:
                    raise CodeLogicError("room %s not in headers" % (room,))
                else:
                    compressed_list[cindex]['start_time_list'][hindex] = meet_str
        for compressed_row in compressed_list:
            datasheet.append(compressed_row['start_time_list'])
        datasheet_list.append(datasheet)
        book = Databook(datasheet_list)
        bookname_xls_relpath = "2014IndividualConference_allbytime.xls"
        bookname_xls_fullpath = os.path.join(self.dir_path, bookname_xls_relpath)
        with open(bookname_xls_fullpath,'wb') as f:
            f.write(book.xls)
        f.close()

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

    def generate_divteamxls(self):
        headers = ['Game Date', 'Day', 'Time', 'Division', 'Home',
        'Visitor', 'Venue']
        file_list = list()
        for divinfo in self.divinfo_list:
            div_id = divinfo['div_id']
            div_age = divinfo['div_age']
            div_gen = divinfo['div_gen']
            div_str = div_age + div_gen
            totalteams = divinfo['totalteams']
            datasheet_list = list()
            for team_id in range(1, totalteams+1):
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

    def mkdir_p(self, path):
        ''' http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
        '''
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise
