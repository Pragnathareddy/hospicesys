from typing import Text
from django.contrib import admin

from .models import   Conversation ,User, Text 

# Register your models here.
 
 
admin.site.register(Conversation)
admin.site.register(Text)
 
