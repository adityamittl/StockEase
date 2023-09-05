ajaxGET('/number_complaints').then((data)=>{
    document.getElementById('complaint-count').innerHTML = data['data']
})