from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
from .models import assign,complaints
from datetime import datetime
from assetsData.models import *
import json

def employeeHome(request):
    return render(request, "employee/dashboard.html", context={'data':assign.objects.filter(user = request.user, pickedUp = True)})


def pickup(request):
    items = assign.objects.filter(user=request.user, pickedUp=False)
    return render(request, "employee/pickup.html", context={"data": items})


# Work After Initial data population
def pickup_action(request, id):
    if request.method == "POST":
        # Process sending mail here!
        if id != "all":
            item = assign.objects.get(id=int(id))
            item.assigned_to_pickup = request.POST.get("pickupPerson")
            item.assigned_person = True
            date = request.POST.get("pickupDate").split("/")
            item.pickupDate = datetime.strptime("-".join([date[2], date[0], date[1]]),"%Y-%m-%d")
            item.save()
        else:
            items = assign.objects.filter(user=request.user,assigned_person = False)
            for item in items:
                item.assigned_to_pickup = request.POST.get("pickupPerson")
                item.assigned_person = True
                date = request.POST.get("pickupDate").split("/")
                item.pickupDate = datetime.strptime("-".join([date[2], date[0], date[1]]),"%Y-%m-%d")
                item.save()
        return HttpResponse("<script>parent.location.reload();</script>")
    item_type = None
    if id == "all":
        data = None
        item_type = False
    else:
        data = assign.objects.get(id=int(id))
        item_type = True
    return render(
        request,
        "employee/pickupAction.html",
        context={"data": data, "item_type": item_type},
    )

#Editing of the pickup date and person
def pickup_action_edit(request, id):
    if request.method == "POST":
        # Process sending mail here!
        if id != "all":
            item = assign.objects.get(id=int(id))
            item.assigned_to_pickup = request.POST.get("pickupPerson")
            item.assigned_person = True
            date = request.POST.get("pickupDate").split("/")
            item.pickupDate = datetime.strptime("-".join([date[2], date[0], date[1]]),"%Y-%m-%d")
            item.save()

        return HttpResponse("<script>parent.location.reload();</script>")
    try:
        data = assign.objects.get(id=int(id))
        item_type = True
    except:
        return HttpResponse("LOL, you've lost")

    return render(
        request,
        "employee/pickupAction.html",
        context={"data": data, "item_type": item_type},
    )


def new_complaint(request):
    if request.method == "POST":
        print(request.POST)
        complaints.objects.create(user = request.user, complaint_item = assign.objects.get(id = request.POST.get('item')), description = request.POST.get("comment"), complaint_status = "SUBMITTED")
        return redirect("complaint status")
    
    # Send my items from the database to the template for selection of the item from the select tag!
    items = assign.objects.filter(user = request.user)
    return render(request, "employee/complaint_new.html",context={"data":items})


def complaint_status(request):
    data = complaints.objects.filter(user = request.user).order_by('-id')
    return render(request, "employee/complaint_status.html", context={"data":data})


def profile_dash(request):
    data = Building_Name.objects.all()
    prof = profile.objects.get(user = request.user)
    return render(request,"employee/profile.html", context={"data":data, 'prof':prof})

def getfloors(request):
    if request.method == 'POST':
        a = json.loads(request.body.decode('utf-8'))['data']
        locations = Location_Description.objects.filter(building = Building_Name.objects.get(code = a))
        floors = set()
        res = []
        for location in locations:
            floors.add(location.floor.code)
        for i in floors:
            res.append({i:Floor_Code.objects.get(code = i).name})
        return JsonResponse({"data":res})