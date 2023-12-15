ajaxGET('/notification/count').then((data)=>{
    document.getElementById('complaint-count').innerHTML = data['data']
})