from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('store.urls')),
    path("", include("store.url_employee")),
    path("", include("accounts.urls")),
]

admin.site.site_header  =  "LNMIIT | IMS"  
admin.site.site_title  =  "LNMIIT | IMS"
admin.site.index_title  =  "LNMIIT | IMS"