from django.shortcuts import render, redirect
import openai
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.forms import UserCreationForm
from .models import Room,Topic,Message
from .forms import RoomForm, UserForm









# Use the OpenAI API key 
openai.api_key = ('api key')

def analyze_essay(essay_text):
      
    # Use GPT-3 
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Determine if the following is inappropiate, mean or abusive; if it is, write the word True else write False: {essay_text}.",
        max_tokens=400,
        n=1,
        stop=None,
        temperature=0.1,
    )
    feedback = response["choices"][0]["text"].strip()
    return feedback
    
    









def loginPage(request):
    page = "login"
    if request.user.is_authenticated:
        return redirect("home")

    if request.method =="POST":
        username= request.POST.get("username").lower()
        password=request.POST.get("password")

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request,"User does not exist")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request,user)
            return redirect("home")
        else:
            messages.error(request,"Username OR password does not exist")

    context = {"page":page}
    return render(request,"base/login_register.html",context)

def logoutUser(request):
    logout(request)
    return redirect("home")

def registerPage(request):
    
    form = UserCreationForm()
    if request.method =="POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request,user)
            return redirect("home")
        else:
            messages.error(request,"An error occurred during regestration")

    return render(request,"base/login_register.html",{"form":form})

def home(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q)|
        Q(name__icontains=q)|
        Q(description__icontains=q)
        )
    topics = Topic.objects.all()
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    context = {"rooms": rooms,"topics":topics,"room_count":room_count,"room_messages":room_messages}
    return render(request,"base/home.html",context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    error_message = ""
    participants = room.participants.all()

    if request.method == "POST":
        message_body = request.POST.get("body")
        if analyze_essay(message_body) == "True":
            error_message = "This is a safe space. Try writing something nice:)"
        else:
            message = Message.objects.create(
                user=request.user,
                room=room,
                body=message_body
            )
            room.participants.add(request.user)
            return redirect("room", pk=room.id)

    context = {"room": room, "room_messages": room_messages, "error_message": error_message,"participants":participants}
    return render(request, "base/room.html", context)


def userProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {"user":user,"rooms":rooms,"room_messages":room_messages,"topics":topics}
    return render(request,"base/profile.html",context)




@login_required(login_url="login")
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method =="POST":
        topic_name = request.POST.get("topic")
        topic,created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get("name"),
            description=request.POST.get("description")
        )
        
        return redirect("home")

    context = {"form":form,"topics":topics}
    return render(request,"base/room_form.html",context)

@login_required(login_url='login')
def updateRoom(request,pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance = room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse("You are not allowed here")

    if request.method =="POST":
        topic_name=request.POST.get("topic")
        topic,created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get("name")
        room.topic = topic
        room.description = request.POST.get("description")
        room.save()
        return redirect("home")
    context ={"form":form,"topics":topics,"room":room}
    return render(request, "base/room_form.html",context)

@login_required(login_url='login')
def deleteRoom(request,pk):
    room = Room.objects.get(id=pk)
    if request.user != room.host:
        return HttpResponse("You are not allowed here")
    if request.method =="POST":
        room.delete()
        return redirect("home")
    return render(request, "base/delete.html",{"obj": room})


@login_required(login_url='login')
def deleteMessage(request,pk):
    message = Message.objects.get(id=pk)
    if request.user != message.user:
        return HttpResponse("You are not allowed here")
    if request.method =="POST":
        message.delete()
        return redirect("home")
    return render(request, "base/delete.html",{"obj": message})

@login_required(login_url="login")
def updateUser(request):
    user= request.user
    form = UserForm(instance=user)

    if request.method == "POST":
        form = UserForm(request.POST,instance=user)
        if form.is_valid():
            form.save()
            return redirect("user-profile",pk=user.id)


    return render(request,"base/update-user.html",{"form":form})

def topicsPage(request):
    topics = Topic.objects.filter()
    context = {"topics":topics}
    return render(request,"base/topics.html",context)