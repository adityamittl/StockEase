from django.db import models
from django.contrib.auth.models import User

# Database schema for the initial populated data


class Finantial_Year(models.Model):
    yearName = models.CharField(max_length=100)

    def __str__(self):
        return self.yearName


# ------------------ Item anem --------------------
# specifing the asset super catagory (Main catagory)
class Main_Catagory(models.Model):
    Consumable_type = models.CharField(max_length=200)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# To specify the subcatagory of the asset type (Sub catagory)
class Sub_Catagory(models.Model):
    name = models.CharField(max_length=100)
    code = models.IntegerField()

    def __str__(self):
        return self.name


# to specify the asset type (Assery Type)
class Asset_Type(models.Model):
    mc = models.ForeignKey(Main_Catagory, on_delete=models.CASCADE, null=True)
    sc = models.ForeignKey(Sub_Catagory, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=500)
    code = models.IntegerField()
    Final_Code = models.CharField(max_length=200)
    remark = models.TextField(null=True, blank=True)
    Last_Assigned_serial_Number = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.name


# ------------ Location Master ---------------------

# Floor and its corrosponding code


class Floor_Code(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Building_Name(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Location_Description(models.Model):
    description = models.CharField(max_length=500)
    code = models.CharField(max_length=100)
    floor = models.ForeignKey(Floor_Code, on_delete=models.CASCADE)
    building = models.ForeignKey(Building_Name, on_delete=models.CASCADE, blank=True, null=True)
    Final_Code = models.CharField(max_length=200)

    def __str__(self):
        return self.Final_Code


# ------------ Departments and labs name --------------
class Departments(models.Model):
    name = models.CharField(max_length=300)
    code = models.CharField(max_length=100, default=" ")

    def __str__(self):
        return self.name


# -------------- Vendor Database -----------------
class Service_Type(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Vendor_Attachments(models.Model):
    File_Name = models.CharField(max_length=500)


class Vendor(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(null=True, blank=True)
    GST_No = models.CharField(max_length=100, null=True, blank=True)
    contact_No = models.CharField(max_length=100, null=True, blank=True)
    Email = models.CharField(max_length=100, null=True, blank=True)
    services = models.ManyToManyField(Service_Type, blank=True)
    attach = models.ManyToManyField(Vendor_Attachments, blank=True)

    def __str__(self):
        return self.name


class stock_register(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ------------------ User Information -------------------

# Designations in the institute

class designation(models.Model):
    designation_name = models.CharField(max_length=100)
    designation_id = models.CharField(max_length=30, null=True, blank = True)

    def __str__(self):
        return self.designation_name

class profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    login_type = models.CharField(max_length=100, null = True, blank=True)
    department = models.ForeignKey(Departments, on_delete=models.CASCADE, blank=True)
    designation = models.ForeignKey(designation, on_delete=models.CASCADE)
    location = models.ForeignKey(Location_Description, on_delete=models.CASCADE, null=True, blank=True) # Location of the employee cabin, so that the item can be easily assigned to them! Filled by the user itself
    
    def __str__(self):
        return self.user.username


class backupDate(models.Model):
    date = models.DateField(auto_now=True)
    backup_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    user_ip = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return str(self.date)