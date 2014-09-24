#!/usr/local/bin/python2.7
# Copyright YukonTR 2014
import gspread
from operator import itemgetter
from itertools import groupby
import re
import copy
from pprint import pprint
from dateutil import parser
from sched_exceptions import CodeLogicError
import logging
STUDENT_NAME = 'SBA Student Name'
LAST_NAME = 'Last Name'
FIRST_NAME = 'First Name'
TIMESTAMP = 'Timestamp'
TEACHER_HEADER = 'Teacher/Coach Office Hours'
TEACHERNAME_PATTERN = "([\w.]+ [\w.]+) -"
HEAD_COACH_LIST = ['Martin Benes', 'Jeff Kai', 'Katharina Golik', 'Trevor Tanhoff', 'Seth McCadam', 'Jim Hudson']
HEAD_COACH_DISCIP_LIST = [{'name':'Martin Benes', 'dtype':'n'},
    {'name':'Jeff Kai', 'dtype':'fism'},
    {'name':'Katharina Golik', 'dtype':'fisw'},
    {'name':'Trevor Tanhoff', 'dtype':'fr'},
    {'name':'Seth McCadam', 'dtype':'u16'},
    {'name':'Jim Hudson', 'dtype':'u14'}]
headindexerGet = lambda x: dict((p['dtype'],i) for i,p in enumerate(HEAD_COACH_DISCIP_LIST)).get(x)
ASST_COACH_LIST = ['Jeff Schloss', 'Devin Gill', 'Karen Lundgren', 'Caitlin Curran']
ASST_COACH_DISCIP_LIST = [{'name':'Jeff Schloss', 'dtype':'n'},
    {'name':'Devin Gill', 'dtype':'fism'},
    {'name':'Caitlin Curran', 'dtype':'n'},
    {'name':'Karen Lundgren', 'dtype':'u16'},
]
asstindexerGet = lambda x: dict((p['name'],i) for i,p in enumerate(ASST_COACH_DISCIP_LIST)).get(x)
COACH_NAME_LIST = ['Martin Benes', 'Jeff Schloss', 'Seth McCadam', 'Jeff Kai', 'Devin Gill', 'Karen Lundgren', 'Katharina Golik', 'Trevor Tanhoff', 'Caitlin Curran']
MAX_SLOTS = 24
def custom_pprint(a_list, title_str):
    fout = open(title_str+".txt", "w")
    logging.info(title_str)
    fout.write(title_str+"\n")
    for a in a_list:
        logging.info("----------------------")
        fout.write("---------------------\n")
        pprint(a, fout)
        logging.info("schedule %s", a)
    fout.close()
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
    # create normalized student->teacher request map list
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

    custom_pprint(norm_student_teacher_map_list, "student_request_list")
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
                # head coach priority 1 gives them two slots per student
                priority = 1 if teacher_name in HEAD_COACH_LIST else 2
                teacher_schedule_list.append({'teacher_name':teacher_name, 'schedule_list':default_teachersched_list,
                    'earliest_open_index':0, 'priority':priority})
        student_teacher_schedule_list = [x for x in teacher_schedule_list if x['teacher_name'] in teacher_name_list]
        sindexerGet = lambda x: dict((p['teacher_name'],i) for i,p in enumerate(student_teacher_schedule_list)).get(x)
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
            copy_list = copy.copy(common_open_index_list)
            if teacher_name in HEAD_COACH_LIST:
                # if a teacher is a head coach, we need to allocate a 20-min (double)
                # slot.  Remove single slots from the open index list
                for k, g in groupby(enumerate(copy_list), lambda (i,x):i-x):
                    g_list = list(g)
                    if len(g_list) == 1:
                        drop_index = g_list[0][1]
                        common_open_index_list.remove(drop_index)
            elif teacher_name in ASST_COACH_LIST:
                # if the teacher is an assistant coach
                # first get discipline
                asstindex = asstindexerGet(teacher_name)
                asstdiscp = ASST_COACH_DISCIP_LIST[asstindex]['dtype']
                # get head coach for that discipline
                headindex = headindexerGet(asstdiscp)
                headcoach_name = HEAD_COACH_DISCIP_LIST[headindex]['name']
                if headcoach_name in studentteacher_seen_set:
                    # head coach already has been scheduled (should be the case as
                    # schedule list is sorted by priority first)
                    headcoach_schedule_list = student_teacher_schedule_list[sindexerGet(headcoach_name)]['schedule_list']
                    hindexerGet = lambda x: [i for i,p in enumerate(headcoach_schedule_list) if p['student_name']==x]
                    # get slots where hc is seeing current student
                    hindex_list = hindexerGet(student_name)
                    for hindex in hindex_list:
                        tsched_slot = tsched_list[hindex]
                        if not tsched_slot['sched_flag']:
                            ssched_slot = ssched_list[hindex]
                            # note there could be more than one assistant coach
                            if 'altteacher_list' in ssched_list:
                                ssched_slot['altteacher_list'].append(teacher_name)
                            else:
                                ssched_slot['altteacher_list'] = [teacher_name]
                            tsched_slot = tsched_list[hindex]
                            tsched_slot['student_name'] = student_name
                            tsched_slot['sched_flag'] = True
                        else:
                            logging.debug("asst coach %s not able to see student %s at slot %d" % (teacher_name, student_name, hindex))
                            #raise CodeLogicError('asst coach %s already has spot scheduled at slot %d for student %s' % (teacher_name, hindex, student_name))
                        studentteacher_seen_set.add(teacher_name)
                        # update min open index
                        teacher_open_index_list = [i for i,j in enumerate(tsched_list) if not j['sched_flag']]
                        teacher_schedule['earliest_open_index'] = min(teacher_open_index_list)
                    # go to next teacher
                    continue
            studentteacher_seen_set.add(teacher_name)
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
    custom_pprint(teacher_assign_list, "teacher_assign_list")
    custom_pprint(student_schedule_list, "student_schedule_list")
    custom_pprint(teacher_schedule_list, "teacher_schedule_list")

