from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
from .models import assign,complaints,Ledger
from datetime import datetime
from assetsData.models import *
import json
from .roles import check_role
from .models import *
from datetime import date
from django.db import transaction

@check_role()
def employeeHome(request):
    hod = False
    if profile.objects.get(user = request.user).designation.designation_id == 'HOD':
        hod = True
    return render(request, "employee/dashboard.html", context={'data':assign.objects.filter(user = request.user, pickedUp = True, item__item_type = "FIXED ASSET"), 'hod':hod})

@check_role(redirect_to="/")
def pickup(request):
    hod = False
    if profile.objects.get(user = request.user).designation.designation_id == 'HOD':
        hod = True
    items = assign.objects.filter(user=request.user, pickedUp=False)
    return render(request, "employee/pickup.html", context={"data": items, 'hod':hod})


# Work After Initial data population
@check_role(redirect_to="/")
def pickup_action(request, id):
    hod = False
    if profile.objects.get(user = request.user).designation.designation_id == 'HOD':
        hod = True
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
        context={"data": data, "item_type": item_type, 'hod':hod},
    )

#Editing of the pickup date and person
@check_role(redirect_to="/")
def pickup_action_edit(request, id):
    hod = False
    if profile.objects.get(user = request.user).designation.designation_id == 'HOD':
        hod = True
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
        context={"data": data, "item_type": item_type, 'hod':hod},
    )

@check_role(redirect_to="/")
def new_complaint(request):
    hod = False
    if profile.objects.get(user = request.user).designation.designation_id == 'HOD':
        hod = True
    if request.method == "POST":
        print(request.POST)
        complaints.objects.create(user = request.user, complaint_item = assign.objects.get(id = request.POST.get('item')), description = request.POST.get("comment"), complaint_status = "SUBMITTED")
        return redirect("complaint status")
    
    # Send my items from the database to the template for selection of the item from the select tag!
    items = assign.objects.filter(user = request.user)
    return render(request, "employee/complaint_new.html",context={"data":items, 'hod':hod})

@check_role(redirect_to="/")
def complaint_status(request):
    hod = False
    if profile.objects.get(user = request.user).designation.designation_id == 'HOD':
        hod = True
    data = complaints.objects.filter(user = request.user).order_by('-id')
    return render(request, "employee/complaint_status.html", context={"data":data, 'hod':hod})

@check_role(redirect_to="/")
def profile_dash(request):
    hod = False
    if profile.objects.get(user = request.user).designation.designation_id == 'HOD':
        hod = True
    if(request.method == 'POST'):
        if not request.POST.get('room'):
            return redirect('profile')
        
        usr = profile.objects.get(user = request.user)
        usr.location = Location_Description.objects.get(Final_Code = request.POST.get('room'))
        # usr.save()
        return redirect('profile')
    data = Building_Name.objects.all()
    prof = profile.objects.get(user = request.user)
    return render(request,"employee/profile.html", context={"data":data, 'prof':prof, 'hod':hod})

def hod_dash(request):
    pfl = profile.objects.get(user = request.user)
    if pfl.designation.designation_id == 'HOD':
        dpt = pfl.department

        items = assign.objects.filter(item__current_department = dpt)

        return render(request, 'employee/hod_view.html', context={"data":items})

    else:
        return redirect("NotFound")

def getfloors(request):
    if request.method == 'POST':
        a = json.loads(request.body.decode('utf-8'))['data']
        floors = set()
        res = []
        if a == "all":
            locations = Floor_Code.objects.all()
            for i in locations:
                res.append({i.code:i.name})

        else:
            locations = Location_Description.objects.filter(building = Building_Name.objects.get(code = a))
            for location in locations:
                floors.add(location.floor.code)
            for i in floors:
                res.append({i:Floor_Code.objects.get(code = i).name})
            
        return JsonResponse({"data":res})
    

def getRooms(request):
    if request.method == 'POST':
        building = json.loads(request.body.decode('utf-8'))['building']
        floor = json.loads(request.body.decode('utf-8'))['floor']
        locations = Location_Description.objects.filter(building = Building_Name.objects.get(code = building), floor = Floor_Code.objects.get(code = floor))
        rooms = set()
        res = []
        for location in locations:
            rooms.add(location.Final_Code)
        for i in rooms:
            res.append({i:i.split(" ")[2]})
        return JsonResponse({"data":res})
    
def notifications(request):
    data = assign.objects.filter(user = request.user, dumped_review = True) 
    notfs = employee_notifications.objects.filter(user = request.user).order_by("-notification_date")
    return render(request, "employee/notifications.html", context = {"data":data, "notfs":notfs})

@transaction.atomic
def notificationAction(request):
    if request.method == 'POST':
        data_received = json.loads(request.body.decode())
        print(data_received)
        if data_received["type"] == "dump":
            if data_received["action"] == 'approve':
                # dump item successfully!
                item = Ledger.objects.get(Item_Code = data_received["id"])
                item.Purchase_Item.quantity -=1
                item_assign = assign.objects.get(item = item)
                Dump.objects.create(Item = item, Dump_Date = item_assign.action_date, Remark= item_assign.dumped_review)
                item_assign.delete()
                item.Is_Dump = True
                if item.isIssued:
                    item.isIssued = False
                item.Purchase_Item.save()
                item.save()

                # creating notification for the store admin
                admin_notifications.objects.create(notification_date = datetime.now(), notification = f'item {item.Purchase_Item.name} with item number {item.Item_Code} has been successfully approved by the user and dumped on {date.today()} which was located initially on location {item.Location_Code.Final_Code}', notification_type = "success")
                return JsonResponse({"type" : "success"})
            
            elif data_received["action"] == "reject":
                item = Ledger.objects.get(Item_Code = data_received["id"])
                item_assign = assign.objects.get(item = item)
                item_assign.dumped_review = False
                item_assign.action_date = date.today()

                admin_notifications.objects.create(notification_date = datetime.now(), notification = f'item {item.Purchase_Item.name} with item number {item.Item_Code} has been rejected by the user on {date.today()}', notification_type = "warning")

                return JsonResponse({"type":"success"})
        
        if data_received["type"] == "notification":
            if data_received["action"] == "mark_as_read":
                noti = employee_notifications.objects.get(id = data_received["id"])
                noti.status = 'read'
                noti.save()
                return JsonResponse({"type":"success_button_rem"})
            
            elif data_received["action"] == 'delete':
                employee_notifications.objects.get(id = data_received["id"]).delete()
                return JsonResponse({"type":"success_rem"})

            else:
                return JsonResponse({"type":"failure"})
        else:
            return JsonResponse({"type":"failure"})
    else:
        return redirect("NotFound")
        
def notif_count(request):
    if request.method == "GET":
        return JsonResponse({"data":employee_notifications.objects.filter(user = request.user, status = "unread").count()})

    return redirect("NotFound")