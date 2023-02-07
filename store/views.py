import json
from django.shortcuts import render,redirect
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
import pandas as pd
import csv
from datetime import date, datetime
from assetsData.models import *


def entry(request):
    date = str(datetime.now()).split(' ')[0].split('-')
    month = int(date[1])
    year = int(date[0])
    fy = str()
    if month<4:
        fy = str(year-1)+"-" +str(year)
    else:
        fy = str(year)+"-" +str(year+1)
    print(fy)
    return render(request, 'entry.html', context={'fy': fy})

def vendor_details(request):
    vendors = Vendor.objects.all()
    return render(request, 'vendor_entry.html', context={'data':vendors})

@transaction.atomic
def new_vendor(request):
    if request.method== 'POST':
        name = request.POST.get('vendorName')
        address = request.POST.get('Address')
        gst = request.POST.get('gstNo')
        email = request.POST.get('email')
        contact = request.POST.get('contactNo')
        attachments = request.FILES.getlist('attachments')
        service = request.POST.getlist('services')
        vendor = Vendor.objects.create(name = name, address = address, GST_No = gst, contact_No = contact, Email = email)
        for x in attachments:
            fs = FileSystemStorage(location='media/vendors/')
            filename = fs.save(x.name, x)
            attach = Vendor_Attachments.objects.create(File_Name = filename)
            vendor.add(attach)

        for y in service:
            try:
                Service_Type.objects.get(name = y.upper())
            except:
                vendor.services.add(Service_Type.objects.create(name = y.upper()))
        vendor.attach.save()
        
        return render(request, 'newVendor.html', context={'close':True})
        
    return render(request, 'newVendor.html')

@transaction.atomic
def locationCode(request):
    if request.method == 'POST':
        file = request.FILES.get('dataCSV')
        data = file.read().decode('utf-8')
        newData = data.split('\r\n')
        x = csv.DictReader(newData)
        fields = x.fieldnames

        for row in x:
            try:
                Building_Name.objects.get(name = row[fields[0]])
            except:
                Building_Name.objects.create(name = row[fields[0]], code = row[fields[1]])
        return redirect('location')

    data = Building_Name.objects.all()
    return render(request,'locations.html', context={'data':data})

def new_location(request):
    return render(request,'newLocation.html')

def departments(request):
    return render(request,'departments.html')

@transaction.atomic
def itemAnem(request):
    if request.method == 'POST':
        file = request.FILES.get('dataCSV')
        data = file.read().decode('utf-8')
        newData = data.split('\r\n')
        x = csv.DictReader(newData)
        for row in x:
            mc = Main_Catagory.objects.get(name = row['MAIN CATEGORY'].upper(), code = row['MC CODE'])
            sc = Sub_Catagory.objects.get(name = row['SUB CATEGORY'].upper(), code = int(row['SC CODE']))
            las = row['last serial no assigned']
            if las == '':
                las = 0
            else:
                las = int(las)
            try:
                Asset_Type.objects.get(Final_Code = row['FINAL CODE'])
            except:
                Asset_Type.objects.create(mc = mc, sc = sc,name = row['ASSET TYPE'].upper(), code = row['AT CODE'], Final_Code = row['FINAL CODE'], Last_Assigned_serial_Number = las)

        return redirect('itemAnem')
    data = Asset_Type.objects.all()
    return render(request,'itemAnem.html', context={'data':data})


def findVendor(request):
    if request.method == 'POST':
        vs = request.body.decode('utf-8')
        # print(vs)
        y = vs.split("=")[1].replace("+"," ")
        res = Vendor.objects.filter(name__icontains = y)
        data = []

        for i in res:
            data.append(i.name)
        return JsonResponse({'vendors' : data})


# Codes of initial database
@transaction.atomic
def sub_category(request):
    if request.method == 'POST':
        file = request.FILES.get('dataCSV')
        print(str(file))
        data = file.read().decode('utf-8')
        newData = data.split('\r\n')
        Number_of_entry = len(newData)
        count = 0
        for i in range(1, Number_of_entry):
            key = ''
            val = ''
            temp = newData[i].split(',')
            if len(temp)>2:
                key = ",".join(temp[:len(temp)-1]).replace('"','')
                val = temp[len(temp)-1]
            elif len(temp) == 2:
                key = temp[0]
                val = temp[1]
            if key:
                Sub_Catagory.objects.create(name = key.upper(), code = int(val))
        return redirect('sub_category')
    
    data = Sub_Catagory.objects.all()
    return render(request, 'subcatagory.html', context={'data':data})


def main_category(request):
    data = Main_Catagory.objects.all()
    return render(request,'maincategory.html',context={'data':data})


def findItem(request):
    if request.method == 'POST':
        vs = request.body.decode('utf-8')
        y = vs.split("=")[1].replace("+"," ")
        res = Asset_Type.objects.filter(name__icontains = y.upper())
        # print(res)
        data = []
        for i in res:
            data.append(i.name)
        return JsonResponse({'items' : data})


def FetchDetails(request):
    vs = request.body.decode('utf-8')
    y = vs.split("=")[1].replace("+",' ')
    res = Asset_Type.objects.get(name = y)

    return JsonResponse({'code':res.Final_Code, 'lsn' : res.Last_Assigned_serial_Number})

def itemAnem_download(request):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="itemAnem.csv"'},
    )
    writer = csv.writer(response)
    val = Asset_Type.objects.all()
    writer.writerow(['S.NO','Item Category',' MAIN CATEGORY',' MC CODE',' SUB CATEGORY', 'SC CODE', 'ASSET TYPE', 'AT CODE', 'FINAL CODE', 'last serial no assigned'])
    i = 1
    for data in val:
        writer.writerow([i,data.mc.Consumable_type, data.mc.name, data.mc.code, data.sc.name, data.sc.code, data.name, data.code, data.Final_Code, data.Last_Assigned_serial_Number])

    return response