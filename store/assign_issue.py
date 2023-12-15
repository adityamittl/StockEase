import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from datetime import date
from dateutil.relativedelta import relativedelta
from assetsData.models import *
from .models import *
from django.contrib.auth.models import User
from django.contrib import messages

from .roles import check_role, check_role_ajax
import threading

from .sendMail import email_send


@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def assign_func(request):
    # print(request.POST)
    if request.method == "POST":
        items = json.loads(
            request.POST.get("selected_items_data")
        )  # Items is a JSON that has selected items to assign and user's information such as username and department id
        uname = items["User_data"]["name"]
        department_id = items["User_data"]["department"]
        del items[
            "User_data"
        ]  # Removing the user's information object from the items dictionary such that only selected items is present!
        comment = request.POST.get("message")  # Use This in the mail to the person!

        user_profile = User.objects.get(username=uname)

        data = dict()
        temp_container = list() # storing item details

        for i in items:
            # print(items[i]["item_id"])
            item_vals = dict()

            temp = Ledger.objects.filter(Purchase_Item__name=items[i]["item_name"], isIssued = False, Is_Dump = False) #got all the ledger of that name

            # quantity requested by the user
            qty = int(items[i]["quantity"])
            for j in range(qty):

                ao = assign.objects.create(item=temp[j], user=user_profile)

                item_vals["name"] = temp[j].Purchase_Item.name
                item_vals["item_code"] = temp[j].Item_Code
                item_vals["department"] = department_id
                # creating user notification
                employee_notifications.objects.create(
                    user = user_profile, 
                    notification_date = date.today(),
                    notification = f"Item with item number {temp[j].Item_Code} has been succesfully assigned to you, pick it up from the store!",
                    notification_type = "success",
                    action_url = f"/pickup/action/{ao.id}"
                )
                temp_container.append(item_vals)


                update_query = Ledger.objects.get(id = temp[j].id)
                update_query.isIssued = True
                update_query.save()
        
        data["items"] = temp_container
        data["comment"] = comment
        data["name"] = user_profile.first_name + " " + user_profile.last_name

        # Now we need to send emails to two persons-
        # 1. Department HOD
        # 2. Respective assigning person.
        alt_email = request.POST["alt_email"]
        threading.Thread(target=email_send, args=(user_profile,data, False, "assign", alt_email)).start()
        # email_send(user_profile,data, False, "assign") # sending email!
        messages.success(request, f"/issue/item?type=user&uname={uname}")
        return redirect("assign")

    department = Departments.objects.all()
    return render(request, "assign.html", context={"data": department})



@check_role(role = "STORE", redirect_to= "employee_home")
def issue(request):
    return render(request, "issue.html")


@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def issue_all_username(request):
    if request.method == 'POST':
        items = assign.objects.filter(user__username=request.GET["uname"], pickedUp = False)
        if items[0].pickedUp :
            return HttpResponse("Items has already been pickedup")
        inos = []

        data = dict()
        temp_container = list() # storing item details

        usr = None
        for item in items:
            temp_data = dict()


            item.pickedUp = True
            item.item.remark = request.POST["remarks"]
            locationCode = ""
            item.pickupDate = date.today()

            # Assigning location
            if "room" in request.POST.keys():
                item.item.Location_Code = Location_Description.objects.get(
                    Final_Code=request.POST["room"]
                )
                locationCode = request.POST["room"]
            else:
                # Admin didn't changed the user's Location, hence getting it.

                location_item = profile.objects.get(user=item.user).location
                item.item.Location_Code = location_item
                locationCode = location_item.Final_Code

            # Creating the item number with location

            item_code = f"LNM {locationCode} {item.item.Item_Code}"
            inos.append(item_code)
            item.item.Final_Code = item_code
            item.item.save()
            item.save()

            # notify user in their notificatoin section too!
            employee_notifications.objects.create(
                user = item.user,
                notification_date = date.today(), 
                notification = f"Item with item number {item_code} has been successfylly assigned to you and addded to your inventory", 
                notification_type = "success"
            )

            temp_data["name"] = item.item.Purchase_Item.name
            temp_data["item_code"] = item.item.Final_Code
            temp_data["location"] = item.item.Location_Code.Final_Code
            temp_data["department"] = item.item.current_department.name
            usr = item.user
            data["name"] = item.user.first_name + " "+ item.user.last_name
            temp_container.append(temp_data)

        data["items"] = temp_container

        # sending emails
        threading.Thread(target=email_send, args=(usr, data, False, "issue")).start()
        # email_send(usr, data, False, "issue")
        return render(request,"done.html",context={'data':inos})

    uname = request.GET["uname"]
    if uname == "":
        return HttpResponse("No user selected")
    items = assign.objects.filter(user__username=uname, pickedUp=False, item__item_type ="FIXED ASSET")
    if not items:
        return HttpResponse("No Items are available for the user")
    return render(
        request,
        "issue_all_once.html",
        context={
            "data": items,
            "prof": profile.objects.get(user__username=uname),
            "loc": Building_Name.objects.all(),
        },
    )



@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def issueItem(request):
    
    if request.method == "POST":
        if request.GET["type"] == "item":
            # When the item is assigning by the item code
            item = assign.objects.get(item__Item_Code=request.GET["code"])
            if item.pickedUp :
                return HttpResponse("Items has already been pickedup")
            item.pickedUp = True
            item.item.remark = request.POST["remarks"]
            locationCode = ""
            item.pickupDate = date.today()

            data_email = dict()
            temp_container = list() # storing item details


            # Assigning location
            if "room" in request.POST.keys():
                item.item.Location_Code = Location_Description.objects.get(
                    Final_Code=request.POST["room"]
                )
                locationCode = request.POST["room"]
            else:
                # Admin didn't changed the user's Location, hence getting it.

                location_item = profile.objects.get(user=item.user).location
                item.item.Location_Code = location_item
                locationCode = location_item.Final_Code

            # Creating the item number with location

            item_code = f"LNM {locationCode} {item.item.Item_Code}"
            item.item.Final_Code = item_code
            item.item.save()
            item.save()

            # creating notification for user 
            employee_notifications.objects.create(
                user = item.user,
                notification_date = date.today(), 
                notification = f"Item with item number {item_code} has been successfully pickedup and assigned to you, and added to your inventory",
                notification_type = "success"
            )

            temp_container.append({"name":item.item.Purchase_Item.name, "item_code":item.item.Final_Code, "location":item.item.Location_Code.Final_Code, "department" : item.item.current_department.name})
            data_email["items"] = temp_container
            data_email["name"] = item.user.first_name + " "+ item.user.last_name
            data_email["pickedup"] = request.POST.get("Pickup_P")

            threading.Thread(target=email_send, args=(item.user, data_email, False, "issue")).start()
            # email_send(item.user, data_email, False, "issue")

            # when the user is assigning item by the user.
            # return the label
            return render(request, "done.html", context={'data':[item_code]})
        if request.GET["type"] == "user":
            uname = request.GET["uname"]
            item_locations = dict(request.POST)["checked_data"] # item locations selected by user
            items = assign.objects.filter(
                user=User.objects.get(username=uname), pickedUp=False
            )

            data = []
            # print(items.count())
            if items.count() == 0:
                return HttpResponse("These items has already been assigned!")


            for i in range(len(item_locations)):
                temp = dict()
                temp["location"] = item_locations[i]
                temp["item_code"] = items[i].item.Item_Code
                # temp["catagory"] = items[i].item.Purchase_Item.mc
                temp["name"] = items[i].item.Purchase_Item.name
                temp["final_code"] = temp["item_code"]+" "+temp["location"]
                data.append(temp)
            
            pfile = profile.objects.get(user__username = uname)

            return render(request, "bulk_verify.html", context={"data":data, "prof":pfile})
            

    if request.method == "GET":
        try:
            if request.GET["type"] == "item":
                code = request.GET["code"]
                if code == "":
                    return HttpResponse("No Item code is selected")
                try:
                    item_dets = assign.objects.get(item__Item_Code=code, pickedUp=False)
                except:
                    return HttpResponse(
                        "Item has been already assigned, you can shift item to realocate to someone"
                    )
                location_info = Building_Name.objects.all()
                prof = profile.objects.get(user=item_dets.user)
                return render(
                    request,
                    "issue_in.html",
                    context={"data": item_dets, "loc": location_info, "prof": prof},
                )
        except:
            return redirect("NotFound")
        # try:
        if request.GET["type"] == "user":
            uname = request.GET["uname"]
            if uname == "":
                return HttpResponse('No user is selected')
            ca = dict()
            items_fixed = assign.objects.filter(
                user=User.objects.get(username=uname), pickedUp=False, item__item_type = "FIXED ASSET"
            )

            items_consumable = assign.objects.filter(
                user=User.objects.get(username=uname), pickedUp=False, item__item_type = "CONSUMABLE"
            )

            # creating a dictionary of fixed asset items with all the necessary details required!

            
            for i in items_consumable:
                if i.item.Purchase_Item.name in ca.keys():
                    ca[i.item.Purchase_Item.name] = {
                        "quantity" : ca[i.item.Purchase_Item.name]["quantity"]+1
                    }
                else:
                    ca[i.item.Purchase_Item.name] = {
                        "quantity" : 1
                    }

            # appending stock register names in it
            for i in ca.keys():
                srValue = entry_to_register.objects.get(item__name = i)
                ca[i]["regno"] = srValue.register_number
                ca[i]["pageno"] = srValue.pageno
            
            fa = {}
            for i in items_fixed:
                etr = entry_to_register.objects.get(item = i.item.Purchase_Item)
                fa[i.item.Purchase_Item.name] = {
                    "page" : etr.pageno,
                    "register": etr.register_number,
                    "code":i.item.Item_Code,
                    "name":i.item.Purchase_Item.name,
                    "catagory": i.item.Purchase_Item.mc.name
                }

            buildings = Building_Name.objects.all()
            print(fa)
            return render(request, "issue_un.html", context={"data": items_fixed, "consumable":ca, 'uname':uname, 'buildings':buildings, "ccounts":items_consumable.count(), "fr" : fa})
        # except:
        #     return redirect("NotFound")
    else:
        return JsonResponse({"Status": "Prohibited"})

    return redirect("NotFound")


@check_role(role="STORE", redirect_to="/employee")
def mapitems_to_locations(request):
    if request.method == "POST":
        items_with_location = [i for i in request.POST.keys() if "location" in i]

        issued_by_other_operator = list()
        items_data = list()

        for i in items_with_location:
            item_code = i.split("_")[1]
            location_code = request.POST.get(i)


            item = assign.objects.get(item__Item_Code = item_code)
            if item.pickedUp:
                issued_by_other_operator.append(item_code)
                continue
            
            item.pickedUp = True
            item.item.remark = request.POST["remarks"]
            item.pickupDate = date.today()

            final_item_code = f"LNM {location_code} {item_code}"
            # giving item the location code
            item.item.Location_Code = Location_Description.objects.get(Final_Code = location_code)
            item.item.Final_Code = f"LNM {location_code} {item_code}" 
            item.assigned_to_pickup = request.POST.get("picked_up_person")
            item.item.save()
            item.save()
            
            # creating user notification 
            employee_notifications.objects.create(
                user = item.user,
                notification_date = date.today(), 
                notification = f"Item with item number {final_item_code} has been successfully pickedup and assigned to you, and added to your inventory",
                notification_type = "success"
            )


            # each items details!
            items_data.append({"name" : item.item.Purchase_Item.name, "item_code":item.item.Final_Code, "location":item.item.Location_Code.Final_Code, "department" : item.item.current_department.name})

        # data to send emails!
        data_email = {
            "items" : items_data,
            "pickedup" : request.POST["picked_up_person"],
            "name" : request.GET["uname"]
        }
        threading.Thread(target=email_send, args=(User.objects.get(username = request.GET["uname"]), data_email, False, "issue")).start()

        return render(request, "done.html", context={'data':[item_code], "error" : True, "error_data":issued_by_other_operator})

    items = assign.objects.filter(user__username=request.GET["uname"], pickedUp=False, item__item_type = "FIXED ASSET")
    return render(request, "issue_location_code.html", context={
            "data": items,
            "prof": profile.objects.get(user__username=request.GET["uname"]),
            "loc": Building_Name.objects.all(),
        })


@transaction.atomic()
@check_role_ajax(role="STORE")
def bulkAssign(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode())
        # Assigning the data
        usr = data["user"]
        assignee_user = data['data']


        data = dict()
        temp_container = list() # storing item details


        final_codes = []
        for i in assignee_user:

            temp_data = dict()
            assigning_data = assign.objects.get(item__Item_Code = i["item_code"])
            # print(assigning_data)
            assigning_data.pickupDate = date.today()
            assigning_data.pickedUp = True
            assigning_data.save()
            
            final_item_code = "LNM "+i["location"]+" "+i["item_code"]
            # assigning final item code to the item
            item = Ledger.objects.get(Item_Code = i["item_code"])
            item.Location_Code = Location_Description.objects.get(Final_Code = i["location"])
            item.Final_Code = "LNM "+i["location"]+" "+i["item_code"]
            item.current_department = profile.objects.get(user__username = usr).department
            item.isIssued = True
            item.save()

            # changing last assign of the item
            item_main = item.Purchase_Item
            item_main.Last_Assigned_serial_Number = item_main.Last_Assigned_serial_Number +1
            item_main.save()

            # User notification 
            employee_notifications.objects.create(
                user = assigning_data.user,
                notification_date = date.today(), 
                notification = f"Item with item number {final_item_code} has been successfully pickedup and assigned to you, and added to your inventory",
                notification_type = "success"
            )

            temp_data["name"] = assigning_data.item.Purchase_Item.name
            temp_data["item_code"] = assigning_data.item.Final_Code
            temp_data["location"] = assigning_data.item.Location_Code.Final_Code
            temp_data["department"] = assigning_data.item.current_department.name
            data["name"] = assigning_data.user.first_name + " "+ assigning_data.user.last_name
            temp_container.append(temp_data)

            final_codes.append("LNM "+i["location"]+" "+i["item_code"])
        
        data["items"] = temp_container

        threading.Thread(target=email_send, args=(usr, data, False, "issue")).start()
        # email_send(usr, data, False, "issue")


        return JsonResponse({"data":str(final_codes)})

    return redirect("NotFound")

@transaction.atomic
@check_role_ajax(role="STORE")
def issueConsumeable(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode())
        print(data)
        assign_name = data["name"]
        quantity = int(data["quantity"])
        # assign consmable item to the user!
        assign_object = assign.objects.filter(item__Purchase_Item__name = assign_name, pickedUp = False, item__item_type = "CONSUMABLE")
        print(assign_func)
        for i in range(quantity):
            temp_view = assign.objects.get(id = assign_object[i].id)
            temp_view.pickedUp = True
            temp_view.pickupDate = date.today()
            temp_view.item.isIssued = True
            temp_view.item.save()
            temp_view.save()
        return JsonResponse({"status":"success"})
    return JsonResponse({"status":"error"})