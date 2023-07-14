import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
import csv
from datetime import datetime
from assetsData.models import *
from .models import *
from django.contrib.auth.models import User
import json
import secrets
import zipfile
from io import StringIO, BytesIO
from django.core.files.base import ContentFile
from datetime import datetime, date
from django.views import View
import concurrent.futures
from django.contrib import messages
from django.http import HttpResponseRedirect
from .label import create_label
from django.http import FileResponse

password_length = 8


@transaction.atomic
def entry(request):
    if request.method == "POST":
        quantity = int(request.POST.get("stockQuantity"))
        result = dict(request.POST)
        billNO = request.POST.get("invoiceNumber")
        doe = request.POST.get("EntryDate")
        doi = request.POST.get("DOI")
        item = Asset_Type.objects.get(Final_Code=result["ACN"][0].replace("&amp;", "&"))
        item.Last_Assigned_serial_Number += 1
        item.save()
        vendor = Vendor.objects.get(name=result["vendorName"][0].replace("&amp;", "&"))

        dte = [int(doe.split("/")[1]), int(doe.split("/")[2])]
        fy = str()
        fy = (
            str(dte[1] - 1) + "-" + str(dte[1])
            if dte[0] < 4
            else str(dte[1]) + "-" + str(dte[1] + 1)
        )

        print(fy)
        finantialYear = None

        try:
            finantialYear = Finantial_Year.objects.get(yearName=fy)
        except:
            finantialYear = Finantial_Year.objects.create(yearName=fy)
        for i in range(quantity):
            finalCode = (
                result.get("ACN")[0]
                + " "
                + "{:04d}".format(int(result.get(f"item_{i}")[0]))
            )
            inner = result.get(f"item_{i}")
            # print(inner[7].upper().replace("&AMP;", "&"))
            Ledger.objects.create(
                Vendor=vendor,
                bill_No=billNO,
                Date_Of_Entry=datetime.strptime(doe, "%d/%m/%Y").strftime("%Y-%m-%d"),
                Date_Of_Invoice=datetime.strptime(doi, "%d/%m/%Y").strftime("%Y-%m-%d"),
                Purchase_Item=item,
                Rate=inner[3],
                Discount=inner[4],
                Tax=inner[5],
                Ammount=inner[6],
                buy_for=Departments.objects.get(
                    name=inner[8].upper().replace("&AMP;", "&")
                ),
                current_department=Departments.objects.get(
                    name=inner[8].upper().replace("&AMP;", "&")
                ),
                stock_register=stock_register.objects.get(
                    name=inner[7].upper().replace("&AMP;", "&")
                ),
                Item_Code=finalCode,
                make=inner[1].replace("&amp;", "&"),
                sno=inner[2].replace("&amp;", "&"),
                Financial_Year=finantialYear,
            )

        return redirect("entry")

    departments = Departments.objects.all()
    sr = stock_register.objects.all()
    return render(
        request, "entry.html", context={"departments": departments, "stockRegister": sr}
    )


def vendor_details(request):
    vendors = Vendor.objects.all()
    return render(request, "vendor_entry.html", context={"data": vendors})


@transaction.atomic
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
                vendor.add(attach)

        for y in service:
            try:
                Service_Type.objects.get(name=y.upper())
            except:
                vendor.services.add(Service_Type.objects.create(name=y.upper()))
        vendor.save()

        return render(request, "newVendor.html", context={"close": True})

    return render(request, "newVendor.html")


@transaction.atomic
def locationCode(request):
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

    data = Location_Description.objects.all()
    return render(request, "locations.html", context={"data": data})


def new_location(request):
    return render(request, "newLocation.html")


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
def itemAnem(request):
    if request.method == "POST":
        file = request.FILES.get("dataCSV")
        data = file.read().decode("utf-8")
        newData = data.split("\r\n")
        x = csv.DictReader(newData)
        try:
            for row in x:
                mc = Main_Catagory.objects.get(
                    name=row["MAIN CATEGORY"].upper(), code=row["MC CODE"]
                )
                sc = Sub_Catagory.objects.get(
                    name=row["SUB CATEGORY"].upper(), code=int(row["SC CODE"])
                )
                las = row["last serial no assigned"]
                if las == "":
                    las = 0
                else:
                    las = int(las)
                try:
                    Asset_Type.objects.get(Final_Code=row["FINAL CODE"])
                except:
                    Asset_Type.objects.create(
                        mc=mc,
                        sc=sc,
                        name=row["ASSET TYPE"].upper(),
                        code=row["AT CODE"],
                        Final_Code=row["FINAL CODE"],
                        Last_Assigned_serial_Number=las,
                    )

        except:
            return render(
                request,
                "itemAnem.html",
                context={
                    "error": "Use the correct formatted csv file to import the data, Headers must be in the format "
                },
            )

        return redirect("itemAnem")
    data = Asset_Type.objects.all()
    return render(request, "itemAnem.html", context={"data": data})


def findVendor(request):
    if request.method == "POST":
        vs = request.body.decode("utf-8")
        # print(vs)
        y = vs.split("=")[1].replace("+", " ")
        res = Vendor.objects.filter(name__icontains=y)
        data = []

        for i in res:
            data.append(i.name)
        return JsonResponse({"vendors": data})


# Codes of initial database
@transaction.atomic
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
                        Consumable_type=i["CONSUMABLE TYPE"],
                        name=i["MAIN CATEGORY"],
                        code=i["CODE"],
                    )
        except:
            return HttpResponse("Data must be in prescribed format")
    data = Main_Catagory.objects.all()
    return render(request, "maincategory.html", context={"data": data})


def findItem(request):
    if request.method == "POST":
        vs = request.body.decode("utf-8")
        y = vs.split("=")[1].replace("+", " ")
        res = Asset_Type.objects.filter(name__icontains=y.upper())
        # print(res)
        data = []
        for i in res:
            data.append(i.name)
        return JsonResponse({"items": data})


def FetchDetails(request):
    vs = request.body.decode("utf-8")
    y = vs.split("=")[1].replace("+", " ")
    res = Asset_Type.objects.get(name=y)

    return JsonResponse(
        {"code": res.Final_Code, "lsn": res.Last_Assigned_serial_Number}
    )


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
                pswd = secrets.token_urlsafe(password_length)
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
                )
                print("Okay")

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


def edit_user(request, uname):
    if request.method == "POST":
        # Updating basic usesr information (user matadata)
        usr = User.objects.get(username=uname)
        usr.first_name = request.POST.get("first_name")
        usr.last_name = request.POST.get("last_name")
        usr.email = request.POST.get("email")
        usr.save()

        is_location_change = False
        old_location = ""
        pfile = profile.objects.get(user=usr)

        # Updating locationin information
        if request.POST.get("room"):
            is_location_change = True
            old_location = pfile.location.Final_Code
            new_location = Location_Description.objects.get(
                Final_Code=request.POST.get("room")
            )
            pfile.location = new_location

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

        pfile.designation = designation.objects.get(
            designation_id=request.POST.get("designation")
        )

        pfile.save()

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


# ---------------- Assign and issue module -----------------


@transaction.atomic
def assign_func(request):
    print(request.POST)
    if request.method == "POST":
        items = json.loads(
            request.POST.get("selected_items_data")
        )  # Items is a JSON that has selected items to assign and user's information such as username and department id
        uname = items["User_data"]["name"]
        department_id = items["User_data"]["department"]
        del items[
            "User_data"
        ]  # Removeing the user's information object from the items dictionary such that only selected items is present!
        comment = request.POST.get("message")  # Use This in the mail to the person!

        user_profile = User.objects.get(username=uname)

        for i in items:
            print(items[i]["item_id"])
            temp = Ledger.objects.get(Item_Code=items[i]["item_id"])
            assign.objects.create(item=temp, user=user_profile)
            temp.isIssued = True
            temp.save()

        # Now we need to send emails to two persons-
        # 1. Department HOD
        # 2. Respective assigning person.
        
        messages.success(request, f"/issue/item?type=user&uname={uname}")
        return redirect("assign")

    department = Departments.objects.all()
    return render(request, "assign.html", context={"data": department})


def issue(request):
    return render(request, "issue.html")

@transaction.atomic
def issue_all_username(request):
    if request.method == 'POST':
        items = assign.objects.filter(user__username=request.GET["uname"], pickedUp = False)
        inos = []
        for item in items:
            item.pickedUp = True
            item.item.remark = request.POST["remarks"]
            locationCode = ""

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
        
        return redirect(f"/done?code={inos}")

    uname = request.GET["uname"]
    items = assign.objects.filter(user__username=uname, pickedUp=False)
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


@transaction.atomic()
def issueItem(request):
    # print(request.GET)
    if request.method == "POST":
        # When the item is assigning by the item code
        item = assign.objects.get(item__Item_Code=request.GET["code"])
        item.pickedUp = True
        item.item.remark = request.POST["remarks"]
        locationCode = ""

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

        # when the user is assigning item by the user.
        # return the label
        return redirect(f"/done?codes={[item_code]}")
        


    if request.method == "GET":
        if request.GET["type"] == "item":
            code = request.GET["code"]
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
        if request.GET["type"] == "user":
            uname = request.GET["uname"]
            items = assign.objects.filter(
                user=User.objects.get(username=uname), pickedUp=False
            )
            return render(request, "issue_un.html", context={"data": items, 'uname':uname})
    else:
        return JsonResponse({"Status": "Prohibited"})


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
            i += 1
        return [itemAnem, "itemAnem.csv"]

    def get_users(self):
        usrs = StringIO()
        writer = csv.writer(usrs)
        pfs = profile.objects.all()
        i = 0
        writer.writerow(["Sno", "Name", "Email", "Department", "Designation"])

        for data in pfs:
            writer.writerow(
                [
                    i,
                    data.user.first_name,
                    data.user.email,
                    data.department.code,
                    data.designation,
                ]
            )
            i += 1
        return [usrs, "users.csv"]

    def get_mainCode(self):
        temp = StringIO()
        writer = csv.writer(temp)
        pfs = Main_Catagory.objects.all()
        i = 0
        writer.writerow(["Sno", "CONSUMABLE_TYPE", "NAME", "CODE"])

        for data in pfs:
            writer.writerow([i, data.Consumable_type, data.name, data.code])
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

    def get_ledger(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = Ledger.objects.all()
        writer.writerow(
            [
                "S.NO",
                "FINANTIAL YEAR",
                "VENDOR",
                "BILL NO",
                "DATE OF ENTRY",
                "DATE OF INVOICE",
                "PURCHASE ITEM CODE",
                "RATE",
                "DISCOUNT",
                "TAX",
                "AMMOUNT",
                "MAKE",
                "BUY FOR",
                "STOCK REGISTER",
                "LOCATION CODE",
                "ITEM CODE",
                "FINAL CODE",
                "REMARK",
                "SHIFT HISTORY",
                "IS DUMP",
                "IS ISSUED",
            ]
        )
        i = 1
        for data in sc:
            writer.writerow(
                [
                    i,
                    data.Finantial_Year.yearName,
                    data.Vendor.name,
                    data.bill_No,
                    data.Date_Of_Entry,
                    data.Date_Of_Invoice,
                    data.Purchase_Item.Final_Code,
                    data.Rate,
                    data.Discount,
                    data.Tax,
                    data.Ammount,
                    data.make,
                    data.buy_for.code,
                    data.stock_register.name,
                    data.Location_Code,
                    data.Item_Code,
                    data.Final_Code,
                    data.remark,
                    "pending",
                    data.Is_Dump,
                    data.isIssued,
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
            ]
            for f in concurrent.futures.as_completed(results):
                files.append((f.result()[0], f.result()[1]))

        with zipfile.ZipFile(s, "w", zipfile.ZIP_DEFLATED) as zf:
            for data, filename in files:
                zf.writestr(filename, data.getvalue())

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


def home(request):
    return render(request, "dashboard_admin.html")


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
    for i in users:
        res[i.Item_Code] = i.Purchase_Item.name
    print(res)
    return JsonResponse(res)


def itemAnem_edit(request, itemId):
    pass


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
            res.append(i.first_name + " " + i.last_name)
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


def searchItems(request):
    if request.method == "POST":
        return JsonResponse(
            {"Data": fetchData(request.POST.get("catagory"), request.POST.get("item"))}
        )


# Dashboard of admin where they can search for item and fire this query on search, this is an AJAX call
def create_AJAX_html():
    pass


def findDetailed(request):
    item = request.POST.get("item")
    catagory = request.POST.get("catagory")

    try:
        data = Ledger.objects.filter(
            Location_Code=Location_Description.objects.get(Final_Code=item)
        )
    except:
        data = Ledger.objects.filter(Item_Code=item)
    innerStr = ""
    sno = 1
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
    <div class="relative overflow-x-auto" style="border-radius: 0.5rem;">
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
    # print(item, request.POST)
    return JsonResponse({"data": res})


# codes' stock register page


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
def dump(request):
    if request.method == "POST":
        item_code = request.POST.get("itemcode_final")
        dump_date = request.POST.get("dumpdate")
        remark = request.POST.get("remark")
        item = Ledger.objects.get(Item_Code=item_code)
        item.Is_Dump = True

        # Uncheck the
        if item.isIssued:
            item.isIssued = False

        item.save()

        Dump.objects.create(
            Item=item,
            Dump_Date=datetime.strptime(dump_date, "%d/%m/%Y").strftime("%Y-%m-%d"),
            Remark=remark,
        )

        # Removing relationship with the assigned person and the item..

        assign.objects.get(item=item).delete()
        messages.success(request, f"Successfully Dumped Item {item_code}")
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

        person = assign.objects.get(item=item_details)

        res["Assigned to"] = person.user.first_name + " " + person.user.last_name

        itemList = ""

        for key, value in res.items():
            itemList += f"""
            <tr class="bg-white dark:bg-gray-800">
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    {key}
                </th>
                <td class="px-6 py-4">
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

        return JsonResponse({"data": htmlWrap})


def item_relocate(request):
    if list(request.GET.keys()) == ["old", "new", "user"]:
        old_location = request.GET["old"]
        new_location = request.GET["new"]
        assignee_user = User.objects.get(username=request.GET["user"])
        items = assign.objects.filter(user=assignee_user)

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


def searchItemByNo(request):
    try:
        request.GET.get("username")
        uname = request.POST.get("item")
        items = assign.objects.filter(
            user__username__icontains=uname, pickedUp=False
        ) | assign.objects.filter(user__first_name__icontains=uname, pickedUp=False)

        res = set()
        for i in items:
            res.add(i.user.username)

        return JsonResponse({"data": list(res)})
    except:
        pass

    ino = request.POST.get("item")
    items = assign.objects.filter(item__Item_Code__icontains=ino, pickedUp=False)
    res = list()
    for i in items:
        res.append(i.item.Item_Code)

    return JsonResponse({"data": res})


def done(request):
    if request.method == 'POST':
        x = request.GET['code']
        res = []
        for i in x.split(","):
            res.append(i.replace("['","").replace("']","").replace("'","").replace("'",""))

        return FileResponse(
            create_label(res), as_attachment=True, filename="label.pdf"
        )
    return render(request, "done.html")