from django.db import models
from django.db.models import Manager

from portal.models import BaseModel, User, Dropdowns


# Create your models here.

class FacultyInfo(BaseModel):
    faculty = models.ForeignKey(User, on_delete= models.SET_NULL, related_name= "faculty_info", null= True)
    course = models.ForeignKey(Dropdowns, related_name= "faculty_course", on_delete= models.SET_NULL, null= True)
    year = models.ForeignKey(Dropdowns, related_name= "faculty_year", on_delete= models.SET_NULL, null= True)
    department = models.ForeignKey(Dropdowns, related_name= "faculty_department", on_delete= models.SET_NULL, null= True)
    section = models.ForeignKey(Dropdowns, related_name= "faculty_section", on_delete= models.SET_NULL, null= True)
    subject = models.ForeignKey(Dropdowns, related_name= "faculty_subject", on_delete= models.SET_NULL, null= True)

    class Meta:
        db_table = "faculty_info"

class ExamSchedules(BaseModel):
    class ExamStatus(models.IntegerChoices):
        HELD = 1
        PENDING = 2

    course = models.ForeignKey(Dropdowns, on_delete= models.SET_NULL, related_name= "scheduled_course", null= True)
    department = models.ForeignKey(Dropdowns, on_delete= models.SET_NULL, related_name= "scheduled_department", null= True)
    year = models.ForeignKey(Dropdowns, on_delete= models.SET_NULL, related_name= "scheduled_year", null= True)
    examination = models.ForeignKey(Dropdowns, on_delete= models.SET_NULL, related_name= "exam_type", null= True)
    subject = models.ForeignKey(Dropdowns, on_delete= models.SET_NULL, related_name= "scheduled_subject", null= True)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    exam_status = models.IntegerField(choices= ExamStatus)
    faculty = models.ForeignKey(User, on_delete= models.SET_NULL, related_name= "selected_name", null= True)

    class Meta:
        db_table = "exam_schedules"

class QuestionPaper(BaseModel):
    schedule = models.ForeignKey(ExamSchedules, on_delete= models.SET_NULL, related_name= "exam", null= True)
    value = models.TextField(blank= True)
    parent = models.ForeignKey("self", on_delete= models.SET_NULL, related_name= "child", null= True)
    faculty = models.ForeignKey(User, on_delete= models.SET_NULL, related_name= "faculty", null= True)
    selection_status= models.BooleanField(default= False)

    class Meta:
        db_table = "question_paper"
