from django.shortcuts import render
from django.views import View
from django.db import transaction
from .models import *

# ------- Logic for data Entry --------

# @transaction.atomic
# class dataEntry(View):
#     def post(self, request):
