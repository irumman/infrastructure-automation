#Directory structure : rest_api ( api, scripts)

import cherrypy
import os
import json
import time
import simplejson
import sys
import psycopg2 as pg
import csv
import boto3
from boto3.s3.transfer import S3Transfer
from datetime import datetime
import time


currDir =  os.path.abspath(os.path.dirname(__file__))
def pgExecutequery(vHost,vDB,vUser,vPassword,vPort,vQuery):
  global vRows
  global vErr
  try:
    vConn = ''
    vCursor = ''
    vconn_string = "dbname='" + vDB +  "' host='" + vHost + "' user='" +  vUser  + "' password='" + vPassword + "' port='" + vPort + "' connect_timeout = 10 options='-c statement_timeout=1000'"  
    vConn=pg.connect(vconn_string)
    vCursor = vConn.cursor()
    vCursor.execute(vQuery)
    vRows = vCursor.fetchall()
    return vRows
  except Exception as  e:
     vErr='ERROR: ' + str(e)
     return vErr

  finally:
    if vCursor:
      vCursor.close()
    if vConn:
      vConn.close()

def upload_to_s3(vFile,vBucket,vS3ObjectName):
  try:
    #If looks for AWS credential in ~/.aws    
    os.environ['AWS_PROFILE'] = 'rumman'
    client = boto3.client('s3')
    #config = TransferConfig(multipart_threshold=8 * 1024 * 1024,max_concurrency=10,num_download_attempts=10)
    transfer = S3Transfer(client)
    results = client.list_objects(Bucket=vBucket)
    #print (results[vBucket])
    vS3ObjectName = 'execute_query_api/' + vS3ObjectName
    transfer.upload_file(vFile, vBucket, vS3ObjectName)
    return 'Uploaded to https://s3.amazonaws.com/' + vBucket + '/' + vS3ObjectName
    #transfer = S3Transfer(client)     
     
  except Exception as e: 
    #print (str(e))
    return 'ERROR: ' + str(e)  


def pg_data_to_s3(JsonArgs):
    try:
        # load JSON to dictionary variable
        TMP_LOCATION='/tmp'
        vJsonArgs = {}
        outJson = {}
        #JsonArgs = cherrypy.request.json
        
        for vJsonArgs in JsonArgs: 
          outJson[vJsonArgs['name']] = {}
          #raise Exception( 'this is pg_data_to_s3' )
          REQUIRED_PARAMETERS=['name','host','db','query','user','password','port','bucket']
          for each in REQUIRED_PARAMETERS:
            #print (each)
            if each not in vJsonArgs:
              raise Exception('Required parameter missing; Required parameters are ' + str(REQUIRED_PARAMETERS) )
             
          if type(vJsonArgs['host']) is list:
            vTargetHostList = vJsonArgs['host']
          else:  
            vTargetHostList = vJsonArgs['host'].split(',')
          #print(vTargetHostList)  
          
          
          #for eachHost in vTargetHostList:
             #print (eachHost)
             #continue
          for eachHost in vTargetHostList:
            try:
              lemsg = {}
              
              cherrypy.log('pg_data_to_s3: Set ' + eachHost + ': Executing query on ' + eachHost  )
              vRows = []
              vRows =  pgExecutequery(eachHost,vJsonArgs['db'],vJsonArgs['user'],vJsonArgs['password'],vJsonArgs['port'],vJsonArgs['query'])
              if type(vRows) is str :
                vOut = vRows
                raise Exception(vOut)
              
              CSV_FILE= vJsonArgs['name'] + '_' + eachHost + '_' + vJsonArgs['db'] + '_' +  str(datetime.now().strftime('%Y%m%d%H%M%S')) + '' + str(time.strftime("%Z")) + '.csv'  
              #print ('creating file ' + vJsonArgs['location'] ) 
              with open(TMP_LOCATION + '/' +  CSV_FILE, 'w') as vCsvFile:
                file_writer = csv.writer(vCsvFile)
                for eachRow in vRows:
                  file_writer.writerow(eachRow)
              
              vOut = 'CSV File created at ' + TMP_LOCATION + '/' +  CSV_FILE
              #vOut = upload_to_s3(TMP_LOCATION + '/' +  CSV_FILE,vJsonArgs['bucket'],CSV_FILE)
              if 'ERROR:' not in vOut:
                lemsg = {
                'host'  : eachHost,
                'db'    : vJsonArgs['db'], 
                'status': 'successful',
                'description' : vOut,
                }
                
              else:
                raise Exception(vOut)
            except Exception as  e:   
              lemsg = {
              'host'  : eachHost,
              'db'    : vJsonArgs['db'], 
              'status': 'failure',
              'description' : str(e),
              }
            outJson[vJsonArgs['name']][eachHost] = lemsg 
            
    except Exception as  e:
          # send 500 message header code to client
          #print e
          #raise cherrypy.HTTPError(500)


          # failure JSON message
          #cherrypy.log('this is erro')
          lemsg = {
          'status': 'failure',
          'execution': 'failed',
          'errorMessage': str(e)
          }
          
          outJson[vJsonArgs['name']]['programError'] = lemsg
    return json.dumps(outJson) #.encode('utf8')







