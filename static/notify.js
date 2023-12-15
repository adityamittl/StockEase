ajaxPOST({},"/alert").then(data =>{
    document.getElementById("notificationCount").innerHTML = data["count"]
})