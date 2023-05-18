from django.db import models
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, BaseUserManager
from datetime import datetime
from django.db.models import Count
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.IntegerField(default=3)
    is_cpa = models.BooleanField(default=False)
    is_legal = models.BooleanField(default=False)
    is_hr = models.BooleanField(default=False)
    
class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(default="", max_length=15)
    name = models.CharField(default="", max_length=100)
    page = models.IntegerField()
    file = models.FileField(upload_to='')
    description = models.CharField(default="", max_length=300)
    created_at = models.DateTimeField(default=datetime.now)

    @staticmethod
    def get_counts():
        count_by_type = Document.objects.values(
            'category').annotate(count=Count('category'))
        total_count = Document.objects.count()
        return count_by_type, total_count


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.CharField(default="", max_length=100)
    type = models.CharField(default=1, max_length=2)
    created_at = models.DateTimeField(default=datetime.now)


class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_category = models.CharField(default="", max_length=50)
    name = models.CharField(default="", max_length=50)
    created_at = models.DateTimeField(default=datetime.now)


class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_category = models.CharField(default="", max_length=50)
    chat_history = models.CharField(default="", max_length=50)
    message = models.CharField(default="", max_length=500)
    response = models.CharField(default="", max_length=500)
    sent = models.DateTimeField(default=datetime.now)
    received = models.DateTimeField(default=datetime.now)
