from django.urls import path, include
from .views import *

# Urls for store Administrator

urlpatterns = [
    path('entry',entry, name='entry'),
    path('vendors',vendor_details, name='vendor_details'),
    path('vendor/new',new_vendor, name='new_vendor'),
    path('locationMaster', locationmaster, name = 'locationMaster'),
    path('location',locationCode, name='location'),
    path('location/new',new_location, name='new_location'),
    path('departments',departments, name='departments'),
    path('itemanem',itemAnem, name='itemAnem'),
    path('itemanem/edit/<str:itemId>',itemAnem_edit, name='itemAnem_edit'),
    path('itemanem/download',itemAnem_download, name='itemAnem_download'),
    path('findVendor',findVendor, name='findVendor'),
    path('subcategory',sub_category, name='sub_category'),
    path('maincategory',main_category, name='main_category'),
    path('findItem',findItem, name='findItem'),
    path('FetchDetails',FetchDetails, name='FetchDetails'),
    path('users',users, name='users'),
    path('user/<str:uname>',edit_user, name='editusers'),
    path('assign',assign_func, name='assign'),
    path('backup', backup.as_view()),
    path('backup_reminder', backupreminder),
    path('getDepartmentUsers/<str:dpt>', getDepartmentUsers),
    path('getDepartmentItems/<str:dpt>', getDepartmentItems),
    path('', home),
    path('searchItems', searchItems),
    path('findDetailed', findDetailed),
    path('stockRegister', stockRegister, name="stockRegister"),
]


