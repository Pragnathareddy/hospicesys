from datetime import date, datetime, time
import chat
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import AllowAllUsersModelBackend
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import render
from django.urls import reverse
import json
from .models import  Conversation,   User,  Text
from appointments.models import Doctor
from django.shortcuts import redirect
import uuid
import sys
from django.db.models import Q
import time
from django.core.mail import send_mail
from django.core import serializers
import boto3
import os

 

def conversations(request):
    if request.user.is_authenticated:
        convos = (Conversation.objects.filter(
            Q(user1=request.user) | Q(user2=request.user))).order_by('-lastInteracted')

        print(convos)
        return render(request, "chat/conversations.html", {
            "students": User.objects.all().exclude(id=request.user.id),
            "conversations": convos
        })
 
 
def editProfileImage(request):
    if request.method == "POST":
        user = request.user
        # print(request.__dict__, file=sys.stderr)
        user.profile_pic.delete()
        user.profile_pic = request.FILES.get('img')
        user.save()
    next = request.POST.get('next', '/')
    return HttpResponseRedirect(next)


def addConversation(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data["username"]
        to = User.objects.get(username=username)

        if not Conversation.objects.filter(user1=request.user, user2=to).exists() and not Conversation.objects.filter(user1=to, user2=request.user).exists():
            conversation = Conversation()
            conversation.user1 = request.user
            conversation.user2 = to
            conversation.lastInteracted = int(time.time())
            conversation.save()

    if request.method == "DELETE":
        data = json.loads(request.body)
        id = data["id"]
        Conversation.objects.get(id=id).delete()

    return HttpResponse()


def sendText(request):
    if request.method == "POST":
        data = json.loads(request.body)

        id = data["id"]
        sender = request.user
        text = data["text"]
        reciever = None
        conversation = Conversation.objects.get(id=id)
        if sender == conversation.user1:
            reciever = conversation.user2
        else:
            reciever = conversation.user1

        newText = Text()
        newText.sender = sender
        newText.reciever = reciever
        newText.date = datetime.now()
        newText.text = text

        newText.save()
        conversation.texts.add(newText)
        conversation.lastInteracted = int(time.time())
        conversation.save()

        if conversation.user1 == request.user:
            conversation.readUser2 = False
            conversation.readUser1 = True
        elif conversation.user2 == request.user:
            conversation.readUser1 = False
            conversation.readUser2 = True

        conversation.save()

    return HttpResponse()

 