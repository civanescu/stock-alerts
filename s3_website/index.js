
//document.write(window.location.search);

function getSpace(s,l){
    let ret = "";
    while(s.length+ret.length<l){
  ret = ret + " ";
}
return ret;
}


location.querystring = (function() {
	// The return is a collection of key/value pairs
    let result = {};

    // Gets the query string with a preceding '?'
    let querystring = location.search;

    // document.location.search is empty if a query string is absent
	if (!querystring)
		return result;

	// substring(1) to remove the '?'
    let pairs = querystring.substring(1).split("&");
    let splitPair;

    // Load the key/values of the return collection
	for (let i = 0; i < pairs.length; i++) {
		splitPair = pairs[i].split("=");
		result[splitPair[0]] = splitPair[1];
	}

	return result;
})();

function createRequestObject(){
    let request_o; //declare the variable to hold the object.
    let browser = navigator.appName; //find the browser name
	if(browser === "Microsoft Internet Explorer"){
		/* Create the object using MSIE's method */
		request_o = new ActiveXObject("Microsoft.XMLHTTP");
	}else{
		/* Create the object using another browser's method */
		request_o = new XMLHttpRequest();
	}
	return request_o; //return the object
}

/* You can get more specific with version information by using
	parseInt(navigator.appVersion)
	Which will extract an integer value containing the version
	of the browser being used.
*/
/* The variable http will hold our new XMLHttpRequest object. */
let http = createRequestObject();

function getList(){
	http.open('get', location.protocol+'//'+location.hostname);
	http.onreadystatechange = handleList;
	http.send(null);
}

function handleList(){
	/* Make sure that the transaction has finished. The XMLHttpRequest object
		has a property called readyState with several states:
		0: Uninitialized
		1: Loading
		2: Loaded
		3: Interactive
		4: Finished */
    if (http.readyState === 4) { //Finished loading the response
        let i;
        /* We have got the response from the server-side script,
                    let's see just what it was. Using the responseText property of
                    the XMLHttpRequest object. */
        let response = http.responseXML;

        let filex = response.getElementsByTagName('Contents');

        let res = '';
        let fileList = [];
        for (i = 0; i < filex.length; i++) {
            let fileData = [];
            fileList[i] = fileData;
            let size = filex[i].getElementsByTagName('Size')[0].firstChild.data;
            let name = filex[i].getElementsByTagName('Key')[0].firstChild.data;
            let lastmod = filex[i].getElementsByTagName('LastModified')[0].firstChild.data;
            let link = "<A HREF=\"" + name + "\">" + name + "</A>";
            let deleteButton = "<button onclick=\"deleteFile('" + name + "')\">Delete</button>";
            fileData[0] = name;
            fileData[1] = size;
            fileData[2] = lastmod;
            fileData[3] = link;
            fileData[4] = deleteButton;
        }

        fileList.sort(getSort());
        //document.write(getSort());
        for (i = 0; i < fileList.length; i++) { //length is the same as count($array)
            let fileData = fileList[i];
            let name = fileData[0];
            let size = fileData[1];
            let lastmod = fileData[2];
            let link = fileData[3];
            let deleteButton = fileData[4]
            res = res + getSpace(size, 15) + size + " B ";
            res = res + " " + getSpace(lastmod, 20) + lastmod + " ";
            res = res + " " + link + getSpace(name, 50) + " ";
            // res += deleteButton + "<br>";
            res = res + "<BR>";
        }


        document.getElementById('bucket_list').innerHTML = "<PRE>" + getLink() + "<BR>" + res + "</PRE>";
    }
	}

// function to delete
function deleteFile(fileName) {
	console.log("Delete file: "+fileName)
}

function getQueryVariable(variable) {
    let query = window.location.search.substring(1);
    let vars = query.split("&");
    for (let i=0; i<vars.length; i++) {
        let pair = vars[i].split("=");
        if (pair[0] === variable) {
return pair[1];
}
}
return null;
}


function sortSize(a,b) {
   if(parseInt(a[1]) > parseInt(b[1])) return 1;
   if(parseInt(a[1]) < parseInt(b[1])) return -1;
   return 0;
 }
function sortSizeDesc(a,b) { return (-sortSize(a,b)); }
function sortLastmod(a,b) {
   if(a[2] > b[2]) return 1;
   if(a[2] < b[2]) return -1;
   return 0;
}
function sortLastmodDesc(a,b) { return (-sortLastmod(a,b)); }

function sortName(a,b) {
   if(a[0] > b[0]) return 1;
   if(a[0] < b[0]) return -1;
   return 0;
}
function sortNameDesc(a,b) { return -sortName(a,b); }
//document.write('http://'+location.hostname);

function getSort(){
  var s = getQueryVariable("sort");
  var d = getQueryVariable("sortdir");
  if(s==='size'){ return d === 'desc' ? sortSizeDesc : sortSize}
  if(s==='name'){ return d === 'desc' ? sortNameDesc : sortName}
  if(s==='lastmod'){ return d === 'desc' ? sortLastmodDesc : sortLastmod}
  return sortName;
}


function getLink(){
  return "             "+getLinkSize() + "  " + getLinkLastmod() + "              " + getLinkName() + "   " ;
}

function getNextSortDir(sortCol){
  if (sortCol === getQueryVariable("sort"))
      return getQueryVariable("sortdir") === 'desc' ? 'asc' : 'desc';
  return 'asc'
}

function getLinkSize(){
  return "<A HREF=\"?sort=size&sortdir=" +getNextSortDir('size') +"\">Size</A>";
}
function getLinkName(){
  return "<A HREF=\"?sort=name&sortdir=" +getNextSortDir('name') +"\">Name</A>";
}
function getLinkLastmod(){
  return "<A HREF=\"?sort=lastmod&sortdir=" +getNextSortDir('lastmod') +"\">Lastmodified</A>";
}
