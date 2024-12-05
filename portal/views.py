import datetime
import json
import re

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse

from portal.functions import check_role, get_course_duration, get_year_instance, get_course_instance, \
    create_faculty_info_details, create_student_info_details, get_auth_table_data, get_faculty_info
from portal.models import Dropdowns, Roles, LeftPanel, User, RoleMapping


# Create your views here.

def index(request):
    available_roles_list = list(Roles.objects.all().values_list("role", flat=True).exclude(status= "3"))
    flag = check_role(request.user, available_roles_list)
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
    if request.method == "GET":
        user_role_instance_list = request.user.roles.all().exclude(status= "3")
        print(user_role_instance_list[0])
        data = []
        for user_role_instance in user_role_instance_list:
            print(user_role_instance)
            my_dict = {}
            left_panel_parent_instances = LeftPanel.objects.filter(role= user_role_instance).exclude(status= "3")
            print(left_panel_parent_instances)
            if not left_panel_parent_instances.exists():
                res = {"message": "Left panel is not assigned for the requested role"}
                return JsonResponse(res, status= 404)
            my_dict.update({"role": user_role_instance.role, "left_panel": []})
            left_panel = []
            for parent_instance in left_panel_parent_instances:
                if not parent_instance.parent:
                    opt_dict = {"id": parent_instance.id, "parent_id": None, "title": parent_instance.title, "url": parent_instance.url,
                                "priority": parent_instance.priority, "icon": parent_instance.icon, "children": []}
                    children = list(parent_instance.child.all().values("id", "parent_id", "title", "url", "priority").exclude(status= "3"))
                    opt_dict["children"] = children
                    left_panel.append(opt_dict)
            my_dict["left_panel"].append(left_panel)
            data.append(my_dict)
        res = {"message": "success", "data": data}
        return JsonResponse(res, status= 200)
    elif request.method == "POST":
        pass
    elif request.method == "DELETE":
        pass
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 405)

def dashboard(request):
    available_roles_list = list(Roles.objects.all().values_list("role", flat=True).exclude(status="3"))
    flag = check_role(request.user, available_roles_list)
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
    if not request.method == "GET":
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 405)
    user_roles = list(request.user.roles.all().exclude(status= "3").values_list("role", flat= True))
    if "admin" in user_roles:
        course_base_instance = Dropdowns.objects.filter(value= "courses").exclude(status= "3").first()
        if not course_base_instance:
            courses = 0
        else:
            courses = len(course_base_instance.child.all().values_list("value", flat= True).exclude(status= "3"))
        employees = len(User.objects.all().exclude(status= "3").exclude(roles__role__in= ['admin', 'student']))
        students = len(User.objects.all().filter(roles__role= "student").exclude(status= "3"))
        res = {"message": "success", "roles": list(request.user.roles.all().exclude(status= "3").values_list("role")), "data": [{"courses": courses, "employees": employees, "students": students}]}
        return JsonResponse(res, status= 200)
    elif "coe" in user_roles:
        course_base_instance = Dropdowns.objects.filter(value="courses").exclude(status="3").first()
        if not course_base_instance:
            courses = 0
        else:
            courses = len(course_base_instance.child.all().values_list("value", flat=True).exclude(status="3"))
        students = len(User.objects.all().filter(roles__role="student").exclude(status="3"))
        res = {"message": "success", "roles": list(request.user.roles.all().exclude(status="3").values_list("role")),
               "data": [{"courses": courses, "students": students}]}
        return JsonResponse(res, status=200)
    elif "faculty" in user_roles:

        res = {"message": "success"}
        return JsonResponse(res, status= 200)

def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        if not (email or password):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
        if not bool(re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
            res = {"message" : "Email is invalid"}
            return JsonResponse(res, status= 400)
        elif not bool(re.match(r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$", password)):
            res = {"message" : "Password is invalid"}
            return JsonResponse(res, status= 400)
        user_instance = User.objects.filter(email= email).exclude(status= "3").first()
        if not user_instance:
            res = {"message": "Email is not registered"}
            return JsonResponse(res, status= 400)
        user_instance = authenticate(email= email, password= password)
        if user_instance:
            login(request, user_instance)
            roles_list = list(request.user.roles.all().values_list("role", flat= True).exclude(status= "3"))
            res = {"message": "Login is successful !!!", "roles": roles_list}
            return JsonResponse(res, status= 200)
        else:
            res = {"message": "Incorrect password"}
            return JsonResponse(res, status= 400)
    elif request.method == "GET":
        if request.user.is_authenticated:
            roles = list(request.user.roles.all().values_list("role", flat=True))
            res = {"message": "Login is successful !!!", "roles": roles}
            return JsonResponse(res, status=200)
        else:
            res = {"message": "Login is required !!!"}
            return JsonResponse(res, status=401)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 405)

def logout_user(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            logout(request)
            res = {"message" : "Logout is successful"}
            return JsonResponse(res, status= 200)
        else:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status= 401)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status= 405)

def dropdowns(request):
    flag = check_role(request.user, ["admin", "coe"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
    if request.method == "POST":
        data = json.loads(request.body)
        parent_id = data.get("pid")
        course_duration = None
        if not parent_id:
            course_duration = data.get("duration")
            if not course_duration:
                res = {"message": "course_duration is required to be specified while creating new course"}
                return JsonResponse(res, status= 400)
            elif course_duration <= 0:
                res = {"message": "Invalid value for course_duration"}
                return JsonResponse(res, status= 400)
        value = data.get("value")
        if not value:
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)

        parent_instance = Dropdowns.objects.filter(id= parent_id).exclude(status= "3")
        print(parent_instance)
        if parent_instance.exists():
            parent_instance = parent_instance.first()
        if not parent_id and course_duration:
            base_instance = Dropdowns.objects.filter(value= "courses").exclude(status= "3")
            if base_instance.exists():
                base_instance = base_instance.first()
            else:
                base_instance = Dropdowns.objects.create(value= "courses", status= 1)
            new_course_instance = base_instance.child.filter(value= value).exclude(status= "3")
            if new_course_instance.exists():
                res = {"message": "Course already exists"}
                return JsonResponse(res, status= 409)
            else:
                new_course_instance = base_instance.child.create(value= value, status= "1")
                new_course_instance.child.create(value= course_duration, status= "1")
                res = {"message": "Course has been added"}
                return JsonResponse(res, status= 201)
        elif parent_instance.parent.value == "courses":
            duration = int(parent_instance.child.first().value)
            department_instance = parent_instance.child.filter(value= value).exclude(status= "3").first()
            if department_instance:
                res = {"message": "Department already exists"}
                return JsonResponse(res, status= 409)
            department_instance = parent_instance.child.create(value= value, status= "1")
            for year in range(1, duration + 1):
                year_instance = department_instance.child.create(value= f"{year}", status= "1")
                year_instance.child.create(value= "subjects", status= "1")
            res = {"message": "Department has been added"}
            return JsonResponse(res, status= 201)
        elif isinstance(value, list):
            subject_base_instance = parent_instance.child.filter(value= "subjects").first()
            for subject in value:
                if subject_base_instance.child.filter(value= subject).exclude(status= "3").exists():
                    res = {"message": f"Subject already exists"}
                    return JsonResponse(res, status= 409)
                subject_base_instance.child.create(value= subject, status= "1")
            res = {"message": "Subject has been added"}
            return JsonResponse(res, status= 201)
        child = parent_instance.child.filter(value= value).exclude(status= "3")
        if child.exists():
            res = {"message": "Resource already exists"}
            return JsonResponse(res, status= 409)
        parent_instance.child.create(value= value, status= "1")
        res = {"message": "Resource is created successfully"}
        return JsonResponse(res, status= 201)
    elif request.method == "GET":
        parent_id = request.GET.get("pid")
        parent_instance = Dropdowns.objects.filter(id= parent_id).exclude(status= "3")
        if not parent_instance.exists():
            res = {"message": "No parent exists"}
            return JsonResponse(res, status= 404)
        parent_instance = parent_instance.first()
        if parent_instance.parent.value == "courses":
            children = parent_instance.child.all()[1:].values("id", "parent_id", "value")
            print(list(children))
        elif parent_instance.child.filter(value= "subjects").exclude(status= "3").exists():
            res = {"message": "success", "sections": [], "subjects": []}
            section = []
            section_info = list(parent_instance.child.all()[1:].values("id", "parent_id", "value"))
            section.append(section_info)
            subjects_base_instance = parent_instance.child.filter(value= "subjects").exclude(status= "3").first()
            subjects = list(subjects_base_instance.child.all().values("id", "parent_id", "value").exclude(status= "3"))
            res["sections"] = section_info
            res["subjects"] = subjects
            return JsonResponse(res, status= 200)
        else:
            children = parent_instance.child.all().values("id", "parent_id", "value")
        res = {"message": "success", "data": list(children)}
        return JsonResponse(res, status= 200)
    elif request.method == "PATCH":
        pass
    elif request.method == "DELETE":
        pass
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 409)

def get_courses_list(request):
    flag = check_role(request.user, ["admin", "coe"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
    if request.method == "GET":
        course_base_instance = Dropdowns.objects.filter(value= "courses").exclude(status= "3").first()
        if not course_base_instance:
            res = {"message": "Currently, there are no courses"}
            return JsonResponse(res, status= 404)
        course_instance_list = course_base_instance.child.all().exclude(status= "3")
        if not course_instance_list.exists():
            res = {"message": "Currently, there are no courses"}
            return JsonResponse(res, status= 404)
        data = []
        for course_instance in course_instance_list:
            my_dict = {"course_id": course_instance.id, "course_name": course_instance.value, "duration": course_instance.child.first().value}
            data.append(my_dict)
        res = {"message": "success", "data": data}
        return JsonResponse(res, status= 200)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 405)

def get_genders_list(request):
    flag = check_role(request.user, ["admin"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
    if request.method == "GET":
        gender_list = list(Dropdowns.objects.filter(value= "gender", parent=None)[0].child.values("id", "value"))
        res = {"message": "success", "data": gender_list}
        return JsonResponse(res, status= 200)
    elif request.method == "POST":
        data = json.loads(request.body)
        new_gender = data.get("gender")
        parent = Dropdowns.objects.filter(value= "gender").exclude(status= "3").first()
        if parent.child.filter(value= new_gender).exclude(status= "3"):
            res = {"message": "Already exists"}
            return JsonResponse(res, status= 409)
        parent.child.create(value= new_gender, status= "1")
        res = {"message": "Gender is added successfully"}
        return JsonResponse(res, status= 201)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 405)

def registration(request):
    flag = check_role(request.user, ["admin"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
    if request.method == "POST":
        data = json.loads(request.body)
        reg_type = data.get("type")
        first_name = data.get("first_name")
        middle_name = data.get("middle_name")
        last_name = data.get("last_name")
        email = data.get("email")
        phone_number = data.get("phone_number")
        gender_id = data.get("gender_id")
        dob = data.get("dob")
        course_id = data.get("course_id")
        duration = get_course_duration(course_id)
        if isinstance(duration, dict):
            return JsonResponse(duration["res"], status= duration["status"])
        detail = data.get("detail")
        department_id = data.get("department_id")
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        if not (reg_type and first_name and email and phone_number and gender_id and dob and course_id
                 and department_id and detail and password and confirm_password):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
        for det in detail:
            year_id = det.get("year")
            year_instance = get_year_instance(course_id,department_id, year_id)
            if isinstance(year_instance, dict):
                return JsonResponse(year_instance["res"], status= year_instance["status"])
            det["year_id"] = det["year_instance"] = year_instance
            section = det.get("section")
            subject_id = det.get("subject")
            if reg_type == "faculty":
                subject_base_instance = year_instance.child.filter(value="subjects").exclude(status="3").first()
                subject_instance = subject_base_instance.child.filter(id= subject_id).exclude(status= "3").first()
                if not subject_instance:
                    res = {"message": f"Selected subject with id-{subject_id} is not available"}
                    return JsonResponse(res, status= 404)
                det["subject_id"] = det["subject_instance"] = subject_instance
            instance_list = []
            for section_id in section:
                section_instance = year_instance.child.filter(id= section_id).exclude(status= "3").first()
                if not section_instance:
                    res = {"message": "Selected section does not exist under given course, year, department"}
                    return JsonResponse(res, status= 404)
                instance_list.append(section_instance)
            det["section"] = det["section_instance_list"] = instance_list
        course_instance = get_course_instance(course_id)
        if isinstance(course_instance, dict):
            return JsonResponse(course_instance["res"], status= course_instance["status"])
        if not bool(re.match(r'^\d{2}/\d{2}/\d{4}$', dob)):
            res = {"message" : "Invalid form of dob. Required format = \'dd/mm/yyyy\'"}
            return JsonResponse(res, status= 400)
        dob = dob.split("/")
        dob = datetime.date(int(dob[2]), int(dob[1]), int(dob[0]))
        difference = datetime.date.today() - datetime.timedelta(days= 15*365)
        if dob > difference:
            res = {"message": "Not eligible for admission in college"}
            return JsonResponse(res, status= 400)
        if not bool(re.match(r'\b[a-z|A-Z]{2,25}', first_name)):
            res = {"message" : "First name is invalid"}
            return JsonResponse(res, status= 400)
        elif middle_name:
            first_name = first_name.capitalize()
            middle_name = middle_name.capitalize()
            if not bool(re.match(r'\b[a-z|A-Z]{2,25}', middle_name)):
                res = {"message" : "Middle name is invalid"}
                return JsonResponse(res, status= 400)
        if last_name:
            last_name = last_name.capitalize()
            if not bool(re.match(r'\b[a-z|A-Z]{2,25}', last_name)):
                res = {"message" : "Last name is invalid"}
                return JsonResponse(res, status= 400)
        else:
            last_name = ""
        if not bool(re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
            res = {"message" : "Email is not valid"}
            return JsonResponse(res, status= 400)
        elif not bool(re.match(r'(0|91)?[6-9][0-9]{9}', phone_number)):
            res = {"message" : "Phone number is not valid"}
            return JsonResponse(res, status= 400)
        gender_base_instance = Dropdowns.objects.filter(value= "gender").exclude(status= "3").first()
        if not gender_base_instance:
            res = {"message": "Genders are not defined by the server"}
            return JsonResponse(res, status= 404)
        gender_instance = gender_base_instance.child.filter(id= gender_id).exclude(status= "3").first()
        if not gender_instance:
            res = {"message": "Gender does not exists"}
            return JsonResponse(res, status= 404)
        user = User.objects.filter(email= email).exclude(status= "3")
        if user.exists():
            res = {"message": "User email already exists"}
            return JsonResponse(res, status= 409)
        if password == confirm_password:
            user_obj = User.objects.create_user(email= email, password= password, first_name= first_name, middle_name= middle_name, last_name= last_name, phone_number= phone_number, dob= dob, gender= gender_instance, status= "1")
            faculty_role = Roles.objects.get(role="Faculty")
            student_role = Roles.objects.get(role="Student")
            if reg_type == "faculty":
                RoleMapping.objects.create(user= user_obj, role= faculty_role, status= "1")
                response = create_faculty_info_details(course_id, department_id, detail, faculty_id= user_obj.id)
                if isinstance(response, dict):
                    return JsonResponse(response["res"], status= response["status"])
            elif reg_type == "student":
                RoleMapping.objects.create(user= user_obj, role= student_role, status= "1")
                response = create_student_info_details(course_id, department_id, detail, student_id= user_obj.id)
                if isinstance(response, dict):
                    return JsonResponse(response["res"], status= response["status"])
            else:
                res = {"message" : "Registration type is not specifically provided"}
                return JsonResponse(res, status= 400)
            res = {"message": "Registration is successful"}
            return JsonResponse(res, status=200)
        else:
            res = {"message": "Password is not matching"}
            return JsonResponse(res, status=400)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)

def records(request):
    flag = check_role(request.user, ["admin"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
    if request.method == "GET":
        choice = request.GET.get("choice")
        if choice == "student":
            student_info_list = []
            users_list = User.objects.filter(roles__role= "student").exclude(status= "3")
            for student in users_list:
                student_info = student.student_info.first()
                info = get_auth_table_data(student)
                student_info_dict = {"student_id": student_info.id, "course": student_info.course.value, "department": student_info.department.value, "year": student_info.year.value, "section": student_info.section.value}
                info["academic_info"] = student_info_dict
                student_info_list.append(info)
            res = {"message": "success", "data": student_info_list}
            return JsonResponse(res, status= 200)
        elif choice == "faculty":
            faculty_info_list = list()
            faculty_dict = coe_dict = hod_dict = dict()
            users_list = User.objects.all().exclude(status= "3").exclude(roles__role__in= ["student", "admin"])
            faculty_list = list()
            for faculty in users_list:
                coe_list = hod_list = list()
                faculty_info = faculty.faculty_info.all()
                roles = list(faculty.roles.all().values_list("role", flat= True))
                if "coe" in roles:
                    coe_dict = {"coe": []}
                    coe_info = get_auth_table_data(faculty)
                    coe_list.append(coe_info)
                    coe_dict["coe"] = coe_list
                    faculty_info_list.append(coe_dict)
                if "hod" == roles[0]:
                    hod_info = get_auth_table_data(faculty)
                    hod_info.update({"department": faculty_info.first().department.id})
                    hod_list.append(hod_info)
                    hod_dict.update({"hod":hod_list})
                    faculty_info_list.append(hod_dict)
                if "faculty" in roles:
                    faculty_dict = dict()
                    info = get_auth_table_data(faculty)
                    info["roles"] = roles
                    info["academic_info"] = get_faculty_info(faculty_info)
                    print(info)
                    faculty_list.append(info)
                    faculty_dict.update({"faculty": faculty_list})
            faculty_info_list.append(faculty_dict)
            res = {"message": "success", "data": faculty_info_list}
            return JsonResponse(res, status= 200)
        elif choice == "courses":
            course_base_instance = Dropdowns.objects.filter(value= "courses").exclude(status= "3").first()
            if not course_base_instance:
                res = {"message": "Currently there are no courses available"}
                return JsonResponse(res, status= 404)
            courses = course_base_instance.child.all().exclude(status= "3")
            data = list()
            for course in courses:
                department_list = list()
                course_id = course.id
                course_name = course.value
                duration = int(course.child.first().value)
                departments = course.child.all().exclude(status= "3")[1:]
                course_dict =  {"course_id": course_id, "course_name": course_name, "course_duration": duration, "departments": []}
                for department in departments:
                    year_list = list()
                    department_id = department.id
                    department_name = department.value
                    years = department.child.all().exclude(status= "3")
                    department_dict = {"department_id": department_id, "department_name": department_name, "years": []}
                    for year in years:
                        year_id = year.id
                        year_name = year.value
                        sections = list(year.child.all().exclude(status= "3")[1:].values_list("value", flat= True))
                        subject_base_instance = year.child.first()
                        subjects_list = list(subject_base_instance.child.all().exclude(status= "3").values_list("value", flat= True))
                        year_dict = {"year_id": year_id, "year_name": year_name, "sections": sections, "subjects": subjects_list}
                        year_list.append(year_dict)
                    department_dict["years"].append(year_list)
                    department_list.append(department_dict)
                course_dict["departments"].append(department_list)
                data.append(course_dict)
            res = {"message": "success", "data": data}
            return JsonResponse(res, status= 200)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 200)

def examination_types(request):
    flag = check_role(request.user,  ["admin", "coe"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
    if request.method == "GET":
        examinations = Dropdowns.objects.filter(parent__value= "exam_type").all().exclude(status= "3").values("id", "parent_id", "value")
        examinations = list(examinations)
        res = {"message": "success", "data": examinations}
        return JsonResponse(res, status= 200)
    elif request.method == "POST":
        data = json.loads(request.body)
        exam_name = data.get("exam_name")
        exam_duration = data.get("exam_duration")
        maximum_marks = data.get("maximum_marks")
        if not (exam_name and exam_duration and maximum_marks):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
        parent = Dropdowns.objects.filter(value= "exam_type").exclude(status= "3").first()
        if not parent:
            parent = Dropdowns.objects.create(value= "exam_type", status= "1")
        if parent.child.filter(value= exam_name).exclude(status= "3").exists():
            res = {"message": "Already exists"}
            return JsonResponse(res, status= 409)
        exam_type = parent.child.create(value= exam_name, status= "1")
        exam_type.child.create(value= exam_duration, status= "1")
        exam_type.child.create(value= maximum_marks, status= "1")
        res = {"message": "Examination type is successfully added"}
        return JsonResponse(res, status= 201)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 405)
