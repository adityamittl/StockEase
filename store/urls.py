from django.urls import path
from .views import *


urlpatterns = [
    path('entry',entry, name='entry'),
    path('vendors',vendor_details, name='vendor_details'),
    path('vendor/new',new_vendor, name='new_vendor'),
    path('locationMaster', locationmaster, name = 'locationMaster'),
    path('location',locationCode, name='location'),
    path('location/new',new_location, name='new_location'),
    path('departments',departments, name='departments'),
    path('itemanem',itemAnem, name='itemAnem'),
    path('itemanem/download',itemAnem_download, name='itemAnem_download'),
    path('findVendor',findVendor, name='findVendor'),
    path('subcategory',sub_category, name='sub_category'),
    path('maincategory',main_category, name='main_category'),
    path('findItem',findItem, name='findItem'),
    path('FetchDetails',FetchDetails, name='FetchDetails'),
    path('users',users, name='users'),
    path('user/<str:uname>',edit_user, name='editusers'),
    path('assign',assign, name='assign'),
    path('downloadBackup', backup.as_view())
]


