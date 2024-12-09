from django.contrib.auth.models import UserManager, AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

class BaseModel(models.Model):
    STATUS_CHOICES = {
        "1": "created",
        "2": "updated",
        "3": "deleted",
    }
    status = models.CharField(max_length= 2, choices= STATUS_CHOICES)
    creation_timestamp = models.DateTimeField(auto_now_add= True)
    updation_timestamp = models.DateTimeField(auto_now= True)
    deletion_timestamp = models.DateTimeField(null= True)

    class Meta:
        abstract = True

class Dropdowns(BaseModel):
    value = models.TextField()
    parent = models.ForeignKey("self", on_delete= models.SET_NULL, null= True, related_name= "child")

    class Meta:
        db_table = "dropdowns"

class Roles(BaseModel):
    role = models.TextField()

    class Meta:
        db_table = "roles"

class CustomUserManager(UserManager):
    def create_user(self, email=None, password=None, **kwargs):
        if not email:
            raise ValueError("Must be a valid E-Mail")

        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **kwargs):

        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_active', True)

        return self.create_user(email=email, password=password, **kwargs)

class User(AbstractUser, BaseModel):
    username = None
    email = models.CharField(max_length= 60, unique= True)
    middle_name = models.CharField(max_length= 30, null= True, blank= True)
    phone_number = models.CharField(max_length= 10)
    dob = models.DateField()
    gender = models.ForeignKey(Dropdowns, on_delete= models.SET_NULL, null= True, related_name= "gender")
    roles = models.ManyToManyField(Roles, through= "RoleMapping")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()


    def get_full_name(self):
        full_name = self.first_name
        m_name = str(self.middle_name)
        if m_name:
            full_name += " " + m_name
        l_name = self.last_name
        if l_name:
            full_name += " " + l_name
        return full_name

    class Meta:
        db_table = "portal_users"

class RoleMapping(BaseModel):
    user = models.ForeignKey(User, on_delete= models.SET_NULL, null= True)
    role = models.ForeignKey(Roles, on_delete= models.SET_NULL, null= True)

    class Meta:
        db_table = "role_mapping"

class LeftPanel(BaseModel):
    role = models.ForeignKey(Roles, on_delete= models.SET_NULL, null= True)
    title = models.TextField()
    url = models.TextField(null= True)
    priority = models.SmallIntegerField()
    icon = models.TextField(null= True)
    parent = models.ForeignKey("self", on_delete= models.SET_NULL, null= True, related_name= "child")

    class Meta:
        db_table = "left_panel"

