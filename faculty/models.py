from django.db import models
from django.db.models import Manager

from portal.models import BaseModel, User


# Create your models here.

class FacultyInfo(BaseModel):
    faculty = models.ForeignKey(User, on_delete= models.SET_NULL, related_name= "faculty_info", null= True)
    course = models.ForeignKey("portal.Dropdowns", related_name= "faculty_course", on_delete= models.SET_NULL, null= True)
    year = models.ForeignKey("portal.Dropdowns", related_name= "faculty_year", on_delete= models.SET_NULL, null= True)
    department = models.ForeignKey("portal.Dropdowns", related_name= "faculty_department", on_delete= models.SET_NULL, null= True)
    section = models.ForeignKey("portal.Dropdowns", related_name= "faculty_section", on_delete= models.SET_NULL, null= True)
    subject = models.ForeignKey("portal.Dropdowns", related_name= "faculty_subject", on_delete= models.SET_NULL, null= True)

    objects = Manager()

    class Meta:
        db_table = "faculty_info"

class ExamSchedule(BaseModel):
    pass