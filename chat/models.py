from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.fields import CharField
from django.db.models.fields.files import FileField, ImageField, ImageFieldFile
from django.utils.timezone import localtime, now
from datetime import datetime
import time
import os
import sys
from django.core.files.base import File
from django.core.files.uploadedfile import InMemoryUploadedFile


from django.contrib.auth.models import User
 
class Text(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sender")
    reciever = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reciever")
    date = models.DateTimeField(null=True)
    text = CharField(max_length=1000, default="")


class Conversation(models.Model):
    user1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user1")
    user2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user2")
    texts = models.ManyToManyField(Text, blank=True)
    lastInteracted = models.IntegerField(default=-2)
    readUser1 = models.BooleanField(default=True)
    readUser2 = models.BooleanField(default=True)


 