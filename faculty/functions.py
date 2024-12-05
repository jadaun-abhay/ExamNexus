import datetime
import re

from faculty.models import ExamSchedules
from portal.models import Dropdowns


def check_schedule(course, department, year, exam_type, exam_details):
    college_start_time = datetime.time(9, 0, 0)
    college_end_time = datetime.time(17, 0, 0)
    end_time = None
    for detail in exam_details:
        subject_id = detail.get("subject_id")
        subject_instance = Dropdowns.objects.filter(parent__parent=year, id=subject_id).exclude(status="3").first()
        if not subject_instance:
            response = {"res": {'message': f'Subject with id= {subject_id} is not known'}, "status": 404}
            return response
        exam_date = detail.get("exam_date")
        if not bool(re.match(r"\d{2}/\d{2}/\d{4}", exam_date)):
            response = {"res": {"message": "Wrong format for exam date must be in \'dd/mm/yyyy\'"}, "status": 400}
            return response
        exam_date = datetime.datetime.strptime(exam_date, "%d/%m/%Y").date()
        start_time = detail.get("start_time")
        if not bool(re.match(r"\d{2}:\d{2}:\d{2}", start_time)):
            response = {"res": {"message": "Wrong format for start_time must be in \'hh:mm:ss\'"}, "status": 400}
            return response
        start_time = datetime.datetime.strptime(start_time, "%H:%M:%S")
        exam_duration = float(exam_type.child.first().value)
        duration = datetime.timedelta(hours= exam_duration)
        time_zero = datetime.datetime.strptime('00:00:00', '%H:%M:%S')
        end_time = (start_time - time_zero + duration)
        start_time = start_time.time()
        maximum_marks = exam_type.child.last()
        exam_name = exam_type.value
        exams = ExamSchedules.objects.filter(course=course, department=department, year=year, exam_status="2")
        for exam in exams:
            diff_exam = ExamSchedules.objects.filter(course=course, department=department, year=year,
                                                     exam_status="2").exclude(examination_type= exam_type).order_by(
                'exam_date')
            diff = (exam_date + datetime.timedelta(weeks= 2))
            if diff_exam.exists() and diff_exam.last().exam_date < diff:
                response = {"res": {"message": "Different exams are too close"}, "status": 409}
                return response
            if exam.subject == subject_instance and exam.examination_type == exam_type and exam.exam_date == exam_date:
                response = {"res": {"message": "Same subject is scheduled for the examination"}, "status": 400}
                return response
            if exam.exam_date == exam_date:
                if exam.start_time <= start_time <= exam.end_time:
                    response = {"res": {"message": "Slot is reserved for another exam"}, "status": 400}
                    return response
    return end_time


    # college_start_time = datetime.time(9, 0, 0)
    # college_end_time = datetime.time(17, 0, 0)
    # if index == len(exam_details):
    #     return "done"
    # subject_id = exam_details[index].get("subject_id")
    # subject_instance = Dropdowns.objects.filter(parent__value='subjects', parent__parent=year, id=subject_id).first()
    # if not subject_instance:
    #     response = {
    #         "res": {"message": f"Subject does not exists for {course.value} {department.value} year-{year.value}"},
    #         "status": 404}
    #     return response
    # exam_details[index]["subject_id"] = exam_details[index]["subject_instance"] = subject_instance
    # exam_date = exam_details[index].get("exam_date")
    # if not bool(re.match(r"\d{2}/\d{2}/\d{4}", exam_date)):
    #     response = {
    #         "res": {"message": "Incorrect format of exam date must be like \'dd/mm/yyyy\'"},
    #         "status": 400
    #     }
    #     return response
    # exam_date = datetime.datetime.strptime(exam_date, "%d/%m/%Y")
    # diff = exam_date + datetime.timedelta(weeks=4 * 6)
    # if exam_date > diff:
    #     response = {"res": {"message": "Can not schedule away 6 months from now"}, "status": 400}
    #     return response
    # exam_details[index]["exam_date"] = exam_date
    # exam_start_time = exam_details[index].get("start_time")
    # exam_details[index]["start_time"] = datetime.datetime.strptime(exam_start_time, "%H:%M:%S").time()
    # if not (college_start_time < exam_details[index]["start_time"] < college_end_time):
    #     response = {"res": {"message": "Examination can only be conducted in the academic hours"}, "status": 400}
    #     return response
    # exams = ExamSchedules.objects.filter(course=course, department=department,
    #                                      year=year, exam_status="2").exclude(status="3").order_by("exam_date")
    # print(exams)
    # for exam in exams:
    #     print(exam.examination_type)
    #     scheduled_examination_type = exam.examination_type.value
    #     scheduled_subject = exam.subject.value
    #     scheduled_date = exam.exam_date
    #     if exam_type.value != scheduled_examination_type:
    #         difference = exams.last().exam_date + datetime.timedelta(weeks=4)
    #         if not exam_date >= difference:
    #             response = {
    #                 "res": {"message": f"Can not schedule {exam_type.value} close to {scheduled_examination_type}"},
    #                 "status": 400}
    #             return response
    #     if scheduled_subject == subject_instance.value:
    #         response = {"res": {
    #             "message": f"You are scheduling examination of {subject_instance.value} which already exists and is pending"},
    #                     "status": 409}
    #         return response
    #     if (exam.start_time <= exam_details[index]["start_time"] <= exam.end_time) and exam_details[index][
    #         "exam_date"] == scheduled_date:
    #         response = {"res": {"message": "Slot is occupied"}, "status": 409}
    #         return response
    # check_schedule(course, department, year, exam_type, exam_details, index + 1)
