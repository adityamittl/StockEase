from django.urls import path, include
from .views import *
from django.views.generic import TemplateView
from .assign_issue import *
# Urls for store Administrator

urlpatterns = [
    path("entry", entry, name="entry"),
    path("vendors", vendor_details, name="vendor_details"),
    path("vendor/new", new_vendor, name="new_vendor"),

    # location routes
    path("locationMaster", locationmaster, name="locationMaster"),
    path("location", locationCode, name="location"),
    path("location/new", new_location, name="new_location"),
    path("location/edit", edit_location, name="edit_location"),
    path("departments", departments, name="departments"),

    # Item Emumeration paths
    path("itemanem", itemAnem, name="itemAnem"),
    path("itemanem/download", itemAnem_download, name="itemAnem_download"),
    path("itemanem/edit", itemanem_edit),
    path("itemanem/new", itemanem_new),

    # codes
    path("findVendor", findVendor, name="findVendor"),
    path("subcategory", sub_category, name="sub_category"),
    path("maincategory", main_category, name="main_category"),
    path("findItem", findItem, name="findItem"),
    path("FetchDetails", FetchDetails, name="FetchDetails"),
    path("users", users, name="users"),
    path("users/new", new_user),
    path("user/<str:uname>", edit_user, name="editusers"),
    path("subcategory/new", new_subcatagory),
    path("maincategory/new", new_maincatagory),

    # Assign and issue module
    path("assign", assign_func, name="assign"), #mig
    path("issue", issue), #mig
    path("issue/item", issueItem), #mig
    path("issue/all", issue_all_username), #mig
    path("bulkAssign", bulkAssign), #mig
    path("getDepartmentUsers/<str:dpt>", getDepartmentUsers),
    path("getDepartmentItems/<str:dpt>", getDepartmentItems),
    path("mapitems", mapitems_to_locations), #mig
    path("issueConsumeable",issueConsumeable),
    
    #data backup
    path("backup", backup.as_view()),
    path("backup_reminder", backupreminder),
    # Dashboard
    path("", home),
    path("searchItems", searchItems),
    path("findDetailed", findDetailed),
    path("stockRegister", stockRegister, name="stockRegister"),
    path("stockRegister/View/<str:id>", viewStockEntry,),
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

    # Ajax call for autocomplete of item code
    path("itemsearch", item_search_autocomplete),

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
    path("item/delete",item_delete),

    path("dump/details", dump_details),
    path("sell/details", sold_details),
    path("sell", sell),
    path("alert", notifications),
    path("alert/action", notificationAction),
    path("register",registerMap),
    path("register/new",new_entry_register),
    

    # Item shifts
    path("shift",shift_item),

    # Report generation!
    path("reports", reports),
    path("generate/grn",generate_grn),
    path("grn",grn_fetch),

    # Register to ledger relationship
    path("registerentry",register_to_ledger),
]
