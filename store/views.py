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
    if request.method == 'POST':
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
                    Sub_Catagory.objects.get(code=int(i['CODE']))
                except:
                    Sub_Catagory.objects.create(name=i['SUB CATEGORY'].upper(), code=int(i['CODE']))
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
                    Main_Catagory.objects.get(code = i['CODE'])
                except:
                    Main_Catagory.objects.create(Consumable_type = i['CONSUMABLE TYPE'], name= i['MAIN CATEGORY'], code = i['CODE'])
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
    return HttpResponse(request, uname)


# ---------------- Assign and issue module -----------------

@transaction.atomic
def assign_func(request):
    print(request.POST)
    if request.method == "POST":
        items = json.loads(request.POST.get("selected_items_data")) #Items is a JSON that has selected items to assign and user's information such as username and department id
        uname = items['User_data']["name"]
        department_id = items['User_data']["department"]
        del items["User_data"] # Removeing the user's information object from the items dictionary such that only selected items is present!
        comment = request.POST.get("message") # Use This in the mail to the person! 

        user_profile = User.objects.get(username=  uname)

        for i in items:
            print(items[i]["item_id"])
            temp =  Ledger.objects.get(Item_Code = items[i]["item_id"])
            assign.objects.create(item = temp, user = user_profile)
            temp.isIssued = True
            temp.save()

        # Now we need to send emails to two persons- 
        # 1. Department HOD
        # 2. Respective assigning person.
        messages.success(request, f'/issue/{uname}?type=user')
        return redirect('assign')
    
    department = Departments.objects.all()
    return render(request, "assign.html", context={"data":department})


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
        writer.writerow([
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
            "IS ISSUED"
            ])
        i = 1
        for data in sc:
            writer.writerow([
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
                data.isIssued
                ])
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
    dept = Departments.objects.get(code = dpt)
    users = profile.objects.filter(department = dept)
    res = dict()
    for i in users:
        res[i.user.username] = i.user.first_name+" "+i.user.last_name
    
    return JsonResponse(res)

def getDepartmentItems(request, dpt):
    dept = Departments.objects.get(code = dpt)
    users = Ledger.objects.filter(buy_for = dept, isIssued = False, Is_Dump = False)
    res = dict()
    for i in users:
        res[i.Item_Code] = i.Purchase_Item.name
    print(res)
    return JsonResponse(res)

def itemAnem_edit(request,itemId):
    pass

def searchItems(request):
    if request.method == 'POST':
        search_query = request.POST.get('item')
        it1 = Ledger.objects.filter(Item_Code__icontains=search_query)
        it4 = Ledger.objects.filter(Final_Code__icontains=search_query)
        it2 = User.objects.filter(username__icontains = search_query)
        it3 = Location_Description.objects.filter(Final_Code__icontains = search_query)

        temp = []
        for i in it1:
            temp.append(i.Item_Code)
        for i in it4:
            temp.append(i.Final_Code)
        for i in it2:
            temp.append(i.username)
        for i in it3:
            temp.append(i.Final_Code)
            
        return JsonResponse({"Data":temp})


#Dashboard of admin where they can search for item and fire this query on search, this is an AJAX call
def findDetailed(request):
    item = request.POST.get('item')
    try:
        data = Ledger.objects.filter(Location_Code = Location_Description.objects.get(Final_Code = item))
    except:
        data = Ledger.objects.filter(Item_Code = item)
    innerStr = ""
    sno = 1
    for i in data:
        try:
            innerStr+= f"""<tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
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
            sno+=1
        except:
            innerStr+= f"""<tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
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
    return JsonResponse({'data': res})

#codes' stock register page

def stockRegister(request):
    if request.method == 'POST':
        try:
            stock_register.objects.get(name = request.POST.get("stockEntry").upper())
            return HttpResponse("Entry Already exists")
        except:
            stock_register.objects.create(name= request.POST.get("stockEntry").upper())
        
        return redirect(stockRegister)
        
    data = stock_register.objects.all()

    return render(request,"stockRegister.html", context={"data":data})

@transaction.atomic
def dump(request):
    if request.method == 'POST':
        item_code = request.POST.get("itemcode_final")
        dump_date = request.POST.get('dumpdate')
        remark = request.POST.get('remark')
        item = Ledger.objects.get(Item_Code = item_code)
        item.Is_Dump = True;

        # Uncheck the 
        if item.isIssued :
            item.isIssued = False

        item.save()

        Dump.objects.create(Item = item, Dump_Date = datetime.strptime(dump_date, "%d/%m/%Y").strftime("%Y-%m-%d"), Remark = remark)

        # Removing relationship with the assigned person and the item..

        assign.objects.get(item = item).delete()
        messages.success(request, f'Successfully Dumped Item {item_code}')
        return redirect("dump")
    return render(request, "dump.html")

def find_dump_item(request):
    if request.method == 'POST':
        res = []
        items = Ledger.objects.filter(Item_Code__icontains = request.POST.get('item').upper(), Is_Dump = False)
        for item in items:
            res.append(item.Item_Code)
        return JsonResponse({'data':res})
    
def get_item_details(request):
    if request.method == 'POST':
        res = dict()
        try:
            item_details = Ledger.objects.get(Item_Code = request.POST.get('item').upper())
        except:
            return JsonResponse({'data':'<p class="mb-3 text-gray-500 dark:text-gray-400">Item not Found</p>'})
        res['Item Code'] = item_details.Item_Code
        res['Name'] = item_details.Purchase_Item.name
        res['Buy for'] = item_details.buy_for
        res['Make'] = item_details.make
        res['Date of Entry'] = item_details.Date_Of_Entry
        res['Code with Location'] = item_details.Final_Code
        
        # Details of the responsible person of that item.

        person = assign.objects.get(item = item_details)

        res['Assigned to'] = person.user.first_name + " " + person.user.last_name

        itemList = ""

        for key, value in res.items():
            itemList+= f"""
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

        return JsonResponse({'data' : htmlWrap})
    

def dump2(request):
    return render(request, 'dump2.html')