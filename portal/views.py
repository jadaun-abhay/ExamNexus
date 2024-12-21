import datetime
import json
import re

from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.http import JsonResponse

from faculty.models import FacultyInfo
from portal.functions import check_role, get_course_duration, get_year_instance, get_course_instance, \
    create_faculty_info_details, create_student_info_details, get_auth_table_data, get_faculty_info, \
    get_department_instance, get_admin_dashboard_data, get_coe_dashboard_data, get_hod_dashboard_data, \
    get_faculty_dashboard_data, get_student_dashboard_data
from portal.models import Dropdowns, Roles, LeftPanel, User, RoleMapping, BaseModel

Status = BaseModel.Status


# Create your views here.

def left_panel(request):
    available_roles_list = list(Roles.objects.all().values_list("role", flat=True).exclude(status= Status.DELETED))
    flag = check_role(request.user, available_roles_list)
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "GET":
        roles = request.user.get_roles()
        data = []
        for role in roles:
            left_panel__role = dict()
            left_panel_query_set = LeftPanel.objects.filter(role= role, parent= None).exclude(status= Status.DELETED).order_by("priority")
            if not left_panel_query_set.exists():
                res = {"message": 'Left panel is not defined for the role'}
                return JsonResponse(res, status=404)
            left_panel__role.update({"role": role.role, "left_panel": []})
            for each in left_panel_query_set:
                left_panel__role["left_panel"].append(each.get_all_children()[0])
            data.append(left_panel__role)
        res = {"message": "success", "data": data}
        return JsonResponse(res, status=200)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)

def dashboard(request):
    available_roles_list = list(Roles.objects.all().values_list("role", flat=True).exclude(status= Status.DELETED))
    flag = check_role(request.user, available_roles_list)
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "GET":
        user_roles = list(request.user.roles.exclude(status= Status.DELETED).values_list("role", flat= True).order_by("id"))
        if "admin" in user_roles:
            data = get_admin_dashboard_data()
            res = {"message": "success", "roles": list(request.user.roles.all().exclude(status= Status.DELETED).values_list("role", flat= True)), "data": data}
            return JsonResponse(res, status= 200)
        elif "coe" in user_roles:
            data = get_coe_dashboard_data()
            res = {"message": "success", "roles": list(
                request.user.roles.all().exclude(status=Status.DELETED).values_list("role", flat=True)), "data": data}
            return JsonResponse(res, status=200)
        elif "hod" in user_roles:
            data = get_hod_dashboard_data(request.user)
            res = {"message": "success", "roles": list(
                request.user.roles.all().exclude(status=Status.DELETED).values_list("role", flat=True)), "data": data}
            return JsonResponse(res, status=200)
        elif "faculty" in user_roles:
            data = get_faculty_dashboard_data(request.user)
            res = {"message": "success", "roles": list(
                request.user.roles.all().exclude(status=Status.DELETED).values_list("role", flat=True)), "data": data}
            return JsonResponse(res, status=200)
        elif "student" in user_roles:
            data = get_student_dashboard_data(request.user)
            res = {"message": "success", "roles": list(
                request.user.roles.all().exclude(status=Status.DELETED).values_list("role", flat=True)), "data": data}
            return JsonResponse(res, status=200)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 405)

def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        if not (email or password):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status=400)
        if not bool(re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
            res = {"message": "Email is invalid"}
            return JsonResponse(res, status=400)
        elif not bool(re.match(r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$", password)):
            res = {"message": "Password is invalid"}
            return JsonResponse(res, status=400)
        user_instance = User.objects.filter(email= email).exclude(status= Status.DELETED)
        if not user_instance.exists:
            res = {"message": "Email is not registered"}
            return JsonResponse(res, status=400)
        user_instance = authenticate(email=email, password=password)
        if user_instance:
            login(request, user_instance)
            roles_list = list(request.user.roles.values_list(
                "role", flat=True).exclude(status="3"))
            res = {"message": "Login is successful !!!", "roles": roles_list}
            return JsonResponse(res, status=200)
        else:
            res = {"message": "Incorrect password"}
            return JsonResponse(res, status=400)
    elif request.method == "GET":
        if request.user.is_authenticated:
            roles = list(request.user.roles.values_list("role", flat=True))
            res = {"message": "Login is successful !!!", "roles": roles}
            return JsonResponse(res, status=200)
        else:
            res = {"message": "Login is required !!!"}
            return JsonResponse(res, status=401)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)


def logout_user(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            logout(request)
            res = {"message": "Logout is successful"}
            return JsonResponse(res, status=200)
        else:
            res = {"message": "Login is required !!!"}
            return JsonResponse(res, status=401)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)


def dropdowns_customisation(request):
    flag = check_role(request.user, ["admin"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status= flag["status"])
    if request.method == "GET":
        value = request.GET.get("value")
        parent_id = request.GET.get("parent_id")
        if value == "duration" and parent_id:
            duration = Dropdowns.objects.filter(id= parent_id, parent__value= "course").exclude(status= Status.DELETED).values_list("child__value", flat= True).first()
            if not duration:
                res = {"message": "Duration is not defined for the given course_id"}
                return JsonResponse(res, status= 400)
            res = {"message": "success", "duration": int(duration)}
            return JsonResponse(res, status= 200)
        elif not value and parent_id:
            course = Dropdowns.objects.filter(id= parent_id, parent__value= "course").exclude(status= Status.DELETED).exists()
            if course:
                children = Dropdowns.objects.filter(parent_id= parent_id).exclude(status= Status.DELETED).values("id", "parent_id", "value")[1:]
            else:
                children = Dropdowns.objects.filter(parent_id= parent_id).exclude(status= Status.DELETED).values("id", "parent_id", "value")
            if not children.exists():
                res = {"message": "No children found for given parent_id"}
                return JsonResponse(res, status= 404)
            res = {"message": "success", "data": list(children)}
            return JsonResponse(res, status= 200)
        elif not parent_id and value == "parents":
            parents = Dropdowns.objects.filter(parent= None).exclude(status= Status.DELETED).values("id", "value")
            if not parents.exists():
                res = {"message": "No parents exists"}
                return JsonResponse(res, status= 409)
            res = {"message": "success", "data": list(parents)}
            return JsonResponse(res, status= 200)
        else:
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
    elif request.method == "POST":
        data = json.loads(request.body)
        parent_id = data.get("parent_id")
        value = data.get("value")
        if isinstance(value, dict) and not parent_id:
            course_head = Dropdowns.objects.filter(value= "course").first()
            print(value)
            print(Dropdowns.objects.filter(parent__value= "course", value= value.get("course")))
            course, status = Dropdowns.objects.filter(parent__value= "course", value= value.get("course")).exclude(status= Status.DELETED).get_or_create(defaults= {"value": value.get("course"), "parent": course_head, "status": Status.CREATED})
            if not status:
                res = {"message": "Course already exists"}
                return JsonResponse(res, status= 409)
            else:
                duration, status = Dropdowns.objects.filter(parent= course, value= value.get("duration")).exclude(status= Status.DELETED).get_or_create(defaults= {"value": value.get("duration"), "parent": course, "status": Status.CREATED})
            res = {"message": "Course is added"}
            return JsonResponse(res, status= 201)
        elif value and parent_id:
            course = Dropdowns.objects.filter(id= parent_id, parent__value= "course").prefetch_related("child")
            if course.exists():
                department, status = Dropdowns.objects.filter(parent_id= parent_id, value= value).exclude(status= Status.DELETED).get_or_create(defaults= {"value": value, "parent_id": parent_id, "status": Status.CREATED})
                if not status:
                    res = {"message": "Department already exists"}
                    return JsonResponse(res, status= 409)
                duration = int(course.first().child.first().value)
                year_list = [Dropdowns(value= f"{year}", status= Status.CREATED, parent= department) for year in range(1, duration+1)]
                Dropdowns.objects.bulk_create(year_list)
                res = {"message": "Department has been added"}
                return JsonResponse(res, status= 201)
            child, status = Dropdowns.objects.filter(parent_id= parent_id, value= value).exclude(status= Status.DELETED).get_or_create(defaults= {"value": value, "parent_id": parent_id, "status": Status.CREATED})
            if not status:
                res = {"message": "Resource already exists"}
                return JsonResponse(res, status= 409)
            else:
                res = {"message": "Resource has been created successfully"}
                return JsonResponse(res, status= 201)
        elif value and not parent_id:
            new_parent, status = Dropdowns.objects.filter(value= value, parent_id= parent_id).exclude(status= Status.DELETED).get_or_create(defaults= {"value": value, "parent_id": None, "status": Status.CREATED})
            if not status:
                res = {"message": "Parent already exists"}
                return JsonResponse(res, status= 409)
            res = {"message": "Parent has been added"}
            return JsonResponse(res, status= 201)
        else:
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
    elif request.method == "PATCH":
        data = json.loads(request.body)
        value = data.get("value")
        parent_id = data.get("parent_id")
        if not value:
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
        if parent_id:
            Dropdowns.objects.filter(value= value, parent_id= parent_id).exclude(status= Status.DELETED).update(value= value, status= Status.UPDATED, updation_timestamp= datetime.datetime.now())
        else:
            Dropdowns.objects.filter(value= value, parent_id= parent_id).exclude(status= Status.DELETED).update(value= value, status= Status.UPDATED, updattion_timestamp= datetime.datetime.now())
        res = {"message": "Updation has been applied"}
        return JsonResponse(res, status= 200)
    elif request.method == "DELETE":
        data = json.loads(request.body)
        id = data.get("id")
        Dropdowns.objects.filter(id= id).exclude(status= Status.DELETED).update(status= Status.DELETED, deletion_timestamp= datetime.datetime.now())
        res = {"message": "Resource has been deleted"}
        return JsonResponse(res, status= 200)

def dropdowns(request):
    roles = list(Roles.objects.exclude(role= "admin").values_list("role", flat= True))
    flag = check_role(request.user, roles)
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "GET":
        parent_id = request.GET.get("parent_id")
        value = request.GET.get("value")
        if not value and parent_id:
            course = Dropdowns.objects.filter(id=parent_id, parent__value="course").exclude(
                status=Status.DELETED).exists()
            if course:
                children = Dropdowns.objects.filter(parent_id=parent_id).exclude(status=Status.DELETED).values("id", "parent_id", "value")[1:]
            else:
                children = list(Dropdowns.objects.filter(parent_id= parent_id).exclude(status= Status.DELETED).values("id", "parent_id", "value"))
            if not children:
                res = {"message": "No children under the given parent_id"}
                return JsonResponse(res, status= 404)
            res = {"message": "success", "data": children}
            return JsonResponse(res, status= 200)
        elif not parent_id and value == "parents":
            parents = Dropdowns.objects.filter(parent= None).exclude(status= Status.DELETED).values("id", "parent_id", "value")
            if not parents.exists():
                res = {"message": "No parents exists"}
                return JsonResponse(res, status= 404)
            res = {"message": "success", "data": list(parents)}
            return JsonResponse(res, status= 200)
        elif value == "duration" and parent_id:
            duration = Dropdowns.objects.filter(parent__value= "course", id= parent_id).exclude(status= Status.DELETED).values_list("child__value", flat= True).first()
            if not duration:
                res = {"message": 'Duration is not defined for the given course'}
                return JsonResponse(res, status= 404)
            res = {"message": "success", "duration": int(duration)}
            return JsonResponse(res, status= 200)
        else:
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status= 405)


def registration(request):
    flag = check_role(request.user, ["admin"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
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
            return JsonResponse(duration["res"], status=duration["status"])
        detail = data.get("detail")
        department_id = data.get("department_id")
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        if not (reg_type and first_name and email and phone_number and gender_id and dob and course_id
                and department_id and detail and password and confirm_password):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status=400)
        course_instance = get_course_instance(course_id)
        if isinstance(course_instance, dict):
            return JsonResponse(course_instance["res"], status=course_instance["status"])
        for det in detail:
            year_id = det.get("year")
            year_instance = get_year_instance(
                course_id, department_id, year_id)
            if isinstance(year_instance, dict):
                return JsonResponse(year_instance["res"], status=year_instance["status"])
            det["year_id"] = det["year_instance"] = year_instance
            section = det.get("section")
            subject_id = det.get("subject")
            subject_instance = None
            if reg_type == "faculty":
                subject_base_instance = year_instance.child.filter(
                    value="subjects").exclude(status= Status.DELETED).first()
                subject_instance = subject_base_instance.child.filter(
                    id=subject_id).exclude(status= Status.DELETED).first()
                if not subject_instance:
                    res = {
                        "message": f"Selected subject with id-{subject_id} is not available"}
                    return JsonResponse(res, status=404)

                det["subject_id"] = det["subject_instance"] = subject_instance
            instance_list = []
            for section_id in section:
                section_instance = year_instance.child.filter(
                    id=section_id).exclude(status= Status.DELETED).first()
                if not section_instance:
                    res = {
                        "message": "Selected section does not exist under given course, year, department"}
                    return JsonResponse(res, status=404)
                fac_info = FacultyInfo.objects.filter(course=course_instance,
                                                      department=get_department_instance(
                                                          course_id, department_id),
                                                      year=year_instance, subject=subject_instance,
                                                      section=section_instance).exclude(status= Status.DELETED)
                if fac_info.exists():
                    res = {"message": "Another faculty is already assigned"}
                    return JsonResponse(res, status=409)
                instance_list.append(section_instance)
            det["section"] = det["section_instance_list"] = instance_list

        if not bool(re.match(r'^\d{2}/\d{2}/\d{4}$', dob)):
            res = {"message": "Invalid form of dob. Required format = \'dd/mm/yyyy\'"}
            return JsonResponse(res, status=400)
        dob = dob.split("/")
        dob = datetime.date(int(dob[2]), int(dob[1]), int(dob[0]))
        difference = datetime.date.today() - datetime.timedelta(days=15 * 365)
        if dob > difference:
            res = {"message": "Enjoy your childhood first !!!"}
            return JsonResponse(res, status=400)
        if not bool(re.match(r'\b[a-z|A-Z]{2,25}', first_name)):
            res = {"message": "First name is invalid"}
            return JsonResponse(res, status=400)
        elif middle_name:
            first_name = first_name.capitalize()
            middle_name = middle_name.capitalize()
            if not bool(re.match(r'\b[a-z|A-Z]{2,25}', middle_name)):
                res = {"message": "Middle name is invalid"}
                return JsonResponse(res, status=400)
        if last_name:
            last_name = last_name.capitalize()
            if not bool(re.match(r'\b[a-z|A-Z]{2,25}', last_name)):
                res = {"message": "Last name is invalid"}
                return JsonResponse(res, status=400)
        else:
            last_name = ""
        if not bool(re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
            res = {"message": "Email is not valid"}
            return JsonResponse(res, status=400)
        elif not bool(re.match(r'(0|91)?[6-9][0-9]{9}', phone_number)):
            res = {"message": "Phone number is not valid"}
            return JsonResponse(res, status=400)
        gender_base_instance = Dropdowns.objects.filter(
            value="gender").exclude(status="3").first()
        if not gender_base_instance:
            res = {"message": "Genders are not defined by the server"}
            return JsonResponse(res, status=404)
        gender_instance = gender_base_instance.child.filter(
            id=gender_id).exclude(status="3").first()
        if not gender_instance:
            res = {"message": "Gender does not exists"}
            return JsonResponse(res, status=404)
        user = User.objects.filter(email=email).exclude(status="3")
        if user.exists():
            res = {"message": "User email already exists"}
            return JsonResponse(res, status=409)
        if password == confirm_password:
            user_obj = User.objects.create_user(email=email, password=password, first_name=first_name,
                                                middle_name=middle_name, last_name=last_name, phone_number=phone_number,
                                                dob=dob, gender=gender_instance, status= Status.CREATED)
            faculty_role = Roles.objects.get(role="Faculty")
            student_role = Roles.objects.get(role="Student")
            if reg_type == "faculty":
                RoleMapping.objects.create(
                    user=user_obj, role=faculty_role, status= Status.CREATED)
                response = create_faculty_info_details(
                    course_id, department_id, detail, faculty_id=user_obj.id)
                if isinstance(response, dict):
                    return JsonResponse(response["res"], status=response["status"])
            elif reg_type == "student":
                RoleMapping.objects.create(
                    user=user_obj, role=student_role, status= Status.CREATED)
                response = create_student_info_details(
                    course_id, department_id, detail, student_id=user_obj.id)
                if isinstance(response, dict):
                    return JsonResponse(response["res"], status=response["status"])
            else:
                res = {"message": "Registration type is not specifically provided"}
                return JsonResponse(res, status=400)
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
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "GET":
        choice = request.GET.get("choice")
        if choice == "student":
            student_info_list = []
            users_list = User.objects.filter(
                roles__role="student").exclude(status= Status.DELETED)
            for student in users_list:
                student_info = student.student_info.first()
                info = get_auth_table_data(student)
                student_info_dict = {"student_id": student_info.id, "course": student_info.course.value,
                                     "department": student_info.department.value, "year": student_info.year.value,
                                     "section": student_info.section.value}
                info["academic_info"] = student_info_dict
                student_info_list.append(info)
            res = {"message": "success", "data": student_info_list}
            return JsonResponse(res, status=200)
        elif choice == "faculty":
            faculty_info_list = list()
            faculty_dict = coe_dict = hod_dict = dict()
            users_list = User.objects.all().exclude(status= Status.DELETED).exclude(
                roles__role__in=["student", "admin"])
            faculty_list = list()
            for faculty in users_list:
                coe_list = hod_list = list()
                faculty_info = faculty.faculty_info.all()
                roles = list(
                    faculty.roles.all().values_list("role", flat=True))
                if "coe" in roles:
                    coe_dict = {"coe": []}
                    coe_info = get_auth_table_data(faculty)
                    coe_list.append(coe_info)
                    coe_dict["coe"] = coe_list
                    faculty_info_list.append(coe_dict)
                if "hod" == roles[0]:
                    hod_info = get_auth_table_data(faculty)
                    print(hod_info)
                    hod_info.update({"course": faculty_info.first(
                    ).course.id, "department": faculty_info.first().department.id})
                    hod_list.append(hod_info)
                    hod_dict.update({"hod": hod_list})
                    faculty_info_list.append(hod_dict)
                if "faculty" in roles:
                    faculty_dict = dict()
                    info = get_auth_table_data(faculty)
                    info["roles"] = roles
                    info["academic_info"] = get_faculty_info(faculty_info)
                    print()
                    faculty_list.append(info)
                    faculty_dict.update({"faculty": faculty_list})
            faculty_info_list.append(faculty_dict)
            res = {"message": "success", "data": faculty_info_list}
            return JsonResponse(res, status=200)
        elif choice == "courses":
            course_base_instance = Dropdowns.objects.filter(
                value="courses").exclude(status= Status.DELETED).first()
            if not course_base_instance:
                res = {"message": "Currently there are no courses available"}
                return JsonResponse(res, status=404)
            courses = course_base_instance.child.all().exclude(status= Status.DELETED)
            data = list()
            for course in courses:
                department_list = list()
                course_id = course.id
                course_name = course.value
                duration = int(course.child.first().value)
                departments = course.child.all().exclude(status= Status.DELETED)[1:]
                course_dict = {"course_id": course_id, "course_name": course_name, "course_duration": duration,
                               "departments": []}
                for department in departments:
                    year_list = list()
                    department_id = department.id
                    department_name = department.value
                    years = department.child.all().exclude(status= Status.DELETED)
                    department_dict = {"department_id": department_id,
                                       "department_name": department_name, "years": []}
                    for year in years:
                        year_id = year.id
                        year_name = year.value
                        sections = list(year.child.all().exclude(status= Status.DELETED)[
                                        1:].values_list("value", flat=True))
                        subject_base_instance = year.child.first()
                        subjects_list = list(
                            subject_base_instance.child.all().exclude(status= Status.DELETED).values_list("value", flat=True))
                        year_dict = {"year_id": year_id, "year_name": year_name, "sections": sections,
                                     "subjects": subjects_list}
                        year_list.append(year_dict)
                    department_dict["years"].append(year_list)
                    department_list.append(department_dict)
                course_dict["departments"].append(department_list)
                data.append(course_dict)
            res = {"message": "success", "data": data}
            return JsonResponse(res, status=200)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=200)


def examination_types(request):
    flag = check_role(request.user, ["admin", "coe", "hod"])
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    if request.method == "GET":
        examinations = Dropdowns.objects.filter(parent__value="examinations").all().exclude(status= Status.DELETED).values("id", "parent_id", "value")
        if not examinations.exists():
            res = {"message": "Admin has not defined exam_names yet."}
            return JsonResponse(res, status= 404)
        examinations = list(examinations)
        res = {"message": "success", "data": examinations}
        return JsonResponse(res, status=200)
    elif request.method == "POST":
        data = json.loads(request.body)
        exam_name = data.get("exam_name")
        exam_duration = data.get("exam_duration")
        maximum_marks = data.get("maximum_marks")
        total_questions = data.get("questions")
        if not (exam_name and exam_duration and maximum_marks and total_questions):
            res = {"message": "Information given is not sufficient"}
            return JsonResponse(res, status= 400)
        parent = Dropdowns.objects.filter(
            value="exam_type").exclude(status= Status.DELETED).first()
        if not parent:
            parent = Dropdowns.objects.create(value="exam_type", status="1")
        if parent.child.filter(value=exam_name).exclude(status= Status.DELETED).exists():
            res = {"message": "Already exists"}
            return JsonResponse(res, status=409)
        exam_type = parent.child.create(value=exam_name, status= Status.CREATED)
        exam_type.child.create(value=exam_duration, status= Status.CREATED)
        exam_type.child.create(value=maximum_marks, status= Status.CREATED)
        exam_type.child.create(value=total_questions, status= Status.CREATED)
        res = {"message": "Examination type is successfully added"}
        return JsonResponse(res, status=201)
    else:
        res = {"message": "Invalid request method"}
        return JsonResponse(res, status=405)


def profile(request):
    available_roles_list = list(Roles.objects.all().values_list("role", flat=True).exclude(status= Status.DELETED))
    flag = check_role(request.user, available_roles_list)
    if isinstance(flag, dict):
        return JsonResponse(flag["res"], status=flag["status"])
    user_roles = list(request.user.roles.exclude(status= Status.DELETED).values_list("role", flat=True).order_by("id"))
    if "admin" in user_roles:
        admin_info = list(User.objects.filter(email= request.user.email).exclude(status= Status.DELETED).values("id", "first_name", "middle_name", "last_name", "email", "phone_number", "dob", "gender__value"))
        res = {"message": "success", "data": admin_info}
        return JsonResponse(res, status= 200)
    elif "coe" in user_roles:
        coe_info = list(User.objects.filter(email= request.user.email).exclude(status= Status.DELETED).values("id", "first_name", "middle_name", "last_name", "email", "phone_number", "dob", "gender__value"))
        res = {"message": "success", "data": coe_info}
        return JsonResponse(res, status= 200)
    elif "hod" in user_roles:
        hod_info = list(User.objects.filter(email= request.user.email).exclude(status= Status.DELETED).values("id", "first_name", "middle_name", "last_name", "email", "phone_number", "dob", "gender__value", "faculty_info__course__value", "faculty_info__department__value"))
        res = {"message": "success", "data": hod_info}
        return JsonResponse(res, status= 200)
    elif "faculty" in user_roles:
        faculty_info = list(User.objects.filter(email= request.user.email).exclude(status= Status.DELETED).values("id", "first_name", "middle_name", "last_name", "email", "phone_number", "dob", "gender__value", "faculty_info__course__value", "faculty_info__department__value", "faculty_info__year__value", "faculty_info__section__value", "faculty_info__subject__value"))
        res = {"message": "success", "data": faculty_info}
        return JsonResponse(res, status= 200)
    elif "student" in user_roles:
        student_info = list(User.objects.filter(email= request.user.email).exclude(status= Status.DELETED).values("id", "first_name", "middle_name", "last_name", "email", "phone_number", "dob", "gender__value", "student_info__course__value", "student_info__department__value", "student_info__year__value", "student_info__section__value"))
        res = {"message": "success", "data": student_info}
        return JsonResponse(res, status= 200)
