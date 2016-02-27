import cherrypy
import os
import sys
import json

currDir =  os.path.abspath(os.path.dirname(__file__))
libDir = currDir + '/../lib'
sys.path.append(libDir)
#sys.path.insert(0, r'/')
#importdir.do(libDir, globals())
import importdir
importdir.do(libDir, globals())

def import_from(module, name,str):
    module = __import__(module, fromlist=[name])
    v = getattr(module, name)(str)
    return v

@cherrypy.popargs('function')
class automation_rest_api(object):

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self,function):
       cherrypy.log ('function name: ' + function)
       if not(os.path.exists(libDir + '/' + function + '.py')):
          return 'FATAL: Invalid function'
       outJson = {}
       JsonArgs = cherrypy.request.json
       mods = [m.__name__ for m in sys.modules.values() if m]
       outJson = import_from(function,function,JsonArgs)
       return json.dumps(outJson)
                                   
if __name__ == '__main__':
    cherrypy.quickstart(automation_rest_api(),'/')
    #main()