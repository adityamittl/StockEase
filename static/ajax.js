function ajaxPOST(bid, url) {
    return new Promise((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.open('POST', url);
        xhr.setRequestHeader('X-CSRFToken', document.getElementsByName("csrfmiddlewaretoken")[0].value);
        xhr.send(JSON.stringify(bid));

        xhr.onreadystatechange = function () {
            if (xhr.readyState == 4 && xhr.status == 200) {
                resolve(JSON.parse(this.responseText));
            }
        };
    })
}
function ajaxGET(url) {
    return new Promise((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.open('GET', url);
        xhr.send();

        xhr.onreadystatechange = function () {
            if (xhr.readyState == 4 && xhr.status == 200) {
                resolve(JSON.parse(this.responseText));
            }
        };
    })
}
