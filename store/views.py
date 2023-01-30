from django.shortcuts import render

# Create your views here.

def entry(request):
    print(request.body.decode('utf-8').split("&"))
    print(request.POST)
    return render(request, 'entry.html')

def vendor_details(request):
    return render(request, 'vendor_entry.html')


def new_vendor(request):
    return render(request, 'newVendor.html')

def locationCode(request):
    return render(request,'locations.html')

def new_location(request):
    return render(request,'newLocation.html')

def departments(request):
    return render(request,'departments.html')