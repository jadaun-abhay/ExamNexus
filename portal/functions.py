from django.http import JsonResponse

from faculty.models import FacultyInfo
from portal.models import Dropdowns, User
from student.models import StudentInfo


def check_role(user_instance, allowed_roles_list):
    if not user_instance.is_authenticated:
        response = {"res": {"message": "Login is required !!!"}, "status": 401}
        return response
    user_roles_list = list(user_instance.roles.all().values_list("role", flat= True))
    if user_roles_list[0] in allowed_roles_list:
        return True
    for role in allowed_roles_list:
        if not role in user_roles_list:
            response = {"res": {"message": "You are not authorised"}, "status": 403}
            return response
    return True

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
    course_instance = get_course_instance(course_id)
    if isinstance(course_instance, dict):
        return course_instance
    department_instance = get_department_instance(course_id, department_id)
    if isinstance(department_instance, dict):
        return department_instance
    faculty_instance = User.objects.filter(id= faculty_id).exclude(status= "3").first()
    if not faculty_instance:
        response = {"res": {"message": "Faculty does not exists"}, "status": 404}
        return response
    for det in detail:
        year_instance = det.get("year_instance")
        year_id = year_instance.id
        section_instances = det.get("section_instance_list")
        subject_instance = det.get("subject_instance")
        for instance in section_instances:
            FacultyInfo.objects.create(course= course_instance, department= department_instance, faculty= faculty_instance, status= "1", year= year_instance, section= instance, subject= subject_instance)
    return "done"

def create_student_info_details(course_id, department_id, detail, student_id):
    course_instance = get_course_instance(course_id)
    if isinstance(course_instance, dict):
        return course_instance
    department_instance = get_department_instance(course_id, department_id)
    if isinstance(department_instance, dict):
        return department_instance
    student = User.objects.filter(id= student_id).exclude(status= "3").first()
    if not student:
        response = {"res": {"message": "Student does not exists"}, "status": 404}
        return response
    for det in detail:
        year_instance = det.get("year_instance")
        year_id = year_instance.id
        section_instance = det.get("section_instance_list")[0]
        StudentInfo.objects.create(course= course_instance, department= department_instance, student= student, year= year_instance, section= section_instance, status= "1")
    return "done"

def get_auth_table_data(user_obj):
    my_dict = {"full_name": user_obj.get_full_name(), "email": user_obj.email, "phone_number": user_obj.phone_number, "dob": user_obj.dob, "gender": user_obj.gender.value}
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
        subject = faculty_info.values_list("subject__value", flat= True).distinct()
        detail_dict = {"year": year_dict.get("year__value"), "section_list": section_list, "subject": subject[0]}
        detail.append(detail_dict)
        my_dict = {"course": course, "department": department, "detail": detail}
        if len(roles) > 1:
            my_dict["roles"] = roles
        return my_dict
