from django.urls import path
from .views import *


urlpatterns = [
    path('entry',entry, name='entry'),
    path('vendor',vendor_details, name='vendor_details'),
    path('vendor/new',new_vendor, name='new_vendor'),
    path('location',locationCode, name='location'),
    path('location/new',new_location, name='new_location'),
    path('departments',departments, name='departments'),
]


