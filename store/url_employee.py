from django.urls import path
from .view_employee import *

urlpatterns = [
    path("employee",employeeHome, name='employee_home'),
    path("pickup",pickup),
    path("pickup/action/<str:id>",pickup_action),
    path("pickup/edit/<str:id>/",pickup_action_edit),
    path("complaint/new",new_complaint, name="new complaint"),
    path("complaint/status",complaint_status, name="complaint status"),
    path("profile",profile_dash, name="profile"),
    path('hod', hod_dash),
    
    # Ajax call endpoints for the location selection
    path("getFloors",getfloors),
    path("getRooms",getRooms),
]