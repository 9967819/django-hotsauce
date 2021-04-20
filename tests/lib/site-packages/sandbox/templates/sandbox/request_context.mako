## -*- coding: utf-8 -*-

<%
cat = data['cat']
%>

<html>
<head>
    <title>Test page</title>
</head>
<body>
${header(cat)}
</body>
</html>
<%def name="header(foo)">
    Hello, ${foo}
</%def>

