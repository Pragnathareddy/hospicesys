from os import stat
from django.urls import re_path as url
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
 

 
 
    path("conversations/",
         views.conversations, name="conversations"),
    path("addConversation/", views.addConversation, name="addConversation"),
    path("sendText/", views.sendText, name="sendText"),
    path("editProfileImage/", views.editProfileImage, name="editProfileImage"),
 

 
]
