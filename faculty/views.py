import datetime
import json
import re

from django.http import JsonResponse
from django.shortcuts import render

from faculty.functions import check_schedule
from faculty.models import ExamSchedules
from portal.functions import check_role, get_course_instance, get_department_instance, get_year_instance, \
    get_subject_instance
from portal.models import Dropdowns


# Create your views here.

def index(request):
    res = {"message": "Hello World"}
    return JsonResponse(res, status=200)


# def schedule(request):
#     flag = check_role(request.user, ["coe"])
#     if isinstance(flag, dict):
#         return JsonResponse(flag["res"], status=flag["status"])
#     if request.method == "POST":
#         data = json.loads(request.body)
#         course_id = data.get("course_id")
#         department_id = data.get("department_id")
#         year_id = data.get("year_id")
#         exam_type_id = data.get("exam_type_id")
#         exam_details = data.get("exam_details")
#         if not course_id and department_id and year_id and exam_type_id and exam_details:
#             res = {"message": "Information given is not sufficient"}
#             return JsonResponse(res, status= 400)
#         exam_type = Dropdowns.objects.filter(parent__value="exam_type", id=exam_type_id).first()
#         course_instance = get_course_instance(course_id)
#         if isinstance(course_instance, dict):
#             return JsonResponse(course_instance["res"], status=course_instance["status"])
#         department_instance = get_department_instance(course_id, department_id)
#         if isinstance(department_instance, dict):
#             return JsonResponse(department_instance["res"], status=department_instance["status"])
#         year_instance = get_year_instance(course_id, department_id, year_id)
#         if isinstance(year_instance, dict):
#             return JsonResponse(year_instance["res"], year_instance["status"])
#         college_start_time = datetime.time(9, 0, 0)
#         college_end_time = datetime.time(17, 0, 0)
#         for detail in exam_details:
#             exam_date = detail.get("exam_date")
#             if not bool(re.match(r"^\d{2}/\d{2}/\d{4}$", exam_date)):
#                 res = {"message": "format for exam_date is invalid. Required format: \'dd/mm/yyyy\'"}
#                 return JsonResponse(res, status= 400)
#             exam_date = datetime.datetime.strptime(exam_date, "%d/%m/%Y")
#             subject_id = detail.get("subject_id")
#             start_time = detail.get("start_time")
#             start_time = datetime.datetime.strptime(start_time, "%H:%M:%S").time()
#             end_time = detail.get("end_time")
#             end_time = datetime.datetime.strptime(end_time, "%H:%M:%S").time()
#             subject_instance = Dropdowns.objects.filter(parent__value="subjects", id=subject_id)
#             exams = ExamSchedules.objects.filter(exam_status="2", course=course_instance,
#                                                  department=department_instance, year=year_instance).exclude(
#                 status="3").order_by("exam_date")
#             if not (college_start_time < start_time < college_end_time):
#                 res = {"message": "Examination can only be conducted in the academic hours"}
#                 return JsonResponse(res, status= 400)
#             for exam in exams:
#                 examination_type = exam.examination_type.value
#                 subject = exam.subject.value
#                 scheduled_date = exam.exam_date
#                 if exam_type.value != examination_type:
#                     difference = exams.last().exam_date + datetime.timedelta(weeks=4)
#                     if not exam_date >= difference:
#                         res = {"message": f"Can not schedule {exam_type.value} close to {examination_type}"}
#                         return JsonResponse(res, status=400)
#                 if exam.subject == subject:
#                     res = {"message": "You are scheduling examination of a subject which already exists and is pending"}
#                     return JsonResponse(res, status=400)
#                 if exam.start_time <= start_time <= exam.end_time:
#                     res = {"message": "Scheduling of exam in a scheduled slot is not possible"}
#                     return JsonResponse(res, status=400)
#             ExamSchedules.objects.create(status="1", exam_status="2", course=course_instance,
#                                          department=department_instance, year= year_instance, examination_type= exam_type,
#                                          exam_date= exam_date, subject= subject_instance.first(), start_time= start_time, end_time= end_time)
#         res = {"message": "Schedule is added successfully"}
#         return JsonResponse(res, status= 200)
#     if request.method == "GET":
#         pass
#     else:
#         res = {"message": "Invalid request method"}
#         return JsonResponse(res, status= 405)

def schedule(request):
    flag = check_role(request.user, ["coe", "admin"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "POST":
        data = json.loads(request.body)
        course_id = data.get("course_id")
        department_id = data.get("department_id")
        year_id = data.get("year_id")
        exam_type = data.get("exam_type_id")
        exam_details = data.get("exam_details")
        if not (course_id and department_id and year_id and exam_type and exam_details):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
        exam_type = Dropdowns.objects.filter(parent__value="exam_type", id=exam_type).exclude(status="3").first()
        if not exam_type:
            res = {"message": "Exam type is not defined"}
            return JsonResponse(res, status= 400)
        course_instance = get_course_instance(course_id)
        if isinstance(course_instance, dict):
            return JsonResponse(course_instance["res"], status=course_instance["status"])
        department_instance = get_department_instance(course_id, department_id)
        if isinstance(department_instance, dict):
            return JsonResponse(department_instance["res"], status=department_instance["status"])
        year_instance = get_year_instance(course_id, department_id, year_id)
        if isinstance(year_instance, dict):
            return JsonResponse(year_instance["res"], status=year_instance["status"])
        flag = check_schedule(course_instance, department_instance, year_instance, exam_type, exam_details)
        if isinstance(flag, dict):
            return JsonResponse(flag["res"], status=flag["status"])
        zero_time = datetime.datetime.min
        print("HELLO", type(flag + zero_time), (flag+zero_time).time().strftime("%H:%M:%S"))
        flag = (flag+zero_time).time().strftime("%H:%M:%S")
        # print("HeLLO", type(zero_time + flag))
        for detail in exam_details:
            subject_id = detail.get("subject_id")
            subject_instance = get_subject_instance(course_id, department_id, year_id, subject_id)
            exam_date = detail.get("exam_date")
            exam_date = datetime.datetime.strptime(exam_date, "%d/%m/%Y")
            exam = ExamSchedules.objects.create(status="1", course=course_instance, department=department_instance,
                                                year=year_instance, examination_type=exam_type,
                                                subject=subject_instance, exam_date= exam_date,
                                                start_time=detail.get("start_time"), end_time= flag,
                                                exam_status="2")
        res = {"message": "success", "data": "Schedule has been added"}
        return JsonResponse(res, status=201)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 405)
