from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Ledger)
admin.site.register(assign)
admin.site.register(complaints)
admin.site.register(Dump)
admin.site.register(Shift_History)
admin.site.register(admin_notifications)
admin.site.register(employee_notifications)
admin.site.register(entry_to_register)