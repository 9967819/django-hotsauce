## coding: utf-8 

<% 
from django import get_version
local_version = data['local_version']
django_version = get_version()
media_url = data['media_url']
request = data['request']
if 'REMOTE_USER' in request.environ:
    user = request.environ['REMOTE_USER']
else:
    user = 'anonymous'
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
##<link href="${media_url}favicon.ico" rel="shortcut icon" />
<title>Welcome page</title>
<style type="text/css" media="screen">

body { 
background: #d0d0d0; 
font-family: DejaVu Sans, Bitstream Vera Serif, Helvetica, Verdana, sans-serif; 
font-size: 100%; }
#page { background: #ffffff; margin: 50px; border: 2px solid #c0c0c0; padding: 10px; }
#header { background: #4b6983; border: 2px solid #d0d0d0; text-align: center; padding: 10px; color: #ffffff; }
#header h1 { color: #ffffff; }
#body {padding: 10px;}
#body h2 {background: #d0d0d0; color: #4b6983; padding: 0.6em}
th {background: #d0d0d0; color: #4b6983}
table {border: 2px solid #777; background: #ccc; font-size: 0.9em}
td {border: 1px solid #888; background: #fff}
.tt { font-family: monospace; }
.bold { font-weight: bold; }
.ac {text-align:center}
a:link { color: #4b6983; }
.note{text-align: center; font-weight: bold}
</style>
</head>
<body>
<div id="page">
 <div id="header">
 <h1>Welcome to django-hotsauce-${local_version}, ${user}!</h1>
 </div>
 <div id="body">
    <div class="ac"><h1>It's working!</h1>
    <div class="note">Congratulations for having successfully configured this demo app!
    <p>Reported <a href="http://www.djangoproject.com/">Django</a> version is: <span class="tt">${django_version}</span></p>

    <img src="/kick_camels_butt.gif" alt="Powered by Python" />
    
    </div>
    </div>

##    <h2>Links</h2>
##    <ul>
##    <li>
##     <a href="https://gthc.org/projects/notmm/refapi/" title="API Reference">API Reference</a>
##    </li>
##    <li>
##     <a href="https://gthc.org/projects/notmm/" title="Official website">Official Website</a>
##    </li>
##    <li>
##     <a href="https://gthc.org/wiki/" title="Wiki">Wiki</a>
##    </li>
##    <li>
##     <a href="https://gthc.org/documentation/notmm/handbook/">Developer handbook</a>
##     </li>
##     <li>
##      <a href="https://saya.gthc.org/bugzilla/">Bug tracker</a>
##     </li>
##    </ul>
    
    <h2>Artworks</h2>
    <p>Feel free to put the following logos on your website or blog:</p>
    <table border="0" cellpadding="2">
    <thead>
     <th>Description</th>
     <th>Image file</th>
    </thead>
    <tbody>
    <tr><td>
    <p>notmm is not a monolithic mashup (version 4, 300x147):
    </td><td>
    <img src="notmm-logo-v4-300x147.png" alt="notmm is not a monolithic mashup!"/>
    </td></tr>
    <tr><td>
    0.2.12 diindolylmethane (version 5, 200x199):
    </td><td>
    <img src="notmm-logo-v5-200x199.png" alt="Pepe is not a pony!" />
    </td></tr>
    <tr><td>
    0.3.6 "Sinsemilla" (400x403):</td>
    <td>
    <img src="${media_url}notmm-0.3.6-sensimilla-400x403.png"
    alt="" /></td></tr>
    <tr><td>
    <p>Updated "Powered-by notmm" button:</p></td><td>
    <img src="${media_url}powered-by-notmm.png" alt="Powered by notmm!" />
    </td></tr>
    </tbody>
    </table>
  </div>
</div>
</body>
</html>
