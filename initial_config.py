from assetsData.models import designation, profile, Departments
from django.contrib.auth.models import User

from dotenv import load_dotenv
import os

load_dotenv()

# check if that destination is already created or not
if designation.objects.filter(designation_id = "HOD").count() == 0:
    designation.objects.create(designation_name = "Head of Department",designation_id = "HOD")

if designation.objects.filter(designation_id = "STAFF").count() == 0:
    designation.objects.create(designation_name = "Staff",designation_id = "STAFF")

new_user = User.objects.create_superuser(username = os.getenv("ADMIN_USERNAME"),email = os.getenv("ADMIN_EMAIL"),password = os.getenv("ADMIN_PASSWORD"))
new_department = None

if Departments.objects.filter(name = "store").count() != 0:
    new_department = Departments.objects.get(name = "store")
else:
    new_department = Departments.objects.create(name = "store", code = "store")
profile.objects.create(user = User.objects.get(username = os.getenv("ADMIN_USERNAME")), login_type = "STORE", department = new_department, designation = designation.objects.get(designation_id = "HOD"))