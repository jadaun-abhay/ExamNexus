import datetime
import json

from django.http import JsonResponse

from faculty.functions import check_schedule
from faculty.models import ExamSchedules, FacultyInfo, QuestionPaper
from portal.functions import check_role, get_course_instance, get_department_instance, get_year_instance, \
    get_subject_instance
from portal.models import Dropdowns, BaseModel

Status= BaseModel.Status
ExamStatus = ExamSchedules.ExamStatus


# Create your views here.

def index(request):
    res = {"message": "Hello World"}
    return JsonResponse(res, status=200)


def examination_schedule__coe(request):
    flag = check_role(request.user, ["coe", "admin", "hod"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "POST":
        data = json.loads(request.body)
        course_id = data.get("course_id")
        department_id = data.get("department_id")
        year_id = data.get("year_id")
        exam_id = data.get("exam_id")
        exam_details = data.get("exam_details")
        if not (course_id and department_id and year_id and exam_id and exam_details):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
        examination_instance = Dropdowns.objects.filter(parent__value= "examinations", id= exam_id).exclude(status= Status.DELETED).first()
        if not examination_instance:
            res = {"message": "Exam name is not defined"}
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
        flag = check_schedule(course_instance, department_instance, year_instance, examination_instance, exam_details)
        if isinstance(flag, dict):
            return JsonResponse(flag["res"], status=flag["status"])
        zero_time = datetime.datetime.min
        flag = (flag + zero_time).time().strftime("%H:%M:%S")
        for detail in exam_details:
            subject_id = detail.get("subject_id")
            subject_instance = get_subject_instance(
                course_id, department_id, year_id, subject_id)
            exam_date = detail.get("exam_date")
            exam_date = datetime.datetime.strptime(exam_date, "%d/%m/%Y")
            exam = ExamSchedules.objects.create(status= Status.CREATED, course= course_instance, department= department_instance,
                                                year= year_instance, examination_type= examination_instance,
                                                subject= subject_instance, exam_date= exam_date,
                                                start_time= detail.get("start_time"), end_time= flag,
                                                exam_status= ExamStatus.PENDING)
        res = {"message": "success", "data": "Schedule/s has been added"}
        return JsonResponse(res, status=201)
    elif request.method == "GET":
        exam_id = request.GET.get("exam_id")
        course_id = request.GET.get("course_id")
        department_id = request.GET.get("department_id")
        year_id = request.GET.get("year_id")
        if not (exam_id and course_id and department_id and year_id):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status=400)
        date_sheet = ExamSchedules.objects.filter(course_id=course_id, department_id=department_id, year_id=year_id,
                                                  examination_type_id=exam_id, exam_status="2")
        if not date_sheet.exists():
            res = {"message": "No schedule found"}
            return JsonResponse(res, status=404)
        data = list()
        for schedule in date_sheet:
            schedule_id = schedule.id
            exam_date = schedule.exam_date
            start_time = schedule.start_time
            end_time = schedule.end_time
            department = schedule.department.value
            year = schedule.year.value
            my_dict = {"date": exam_date, "start_time": start_time, "end_time": end_time,
                       "subject": schedule.subject.value, "department": department, "year": year, "schedule_id": schedule_id}
            data.append(my_dict)
        res = {"message": "success", "data": data}
        return JsonResponse(res, status=200)
    elif request.method == "PATCH":
        data = json.loads(request.body)
        exam_id = data.get("exam_id")
        course_id = data.get("course_id")
        department_id = data.get("department_id")
        year_id = data.get("year_id")
        subject_id = data.get("subject_id")
        exam_schedule = ExamSchedules.objects.filter(
            course_id=course_id, department_id=department_id, year_id=year_id, subject_id=subject_id).exclude(status="3").exclude(exam_status="1")
        if not exam_schedule.exists():
            res = {"message": "Exam schedule is not defined for given information"}
            return JsonResponse(res, status=400)
        exam_schedule = exam_schedule.first()
        exam_schedule.subject_id = subject_id
        exam_schedule.save()
        res = {"message": "Updations are applied successfully"}
        return JsonResponse(res, status=200)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)


def schedule__faculty(request):
    flag = check_role(request.user, ["faculty"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if not request.method == "GET":
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)
    faculty_info = FacultyInfo.objects.filter(faculty=request.user)
    data = list()
    for each in faculty_info:
        course_instance = each.course
        department_instance = each.department
        year_instance = each.year
        subject_instance = each.subject
        exams = ExamSchedules.objects.filter(course=course_instance, department=department_instance, year=year_instance,
                                             subject=subject_instance, exam_status="2").exclude(status="3")
        if exams.exists():
            for exam in exams:
                schedule_id = exam.id
                question_data = QuestionPaper.objects.filter(schedule_id=schedule_id, faculty=request.user).exclude(
                    status="3")
                if question_data.exists():
                    continue
                exam_name_id = exam.examination_type.id
                exam_name_instance = exam.examination_type
                exam_details = exam_name_instance.child.all()
                duration = exam_details[0].value
                maximum_marks = exam_details[1].value
                total_questions = exam_details[2].value
                exam_name = exam.examination_type.value
                exam_date = exam.exam_date
                start_time = exam.start_time
                end_time = exam.end_time
                year_id = exam.year.id
                year = exam.year.value
                subject_id = exam.subject.id
                subject_name = exam.subject.value
                detail = dict(schedule_id=schedule_id, duration=duration, maximum_marks=maximum_marks,
                              total_questions=total_questions, exam_name_id=exam_name_id, exam_name=exam_name,
                              year_id=year_id, year=year,
                              exam_date=exam_date, start_time=start_time, end_time=end_time, subject_id=subject_id,
                              subject_name=subject_name)
                data.append(detail)
        else:
            res = {"message": "success", "data": []}
            return JsonResponse(res, status=200)
    res = {"message": "success", "data": data}
    return JsonResponse(res, status=200)


def examination_paper__faculty(request):
    flag = check_role(request.user, ["faculty"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "POST":
        data = json.loads(request.body)
        schedule_id = data.get("schedule_id")
        subject_id = data.get("subject_id")
        year_id = data.get("year_id")
        questions = data.get("questions")
        if not isinstance(questions, list):
            res = {'message': "questions must come in list"}
            return JsonResponse(res, status=400)
        if not (schedule_id and subject_id and year_id and questions):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status=400)
        subject_instance = Dropdowns.objects.filter(
            parent__value="subjects", id=subject_id).exclude(status="3")
        if subject_instance.exists():
            subject_instance = subject_instance.exists()
        else:
            res = {"message": f"Subject not found by id = {subject_id}"}
            return JsonResponse(res, status=400)
        schedule_instance = ExamSchedules.objects.filter(
            id=schedule_id).first()
        year_instance = Dropdowns.objects.filter(
            child__value="subjects", id=year_id).exclude(status="3")
        course_instance = schedule_instance.course
        department_instance = schedule_instance.department
        paper = QuestionPaper.objects.filter(
            schedule=schedule_instance, faculty=request.user).exclude(status="3")
        if paper.exists():
            res = {"message": "Paper has already been created"}
            return JsonResponse(res, status=409)
        i = 0
        for ques_ans_dict in questions:
            question = ques_ans_dict.get("questionText")
            options = ques_ans_dict.get("options")
            answer = ques_ans_dict.get("correctAnswer")
            question_instance = QuestionPaper.objects.filter(value=question, faculty=request.user,
                                                             schedule=schedule_instance).exclude(status="3").exclude(
                schedule__exam_status="2")
            i += 1
            if question_instance.exists():
                res = {"message": f"Question {i} already exists"}

                return JsonResponse(res, status=409)
            ques = QuestionPaper.objects.create(value=question, faculty=request.user, status="1",
                                                schedule=schedule_instance)
            for option in options:
                option = ques.child.create(value=option, status="1")
            correct = ques.child.create(value="answer", status="1")
            correct.child.create(value=answer, status="1")
        res = {"message": "success",
               "data": "Question paper is successfully created and submitted for acceptance by hod"}
        return JsonResponse(res, status=200)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)


def examination_paper__hod(request):
    flag = check_role(request.user, ["hod"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "GET":
        hod_info_instance = FacultyInfo.objects.filter(
            faculty=request.user).first()
        course_instance = hod_info_instance.course
        department_instance = hod_info_instance.department
        exam_id = request.GET.get("exam_id")
        subject_id = request.GET.get("subject_id")
        year_id = request.GET.get("year_id")
        faculty_id = request.GET.get("faculty_id")
        schedule_id = request.GET.get("schedule_id")
        if subject_id:
            if not year_id:
                res = {"message": "year_id is not provided"}
                return JsonResponse(res, status=400)
            schedule_data = ExamSchedules.objects.filter(course=course_instance, department=department_instance,
                                                         year_id=year_id, examination_type_id=exam_id, subject_id=subject_id).exclude(status="3").first()
            if not schedule_data:
                res = {"message": "Examination is not scheduled yet"}
                return JsonResponse(res, status=400)
            if schedule_data.faculty:
                res = {"message": "Paper has been already selected"}
                return JsonResponse(res, status=200)
            schedule_id = schedule_data.id
            subject = schedule_data.subject.value
            year = schedule_data.year.value
            examination = schedule_data.examination_type.value
            faculty_list = QuestionPaper.objects.filter(
                schedule_id=schedule_id).values("faculty_id").distinct()
            faculty_list = faculty_list.values("faculty_id", "faculty__first_name", "faculty__middle_name",
                                               "faculty__last_name")
            for faculty_data in faculty_list:
                faculty_data.update({"subject": subject, "year": year,
                                    "examination": examination, "schedule_id": schedule_id})
            faculty_list = list(faculty_list)
            res = {"message": "success", "data": faculty_list}
            return JsonResponse(res, status=200)
        elif exam_id:
            schedule_data = list(ExamSchedules.objects.filter(course=course_instance, department=department_instance, examination_type_id=exam_id).exclude(
                status="3").values("year_id", "year__value", "subject_id", "subject__value"))
            res = {"message": "success", "data": schedule_data}
            return JsonResponse(res, status=200)
        if faculty_id:
            if not schedule_id:
                res = {"message": "schedule_id is not given"}
                return JsonResponse(res, status=400)
            question_sheet = QuestionPaper.objects.filter(
                schedule_id=schedule_id, faculty_id=faculty_id).exclude(selection_status=True)
            if not question_sheet.exists():
                res = {"message": "Question paper is not available"}
                return JsonResponse(res, status=200)
            i = 0
            data = list()
            each_question_data = dict()
            for question in question_sheet:
                question_text = question.value
                options = list(question.child.values_list(
                    "value", flat=True).exclude(value="answer"))
                answer_instance = question.child.filter(value="answer").first()
                if not answer_instance:
                    res = {"message": "Answer is not provided"}
                    return JsonResponse(res, status=404)
                answer = answer_instance.child.first().value
                i += 1
                each_question_data = {"question_number": f"{
                    i}", "question_text": question_text, "options": options, "answer": answer}
                data.append(each_question_data)
            res = {"message": "success",
                   "schedule_id": schedule_id, "data": data}
            return JsonResponse(res, status=200)
        if schedule_id:
            faculty_list = QuestionPaper.objects.filter(
                schedule_id=schedule_id).values("faculty_id").distinct()
            faculty_list = faculty_list.values(
                "faculty_id", "faculty__first_name", "faculty__middle_name", "faculty__last_name")
            faculty_list = list(faculty_list)
            res = {"message": "success",
                   "schedule_id": schedule_id, "data": faculty_list}
            return JsonResponse(res, status=200)
        else:
            res = {"message": "Invalid data"}
            return JsonResponse(res, status=400)
    elif request.method == "PATCH":
        flag = check_role(request.user, ["hod"])
        if isinstance(flag, dict):
            return JsonResponse(flag["res"], status=flag["status"])
        data = json.loads(request.body)
        faculty_id = data.get("faculty_id")
        schedule_id = data.get("schedule_id")
        if not (faculty_id and schedule_id):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status=400)
        questions = QuestionPaper.objects.filter(
            faculty_id=faculty_id, schedule_id=schedule_id).exclude(selection_status=True)
        if not questions.exists():
            res = {"message": "No question sheet available"}
            return JsonResponse(res, status=404)
        for q in questions:
            q.selection_status = True
            q.save()
        exam = ExamSchedules.objects.filter(id=schedule_id).first()
        exam.faculty_id = faculty_id
        exam.save()
        res = {"message": "Question paper is selected"}
        return JsonResponse(res, status=200)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)


def years_list(request):
    flag = check_role(request.user, ["hod"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    hod_info = FacultyInfo.objects.filter(
        faculty=request.user).exclude(status="3").first()
    if not hod_info:
        res = {"message": "HOD does not exists"}
        return JsonResponse(res, status=400)
    department = hod_info.department
    year_list = list(department.child.values(
        "value", "id").exclude(status="3"))
    res = {"message": "success", "data": year_list}
    return JsonResponse(res, status=200)
