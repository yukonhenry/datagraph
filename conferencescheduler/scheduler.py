#!/usr/local/bin/python2.7
# Copyright YukonTR 2014
import gspread
from operator import itemgetter
import re
STUDENT_NAME = 'SBA Student Name'
LAST_NAME = 'Last Name'
FIRST_NAME = 'First Name'
TEACHER_HEADER = 'Teacher/Coach Office Hours'
TEACHERNAME_PATTERN = "([\w.]+ [\w.]+) -"
def confsched():
    gc = gspread.login("htominaga@gmail.com", "bxoausumpwtuaqid")
    entrysheet = gc.open("Sunday11_21_2014SBA").sheet1
    signup_list = entrysheet.get_all_records()
    signup_list.sort(key=itemgetter(STUDENT_NAME))
    student_name_list = list()
    student_teacher_map_list = list()
    stindexerMatch = lambda x: [i for i,p in enumerate(student_teacher_map_list) if p['student_name']==x]
    for signup_dict in signup_list:
        student_name = signup_dict[STUDENT_NAME]
        if type(student_name) is str:
            name_len = len(student_name.split())
            if name_len == 1:
                student_name += " " + signup_dict[LAST_NAME]
        else:
            name_len = 0
            student_name = signup_dict[LAST_NAME]
        student_name_list.append(student_name)
        teacher_descrip_list_string = signup_dict[TEACHER_HEADER]
        if teacher_descrip_list_string:
            teacher_name_list = re.findall(TEACHERNAME_PATTERN, teacher_descrip_list_string)
        student_teacher_map_list.append({'student_name':student_name,
            'teacher_name_list':teacher_name_list})
        print student_name, teacher_name_list
        print "--------------------------"
    print student_teacher_map_list
    dup_student_name_set = set([x for x in student_name_list if student_name_list.count(x) > 1])
    print dup_student_name_set
    for student_name in dup_student_name_set:
        index_list = stindexerMatch(student_name)
        teacher_name_set = set()
        for index in index_list:
            teacher_name_set.update(student_teacher_map_list[index]['teacher_name_list'])
        teacher_name_list = list(teacher_name_set)
        print student_name, teacher_name_list


