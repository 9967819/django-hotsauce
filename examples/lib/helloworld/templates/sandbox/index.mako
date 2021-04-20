## coding: utf-8 

<% 
from django import get_version
local_version = data['local_version']
django_version = get_version()
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>Welcome page</title>
<style type="text/css" media="screen">
body { 
background: #d0d0d0; 
font-family: Bitstream Vera Sans, sans-serif; 
font-size: 100%; }
#page { background: #ffffff; margin: 50px; border: 2px solid #c0c0c0; padding: 10px; }
#header { background: #4b6983; border: 2px solid #d0d0d0; text-align: center; padding: 10px; color: #ffffff; }
#header h1 { color: #ffffff; }
#body {padding: 10px;}
#body h2 {background: #d0d0d0; color: #4b6983; padding: 0.6em}
.tt { font-family: monospace; }
.bold { font-weight: bold; }
a:link { color: #4b6983; }
</style>
</head>
<body>
<div id="page">
 <div id="header">
 <h1>Welcome to notmm ${local_version}!</h1>
 </div>
 <div id="body">
    <h1>It's working!</h1>
    <p>Congratulations for having successfully configured this demo app!</p>
    <p>Reported Django version is: <span class="tt">${django_version}</span></p>

    <img src="img/notmm-logo-v4-300x147.png" title="notmm is not a monolithic mashup!"/>
    <img src="img/kick_camels_but.gif" alt="Powered by Python" />
    
    <p>You can subscribe to the discussion group
    <a href="http://groups.google.ca/group/notmm-discuss/subscribe">here</a>.</p>
    <h2>Documentation</h2>
    <ul>
    <li>
    <a href="http://gthc.org/projects/notmm/refapi/" title="API Reference">API Reference</a>
    </li>
    <li>
    <a href="http://gthc.org/projects/notmm/" title="Official website">Official Website</a>
    </li>
    <li>
    <a href="http://gthc.org/wiki/" title="Wiki">Wiki</a>
    </ul>
    
    <h2>Artworks</h2>
    <p>Feel free to put the following logos on your website or blog:</p>

    <img src="img/notmm-logo-v5-200x199.png" title="Pepe is not a pony!" />
  </div>
</div>
</body>
</html>
