from django.db.models import Q
from django.template.context_processors import request

from faculty.models import FacultyInfo, ExamSchedules
from portal.models import Dropdowns, User, LeftPanel
from portal.models import BaseModel
from student.models import StudentInfo

Status = BaseModel.Status
ExamStatus = ExamSchedules.ExamStatus

def check_role(user, allowed_roles_list):
    if not user.is_authenticated:
        response = {"res": {"message": "Login is required !!!"}, "status": 401}
        return response
    user_roles_list = list(user.roles.values_list("role", flat= True).order_by("role"))
    user_roles_list = [role.lower() for role in user_roles_list]
    allowed_roles_list = sorted(allowed_roles_list)
    allowed_roles_list = [role.lower() for role in allowed_roles_list]
    intersection_set = set(user_roles_list).intersection(set(allowed_roles_list))
    if intersection_set:
        return True
    response = {"res": {"message": "You are not authorised !!!"}, "status": 403}
    return response

def get_admin_dashboard_data():
    courses = len(Dropdowns.objects.filter(parent__value= "courses").exclude(status= Status.DELETED))
    employees = len(User.objects.exclude(status= Status.DELETED).exclude(roles__role__in= ["admin", "student"]))
    students = len(User.objects.filter(roles__role= "student").exclude(status= Status.DELETED))
    data = [dict(courses= courses, employees= employees, students= students)]
    return dict

def get_coe_dashboard_data():
    courses = len(Dropdowns.objects.filter(parent__value="courses").exclude(status=Status.DELETED))
    employees = len(User.objects.exclude(status=Status.DELETED).exclude(roles__role__in=["admin", "student"]))
    students = len(User.objects.filter(roles__role="student").exclude(status=Status.DELETED))
    data = [dict(courses=courses, employees=employees, students=students)]
    return data

def get_hod_dashboard_data(user):
    hod_info = user.faculty_info.values("course__value", "department__value").exculde(status= Status.DELETED).first()
    course = hod_info.get("course__value")
    department = hod_info.get("department__value")
    employees = len(User.objects.filter(faculty_info__course__value= course, faculty_info__department__value= department).exclude(status= Status.DELETED).values("email").distinct())
    students = len(User.objects.filter(student_info__course__value= course, student_info__department__value= department).exclude(status= Status.DELETED).values("email").distict())
    data = [dict(course= course, department= department, employees= employees, students= students)]
    return data

def get_faculty_dashboard_data(user):
    faculty_info = user.faculty_info.values("course__value", "department__value", "year__value", "subject__value", "section__value").exclude(status= Status.DELETED)
    faculty_dashboard_info = list()
    section_data = list()
    for fac_info in faculty_info:
        total_students = len(User.objects.filter(roles__role= "student", student_info__course__value= fac_info.get("course__value"), student_info__department__value= fac_info.get("department__value"), student_info__year__value= fac_info.get("year__value"), student_info__section__value= fac_info.get("section__value")).exclude(status= Status.DELETED))
        section_info = dict(year= fac_info.get("year__value"), section= fac_info.get("section__value"), total_students= total_students)
        section_data.append(section_info)
        exams = list(ExamSchedules.objects.filter(course__value= fac_info.get("course__value"), department__value= fac_info.get("department__value"), year__value= fac_info.get("year__value"), subject__value= fac_info.get("subject__value"), exam_status= ExamStatus.PENDING).exclude(status= Status.DELETED).exclude(exam__faculty= user).values("id", "year__id", "year__value", "subject__id", "subject__value", "examination__id", "examination__value"))
        if exams:
            faculty_dashboard_info.append(exams)
    return dict(faculty_dashboard_info= faculty_dashboard_info, section_data= section_data)

def get_student_dashboard_data(user):
    pass

def get_course_instance(course_id):
    course_instance = Dropdowns.objects.filter(id= course_id).exclude(status= "3").first()
    if not course_instance:
        response = {"res": {"message": "Given course does not exists in our portal"}, "status": 404}
        return response
    if course_instance.parent.value != "courses":
        response = {"res": {"message": "Given id is not for course"}, "status": 400}
        return response
    return course_instance

def get_course_duration(course_id):
    course_instance = get_course_instance(course_id)
    if isinstance(course_instance, dict):
        return course_instance
    duration_instance = course_instance.child.first()
    if not duration_instance:
        response = {"res": {"message": "Duration is not defined for selected course"}, "status": 400}
        return response
    duration = duration_instance.value
    return duration

def get_department_instance(course_id, department_id):
    course_instance = get_course_instance(course_id)
    if isinstance(course_instance, dict):
        return course_instance
    department_instance = course_instance.child.filter(id= department_id).exclude(status= "3").first()
    if not department_instance:
        response = {"res": {"message": f"Department with id= {department_id} is not available under {course_instance.value}"}, "status": 404}
        return response
    return department_instance

def get_year_instance(course_id, department_id, year_id):
    course_instance = get_course_instance(course_id)
    if isinstance(course_instance, dict):
        return course_instance
    department_instance = get_department_instance(course_id, department_id)
    if isinstance(department_instance, dict):
        return department_instance
    year_instance = department_instance.child.filter(id= year_id).exclude(status= "3").first()
    if not year_instance:
        response = {"res": {"message": f"Year with id= {year_id} does not exists in {course_instance.value} {department_instance.value}"}, "status": 404}
        return response
    return year_instance

def get_section_instance(course_id,department_id, year_id, section_id):
    course_instance = get_course_instance(course_id)
    if isinstance(course_instance, dict):
        return course_instance
    department_instance = get_department_instance(course_id, department_id)
    if isinstance(department_instance, dict):
        return department_instance
    year_instance = get_year_instance(course_id, department_id, year_id)
    if isinstance(year_instance, dict):
        return year_instance
    section_instance = year_instance.child.filter(id= section_id).exclude(status= "3").first()
    if not section_instance:
        response = {"res": {"message": f"section with id= {section_id} is not defined for {course_instance.value} {department_instance.value} year-{year_instance.value}"}, "status": 404}
        return response
    return section_instance

def get_subject_instance(course_id, department_id, year_id, subject_id):
    year_instance = get_year_instance(course_id, department_id, year_id)
    if isinstance(year_instance, dict):
        return year_instance
    subject = Dropdowns.objects.filter(parent__value= "subjects", id= subject_id).first()
    if not subject:
        response = {"res": {"message": f"Subject does not exists in given course-department-year"}, "status": 404}
        return response
    else:
        return subject

def create_faculty_info_details(course_id, department_id, detail, faculty_id):
    faculty_instance = User.objects.filter(id= faculty_id).exclude(status= "3").first()
    if not faculty_instance:
        response = {"res": {"message": "Faculty does not exists"}, "status": 404}
        return response
    faculty_info_list = []
    [[faculty_info_list.append(FacultyInfo(course_id= course_id, department_id= department_id, faculty= faculty_instance, status= Status.CREATED, year_id= each.get("year_id"), section_id= section_id, subject_id= each.get("subject_id"))) for section_id in each.get("section")] for each in detail]
    FacultyInfo.objects.bulk_create(faculty_info_list)
    return "done"

def create_student_info_details(course_id, department_id, detail, student_id):
    student = User.objects.filter(id= student_id).exclude(status= "3").first()
    if not student:
        response = {"res": {"message": "Student does not exists"}, "status": 404}
        return response
    detail = detail[0]
    StudentInfo.objects.create(course_id= course_id, department_id= department_id, student= student_id, year_id= detail.get("year"), section= detail.get("section"), status= Status.CREATED)
    return "done"

def get_auth_table_data(user_obj):
    my_dict = {"first_name": user_obj.first_name, "middle_name": user_obj.middle_name, "last_name": user_obj.last_name, "email": user_obj.email, "phone_number": user_obj.phone_number, "dob": user_obj.dob, "gender": user_obj.gender.value}
    return my_dict

def get_faculty_info(faculty_info):
    my_dict = dict()
    course = faculty_info.first().course.value
    department = faculty_info.first().department.value
    roles = list(faculty_info.first().faculty.roles.all().values_list("role", flat= True).exclude(status= "3"))
    years_list = faculty_info.values("year__value", "year_id").distinct()
    detail = list()
    for year_dict in years_list:
        section_list = list(faculty_info.filter(year= year_dict.get("year_id")).values_list("section__value", flat= True))
        subject = faculty_info.filter(year= year_dict.get("year_id")).values_list("subject__value", flat= True).distinct()
        detail_dict = {"year": year_dict.get("year__value"), "section_list": section_list, "subject": subject[0]}
        detail.append(detail_dict)
        my_dict = {"course": course, "department": department, "detail": detail}
        if len(roles) > 1:
            my_dict["roles"] = roles
    return my_dict




