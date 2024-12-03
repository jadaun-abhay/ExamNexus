from django.db import models
from django.db.models import Manager

from portal.models import BaseModel, User


# Create your models here.

class StudentInfo(BaseModel):
    student = models.ForeignKey(to= User, related_name="student_info", on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey("portal.Dropdowns", related_name="student_course", on_delete=models.SET_NULL, null=True)
    year = models.ForeignKey("portal.Dropdowns", related_name="student_year", on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey("portal.Dropdowns", related_name="student_department", on_delete=models.SET_NULL,
                                   null=True)
    section = models.ForeignKey("portal.Dropdowns", related_name="student_section", on_delete=models.SET_NULL,
                                null=True)

    objects = Manager()

    class Meta:
        db_table = "student_info"
