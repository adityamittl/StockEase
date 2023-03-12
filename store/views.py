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
            print(inner[7].upper().replace("&AMP;", "&"))
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
                Finantial_Year=finantialYear,
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
        vendor.attach.save()

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
                render,
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
        print(str(file))
        data = file.read().decode("utf-8")
        newData = data.split("\r\n")
        Number_of_entry = len(newData)
        count = 0
        for i in range(1, Number_of_entry):
            key = ""
            val = ""
            temp = newData[i].split(",")
            if len(temp) > 2:
                key = ",".join(temp[: len(temp) - 1]).replace('"', "")
                val = temp[len(temp) - 1]
            elif len(temp) == 2:
                key = temp[0]
                val = temp[1]
            if key:
                Sub_Catagory.objects.create(name=key.upper(), code=int(val))
        return redirect("sub_category")

    data = Sub_Catagory.objects.all()
    return render(request, "subcatagory.html", context={"data": data})


def main_category(request):
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
                render,
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


def assign(request):
    return render(request, "assign.html")


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

    def get_subCatagory(self):
        temp = StringIO()
        writer = csv.writer(temp)
        sc = Sub_Catagory.objects.all()
        writer.writerow(["SUB CATEGORY", "CODE"])
        # for data in sc:


    def post(self, request):
        s = ContentFile(b"", f"BackupFiles_{str(date.today())}.zip")
        files = []

        #  CONCURRENTLY FETCHING AND CREATING CSV FILES
        with concurrent.futures.ThreadPoolExecutor() as tpe:
            results = [
                tpe.submit(self.get_itemAnem),
                tpe.submit(self.get_location),
                tpe.submit(self.get_users),
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
        return resp
