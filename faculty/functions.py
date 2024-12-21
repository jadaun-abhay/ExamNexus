import datetime
import re

from faculty.models import ExamSchedules
from portal.models import Dropdowns, BaseModel


Status= BaseModel.Status

def check_schedule(course, department, year, examination, exam_details):
    college_start_time = Dropdowns.objects.filter(parent__value= "college_start_time").exclude(status= Status.DELETED).first()
    if not college_start_time:
        response = {"res": {"message": "College starting time is not defined"}, "status": 400}
        return response
    college_start_time = datetime.datetime.strptime(college_start_time, "%H:%M:%S").time()
    college_end_time = Dropdowns.objects.filter(parent__value="college_end_time").exclude(status= Status.DELETED).first()
    if not college_end_time:
        response = {"res": {"message": "College ending time is not defined"}, "status": 400}
        return response
    college_end_time = datetime.datetime.strptime(college_end_time, "%H:%M:%S").time()
    end_time = None
    for detail in exam_details:
        subject_id = detail.get("subject_id")
        subject_instance = Dropdowns.objects.filter(parent__parent= year, id=subject_id).exclude(status= Status.DELETED).first()
        if not subject_instance:
            response = {"res": {'message': f'Subject with id= {subject_id} is not available'}, "status": 404}
            return response
        exam_date = detail.get("exam_date")
        if not bool(re.match(r"\d{2}/\d{2}/\d{4}", exam_date)):
            response = {"res": {
                "message": "Wrong format for exam date must be in \'dd/mm/yyyy\'"}, "status": 400}
            return response
        exam_date = datetime.datetime.strptime(exam_date, "%d/%m/%Y").date()
        start_time = detail.get("start_time")
        if not bool(re.match(r"\d{2}:\d{2}:\d{2}", start_time)):
            response = {"res": {
                "message": "Wrong format for start_time must be in \'hh:mm:ss\'"}, "status": 400}
            return response
        start_time = datetime.datetime.strptime(start_time, "%H:%M:%S")
        exam_duration = float(examination.child.first().value)
        exam_duration = datetime.timedelta(hours=exam_duration)
        time_zero = datetime.datetime.strptime('00:00:00', '%H:%M:%S')
        end_time = (start_time - time_zero + exam_duration)
        if not (college_start_time <= end_time <= college_end_time):
            response = {"res": {
                "message": "Exam end timings exceeds college time limits"}, "status": 400}
            return response
        start_time = start_time.time()
        if not (college_start_time <= start_time <= college_end_time):
            response = {"res": {
                "message": "Examination can only be conducted in academic hours"}, "status": 400}
            return response
        maximum_marks = examination.child.last()
        examination_text = examination.value
        exams = ExamSchedules.objects.filter(
            course=course, department=department, year=year, exam_status="2")
        for exam in exams:
            diff_exam = ExamSchedules.objects.filter(course=course, department=department, year=year,
                                                     exam_status="2").exclude(examination_type=examination).order_by(
                'creation_timestamp')
            diff = (exam_date + datetime.timedelta(weeks=2))
            # if diff_exam.exists() and diff_exam.last().exam_date < diff:
            #     print("HI", diff_exam.values())
            #     response = {"res": {"message": "Different exams are too close"}, "status": 409}
            #     return response
            if exam.subject == subject_instance and exam.examination_type == examination and exam.exam_date == exam_date:
                response = {"res": {
                    "message": "Same subject is scheduled for the examination"}, "status": 400}
                return response
            if exam.exam_date == exam_date:
                if (exam.start_time <= start_time <= exam.end_time) or (exam.end_time <= end_time <= exam.end_time):
                    response = {
                        "res": {"message": "Slot is reserved for another exam"}, "status": 400}
                    return response
    return end_time
