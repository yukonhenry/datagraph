from tablib import Dataset, Databook
from datetime import datetime
from dateutil import parser
import os, errno

LOCALDIR_PATH = '/home/henry/workspace/datagraph/conferencescheduler/'
FILE_SUFFIX = "_v3"
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
        bookname_xls_relpath = "2014IndividualConference_byStudent"+FILE_SUFFIX+".xls"
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
        bookname_xls_relpath = "2014IndividualConference_byStaff"+FILE_SUFFIX+".xls"
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
        bookname_xls_relpath = "2014IndividualConference_allbytime"+FILE_SUFFIX+".xls"
        bookname_xls_fullpath = os.path.join(self.dir_path, bookname_xls_relpath)
        with open(bookname_xls_fullpath,'wb') as f:
            f.write(book.xls)
        f.close()

    def mkdir_p(self, path):
        ''' http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
        '''
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise
