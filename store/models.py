from django.db import models
from assetsData.models import *
from django.contrib.auth.models import User

# for the shift history of the item


class Shift_History(models.Model):
    From = models.CharField(max_length=200, null=True, blank=True)
    To = models.CharField(max_length=200, null=True, blank=True)
    from_User = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shift_from_user",
    )
    to_User = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shift_to_user",
    )
    Date = models.DateField(auto_now=True)
    remarks = models.TextField(null=True, blank=True)


# Contains all the data that store has!
class Ledger(models.Model):
    # Main_Catagory = models.ForeignKey(Main_Catagory,on_delete=models.CASCADE)
    Financial_Year = models.ForeignKey(Finantial_Year, on_delete=models.DO_NOTHING)
    # Sub_Catagory = models.ForeignKey(Sub_Catagory, on_delete=models.CASCADE)
    Vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    bill_No = models.CharField(max_length=500)
    Date_Of_Entry = models.DateField()
    Date_Of_Invoice = models.DateField()
    Purchase_Item = models.ForeignKey(Asset_Type, on_delete=models.DO_NOTHING)
    Rate = models.CharField(max_length=200)
    Discount = models.CharField(max_length=100)
    Tax = models.CharField(max_length=100)
    Ammount = models.CharField(max_length=1000)
    make = models.CharField(max_length=500, null=True, blank=True)
    sno = models.CharField(max_length=500, null=True, blank=True)
    buy_for = models.ForeignKey(
        Departments, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    current_department = models.ForeignKey(Departments, on_delete=models.DO_NOTHING, null=True, blank=True, related_name= "new_department")
    stock_register = models.ForeignKey(
        stock_register, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    # Make_No = models.CharField(max_length=200)
    Location_Code = models.ForeignKey(Location_Description, on_delete=models.DO_NOTHING, null=True, blank=True)
    Item_Code = models.CharField(max_length=200)
    Final_Code = models.CharField(max_length=500, null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    Shift_History = models.ManyToManyField(Shift_History, blank=True)
    Is_Dump = models.BooleanField(default=False)
    isIssued = models.BooleanField(default=False)
    item_type = models.CharField(max_length = 100, null = True, blank=True)
    pono = models.CharField(max_length = 100, null = True, blank = True)


    class Meta:
        ordering = ['Purchase_Item__name']

# Contains the data of dump of item


class Dump(models.Model):
    Item = models.ForeignKey(Ledger, on_delete=models.CASCADE)
    Dump_Date = models.DateField()
    Remark = models.TextField(null=True, blank=True)
    Is_Sold = models.BooleanField(default=False)
    Date_Of_Sold = models.DateField(null=True, blank=True)
    Sold_Price = models.CharField(max_length=100, null=True, blank=True)


class assign(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    item = models.ForeignKey(Ledger, on_delete=models.DO_NOTHING)
    pickupDate = models.DateField(null=True, blank=True)
    pickedUp = models.BooleanField(default=False)
    assigned_to_pickup = models.CharField(max_length=100)
    assigned_person = models.BooleanField(default=False)
    dumped_review = models.BooleanField(default=False)
    dump_remark = models.TextField(null=True, blank=True)
    action_date = models.DateField(null=True, blank=True)
    

    def __str__(self):
        return self.item.Item_Code

class complaints(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    complaint_item = models.ForeignKey(assign, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    store_replied = models.BooleanField(default=False)
    store_comment = models.TextField(null = True)
    complaint_status = models.CharField(max_length=40, null=True)
    time_registered = models.DateTimeField(auto_now_add=True, null=True)
    time_closed = models.DateTimeField(null=True)


class entry_to_register(models.Model):
    finantialYear = models.ForeignKey(Finantial_Year, on_delete=models.DO_NOTHING, null=True, blank= True)
    item = models.ForeignKey(Asset_Type, on_delete=models.DO_NOTHING, null=True, blank=True)
    pageno = models.IntegerField(null = True, blank = True)
    register_number = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return str(self.finantialYear)

class admin_notifications(models.Model):
    notification_date = models.DateTimeField()
    notification = models.TextField()
    status = models.CharField(max_length=100, default = "unread")
    notification_type = models.CharField(max_length=100)

class employee_notifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_date = models.DateTimeField()
    notification = models.TextField()
    status = models.CharField(max_length=100, default = "unread")
    notification_type = models.CharField(max_length=100)
    action_url = models.CharField(max_length=100, null = True, blank=True)


class grn(models.Model):
    poid = models.CharField(max_length=100)
