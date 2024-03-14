import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
import csv
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from assetsData.models import *
from .models import *
from django.contrib.auth.models import User
import secrets
import zipfile
from io import StringIO, BytesIO
from django.core.files.base import ContentFile
from django.views import View
import concurrent.futures
from django.contrib import messages
from django.http import HttpResponseRedirect
from .label import create_label
from django.http import FileResponse
from .roles import check_role, check_role_ajax
from django.utils.decorators import method_decorator
import threading
from django.db.models import Count
from django.core.paginator import Paginator
import os
from .sendMail import email_send



password_length = 8


@check_role(role = "STORE", redirect_to= "employee_home")
@transaction.atomic
def entry(request):
    if request.method == "POST":
        data = json.loads(request.body.decode())
        # print(data)
        item_codes_list = list(data.keys())
        item_codes_list.remove("meta_data")
        # print(item_codes_list)

        billNO = data["meta_data"]['invoice']
        doe = data["meta_data"]['doe']
        doi = data["meta_data"]['doi']
        pono = data["meta_data"]["po_no"]
        vendor = Vendor.objects.get(name=data["meta_data"]['vendor_name'])

        dte = [int(doe.split("/")[1]), int(doe.split("/")[2])]
        fy = str()
        fy = (
            str(dte[1] - 1) + "-" + str(dte[1])
            if dte[0] < 4
            else str(dte[1]) + "-" + str(dte[1] + 1)
        )

        # print(fy)
        finantialYear = None
        # print(data)
        try:
            finantialYear = Finantial_Year.objects.get(yearName=fy)
        except:
            finantialYear = Finantial_Year.objects.create(yearName=fy)
        
        
        for items in item_codes_list:
            item = Asset_Type.objects.get(name=data[items]["item_name"])
            item_type = "FIXED ASSET" if data[items]["item_type"] == "FA" else "CONSUMABLE"
            quantity = int(data[items]["quantity"])
            item.Last_Assigned_serial_Number += quantity
            item.quantity += quantity

            item.save()

            for j in data[items]["items"]:
                if item_type == "FIXED ASSET":
                    finalCode = (
                        data[items]["item_code"]
                        + " "
                        + "{:04d}".format(int(j["item_number"]))
                    )
                dept = j["purchase_for"].upper().replace("&AMP;","&")
                print("---------------------> ",dept)
                item_ledger = Ledger.objects.create(
                Vendor=vendor,
                bill_No=billNO,
                Date_Of_Entry=datetime.strptime(doe, "%d/%m/%Y").strftime("%Y-%m-%d"),
                Date_Of_Invoice=datetime.strptime(doi, "%d/%m/%Y").strftime("%Y-%m-%d"),
                Purchase_Item=item,
                Rate=j["rate"],
                Discount=j["discount"],
                Tax=j["tax"],
                Ammount=j["ammount"],
                buy_for=Departments.objects.get(
                    name=dept
                ),
                current_department=Departments.objects.get(
                    name=dept
                ),
                stock_register=stock_register.objects.get(
                    name=j["stock_register"].upper().replace("&AMP;","&")
                ),
                make=j["item_make"],
                sno=j["item_sno"],
                Financial_Year=finantialYear,
                pono = pono
                )

                Item_Code = ""
                if item_type == "FIXED ASSET":
                    Item_Code=finalCode
                item_ledger.Item_Code = Item_Code
                item_ledger.item_type = item_type
                item_ledger.save()

        return JsonResponse({"href":"/entry"})

    departments = Departments.objects.all()
    sr = stock_register.objects.all()
    return render(
        request, "entry.html", context={"departments": departments, "stockRegister": sr}
    )

@check_role(role = "STORE", redirect_to= "employee_home")
def vendor_details(request):
    if request.method == "POST":
        vid = request.GET["id"]
        vname = request.POST["vname"]
        address = request.POST["address"]
        gst = request.POST["gst"]
        contactNo = request.POST["contactNo"]
        Email = request.POST["Email"]
        multies = dict(request.POST)
        services = multies["services"]
        # print(request.FILES['attachments'].errors)
        attachments = request.FILES.getlist("attachments")
        print(attachments)
        print(request.POST)
        vendor_object = Vendor.objects.get(id = vid)
        vendor_object.name = vname
        vendor_object.address = address 
        vendor_object.GST_No = gst 
        vendor_object.contact_No = contactNo
        vendor_object.Email = Email
        if len(services) >0:
            for i in services:
                a = Service_Type.objects.create(name = i)
                vendor_object.services.add(a)

        if attachments:
            for x in attachments:
                fs = FileSystemStorage(location="media/vendors/")
                filename = fs.save(x.name, x)
                attach = Vendor_Attachments.objects.create(File_Name=filename)
                vendor_object.attach.add(attach)
        vendor_object.save()
        return redirect("/vendors")


    if "id" in request.GET.keys():
        if request.method == 'GET':
            return render(request, "vendor_view.html", context={"data": Vendor.objects.get(id = request.GET["id"])})
    vendors = Vendor.objects.all()
    return render(request, "vendor_entry.html", context={"data": vendors})


@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def new_vendor(request):
    if request.method == "POST":
        name = request.POST.get("vendorName")
        address = request.POST.get("Address")
        gst = request.POST.get("gstNo")
        email = request.POST.get("email")
        contact = request.POST.get("contactNo")
        attachments = request.FILES.getlist("attachments")
        service = request.POST.getlist("services")
        vendor = Vendor.objects.create(
            name=name, address=address, GST_No=gst, contact_No=contact, Email=email
        )

        if attachments:
            for x in attachments:
                fs = FileSystemStorage(location="media/vendors/")
                filename = fs.save(x.name, x)
                attach = Vendor_Attachments.objects.create(File_Name=filename)
                vendor.attach.add(attach)

        for y in service:
            try:
                Service_Type.objects.get(name=y.upper())
            except:
                vendor.services.add(Service_Type.objects.create(name=y.upper()))
        vendor.save()

        return render(request, "newVendor.html", context={"close": True})

    return render(request, "newVendor.html")

def edit_location(request):

    building = Building_Name.objects.all()
    if request.method == "POST":
        location_code = request.GET["code"]
        location_object = Location_Description.objects.get(Final_Code = location_code)

        # check if the new location code issued by the user already exists or not

        new_code = request.POST["building"]+" "+request.POST["floor"]+" "+request.POST["dcode"]
        if new_code == location_code:
            return render(request, "close.html")
        else:
            # check if the new location code already exists, if yes, throw an error
            if Location_Description.objects.filter(Final_Code = new_code).count() >0:
                return render(request, "newLocation.html", context={"error":True, "msg":"This location code already exists, create a unique one", "data":request.POST, "building":building})
            else:
                location_object.description = request.POST["description"]
                location_object.code = request.POST["dcode"]
                location_object.Final_Code = location_code
                location_object.building = Building_Name.objects.get(code = request.POST["building"])
                location_object.floor = Floor_Code.objects.get(code = Floor_Code.objects.get(code = request.POST["floor"]))

                location_object.save()

                return render(request, "close.html")

    if "code" in request.GET.keys():
        floor = Floor_Code.objects.all()
        building = Building_Name.objects.all()
        try:
            item = Location_Description.objects.get(Final_Code = request.GET["code"])
        except:
            return redirect("NotFound")
        return render(request, "newLocation.html", context={"floor":floor, "building":building, "data":item})

    return redirect("NotFound")
@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def locationCode(request):
    if request.method == "POST" and "autocomplete" in  request.POST.keys():
        locs = Location_Description.objects.filter(Final_Code__icontains = request.POST["code"])[:10]
        res = []
        for i in locs:
            res.append(i.Final_Code)

        return JsonResponse({"Data":res})

    if request.method == "GET" and "code" in request.GET.keys():
        try:
            return render(request, "locations.html", context={"data":Location_Description.objects.filter(Final_Code = request.GET["code"]), "code":request.GET["code"]})

        except:
            return redirect("NotFound")
    if request.method == "POST":
        file = request.FILES.get("dataCSV")
        data = file.read().decode("utf-8")
        newData = data.split("\r\n")
        x = csv.DictReader(newData)
        fields = x.fieldnames
        colCheck = [
            "S.NO.",
            "Name of the building",
            "Code-B",
            "Floor",
            "Code-F",
            "Description",
            "Code-R",
            "Final Code",
        ]

        if fields != colCheck:
            return HttpResponse(
                request,
                "<h2>Column heading of the csv file should have these exact names</h2> <br> <strong>"
                + str(colCheck)
                + "</strong>",
            )

        for row in x:
            finalCode = row["Code-B"] + " " + row["Code-F"] + " " + row["Code-R"]
            try:
                Location_Description.objects.get(Final_Code=finalCode)
            except:
                building = None
                floor = None
                try:
                    building = Building_Name.objects.get(code=row["Code-B"])
                except:
                    building = Building_Name.objects.create(
                        name=row["Name of the building"], code=row["Code-B"]
                    )
                try:
                    floor = Floor_Code.objects.get(code=row["Code-F"])
                except:
                    floor = Floor_Code.objects.create(
                        name=row["Floor"], code=row["Code-F"]
                    )

                Location_Description.objects.create(
                    description=row["Description"],
                    code=row["Code-R"],
                    floor=floor,
                    building=building,
                    Final_Code=finalCode,
                )

        return redirect("location")
    #  pagify
    data = Location_Description.objects.all()
    paginator = Paginator(data, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "locations.html", context={"data": page_obj})

@check_role(role = "STORE", redirect_to= "employee_home")
def new_location(request):
    return render(request, "newLocation.html")

@check_role(role = "STORE", redirect_to= "employee_home")
def locationmaster(request):
    if request.method == "POST":
        file = request.FILES.get("dataCSV")
        data = file.read().decode("utf-8").split("\r\n")
        x = csv.DictReader(data)
        try:
            for row in x:
                try:
                    Building_Name.objects.get(name=row["BUILDING NAME"])
                except:
                    Building_Name.objects.create(
                        name=row["BUILDING NAME"].upper(), code=row["CODE"]
                    )

            return redirect("locationMaster")
        except:
            return render(
                request,
                "locationMaster.html",
                context={
                    "error": "Use the correct formatted csv file to import the data, Headers must be in the format "
                },
            )
    data = Building_Name.objects.all()
    return render(request, "locationMaster.html", context={"data": data})


@check_role(role = "STORE", redirect_to= "employee_home")
def departments(request):
    if request.method == "POST":
        file = request.FILES.get("dataCSV")
        data = file.read().decode("utf-8")
        newData = data.split("\r\n")
        x = csv.DictReader(newData)
        try:
            for row in x:
                try:
                    Departments.objects.get(name=row["Department Name"])
                except:
                    Departments.objects.create(
                        name=row["Department Name"].upper(), code=row["CODE"]
                    )

            return redirect("departments")
        except:
            return render(
                request,
                "departments.html",
                context={
                    "error": "Use the correct formatted csv file to import the data, Headers must be in the format "
                },
            )

    data = Departments.objects.all()
    return render(request, "departments.html", context={"data": data})


@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def itemAnem(request):
    if request.method == "POST" and "autocomplete" in request.POST.keys():
        res = []
        if request.POST["type"] == "bc":
            itm = Asset_Type.objects.filter(Final_Code__icontains = request.POST['item'])[:10]

            for i in itm:
                res.append(i.Final_Code)
        else:
            itm = Asset_Type.objects.filter(name__icontains = request.POST["item"])[:10]
            for i in itm:
                res.append(i.name)
        return JsonResponse({'Data':res})


    if request.method == "POST":
        file = request.FILES.get("dataCSV")
        data = file.read().decode("utf-8")
        newData = data.split("\r\n")
        x = csv.DictReader(newData)
        new_m = 0
        new_s = 0
        try:
            for row in x:
                try:
                    mc = Main_Catagory.objects.get(
                        name=row["MAIN CATEGORY"].upper()
                    )
                except:
                    mc = Main_Catagory.objects.create(
                        name=row["MAIN CATEGORY"].upper(),
                        code = row["MC CODE"]
                    )
                    new_m +=1
                    
                try:
                    sc = Sub_Catagory.objects.get(
                        name=row["SUB CATEGORY"].upper()
                    )
                except:
                    sc = Sub_Catagory.objects.create(
                        name = row["SUB CATEGORY"].upper(), code = row["SC CODE"]
                    )
                    new_s +=1
                las = row["last serial no assigned"]
                print(las, sc, mc)
                if las == "":
                    las = 0
                else:
                    las = int(las)
                try:
                    t = Asset_Type.objects.get(Final_Code=row["FINAL CODE"])
                except:
                    t = Asset_Type.objects.create(
                        mc=mc,
                        sc=sc,
                        name=row["ASSET TYPE"].upper(),
                        code=row["AT CODE"],
                        Final_Code=row["FINAL CODE"],
                        Last_Assigned_serial_Number=las,
                    )
        except:
            return HttpResponse("Data should be in prescribed format only!")

        if new_s or new_m:
            return HttpResponse(f"created {new_m} new main catagories and {new_s} sub catagories in new data insertion")
        return redirect("itemAnem")
    
    if request.method == "GET" and "item" in request.GET.keys():
        if request.GET["type"] == "bc":
            return render(request, "itemAnem.html", context={"data": Asset_Type.objects.filter(Final_Code = request.GET["item"]), "code" : request.GET["item"]})
        else:
            return render(request, "itemAnem.html", context={"data": Asset_Type.objects.filter(name = request.GET["item"]),"code" : request.GET["item"]})

        

    data = Asset_Type.objects.all()
    paginator = Paginator(data, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "itemAnem.html", context={"data": page_obj})


def itemanem_new(request):
    mc = Main_Catagory.objects.all()
    sc = Sub_Catagory.objects.all()
    if request.method == "POST":
        fc = Main_Catagory.objects.get(code = request.POST["mc"]).code+"{:02d}".format(Sub_Catagory.objects.get(name = request.POST["sc"]).code)+"{:03d}".format(int(request.POST["code"]))
        # check if that item number already exists or not, else throw an error on screen! 
        if Asset_Type.objects.filter(Final_Code = fc).count() >0 :
            return render(request, "anem_edit.html", context={"data": request.POST, "msg": "Item with this item number already exists", "error":True, "mc":mc, "sc":sc})
        item = Asset_Type.objects.create(
            mc = Main_Catagory.objects.get(code = request.POST["mc"]), 
            sc = Sub_Catagory.objects.get(name = request.POST["sc"]), 
            name = request.POST["name"],
            code = request.POST["code"],
            remark = request.POST["remark"],
            Last_Assigned_serial_Number = 0,
            quantity = 0,
            Final_Code = fc
        )
        return render(request, "close.html")
    return render(request, "anem_edit.html", context={"mc":mc, "sc":sc, "new" : True})


def itemanem_edit(request):
    if request.method == "POST":
        try:
            item = Asset_Type.objects.get(id = request.GET["id"])
        except:
            return redirect("NotFound")
        
        item.mc = Main_Catagory.objects.get(code = request.POST["mc"])
        item.sc = Sub_Catagory.objects.get(name = request.POST["sc"])
        item.name = request.POST["name"]
        item.code = request.POST["code"]
        item.remark = request.POST["remark"]

        item.Final_Code = Main_Catagory.objects.get(code = request.POST["mc"]).code+"{:02d}".format(Sub_Catagory.objects.get(name = request.POST["sc"]).code)+"{:03d}".format(int(request.POST["code"]))
        item.save()

        return redirect(f"/itemanem?item={item.Final_Code}&type=bc")
    if "id" in request.GET.keys():
        mc = Main_Catagory.objects.all()
        sc = Sub_Catagory.objects.all()
        item = Asset_Type.objects.get(id = request.GET["id"])
        return render(request,"anem_edit.html", context={"mc":mc, "sc":sc,"data": item})
    return request("NotFound")

@check_role_ajax(role = "STORE")
def findVendor(request):
    if request.method == "POST":
        res = Vendor.objects.filter(name__icontains=request.POST["vendor"])
        data = []

        for i in res:
            data.append(i.name)
        return JsonResponse({"vendors": data})
    return redirect("NotFound")


# Codes of initial database
@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def sub_category(request):
    if request.method == "POST":
        file = request.FILES.get("dataCSV")
        data = file.read().decode("utf-8").split("\r\n")
        newData = data
        x = csv.DictReader(data)
        try:
            for i in x:
                try:
                    Sub_Catagory.objects.get(code=int(i["CODE"]))
                except:
                    Sub_Catagory.objects.create(
                        name=i["SUB CATEGORY"].upper(), code=int(i["CODE"])
                    )
        except:
            return HttpResponse("Data must be in prescribed format")

        return redirect("sub_category")

    data = Sub_Catagory.objects.all()
    return render(request, "subcatagory.html", context={"data": data})


@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def main_category(request):
    if request.method == "POST":
        file = request.FILES.get("dataCSV")
        print(str(file))
        data = file.read().decode("utf-8").split("\r\n")
        newData = data
        x = csv.DictReader(data)
        try:
            for i in x:
                try:
                    Main_Catagory.objects.get(code=i["CODE"])
                except:
                    Main_Catagory.objects.create(
                        name=i["MAIN CATEGORY"],
                        code=i["CODE"],
                    )
        except:
            return HttpResponse("Data must be in prescribed format")
    data = Main_Catagory.objects.all()
    return render(request, "maincategory.html", context={"data": data})

@check_role_ajax(role = "STORE")
def findItem(request):
    if request.method == "POST":
        res = Asset_Type.objects.filter(name__icontains=request.POST["vendor"].upper())
        # print(res)
        data = []
        for i in res:
            data.append(i.name)
        return JsonResponse({"items": data})
    return redirect("NotFound")

@check_role_ajax(role = "STORE")
def FetchDetails(request):
    res = Asset_Type.objects.get(name=request.POST["vendor"])

    return JsonResponse(
        {"code": res.Final_Code, "lsn": res.Last_Assigned_serial_Number}
    )

@check_role(role = "STORE", redirect_to= "employee_home")
def itemAnem_download(request):
    try:
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="itemAnem.csv"'},
        )
        writer = csv.writer(response)
        val = Asset_Type.objects.all()
        writer.writerow(
            [
                "S.NO",
                "Item Category",
                " MAIN CATEGORY",
                " MC CODE",
                " SUB CATEGORY",
                "SC CODE",
                "ASSET TYPE",
                "AT CODE",
                "FINAL CODE",
                "last serial no assigned",
            ]
        )
        i = 1
        for data in val:
            writer.writerow(
                [
                    i,
                    data.mc.Consumable_type,
                    data.mc.name,
                    data.mc.code,
                    data.sc.name,
                    data.sc.code,
                    data.name,
                    data.code,
                    data.Final_Code,
                    data.Last_Assigned_serial_Number,
                ]
            )
        # print(response)
        return response
    except:
        return HttpResponse(request, "Try again later, encountered unexpacted error")


@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def users(request):
    if request.method == "POST":
        file = request.FILES.get("dataCSV")
        data = file.read().decode("utf-8")
        newData = data.split("\r\n")
        x = csv.DictReader(newData)
        try:
            for row in x:
                name = row["Name"]
                email = row["Email"]
                department = row["Department"]
                designation = row["Designation"]
                ltype = row['Auth']
                pswd = secrets.token_urlsafe(password_length)[0:password_length]
                print(pswd)
                # try:
                usr = User.objects.create(
                    username=email.split("@")[0],
                    email=email,
                    password=pswd,
                    first_name=name,
                )
                profile.objects.create(
                    department=Departments.objects.get(code=department),
                    designation=designation,
                    user=usr,
                    login_type = ltype.upper()
                )

                # Send mail
                threading.Thread(target=email_send, args=(new_user, {"username":usr.username, "password":pswd}, False, "credentials")).start()
                # threading.Thread(target=email_send, args(usr, pswd, ))

            return redirect("users")

        except:
            return render(
                request,
                "users.html",
                context={
                    "error": "Use the correct formatted csv file to import the data, Headers must be in the format "
                },
            )

    data = profile.objects.all()
    return render(request, "users.html", context={"data": data})


@transaction.atomic
@check_role(role = "STORE", redirect_to= "employee_home")
def edit_user(request, uname):
    if request.method == "POST":
        # Updating basic usesr information (user matadata)
        usr = User.objects.get(username=uname)
        usr.first_name = request.POST.get("first_name")
        usr.last_name = request.POST.get("last_name")
        usr.email = request.POST.get("email")
        usr.save()
        msg = ""

        is_location_change = False
        old_location = ""
        pfile = profile.objects.get(user=usr)

        # Updating location information
        if request.POST.get("room"):
            is_location_change = True
            try:
                old_location = pfile.location.Final_Code
            except:
                pass
            new_location = Location_Description.objects.get(
                Final_Code=request.POST.get("room")
            )
            pfile.location = new_location

            msg = "Your location has been changed by store admin, verify/view at https://localhost:8080/profile"

        # Updating user designation data
        if pfile.department.code != request.POST.get("department"):
            # Shifting all the item of that person to new department

            items_user = assign.objects.filter(user=usr)
            department_new = Departments.objects.get(
                code=request.POST.get("department")
            )
            for i in items_user:
                print(i.item)
                new_shift = Shift_History.objects.create(
                    From=pfile.department.name,
                    To=department_new.name,
                    remarks="Changing Department",
                )
                i.item.Shift_History.add(new_shift)
                i.item.current_department = department_new
                i.item.save()

            pfile.department = department_new

            msg = "Your department has been changed by store admin, verify/view at https://localhost:8080/profile"


        pfile.designation = designation.objects.get(
            designation_id=request.POST.get("designation")
        )

        pfile.save()
        threading.Thread(target=email_send, args=(usr, msg)).start()
        # email_send(usr, msg)
        if is_location_change:
            return redirect(
                f"/items/relocate?old={old_location}&new={request.POST.get('room')}&user={uname}"
            )

        return HttpResponseRedirect(request.path_info)

    items = assign.objects.filter(user=User.objects.get(username=uname))
    profile_data = profile.objects.get(user=User.objects.get(username=uname))
    data = Building_Name.objects.all()
    departments = Departments.objects.all()
    designations = designation.objects.all()
    return render(
        request,
        "userdata.html",
        context={
            "data": items,
            "profile": profile_data,
            "bd": data,
            "departments": departments,
            "designations": designations,
        },
    )

# ------------ Backup data ----------------


class backup(View):
    def get_location(self):
        locations = StringIO()
        writer = csv.writer(locations)
        writer.writerow(
            [
                "S.NO.",
                "Name of the building",
                "Code-B",
                "Floor",
                "Code-F",
                "Description",
                "Code-R",
            ]
        )

        locx = Location_Description.objects.all()
        i = 1
        for data in locx:
            writer.writerow(
                [
                    i,
                    data.building.name,
                    data.building.code,
                    data.floor.name,
                    data.floor.code,
                    data.description,
                    data.code,
                ]
            )
            i += 1
        return [locations, "locations.csv"]

    def get_itemAnem(self):
        itemAnem = StringIO()
        writer = csv.writer(itemAnem)
        val = Asset_Type.objects.all()
        writer.writerow(
            [
                "S.NO",
                " MAIN CATEGORY",
                " MC CODE",
                " SUB CATEGORY",
                "SC CODE",
                "ASSET TYPE",
                "AT CODE",
                "FINAL CODE",
                "last serial no assigned",
            ]
        )
        i = 1
        for data in val:
            writer.writerow(
                [
                    i,
                    data.mc.name,
                    data.mc.code,
                    data.sc.name,
                    data.sc.code,
                    data.name,
                    data.code,
                    data.Final_Code,
                    data.Last_Assigned_serial_Number,
                ]
            )
            i += 1
        return [itemAnem, "itemAnem.csv"]

    def get_users(self):
        usrs = StringIO()
        writer = csv.writer(usrs)
        pfs = profile.objects.all()
        i = 0
        writer.writerow(["Sno", "Name", "Email", "Department", "Designation","login type"])

        for data in pfs:
            writer.writerow(
                [
                    i,
                    data.user.first_name,
                    data.user.email,
                    data.department.code,
                    data.designation,
                    data.login_type
                ]
            )
            i += 1
        return [usrs, "users.csv"]

    def get_mainCode(self):
        temp = StringIO()
        writer = csv.writer(temp)
        pfs = Main_Catagory.objects.all()
        i = 0
        writer.writerow(["Sno", "NAME", "CODE"])

        for data in pfs:
            writer.writerow([i, data.name, data.code])
            i += 1
        return [temp, "main_catagory.csv"]

    def get_subCatagory(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = Sub_Catagory.objects.all()
        writer.writerow(["S.NO", "SUB CATEGORY", "CODE"])
        i = 1
        for data in sc:
            writer.writerow([i, data.name, data.code])
            i += 1
        return [temp, "sub_catagory.csv"]
    
    def get_shifts(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = Shift_History.objects.all()
        writer.writerow(["S.NO", "ID", "FROM", "TO", "FROM USER", "TO USER", "DATE",'REMARK'])
        i = 1
        for data in sc:
            writer.writerow([
                i, 
                data.id, 
                data.From,
                data.To, 
                data.from_User.username,
                data.to_User.username,
                data.Date,
                data.remarks
                ])
            i += 1
        return [temp, "shift_history.csv"]
    
    def get_dump(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = Dump.objects.all()
        writer.writerow(["S.NO", "ITEM_ID", "ITEM", "REMARK", "IS SOLD", "DATE OF SOLD", "SOLD PRICE"])
        i = 1
        for data in sc:
            writer.writerow([
                i, 
                data.id, 
                data.Item.Purchase_Item.name,
                data.Remark, 
                data.Is_Sold,
                data.Date_Of_Sold,
                data.Sold_Price,
                ])
            i += 1
        return [temp, "dump.csv"]
    def get_assign(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = assign.objects.all()
        writer.writerow(["S.NO", "LEDGER ID", "USER", "ITEM", "PICKUP DATE", "PICKEDUP","ASSIGNED TO PICKUP","ASSIGNED PERSON","DUMPED REVIEW","DUMP REMARK","ACTION DATE"])
        i = 1
        for data in sc:
            writer.writerow([
                i, 
                data.item.id,
                data.user.username, 
                data.item.Purchase_Item.name,
                data.pickupDate,
                data.pickedUp,
                data.assigned_to_pickup,
                data.assigned_person,
                data.assigned_person,
                data.dumped_review,
                data.dump_remark,
                data.action_date,
                ])
            i += 1
        return [temp, "assign.csv"]
    
    def get_reg_entry(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = entry_to_register.objects.all()
        writer.writerow(["S.NO", "FINANTIAL YEAR", "ITEM", "PAGE NO", "REGISTER NO"])
        i = 1
        for data in sc:
            writer.writerow([
                i, 
                data.finantialYear.yearName,
                data.item.name,
                data.pageno,
                data.register_number,
                ])
            i += 1
        return [temp, "register_entry.csv"]

    def get_designations(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = designation.objects.all()
        writer.writerow(["S.NO", "NAME", "CODE"])
        i = 1
        for data in sc:
            writer.writerow([
                i, 
                data.designation_name,
                data.designation_id,
                ])
            i += 1
        return [temp, "DESIGNATIONS.csv"]

    def get_stock_register(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = stock_register.objects.all()
        writer.writerow(["S.NO", "NAME"])
        i = 1
        for data in sc:
            writer.writerow([
                i, 
                data.name
                ])
            i += 1
        return [temp, "stock_registers.csv"]

    def get_ledger(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = Ledger.objects.all()
        writer.writerow(
            [
                "S.NO",
                "ID",
                "FINANTIAL YEAR",
                "VENDOR",
                "BILL NO",
                "DATE OF ENTRY",
                "DATE OF INVOICE",
                "PURCHASE ITEM NAME",
                "RATE",
                "DISCOUNT",
                "TAX",
                "AMMOUNT",
                "MAKE",
                "BUY FOR",
                "CURRENT_DEPARTMENT",
                "STOCK REGISTER",
                "LOCATION CODE",
                "ITEM CODE",
                "FINAL CODE",
                "REMARK",
                "SHIFT HISTORY",
                "IS DUMP",
                "IS ISSUED",
                "ITEM TYPE"
            ]
        )
        i = 1
        for data in sc:
            sh = []
            sh_all = data.Shift_History.all()
            for sh_id in sh_all:
                sh.append(sh_id.id)
            writer.writerow(
                [
                    i,
                    data.id,
                    data.Financial_Year.yearName,
                    data.Vendor.name,
                    data.bill_No,
                    data.Date_Of_Entry,
                    data.Date_Of_Invoice,
                    data.Purchase_Item.name,
                    data.Rate,
                    data.Discount,
                    data.Tax,
                    data.Ammount,
                    data.make,
                    data.buy_for.code,
                    data.current_department.code,
                    data.stock_register.name,
                    data.Location_Code,
                    data.Item_Code,
                    data.Final_Code,
                    data.remark,
                    sh,
                    data.Is_Dump,
                    data.isIssued,
                    data.item_type
                ]
            )
            i += 1
        return [temp, "ledger.csv"]

    def get_vendors(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = Vendor.objects.all()
        writer.writerow(
            [
                "S.NO",
                "NAME",
                "ADDRESS",
                "GST_NO",
                "CONTACT_NO",
                "EMAIL",
                "SERVICES",
                "ATTACHMENTS",
            ]
        )
        i = 1
        for data in sc:
            services = list()
            attachments = list()

            for j in data.services.all():
                services.append(j.name)

            for j in data.attach.all():
                attachments.append(j.File_Name)

            writer.writerow(
                [
                    i,
                    data.name,
                    data.address,
                    data.GST_No,
                    data.contact_No,
                    data.Email,
                    services,
                    attachments,
                ]
            )
            i += 1
        return [temp, "vendors.csv"]

    
    def save_backup(self, request):
        pass

    def post(self, request):
        # If the request is to upload zip file containing the data, function overhead to save_backup
        if request.FILES:
            return self.save_backup(request)

        s = ContentFile(b"", f"BackupFiles_{str(date.today())}.zip")
        files = []

        #  CONCURRENTLY FETCHING AND CREATING CSV FILES
        with concurrent.futures.ThreadPoolExecutor() as tpe:
            results = [
                tpe.submit(self.get_itemAnem),
                tpe.submit(self.get_location),
                tpe.submit(self.get_users),
                tpe.submit(self.get_mainCode),
                tpe.submit(self.get_subCatagory),
                tpe.submit(self.get_vendors),
                tpe.submit(self.get_ledger),
                tpe.submit(self.get_assign),
                tpe.submit(self.get_shifts),
                tpe.submit(self.get_dump),
                tpe.submit(self.get_reg_entry),
                tpe.submit(self.get_designations),
                tpe.submit(self.get_stock_register),
            ]
            for f in concurrent.futures.as_completed(results):
                files.append((f.result()[0], f.result()[1]))

        with zipfile.ZipFile(s, "w", zipfile.ZIP_DEFLATED) as zf:
            for data, filename in files:
                zf.writestr(filename, data.getvalue())
        print(os.getcwd()+ "\\media")
        file_size = s.tell()
        s.seek(0)

        resp = HttpResponse(s, content_type="application/zip")
        resp[
            "Content-Disposition"
        ] = f"attachment; filename=BackupFiles_{str(date.today())}.zip"
        resp["Content-Length"] = file_size
        client_ip = request.META.get("REMOTE_ADDR")
        try:
            temp = backupDate.objects.get(id=1)
            temp.date = datetime.now()
            temp.user_ip = client_ip
            temp.save()
        except:
            backupDate.objects.create(id=1, user_ip=client_ip)

        return resp
    @method_decorator(check_role(role = 'STORE'))
    def get(self, request):
        try:
            val = backupDate.objects.get(id=1)
        except:
            val = None
        return render(request, "backup.html", context={"data": val})


def backupreminder(request):
    try:
        backup_date = backupDate.objects.get(id=1)
        dateDiff = (date.today() - backup_date.date).days
        if dateDiff >= 80:
            return JsonResponse({"date": dateDiff, "status": "show"})
        return JsonResponse({"date": dateDiff, "status": "None"})
    except:
        return JsonResponse({"status": "None"})

@check_role(role='STORE', redirect_to='employee_home')
def home(request):
    return render(request, "dashboard_admin.html")

@check_role(role='STORE', redirect_to='employee_home')
def getDepartmentUsers(request, dpt):
    dept = Departments.objects.get(code=dpt)
    users = profile.objects.filter(department=dept)
    res = dict()
    for i in users:
        res[i.user.username] = i.user.first_name + " " + i.user.last_name

    return JsonResponse(res)


def getDepartmentItems(request, dpt):
    dept = Departments.objects.get(code=dpt)
    users = Ledger.objects.filter(buy_for=dept, isIssued=False, Is_Dump=False)
    res = dict()
    count_id = 0
    for i in users:
        if i.item_type == "FIXED ASSET":
            if i.Purchase_Item.name in res.keys():
                res[i.Purchase_Item.name] = {
                    "item_type" : i.item_type,
                    "quantity": res[i.Purchase_Item.name]["quantity"]+1
                }
            else:
                res[i.Purchase_Item.name] = {
                    "item_type" : i.item_type,
                    "quantity": 1
                }
                
        else:
            if i.Purchase_Item.name in res.keys():
                res[i.Purchase_Item.name] = {
                    "item_type" : i.item_type,
                    "quantity": res[i.Purchase_Item.name]["quantity"]+1
                }
            else:
                res[i.Purchase_Item.name] = {
                    "item_type" : i.item_type,
                    "quantity": 1
                }
                
    # looping into res dictionary and append register numbers and pagee number in it

    tdate = date.today()
    tdate = str(tdate).split("-") #year-month-date
    fy = None
    if int(tdate[1]) >=4 and int(tdate[1])<=12:
        fy = tdate[0] +"-"+str(int(tdate[0])+1)
    else:
        fy = str(int(tdate[0])-1) +"-"+tdate[0]
    
    fyyn = Finantial_Year.objects.filter(yearName = fy).count()

    for i in res.keys():
        # i has all the item name
        try:
            entry = entry_to_register.objects.get(finantialYear = fyyn, item__name = i)
            res[i]["reg_no"] = entry.register_number
            res[i]["page_no"] = entry.pageno
        except:
            res[i]["reg_no"] = "NA"
            res[i]["page_no"] = "NA"


    return JsonResponse(res)



def fetchData(typeFetch, val):
    res = []
    if typeFetch == "finalcode":
        for i in Ledger.objects.filter(Final_Code__icontains=val):
            res.append(i.Final_Code)
    elif typeFetch == "itemcode":
        for i in Ledger.objects.filter(Item_Code__icontains=val):
            res.append(i.Item_Code)
    elif typeFetch == "user":
        for i in User.objects.filter(first_name__icontains=val) | User.objects.filter(
            last_name__icontains=val
        ):
            res.append(i.username)
    elif typeFetch == "location":
        for i in Location_Description.objects.filter(Final_Code__icontains=val):
            res.append(i.Final_Code)
    elif typeFetch == "department":
        for i in Departments.objects.filter(
            name__icontains=val
        ) | Departments.objects.filter(code__icontains=val):
            res.append(i.name)
    elif typeFetch == "sr":
        for i in stock_register.objects.filter(name__icontains=val):
            res.append(i.name)
    elif typeFetch == "mc":
        for i in Main_Catagory.objects.filter(name__icontains=val):
            res.append(i.name)
    return res

@check_role_ajax(role ='STORE')
def searchItems(request):
    if request.method == "POST":
        return JsonResponse(
            {"Data": fetchData(request.POST.get("catagory"), request.POST.get("item"))}
        )

    return redirect("NotFound")


# Dashboard of admin where they can search for item and fire this query on search, this is an AJAX call
def create_AJAX_html(item, catagory):
    data = None
    if catagory == 'location':
        data = Ledger.objects.filter(
            Location_Code=Location_Description.objects.get(Final_Code=item)
        )
    
    elif catagory == "itemcode":
        data = Ledger.objects.get(Item_Code=item)
    
    elif catagory == "user":
        data = assign.objects.filter(user__username = item, pickedUp = True, item__item_type = "FIXED ASSET")
        dc = assign.objects.filter(user__username = item, pickedUp = True, item__item_type = "FIXED ASSET")

    elif catagory == 'sr':
        data = Ledger.objects.filter(stock_register__name = item)
    
    elif catagory == "department":
        data = Ledger.objects.filter(current_department__name = item)

    elif catagory == "finalcode":
        data = Ledger.objects.get(Final_Code = item)
    
    else:
        data = Ledger.objects.filter(Purchase_Item__mc__name = item)

    innerStr = ""
    sno = 1
    if catagory in ["location", "department", "mc", "sr"]:
        for i in data:
            try:
                innerStr += f"""<tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
                                        <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                                            {sno}
                                        </th>
                                        <td class="px-6 py-4">
                                            {i.Purchase_Item.name}
                                        </td>
                                        <td class="px-6 py-4">
                                            {i.Final_Code}
                                        </td>
                                        <td class="px-6 py-4">
                                            {i.Ammount}
                                        </td>
                                        <td class="px-6 py-4">
                                            {i.buy_for}
                                        </td>
                                        <td class="px-6 py-4">
                                            {assign.objects.get(item = i).user.first_name} {assign.objects.get(item = i).user.last_name}
                                        </td>
                                        <td class="px-6 py-4">
                                            issued
                                        </td>
                                    </tr>"""
                sno += 1
            except:
                innerStr += f"""<tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
                                        <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                                            {sno}
                                        </th>
                                        <td class="px-6 py-4">
                                            {i.Purchase_Item.name}
                                        </td>
                                        <td class="px-6 py-4">
                                            {i.Final_Code}
                                        </td>
                                        <td class="px-6 py-4">
                                            {i.Ammount}
                                        </td>
                                        <td class="px-6 py-4">
                                            {i.buy_for}
                                        </td>
                                        <td class="px-6 py-4">
                                            -
                                        </td>
                                        <td class="px-6 py-4">
                                            {"Dumped" if i.Is_Dump else "not issued yet"}
                                        </td>
                                    </tr>"""
        res = f"""
        <div class="relative overflow-x-auto shadow-md sm:rounded-lg" style="height: 80vh;">
                        <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
                            <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                                <tr>
                                    <th scope="col" class="px-6 py-3">
                                        S.No
                                    </th>
                                    <th scope="col" class="px-6 py-3">
                                        Item Name
                                    </th>
                                    <th scope="col" class="px-6 py-3">
                                        Item Code
                                    </th>
                                    <th scope="col" class="px-6 py-3">
                                        Ammount
                                    </th>
                                    <th scope="col" class="px-6 py-3">
                                        Bought For
                                    </th>
                                    <th scope="col" class="px-6 py-3">
                                        Assigned to
                                    </th>
                                    <th scope="col" class="px-6 py-3">
                                        Issued or Dumped
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {innerStr}
                            </tbody>
                        </table>
                    </div>
        """
        innerStr = res
    elif catagory == "user":
        innerStr = """
        <div class="relative overflow-x-auto shadow-md sm:rounded-lg" style="height: 80vh;">
    <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
        <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400 sticky top-0"">
            <tr>
                <th scope=" col" class="px-6 py-3">
            S.no
            </th>
            <th scope=" col" class="px-6 py-3">
                Item Name
            </th>
            <th scope="col" class="px-6 py-3">
                Item Code
            </th>
            <th scope=" col" class="px-6 py-3">
                Location
            </th>
            <th scope=" col" class="px-6 py-3">
                Asset Code
            </th>
            <th scope="col" class="px-6 py-3">
                Issue Date
            </th>
            <th scope="col" class="px-6 py-3">
                Invoice Number
            </th>
            </tr>
        </thead>
        <tbody id="vendorDetails" class="overflow-y-scroll" style="max-height: 65vh;">
        """
        for i in data:
            try:
                location_code_allocated = i.item.Location_Code.Final_Code
            except:
                location_code_allocated = "No Location yet"
            innerStr += f"""
                <tr
                    class="bg-white border-b dark:bg-gray-900 dark:border-gray-700">
                    <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                        {sno}
                    </th>
                    <td class="px-6 py-4">
                        {i.item.Purchase_Item.name}
                    </td>
                    <td class="px-6 py-4">
                        {i.item.Item_Code}
                    </td>
                    <td class="px-6 py-4">
                        {location_code_allocated}
                    </td>
                    <td class="px-6 py-4">
                        {i.item.Final_Code}
                    </td>
                    <td class="px-6 py-4">
                        {i.pickupDate}
                    </td>
                    <th class="px-6 py-4">
                        {i.item.bill_No}
                    </th>
                </tr>
            """
            sno+=1

        innerStr+= """
            </tbody>
            </table>
            </div>
        """

    elif catagory in ['itemcode',"finalcode"]:
        innerStr = f"""<iframe src="/availables/view?item={data.Item_Code}" style="height:80vh; width: 100%;" frameborder="0"
                        id="actionFrame"></iframe>"""
    return innerStr

def findDetailed(request):
    item = request.POST.get("item")
    catagory = request.POST.get("catagory")

    res = create_AJAX_html(item, catagory)
    # print(item, request.POST)
    return JsonResponse({"data": res})


# codes' stock register page

@check_role(role='STORE', redirect_to='employee_home')
def stockRegister(request):
    if request.method == "POST":
        try:
            stock_register.objects.get(name=request.POST.get("stockEntry").upper())
            return HttpResponse("Entry Already exists")
        except:
            stock_register.objects.create(name=request.POST.get("stockEntry").upper())

        return redirect(stockRegister)

    data = stock_register.objects.all()

    return render(request, "stockRegister.html", context={"data": data})


@transaction.atomic
@check_role(role='STORE', redirect_to='employee_home')
def dump(request):
    if request.method == "POST":
        item_code = request.POST.get("itemcode_final")
        dump_date = request.POST.get("dumpdate")
        remark = request.POST.get("remark")
        item = Ledger.objects.get(Item_Code=item_code)
        assign_object = assign.objects.get(item = item)
        assign_object.dumped_review = True
        assign_object.dump_remark = remark
        assign_object.action_date = datetime.strptime(dump_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        assign_object.save()
        # send an approval mail for the same!

        messages.success(request, f"Successfully send dump request of item {item_code}")
        return redirect("dump")
    return render(request, "dump.html")


def find_dump_item(request):
    if request.method == "POST":
        res = []
        items = Ledger.objects.filter(
            Item_Code__icontains=request.POST.get("item").upper(), Is_Dump=False
        )
        for item in items:
            res.append(item.Item_Code)
        return JsonResponse({"data": res})

    return redirect("NotFound")

@check_role(role='STORE', redirect_to='employee_home')
def get_item_details(request):
    if request.method == "POST":
        res = dict()
        try:
            item_details = Ledger.objects.get(
                Item_Code=request.POST.get("item").upper()
            )
        except:
            return JsonResponse(
                {
                    "data": '<p class="mb-3 text-gray-500 dark:text-gray-400">Item not Found</p>'
                }
            )
        res["Item Code"] = item_details.Item_Code
        res["Name"] = item_details.Purchase_Item.name
        res["Buy for"] = item_details.buy_for
        res["Make"] = item_details.make
        res["Date of Entry"] = item_details.Date_Of_Entry
        res["Code with Location"] = item_details.Final_Code

        # Details of the responsible person of that item.
        print(item_details)
        try:
            person = assign.objects.get(item=item_details)
            res["Assigned to"] = person.user.first_name + " " + person.user.last_name
        except:
            person = res["Assigned to"] = "Not Existed"

        hasloc = True
        if "user" in request.GET.keys():
            try:
                res["Code with Location"] = "LNM "+" "+ profile.objects.get(user__username = request.GET["user"]).location.Final_Code+" "+item_details.Item_Code
                hasloc = True
            except:
                res["Code with Location"] = "user has not updated their profile location!"
                hasloc = False
            res["Assigned to"] = User.objects.get(username = request.GET["user"]).first_name + " "+ User.objects.get(username = request.GET["user"]).last_name


        itemList = ""

        for key, value in res.items():
            itemList += f"""
            <tr class="bg-white dark:bg-gray-800">
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    {key}
                </th>
                <td class="px-6 py-4" class="item_values">
                    {value}
                </td>
            </tr>
            """

        htmlWrap = f"""
        
        <div class="relative overflow-x-auto" style="border-radius: 10px;">
            <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
                <tbody>
                    {itemList}
                </tbody>
            </table>
        </div>
        <input type="text" style="visibility: hidden; position: absolute" name="itemcode_final" value = "{res['Item Code']}">
        """

        return JsonResponse({"data": htmlWrap, "hasloc": hasloc})

    return redirect("NotFound")


@check_role(role='STORE', redirect_to='employee_home')
def item_relocate(request):
    if list(request.GET.keys()) == ["old", "new", "user"]:
        old_location = request.GET["old"]
        new_location = request.GET["new"]
        assignee_user = User.objects.get(username=request.GET["user"])
        items = assign.objects.filter(user=assignee_user, item__item_type = "FIXED ASSET")

        return render(
            request,
            "relocate_item.html",
            context={
                "old": old_location,
                "new": new_location,
                "user": profile.objects.get(user=assignee_user),
                "items": items,
            },
        )
    return redirect("NotFound")


def relocateFunction(item_id, old_loc, new_loc):
    item = assign.objects.get(id=item_id)

    # Changing item code to the new one
    item_code = " ".join(str(item.item.Final_Code).split(" ")[4::])
    new_code = f"LNM {new_loc} {item_code}"

    # Shifting Item
    new_shift = Shift_History.objects.create(
        From=old_loc,
        To=new_loc,
        remarks="Location changes when the employee's location is changed.",
    )
    item.item.Shift_History.add(new_shift)

    # changing it's location
    [building, floor, room] = new_loc.split(" ")
    location_new = Location_Description.objects.get(Final_Code=new_loc)
    item.item.Location_Code = location_new

    # Give Item a new code
    item.item.Final_Code = new_code

    # Finally saving everything

    item.item.save()

    return new_code

@check_role_ajax(role='STORE')
def relocateItem(request):
    if request.method == "POST":
        post_data = json.loads(request.body.decode("utf-8"))
        new_code = ""
        try:
            item_ids = post_data["data"].keys()  # Flush data for the verification

            for ids in item_ids:
                item_id = ids
                old_loc = post_data["data"][ids]["old"]
                new_loc = post_data["data"][ids]["new"]
                new_code += relocateFunction(item_id, old_loc, new_loc) + "\n"

        except:
            new_code = relocateFunction(
                post_data["data"], post_data["old"], post_data["new"]
            )
        return JsonResponse({"data": new_code, "success": True})

    return redirect("NotFound")


@check_role_ajax(role='STORE')
def getUnassigned(request):
    items = assign.objects.filter(pickedUp=False)
    res = {}
    cnt = 1
    for i in items:
        res[f"{cnt}"] = {
            "item code": i.item.Item_Code,
            "item name": i.item.Purchase_Item.name,
            "department": i.item.current_department.name,
            "issued to": i.user.first_name + " " + i.user.last_name,
            "id": i.id,
        }
        cnt += 1
    return JsonResponse({"data": res})

@check_role_ajax(role='STORE')
def searchItemByNo(request):
    if request.GET.get("username"):
        request.GET.get("username")
        uname = request.POST.get("item")
        items = assign.objects.filter(
            user__username__icontains=uname, pickedUp=False
        ) | assign.objects.filter(user__first_name__icontains=uname, pickedUp=False)

        res = set()
        for i in items:
            res.add(i.user.username)

        return JsonResponse({"data": list(res)})
        
    ino = request.POST.get("item")
    
    items = assign.objects.filter(item__Item_Code__icontains=ino, pickedUp=False)
    res = list()
    for i in items:
        res.append(i.item.Item_Code)

    return JsonResponse({"data": res})

# @check_role(role='STORE')
def done(request):
    if request.method == 'POST':
        # x = request.GET['code']
        data = json.loads(request.body.decode("utf-8"))['code']
        res = []
        for i in data.split(","):
            res.append(i.replace("['","").replace("']","").replace("'","").replace("'",""))
        
        return FileResponse(
            create_label(res), as_attachment=True
        )
    return redirect('NotFound')

# Store complaint module

@check_role(role="STORE")
def complaint_list(request):
    data = complaints.objects.filter(store_replied = False)
    return render(request, 'complaints.html', context={'data':data})


@check_role(role="STORE")
def complaint_view(request):
    if request.method == 'POST':
        print(request.POST)
        code = request.GET['code']
        data = complaints.objects.get(id = code)
        data.complaint_status = 'REPLIED'
        data.store_comment = request.POST.get('remarks')
        data.store_replied = True
        data.time_closed = date.today()
        data.save()

        return redirect('/complaints')
    try:
        code = request.GET['code']
        data = complaints.objects.get(id = code)
        data.complaint_status = 'SEEN'
        data.save()
        return render(request, 'complaints_view.html', context={'data':data})
    
    except:
        return redirect('/complaints')


@check_role_ajax(role="STORE")
def number_complaints(request):
    val = complaints.objects.filter(store_replied = False).count()
    print(val)
    return JsonResponse({'data':f"{val}"})


@check_role(role = "STORE")
def available_items(request):
    if "catagory" in request.GET.keys():
        # viweing the items of a perticular catagory

        catagory_code = request.GET["catagory"]
        # getting the count of different types of item!
        res = Ledger.objects.filter(Is_Dump = False, Purchase_Item__mc__code = catagory_code)
        results = dict()

        # O(N)
        for i in res:
            temp1 = i.Purchase_Item.name
            if temp1 in results.keys():
                results[temp1] += 1
            else:
                results[temp1] = 1
        


        data_res = list()
        
        for i in results.keys():
            temp = dict()
            temp["name"] = i
            temp["count"] = results[i]
            data_res.append(temp)

        return render(request, "available_items.html", context={"data":data_res,"type": "catagory"})

    if "type" in request.GET.keys():
        item_name = request.GET["type"]
        print(item_name)
        print(Asset_Type.objects.get(name__icontains = item_name))
        items_all = Ledger.objects.filter(Purchase_Item__name__icontains = item_name, Is_Dump = False)
        print(items_all)
        return render(request, "available_items.html", context={"data":items_all,"type": "detailed"})
    


    return render(request, "available_items.html", context={"data":Main_Catagory.objects.all(), "type": "all"})

@check_role_ajax(role="STORE")
def getlocations(request):
    if "location" in request.POST.keys():
        query_output = Location_Description.objects.filter(Final_Code__icontains = request.POST.get("location")).order_by("-Final_Code")[:10]
        res = list()

        for i in query_output:
            res.append(i.Final_Code)

        return JsonResponse({"data":res})
    data = json.loads(request.body.decode('utf-8'))
    building = data['building']
    floor = data['floor']

    query_output = None
    res = {}
    if floor == 'all':
        query_output = Location_Description.objects.filter(building__code = building)
    else:
        query_output = Location_Description.objects.filter(building__code = building, floor__code = floor)
    res['count'] = len(query_output)
    res['values'] = list()
    for query in query_output:
        temp = {}
        temp['name'] = query.description
        temp['building_name'] = query.building.name
        temp['floor'] = query.floor.name
        temp['code'] = query.Final_Code
        res['values'].append(temp)
    
    
    return JsonResponse({'data':res})



@check_role(role = "STORE", redirect_to="/employee")
def available_details(request):
    if request.GET["item"]:
        if "type" in request.GET.keys():
            if request.GET["type"] == "FIXED_ASSET":
                item = Ledger.objects.get(Item_Code = request.GET["item"])
            elif request.GET["type"] == "CONSUMABLE":
                item = Ledger.objects.get(id = request.GET["item"])
            else:
                return redirect("NotFound")
        else:
            item = Ledger.objects.get(Item_Code = request.GET["item"])
            
        try:
            assignee = assign.objects.get(item = item)
        except:
            assignee = ""
        dump = False
        if "dump" in request.GET.keys() or "sold" in request.GET.keys():
            dump = Dump.objects.get(Item = item)
        
        sell = False

        if "sold" in request.GET.keys():
            sell = True
        return render(request, "item_details.html", context={"data":item, "assignee" : assignee, "dump":dump, "sell":sell})
    elif request.method == "POST":
        pass
    else:
        return render(request, "404.html")

@check_role(role = "STORE", redirect_to="/employee")
def dump_details(request):
    if request.method == "POST":
        item = Dump.objects.filter(Item__Item_Code__icontains = request.POST["item"], Is_Sold = False)[:10]
        res = []

        for i in item:
            res.append(i.Item.Item_Code)

        print(res)
        return JsonResponse({"Data":res})

    if request.method == "GET" and "item" in request.GET.keys():
        return render(request, "dump_details.html", context={"data":Dump.objects.filter(Item__Item_Code = request.GET["item"]), "code":request.GET["item"]})
    items = Dump.objects.filter(Is_Sold = False)
    paginator = Paginator(items, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "dump_details.html", context={"data":page_obj})


@check_role(role = "STORE", redirect_to="/employee")
def sold_details(request):
    return render(request, "sold_details.html", context={"data":Dump.objects.filter(Is_Sold = True)})

@check_role(role = "STORE", redirect_to="/employee")
def sell(request):
    if request.method == "POST":
        print(request.POST)
        # setting that item is dumped in ledger, updating details in the dump table

        temp = Ledger.objects.get(Item_Code = request.POST["itemcode_final"])
        temp.Is_Dump = True
        temp.save()

        if Dump.objects.filter(Item__Item_Code = request.POST["itemcode_final"]).count() != 0:
            dump_data = Dump.objects.get(Item__Item_Code = request.POST["itemcode_final"])
            dump_data.Date_Of_Sold = datetime.strptime(request.POST["sellingDate"], "%d/%m/%Y").strftime("%Y-%m-%d")
            dump_data.Remark = request.POST["remark"]
            dump_data.Sold_Price = request.POST["selling_price"]
            dump_data.Is_Sold = True
            dump_data.save()
        else:
            Dump.objects.create(
                Item = temp,
                Is_Sold = True,
                Date_Of_Sold = datetime.strptime(request.POST["sellingDate"], "%d/%m/%Y").strftime("%Y-%m-%d"),
                Remark = request.POST["remark"],
                Sold_Price = request.POST["selling_price"],
                Dump_Date = datetime.strptime(request.POST["sellingDate"], "%d/%m/%Y").strftime("%Y-%m-%d"),
            )
        item_code = request.POST["itemcode_final"]
        messages.success(request, f"Item {item_code} has been successfully registered as sold!")
        return redirect("/sell")

    return render(request, "sell.html")


@transaction.atomic()
@check_role(role = "STORE", redirect_to="/employee")
def shift_item(request):
    if "type" in request.GET.keys():
        if request.GET["type"] == "user":
            if request.method == "POST":
                type = request.POST.get("type_of_change")
                print(request.POST)
                usr = User.objects.get(username = request.POST.get("user"))
                item = Ledger.objects.get(Item_Code = request.POST.get("itemcode_final"))
                if type == "user":
                    # only user is shifted, the location is still the same
                    # send mail to the new user, nwe user's department HOD, old user
                    if assign.objects.get(item = item).user == usr:
                        return HttpResponse("Old and the new user are the same!")
                    new_shift = Shift_History.objects.create(from_User = assign.objects.get(item = item).user, to_User = usr, remarks="item is assigned to the new user")
                    assigning_to_new = assign.objects.get(item = item)
                    assigning_to_new.user = usr
                    assigning_to_new.save()

                    item.Shift_History.add(new_shift)

                    # change item department to the new user's department
                    item.current_department = profile.objects.get(user = usr).department
                    item.save()
            
                if type == "user_location":
                    if assign.objects.get(item = item).user == usr:
                        return HttpResponse("Old and the new user are the same!")
                    # only user is shifted, the location is still the same
                    # send mail to the new user, nwe user's department HOD, old user
                    new_loc = profile.objects.get(user = usr).location
                    new_shift = Shift_History.objects.create(from_User = assign.objects.get(item = item).user, to_User = usr, remarks="item is assigned to the new user", From = item.Location_Code.Final_Code, To = new_loc.Final_Code)
                    assigning_to_new = assign.objects.get(item = item)
                    assigning_to_new.user = usr
                    assigning_to_new.save()

                    item.Shift_History.add(new_shift)

                    # change item department to the new user's department
                    item.current_department = profile.objects.get(user = usr).department

                    # change item location
                    item.Location_Code = new_loc

                    # create new final code
                    item.Final_Code = "LNM "+ new_loc.Final_Code + " "+item.Item_Code

                    item.save()

                messages.success(request, "Item has been successfully reassigned")
                return redirect('/shift')
            return render(request, "shift_user.html")
        elif request.GET["type"] == "location":
            if request.method == "POST":
                location_code = request.POST.get("room")
                item_code = request.GET["item"]
                item_object = Ledger.objects.get(Item_Code = item_code)
                if item_object.Location_Code.Final_Code == location_code:
                    messages.error(request,"old and new location should be different")
                    return HttpResponseRedirect(request.path_info)
                
                # creating new shift history
                new_shift = Shift_History.objects.create(From = item_object.Location_Code.Final_Code, To = location_code)

                # Changing location and code of the item ledger
                item_object.Location_Code = Location_Description.objects.get(Final_Code = location_code)
                item_final_code = "LNM "+location_code+" "+ item_object.Item_Code
                item_object.Final_Code = item_final_code
                item_object.Shift_History.add(new_shift)
                item_object.save()

                # sending a success message
                messages.success(request, f"Item {item_final_code} has been successfully relocated! ")

                return redirect("/shift")

            bd = Building_Name.objects.all()
            return render(request, "shift_location.html", context={"bd":bd})
        else:
            return redirect("NotFound;")
    return render(request, "shift_items.html")


@check_role_ajax(role = "STORE")
def search_user(request):
    uname = request.POST.get("item")
    users_auto = profile.objects.filter(user__username__icontains = uname)
    vals = set()
    for i in users_auto:
        vals.add(f"{i.user.first_name} {i.user.last_name} - {i.department.name} - {i.user.username}")

    return JsonResponse({"data":list(vals)})

@check_role(role = "STORE", redirect_to="/employee")
@transaction.atomic
def new_user(request):
    if request.method == 'POST':

        print(request.POST)
        email = request.POST.get("email")
        is_found = User.objects.filter(username = email.split("@")[0]).count()
        
        if is_found != 0:
            return HttpResponse("This user is already existed !")

        pwd = secrets.token_urlsafe(password_length)[0:password_length]
        print(pwd)
        new_user = User.objects.create(username = email.split("@")[0], email = email, password = pwd, first_name = request.POST.get("first_name"), last_name = request.POST.get("last_name"))
        # new_user.password = pwd
        new_user.set_password(pwd)
        new_user.save(update_fields=['password'])
        # new_user.save()

        # creating user profile
        department = Departments.objects.get(code = request.POST.get("department"))
        login_type = "EMPLOYEE"

        if department.name.upper() == 'STORE':
            login_type = "STORE"

        
        profile.objects.create(
            user = new_user,
            login_type = login_type,
            department = department,
            designation = designation.objects.get(designation_id = request.POST.get("designation"))
        )
        
        # send email to the user about the username and password!
        threading.Thread(target=email_send, args=(new_user, {"username":new_user.username, "password":pwd}, False, "credentials")).start()
        # email_send(new_user, {"username":new_user.username, "password":pwd}, False, "credentials")
        messages.success(request ,"user has been successfully created and email is delivered")

        return render(request, "close.html")
    departments = Departments.objects.all()
    return render(request, 'new_user.html', context={"data":departments})


# report generation!
@check_role(role = "STORE", redirect_to= "employee_home")
def reports(request):
    if request.method == "POST":
        sdate = request.POST["start"]
        edate = request.POST["end"]
        if sdate == "" or edate == "": #if the start date is empty, check if the user selected the quick select option
            rtype = request.POST["rtype"]
            if rtype != "":
                edate = date.today()
                if rtype == 'month':
                    sdate = date.today() - relativedelta(months=1)

                elif rtype == 'quaterly':
                    sdate = date.today() - relativedelta(months=4)
                
                elif rtype == 'hyearly':
                    sdate = date.today() - relativedelta(months=6)
                
                else:
                    sdate = date.today() - relativedelta(months=12)
        else:
            sdate = datetime.strptime(sdate, "%m/%d/%Y").strftime("%Y-%m-%d")
            edate = datetime.strptime(edate, "%m/%d/%Y").strftime("%Y-%m-%d")
        # generating query
        print(sdate, edate)
        unassigned_items = Ledger.objects.filter(Date_Of_Entry__range = (sdate, edate), isIssued = False, Is_Dump = False).order_by("-Date_Of_Invoice")
        assigned_items = assign.objects.filter(item__Date_Of_Entry__range = (sdate, edate)).order_by("-item__Date_Of_Invoice")
        return render(request, "report_show.html", context={"data":unassigned_items, "assigned":assigned_items, "sdate":sdate,"edate":edate,"today":date.today()})
    
            
    return render(request, "report_generate.html")

@check_role(role = "STORE", redirect_to= "employee_home")
def register_to_ledger(request):
    if "finantial_year" in request.GET.keys():
        fyear = request.GET.get("finantial_year")

        infos = entry_to_register.objects.filter(finantialYear__yearName = fyear)
        paginator = Paginator(infos, 25)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, "register_to_ledger.html", context={"data":page_obj, "is_view":False})
        

    fy = Finantial_Year.objects.all()
    return render(request, "register_to_ledger.html", context={"fy":fy, "is_view":True})

@check_role_ajax(role = "STORE")
def item_search_autocomplete(request):
    item_code = request.POST.get("item_code")
    fy = request.POST.get("fy")
    item_code = request.POST.get("item_code")
    print(item_code, fy)
    items = entry_to_register.objects.filter(item__Item_Code__icontains = item_code, finantialYear__yearName = fy)[:10]

    res = list()

    for i in items:
        res.append(i.item.Item_Code)

    return JsonResponse({"data":res})

@check_role(role = "STORE", redirect_to= "employee_home")
def notifications(request):
    if request.method == "POST":
        return JsonResponse({"count":admin_notifications.objects.filter(status = "unread").count()})
    
    data = admin_notifications.objects.all().order_by("-notification_date","-id")
    return render(request, "notification.html", context={"data":data, "count":data.filter(status="unread")})


@check_role_ajax(role = "STORE")
def notificationAction(request):
    if request.method == "POST":
        data = json.loads(request.body.decode())
        print(data)
        if data["type"] == "read":
            id = data["id"]
            notify = admin_notifications.objects.get(id = id)
            notify.status = "read"
            notify.save()

            return JsonResponse({"type":"success"})
        elif data["type"] == "delete":
            admin_notifications.objects.get(id = data["id"]).delete()
            return JsonResponse({"type":"success"})
    
        else:
            return JsonResponse({"type":"Failure"})
    else:
        return redirect("NotFound")
    
@check_role(role = "STORE", redirect_to= "employee_home")
def registerMap(request):
    tdate = date.today()
    tdate = str(tdate).split("-") #year-month-date
    fy = None
    if int(tdate[1]) >=4 and int(tdate[1])<=12:
        fy = tdate[0] +"-"+str(int(tdate[0])+1)
    else:
        fy = str(int(tdate[0])-1) +"-"+tdate[0]
    
    fyyn = Finantial_Year.objects.filter(yearName = fy).count()
    if fyyn == 0:
        Finantial_Year.objects.create(yearName = fy)
    
    currFY = Finantial_Year.objects.get(yearName = fy)
    print(currFY)
    if "year" in request.GET.keys():
        try:
            currFY = Finantial_Year.objects.get(yearName = request.GET["year"])
        except:
            return redirect("NotFound")
    try:
        data = entry_to_register.objects.filter(finantialYear = currFY, pageno__isnull = False)
    except:
        return redirect("NotFound")

    paginator = Paginator(data, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # relatively easier way to check number of unique finantial years!

    fyears_all = Finantial_Year.objects.all()
    uniques = list()
    for fy in fyears_all:
        if entry_to_register.objects.filter(finantialYear = fy).count() !=0:
            uniques.append(fy.yearName)

    return render(request, "register_entry.html", context={"data":page_obj, "fy":fy, "allYears":uniques})

@check_role(role = "STORE", redirect_to= "employee_home")
@transaction.atomic
def new_entry_register(request):
    tdate = date.today()
    tdate = str(tdate).split("-") #year-month-date
    fy = None
    if int(tdate[1]) >=4 and int(tdate[1])<=12:
        fy = tdate[0] +"-"+str(int(tdate[0])+1)
    else:
        fy = str(int(tdate[0])-1) +"-"+tdate[0]
    
    fyyn = Finantial_Year.objects.filter(yearName = fy).count()
    if fyyn == 0:
        Finantial_Year.objects.create(yearName = fy)
    
    currFY = Finantial_Year.objects.get(yearName = fy)

    if request.method == "GET":
        if "catagory" in request.GET.keys():
            cat = request.GET["catagory"]
            if cat == "":
                return HttpResponse("No catagory selected")
            
            registerItems = entry_to_register.objects.filter(finantialYear = currFY, pageno__isnull = True, register_number__isnull = True, item__mc__code = cat)
            # in the above query, we've got the number of items in the current fy and not yet entered
            all_items_mc = Asset_Type.objects.filter(mc__code = cat) # list of all the items that are in that main catagory, this may take time sine data can be of scale of hundreds to thousands, but cannot impact much significant lag in the overall application

            
            # create the entry for that fy in the entry_to_register table if that item is not available
            for new_item in all_items_mc:
                if entry_to_register.objects.filter(item = new_item, finantialYear = currFY).count() == 0:
                    entry_to_register.objects.create(item = new_item, finantialYear = currFY)

            registerItems = entry_to_register.objects.filter(finantialYear = currFY, pageno__isnull = True, register_number__isnull = True, item__mc__code = cat)

            return render(request, "selectFY.html", context={"fy":fy, "data":registerItems})
            # return render(request,"selectFY.html")

        return render(request, "catagories_register.html", context={"data":Main_Catagory.objects.all(), "type":"catagory"})

    if request.method == "POST":
        # try:
        data = json.loads(request.body.decode())
        print(data)
        item_no = data["id"]
        print(item_no)
        print(Asset_Type.objects.get(name = item_no))
        # if entry_to_register.objects.filter(item__name = item_no, finantialYear = currFY).count() == 0:
        #     register_value = entry_to_register.objects.create(item = Asset_Type.objects.get(name = item_no), finantialYear = currFY)
        # else:
        register_value = entry_to_register.objects.get(item__name = item_no, finantialYear = currFY)
        register_value.register_number = data["rno"]
        register_value.pageno = data["pno"]
        register_value.save()
        # print(register_value)

        return JsonResponse({"type" : "success"})
        
        # except:
        #     return JsonResponse({"type":"failure"})

@check_role(role = "STORE", redirect_to= "employee_home")   
def grn_fetch(request):
    if "pono" in request.GET.keys():
        try:
            grn_search = grn.objects.get(poid = request.GET["pono"])
            grn_value = grn_search.first().id 
        except:
            grn_search = grn.objects.create(poid = request.GET["pono"])
            grn_value = grn_search.id
        data = Ledger.objects.filter(pono = request.GET["pono"]).distinct("Purchase_Item__name")
        res = {} #resultant items dictionary
        srn = {
            "invoice": set(),
            "stock_register": set(),
            "date": set(),
            "supplier":set()
        }
        total_price = 0
        print(data)
        for i in data:
            try:
                reg_mapping = entry_to_register.objects.get(item = i.Purchase_Item)
            except:
                reg_mapping = {"pageno":"NA", "register_number":"NA"}
            
            item_qty = Ledger.objects.filter(pono = request.GET["pono"], Purchase_Item__name = i.Purchase_Item.name).count()
            
            res[i.Purchase_Item.name] = {
                "name" : i.Purchase_Item.name,
                "cost": i.Rate,
                "discount": i.Discount,
                "ammount": i.Ammount,
                "quantity": item_qty,
                "page" : reg_mapping["pageno"],
                "register" : reg_mapping["register_number"]
            }
            
            total_price = item_qty * float(i.Ammount)


            srn["invoice"].add(i.bill_No)
            srn["stock_register"].add(i.stock_register.name)
            srn["date"].add("-".join(i.Date_Of_Entry.isoformat().split("-")[::-1]))
            srn["supplier"].add(i.Vendor.name)
            # print(res )
        return render(request, "grn.html", context={"data":res, "pono":srn, "poNum":request.GET["pono"], "total": total_price, "round" : round(total_price), "diff" : (round(total_price)*100-int(total_price*100))/100, "grn_no" : grn_value})
    else:
        return redirect("NotFound")

@check_role(role = "STORE", redirect_to= "employee_home")
def generate_grn(request):
    data = Ledger.objects.filter(Is_Dump = False)
    res = {}
    for i in data:
        if i.pono:
            res[i.pono] = 1

    return render(request, "grn_generate.html", context={"data":res})

@check_role(role = "STORE", redirect_to= "employee_home")
def viewStockEntry(request, id):
    res = {}
    total = 0
    sr = stock_register.objects.get(id = id)
    data = Ledger.objects.filter(stock_register = sr, Is_Dump = False)
    for i in data:
        if i.Purchase_Item.name not in res.keys():
            res[i.Purchase_Item.name] = {
                "name" : i.Purchase_Item.name,
                "price" : i.Ammount,
                "total" : float(i.Ammount),
                "quantity" : 1,
            }
            total += float(i.Ammount)
        else:
            res[i.Purchase_Item.name] = {
            "name" : i.Purchase_Item.name,
            "price" : i.Ammount,
            "total" : int((res[i.Purchase_Item.name]["total"] + float(i.Ammount))*100)/100,
            "quantity" : res[i.Purchase_Item.name]["quantity"] + 1
            }
            total += float(i.Ammount)

    return render(request, "viewStockEntries.html", context={"data":res, "total":(int(total*100))/100})

@check_role(role = "STORE", redirect_to= "employee_home")
def item_delete(request):
    if request.method == "POST":
        item_id = json.loads(request.body.decode())["data"]
        item_object = Ledger.objects.get(id = item_id)
        if item_object.isIssued == False:
            item_object.delete()
        return JsonResponse({"type":"success"})
    
    return redirect("NotFound")