from django.urls import path, include
from .views import *
from django.views.generic import TemplateView

# Urls for store Administrator

urlpatterns = [
    path("entry", entry, name="entry"),
    path("vendors", vendor_details, name="vendor_details"),
    path("vendor/new", new_vendor, name="new_vendor"),
    path("locationMaster", locationmaster, name="locationMaster"),
    path("location", locationCode, name="location"),
    path("location/new", new_location, name="new_location"),
    path("departments", departments, name="departments"),
    path("itemanem", itemAnem, name="itemAnem"),
    path("itemanem/edit/<str:itemId>", itemAnem_edit, name="itemAnem_edit"),
    path("itemanem/download", itemAnem_download, name="itemAnem_download"),
    path("findVendor", findVendor, name="findVendor"),
    path("subcategory", sub_category, name="sub_category"),
    path("maincategory", main_category, name="main_category"),
    path("findItem", findItem, name="findItem"),
    path("FetchDetails", FetchDetails, name="FetchDetails"),
    path("users", users, name="users"),
    path("users/new", new_user),
    path("user/<str:uname>", edit_user, name="editusers"),
    # Assign and issue module
    path("assign", assign_func, name="assign"),
    path("issue", issue),
    path("issue/item", issueItem),
    path("issue/all", issue_all_username),
    path("bulkAssign", bulkAssign),
    path("backup", backup.as_view()),
    path("backup_reminder", backupreminder),
    path("getDepartmentUsers/<str:dpt>", getDepartmentUsers),
    path("getDepartmentItems/<str:dpt>", getDepartmentItems),
    # Dashboard
    path("", home),
    path("searchItems", searchItems),
    path("findDetailed", findDetailed),
    path("stockRegister", stockRegister, name="stockRegister"),
    # Item relocation
    path("items/relocate", item_relocate),
    path("relocateItem", relocateItem),
    # Dump item module
    path("dump", dump, name="dump"),
    path("dump/finditem", find_dump_item),
    path("dump/search", get_item_details),
    # AJAX calls
    path(
        "getUnassigned", getUnassigned
    ),  # to get the json of items that are issued but not assigned
    path(
        "issue/searchItems", searchItemByNo
    ),  # for the autocomplete of search in assign by item number
    path("search/user", search_user),
    path("done", done),
    # Lost path
    path("404", TemplateView.as_view(template_name="404.html"), name="NotFound"),
    
    # Complaints
    path("complaints", complaint_list),
    path("complaints/view", complaint_view),
    path("number_complaints", number_complaints),

    # others
    path("availables",available_items),
    path('getlocations',getlocations),
    path("availables/view", available_details),
    path("dump/details", dump_details),
    path("sell/details", sold_details),
    path("sell", sell),

    # Item shifts
    path("shift",shift_item),

]
