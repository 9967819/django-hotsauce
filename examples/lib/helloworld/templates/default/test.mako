<%
foo = 'bar'
%>

<html>
<head>
    <title>Test page</title>
</head>
<body>
${header('quux')}
</body>
</html>
<%def name="header(foo)">
    Hello, ${foo} 
</%def>

