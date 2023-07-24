$('a.delete_option').on('click', function(e) {
    e.preventDefault();
    var filename = e.currentTarget.parentNode.parentNode.childNodes[1].textContent;
    console.log(e.currentTarget.parentNode.parentNode.childNodes[1].textContent);
    console.log("Stopping")
    var xhr = new XMLHttpRequest();
    var url = "/downloads/delete/" + encodeURIComponent(JSON.stringify({"filename": filename}));
    console.log(url);
    xhr.open("GET", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
    if (xhr.readyState === 4 && xhr.status === 200) {
        e.currentTarget.parentNode.parentNode.remove();
    }
};
xhr.send();
});

$('a.ignore_option').on('click', function(e) {
    e.preventDefault();
    var mac = e.currentTarget.parentNode.parentNode.childNodes[1].textContent;
    console.log(e.currentTarget.parentNode.parentNode.childNodes[1].textContent);
    console.log(e.currentTarget);
    var xhr = new XMLHttpRequest();
    var url = "/ignore/" + encodeURIComponent(JSON.stringify({"mac": mac}));
    console.log(url);
    xhr.open("GET", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
    if (xhr.readyState === 4 && xhr.status === 200) {
        e.currentTarget.parentNode.parentNode.remove();
    }
};
xhr.send();
});
