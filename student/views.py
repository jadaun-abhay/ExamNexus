import datetime
import json

from django.http import JsonResponse
from django.shortcuts import render

from faculty.models import ExamSchedules, QuestionPaper
from portal.functions import check_role
from portal.models import Dropdowns


# Create your views here.


def index(request):
    res = {"message": "Hello World"}
    return JsonResponse(res, status=200)


def examinations(request):
    flag = check_role(request.user, ["student"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "GET":
        examinations = Dropdowns.objects.filter(parent__value="examinations").all().exclude(status="3").values("id",
                                                                                                               "parent_id",
                                                                                                               "value")
        if not examinations.exists():
            res = {"message": "Admin has not defined exam_names yet."}
            return JsonResponse(res, status=404)
        examinations = list(examinations)
        res = {"message": "success", "data": examinations}
        return JsonResponse(res, status=200)


def subjects(request):
    flag = check_role(request.user, ["student"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "GET":
        examination_id = request.GET.get("exam_id")
        student_info = request.user.student_info.values(
            "course", "department", "year").first()
        exams = ExamSchedules.objects.filter(
            course_id=student_info["course"], department_id=student_info["department"], year_id=student_info["year"], examination_type_id=examination_id).values("subject__id", "subject__value")
        if not exams.exists():
            res = {"message": "No exams have been scheduled yet"}
            return JsonResponse(res, status=400)
        data = list(exams)
        print(data)
        res = {"message": "success", "data": data}
        return JsonResponse(res, status=200)


def examination(request):
    flag = check_role(request.user, ["student"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "GET":
        subject_id = request.GET.get("subject_id")
        examination_id = request.GET.get("exam_id")
        if not (subject_id and examination_id):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status=400)
        student_info = request.user.student_info.first()
        course_id = student_info.course_id
        department_id = student_info.department_id
        year_id = student_info.year_id
        exam = ExamSchedules.objects.filter(course_id=course_id, department_id=department_id, examination_type_id=examination_id,
                                            year_id=year_id, subject_id=subject_id, exam_status="2").exclude(faculty=None).first()

        if not exam:
            res = {"message": "Date of exam has not arrived yet"}
            return JsonResponse(res, status=400)
        examination = Dropdowns.objects.filter(
            id=examination_id, parent__value="examinations").exclude(status="3").first()
        examination_name = examination.value
        time_duration = float(examination.child.first().value)
        time_duration = datetime.timedelta(hours=time_duration).total_seconds()
        maximum_marks = int(examination.child.all()[1].value)
        faculty = exam.faculty
        schedule_id = exam.id
        questions = QuestionPaper.objects.filter(
            schedule_id=schedule_id, faculty=faculty).exclude(selection_status=False)
        my_dict = dict()
        my_dict.update({"examination_name": examination_name,
                       "time_duration": time_duration, "maximum_marks": maximum_marks})
        question_data = list()
        i = 0
        for question in questions:
            i += 1
            question_text = question.value
            options = list(question.child.values(
                "id", "value").exclude(value="answer"))
            ques_data = {"question_number": f"{i}",
                         "question_text": question_text, "options": options}
            question_data.append(ques_data)
        my_dict["question_sheet"] = question_data
        data = list()
        my_dict["total_questions"] = len(question_data)
        data.append(my_dict)
        res = {"message": "success", "data": data}
        return JsonResponse(res, status=200)
    elif request.method == "POST":
        data = json.loads(request.body)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)
