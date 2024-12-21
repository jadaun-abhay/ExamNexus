from django.contrib.auth.models import UserManager, AbstractUser
from django.db import models

# Create your models here.

class BaseModel(models.Model):
    class Status(models.IntegerChoices):
        CREATED = 1
        UPDATED = 2
        DELETED = 3

    status = models.IntegerField(choices= Status)
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

    def get_roles(self):
        user_roles = list(self.roles.all().exclude(status= BaseModel.Status.DELETED))
        return user_roles

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

    def get_all_children(self, include_self=True):
        r = []
        if include_self:
            parent = self.parent
            if not parent:
                parent_id = None
            else:
                parent_id = parent.id
            my_dict = dict(id= self.id, parent_id= parent_id, title= self.title, url= self.url, priority= self.priority, icon= self.icon, children= list())
            r.append(my_dict)
        for c in LeftPanel.objects.filter(parent=self).exclude(status= BaseModel.Status.DELETED).order_by("priority"):
            _r = c.get_all_children(include_self=True)
            if 0 < len(_r):
                if r:
                    r[-1]["children"].append(_r[0])
        return r

    def get_all_parents(self, include_self= True):
        result = list()
        if include_self:
            my_dict = dict(id = self.id, title= self.title, url= self.url, priority= self.priority, icon= self.icon, parent= list())
            result.append(my_dict)
        for p in LeftPanel.objects.filter(child= self).exclude(status= BaseModel.Status.DELETED):
            _r = p.get_all_parents(include_self= True)
            if 0 < len(_r):
                if result:
                    result[-1]["parent"].append(_r[0])
        return result

    class Meta:
        db_table = "left_panel"

