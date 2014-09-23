#!/usr/local/bin/python2.7
# Copyright YukonTR 2014
import gspread
from operator import itemgetter
import re
from pprint import pprint
from dateutil import parser
from sched_exceptions import CodeLogicError
STUDENT_NAME = 'SBA Student Name'
LAST_NAME = 'Last Name'
FIRST_NAME = 'First Name'
TIMESTAMP = 'Timestamp'
TEACHER_HEADER = 'Teacher/Coach Office Hours'
TEACHERNAME_PATTERN = "([\w.]+ [\w.]+) -"
HEAD_COACH_LIST = ['Martin Benes', 'Jeff Kai', 'Katharina Golik', 'Trevor Tanhoff']
COACH_NAME_LIST = ['Martin Benes', 'Jeff Schloss', 'Seth McCadam', 'Jeff Kai', 'Devin Gill', 'Karen Lundgren', 'Katharina Golik', 'Trevor Tanhoff', 'Caitlin Curran']
MAX_SLOTS = 24
def custom_pprint(a_list, title_str):
    print title_str
    for a in a_list:
        print "----------------------"
        pprint(a)

def confsched():
    gc = gspread.login("htominaga@gmail.com", "bxoausumpwtuaqid")
    #entrysheet = gc.open("Sunday11_21_2014SBA").sheet1
    entrysheet = gc.open("Monday09_23_SBA").sheet1
    # get the entire sheet
    signup_list = entrysheet.get_all_records()
    # sort by student name column
    signup_list.sort(key=itemgetter(STUDENT_NAME))
    student_name_list = list()
    raw_student_teacher_map_list = list()
    stindexerMatch = lambda x: [i for i,p in enumerate(raw_student_teacher_map_list) if p['student_name']==x]
    # sanitize student name list
    signup_list_len = len(signup_list)
    for signup_dict in signup_list:
        student_name = signup_dict[STUDENT_NAME]
        if type(student_name) is str:
            name_len = len(student_name.split())
            if name_len == 1:
                student_name += " " + signup_dict[LAST_NAME]
        else:
            # if student name entry is not valid, default name to last name of
            # person that entered info
            student_name = signup_dict[LAST_NAME]
        student_name_list.append(student_name)
        teacher_descrip_list_string = signup_dict[TEACHER_HEADER]
        if teacher_descrip_list_string:
            teacher_name_list = re.findall(TEACHERNAME_PATTERN, teacher_descrip_list_string)
        else:
            teacher_name_list = None
        raw_student_teacher_map_list.append({'student_name':student_name,
            'teacher_name_list':teacher_name_list,
            'timestamp':parser.parse(signup_dict[TIMESTAMP])})
        print student_name, teacher_name_list
        print "--------------------------"
    #print raw_student_teacher_map_list
    # manage duplicate entries of student name
    dup_student_name_set = set([x for x in student_name_list if student_name_list.count(x) > 1])
    dup_student_name_set_len = len(dup_student_name_set)
    print dup_student_name_set

    dup_student_teacher_map_dict = dict()
    for student_name in dup_student_name_set:
        index_list = stindexerMatch(student_name)
        teacher_name_set = set()
        for index in index_list:
            tn_list = raw_student_teacher_map_list[index]['teacher_name_list']
            if tn_list is not None:
                teacher_name_set.update(tn_list)
        teacher_name_list = list(teacher_name_set) if teacher_name_set else None
        dup_student_teacher_map_dict[student_name] = teacher_name_list
    print dup_student_teacher_map_dict

    norm_student_teacher_map_list = list()
    dupseen_set = set()
    noteacher_count = 0
    for entry in raw_student_teacher_map_list:
        student_name = entry['student_name']
        if student_name not in dup_student_name_set:
            if entry['teacher_name_list']:
                norm_student_teacher_map_list.append(entry)
            else:
                noteacher_count += 1
        elif student_name not in dupseen_set:
            teacher_name_list = dup_student_teacher_map_dict[student_name]
            if teacher_name_list:
                norm_student_teacher_map_list.append({'student_name':student_name,
                    'teacher_name_list':teacher_name_list,
                    'timestamp':entry['timestamp']})
            else:
                noteacher_count += 1
            dupseen_set.add(student_name)
    norm_student_teacher_map_list.sort(key=itemgetter('timestamp'))

    custom_pprint(norm_student_teacher_map_list, "student request list")
    print 'original len', signup_list_len, 'dup entries', dup_student_name_set_len, 'normlen', len(norm_student_teacher_map_list), 'noconf', noteacher_count

    #----------------------------------------------
    #-Make Assignments
    student_schedule_list = list()
    teacher_schedule_list = list()
    teacher_seen_set = set()
    for st_map in norm_student_teacher_map_list:
        student_name = st_map['student_name']
        ssched_list = [{'sched_flag':False, 'teacher_name':""} for x in range(MAX_SLOTS)]
        student_open_index_list = range(MAX_SLOTS)
        teacher_name_list = st_map['teacher_name_list']
        for teacher_name in teacher_name_list:
            if teacher_name not in teacher_seen_set:
                default_teachersched_list = [{'sched_flag':False, 'student_name':""} for x in range(MAX_SLOTS)]
                teacher_seen_set.add(teacher_name)
                priority = 1 if teacher_name in HEAD_COACH_LIST else 2
                teacher_schedule_list.append({'teacher_name':teacher_name, 'schedule_list':default_teachersched_list,
                    'earliest_open_index':0, 'priority':priority})
        student_teacher_schedule_list = [x for x in teacher_schedule_list if x['teacher_name'] in teacher_name_list]
        studentteacher_seen_set = set()
        student_teacher_schedule_list.sort(key=itemgetter('earliest_open_index', 'priority'))
        for teacher_schedule in student_teacher_schedule_list:
            teacher_name = teacher_schedule['teacher_name']
            tsched_list = teacher_schedule['schedule_list']
            teacher_open_index_list = [i for i,j in enumerate(tsched_list) if not j['sched_flag']]
            min_teacher_open_index = min(teacher_open_index_list)
            if min_teacher_open_index != teacher_schedule['earliest_open_index']:
                raise CodeLogicError("teacher min slots does not match %d %d" %(min_teacher_open_index, teacher_schedule['earliest_open_index']))
            common_open_index_list = set(student_open_index_list).intersection(teacher_open_index_list)
            earliest_common_open_index = min(common_open_index_list)
            ssched_slot = ssched_list[earliest_common_open_index]
            if ssched_slot['sched_flag']:
                raise CodeLogicError("Student schedule already scheduled, should be open student %s teacher %s slot_index %d" % (student_name, teacher_name, earliest_common_open_index))
            ssched_slot['teacher_name'] = teacher_name
            ssched_slot['sched_flag'] = True
            student_open_index_list.remove(earliest_common_open_index)
            tsched_slot = tsched_list[earliest_common_open_index]
            # make assignment on the teacher side
            if tsched_slot['sched_flag']:
                 CodeLogicError("Teacher schedule already scheduled, should be open student %s teacher %s slot_index %d" % (student_name, teacher_name, earliest_common_open_index))
            tsched_slot['student_name'] = student_name
            tsched_slot['sched_flag'] = True
            studentteacher_seen_set.add(teacher_name)
            if teacher_name in HEAD_COACH_LIST:
                next_open_index = earliest_common_open_index+1
                nextssched_slot = ssched_list[next_open_index]
                if nextssched_slot['sched_flag']:
                    raise CodeLogicError("head coach %s next slot not open" % (teacher_name,))
                nextssched_slot['teacher_name'] = teacher_name
                nextssched_slot['sched_flag'] = True
                student_open_index_list.remove(next_open_index)
                tsched_slot = tsched_list[next_open_index]
                # make assignment on the teacher side
                if tsched_slot['sched_flag']:
                     CodeLogicError("Teacher schedule already scheduled, should be open student %s teacher %s slot_index %d" % (student_name, teacher_name, earliest_common_open_index))
                tsched_slot['student_name'] = student_name
                tsched_slot['sched_flag'] = True
            # update earliest slot if required
            if earliest_common_open_index == min_teacher_open_index:
                # if the earliest common index is the same as the earliest teacher index, then update teacher's minimum
                teacher_open_index_list = [i for i,j in enumerate(tsched_list) if not j['sched_flag']]
                teacher_schedule['earliest_open_index'] = min(teacher_open_index_list)
            elif earliest_common_open_index < min_teacher_open_index:
                raise CodeLogicError("earliest open %d is earlier than min teacher index %d" %(earliest_common_open_index, min_teacher_open_index))
            #print 'teacher', teacher_name, 'scheduled for student', student_name
        student_schedule_list.append({'student_name':student_name, 'schedule_list':ssched_list})
    #pprint(student_schedule_list)
    #pprint(teacher_schedule_list)
    '''
    teacher_count_list = [{'teacher_name':x['teacher_name'], 'count':[y['sched_flag'] for y in x['schedule_list']].count(True)} for x in teacher_schedule_list]
    teacher_count_list.sort(key=itemgetter('count'), reverse=True)
    pprint(teacher_count_list)
    '''
    teacher_assign_list = [{'teacher_name':x['teacher_name'], 'count':[y['sched_flag'] for y in x['schedule_list']].count(True), 'student_request_list':[y['student_name'] for y in x['schedule_list'] if y['sched_flag']]} for x in teacher_schedule_list]
    teacher_assign_list.sort(key=itemgetter('count'), reverse=True)
    custom_pprint(teacher_assign_list, "teacher assign list")

