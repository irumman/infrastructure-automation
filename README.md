# infrastructure-automation

These are database infrastructure automation script.
>> rest_api: 
from name it suggests it is the rest api which has been build using cherrypy module on python. 

In rest_api
 - api
 - conf
 - lib
 - scripts
 - tmp
 
In api directory, we have automation_rest_api.py

In api
 - automation_rest_api.py

This is the backbone of the rest_api. It takes Json as input and send Json as output. It starts cherrypy engine on 0.0.0.0:8080. With POST operation, it reads the url and get the function name and execute the function from the script directory.
For example:
curl -H "Content-Type: application/json" -d @tmp/in.json -X POST 'localhost:8080/remote_linux_exec/' 
The above one exeuctes the remote_linux_exec function from lib/remote_linux_exec.py
The framework reqruies to have the .py script with the  in lib directory with the same name as URL path and also in that script there must the function with the name same as URL path.

