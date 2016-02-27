import cherrypy
import os
import json
import paramiko
import time

currDir =  os.path.abspath(os.path.dirname(__file__))

def open_ssh_connection(targetHost,targetUser,targetUserPassword=None):

    ssh = paramiko.SSHClient()
    #ssh.load_system_host_keys('/Users/ahmad.iftekhar/.ssh/known_hosts')
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if not targetUserPassword:
       ssh.connect(hostname=targetHost, username=targetUser,timeout=20)
    else:
       ssh.connect(hostname=targetHost, username=targetUser,password=targetUserPassword,timeout=20)
    return ssh


def remote_linux_exec(JsonArgs):
    try:
        # load JSON to dictionary variable
        vJsonArgs = {}
        outJson = {}
        vRemoteTmpFile= currDir + '/../tmp/remote_linux_exec.tmp.'+ str(time.time())+'.sh'
        for vJsonArgs in JsonArgs: 
          #print vJsonArgs
          outJson[vJsonArgs['name']] = {}
          if 'targetUser' not in vJsonArgs:  
            vJsonArgs['targetUser'] = 'postgres'
          
          if ('targetHost' not in vJsonArgs) or (vJsonArgs['targetHost'] == "" ):
            raise Exception("Missing arguments; Required: targetHost,script; Optional: targetUser ")

          if ('script' in vJsonArgs) and ('command' in vJsonArgs):
            raise Exception("script and command are mutually exclusive")
          elif ('command' in vJsonArgs):
            vExecScript = 0
          else:
            vExecScript = 1  

          #Reading the script file. If file not exists, it'll throw an error
          if vExecScript == 1:
            vScriptFile = currDir + '/../scripts/'  + vJsonArgs['script']

            if os.path.exists(vScriptFile) == False:
                raise Exception('Script not found at ' + vScriptFile)
            vFileName,vFileExtension = os.path.splitext(vScriptFile)
            if vFileExtension == '.sh':
                vShell = 'sh'
            elif vFileExtension == '.py':
                vShell = 'python'
            elif vFileExtension == '.pl':        
                vShell = 'perl'
            else:
                vShell = ''    
            
          
          if type(vJsonArgs['targetHost']) is list:
            vTargetHostList = vJsonArgs['targetHost']
          else:  
            vTargetHostList = vJsonArgs['targetHost'].split(',')
          
          
          #for eachHost in vTargetHostList:
          #    print eachHost
          for eachHost in vTargetHostList:
            try:
              lemsg = {}
              vExitStatus = 0
              cherrypy.log('Set ' + vJsonArgs['name'] + ': Executing  on ' + eachHost + ' for user "' + vJsonArgs['targetUser'] +'"' )
              # Open SSH connetion
              if ('UserPassword' not in vJsonArgs) or (vJsonArgs['UserPassword'] == "" ):
                 vPassword = ''
              else:
                 vPassword =  vJsonArgs['UserPassword']

              vSsh = open_ssh_connection(eachHost,vJsonArgs['targetUser'],vPassword )
              
              if vExecScript == 1:
                #Execute the script remotely 
                sftp=vSsh.open_sftp()
                sftp.put(vScriptFile,vRemoteTmpFile)
                vCMD = vShell + ' ' + vRemoteTmpFile
              else:
                vCMD = vJsonArgs['command']  
              
              vChannel = vSsh.get_transport().open_session()
              if ('daemon' in vJsonArgs) and (vJsonArgs['daemon'] == "true" ):
                vChannel.exec_command( vCMD + ' &  \n echo "pid=$!" '  ) 
                vCmdOut =  vChannel.recv(1024)
                vCmdErr = vChannel.recv_stderr(1024)
                vExitStatus = 0
              else:    
                vChannel.exec_command( vCMD ) 
                vExitStatus =  str(vChannel.recv_exit_status())
                vCmdOut =  vChannel.recv(10240) #Capturing 1MB of stdout
                vCmdErr = vChannel.recv_stderr(1024)

              #Remove copied script file
              stdin, stdout, stderr = vSsh.exec_command('rm ' + vRemoteTmpFile)
              #Closing SSH connection
              vSsh.close()
                
              if int(vExitStatus) == 0:
                lemsg = {
                 'host'  : eachHost,
                 'daemon': vJsonArgs['daemon'],
                 'status': 'successful',
                 'scriptOutput' : str(vCmdOut),
                 'exit_status'  : vExitStatus  
                 }
                #print ('-----------' + str(lemsg))
                
              else:
                raise Exception(vCmdErr)
            except Exception as  e:   
              lemsg = {
                'host'  : eachHost,
                'daemon': vJsonArgs['daemon'],
                'status': 'failue',
                'scriptOutput' : str(e),
                'exit_status'  : vExitStatus  
              }
               
            
            outJson[vJsonArgs['name']][eachHost] = lemsg 
    except Exception as  e:
          # send 500 message header code to client
          #print e
          #raise cherrypy.HTTPError(500)


          # failure JSON message
          lemsg = {
          'status': 'failure',
          'execution': 'failed',
          'errorMessage': str(e)
          }
          outJson[vJsonArgs['name']]['programError'] = lemsg
    return json.dumps(outJson) #.encode('utf8')


