from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser
from ckeditor.fields import RichTextField
from cloudinary.models import CloudinaryField

class User(AbstractUser):
    avatar = CloudinaryField(null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    student_class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, blank=True)

class BaseModel(models.Model):
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Department(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Class(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.department.name}"

class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Activity(BaseModel):
    title = models.CharField(max_length=255)
    description = RichTextField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    capacity = models.PositiveIntegerField()
    image = models.ImageField(upload_to='activities/%Y/%m/', null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('open', 'Open'), ('closed', 'Closed'), ('canceled', 'Canceled')],
        default='open'
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    tags = models.ManyToManyField('Tag')

    def __str__(self):
        return self.title

class Participation(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    proof = models.ImageField(upload_to='proofs/%Y/%m/', null=True, blank=True)

    class Meta:
        unique_together = ('student', 'activity')

class DisciplinePoint(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey('Activity', on_delete=models.CASCADE)
    criteria = models.CharField(max_length=255)
    score = models.FloatField()
    total_score = models.FloatField(default=0)

class Report(BaseModel):
    student = models.ForeignKey(User,  related_name='student_reports', on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    proof = models.ImageField(upload_to='reports/%Y/%m/')
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    handled_by = models.ForeignKey(User, related_name='handled_reports', null=True, blank=True, on_delete=models.SET_NULL)


class NewsFeed(BaseModel):
    activity = models.OneToOneField(Activity, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.activity.title

class Tag(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Interaction(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    newsfeed = models.ForeignKey(NewsFeed, on_delete=models.CASCADE)

    class Meta:
        abstract = True

class Like(Interaction):
    class Meta:
        unique_together = ('user', 'newsfeed')

class Comment(Interaction):
    content = models.CharField(max_length=255, null=False)

class Message(BaseModel):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User,related_name='received_messages', on_delete=models.CASCADE)
    content = RichTextField
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
