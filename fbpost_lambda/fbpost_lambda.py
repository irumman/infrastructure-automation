#!/bin/python

from datetime import datetime
import logging, os
import requests
import boto3, botocore
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr


'''
Input: 
json with following keys:
fb_access_token  
fb_post_data = { "message" : "message want to post"} / for reply add { "message" : "message want to post" , "parent" : comment_id }
comment_after_post = { "message" : "comment after post"} ; only allowed with post_type = post; this is to post comment immediately after post
fb_node_id ( groupId to post/postId to add comment/ commentId to add reply)
post_type ( post/comment)
dynamodb{table, key_attr, key_value, sort_key_attr, sort_key_value, fb_post_attr,fb_post_attr_for_comment_after_post, comment_key_value}
{
	"fb_post_data" : { "message" : "this is test from lambda" },
	"comment_after_post" : { "message" : "this is comment after post" },
	"fb_node_id" : "1808415652727018",
	"post_type" : "post"
}
'''
GRAPH_URL_PREFIX = 'https://graph.facebook.com/'

def get_token(s3FilePath):

   s3c = boto3.client('s3')  
   s3FilePath = s3FilePath.replace('s3://','').split('/')
   bucket = s3FilePath[0]
   del  s3FilePath[0]
   s3file =  '/'.join(s3FilePath)
   response = s3c.get_object(Bucket=bucket, Key=s3file)
   content = response['Body'].read().decode('utf-8')
   return content.replace('\n','')

def buildHeader(s3FilePath):
    acces_token = get_token(s3FilePath) 
    return {'Authorization': 'Bearer ' + acces_token}


def fbPost(s3FilePath,node_id,data,post_type):
	vHeaders = buildHeader(s3FilePath)
	vUrl = GRAPH_URL_PREFIX + node_id + '/'

	if post_type == 'comment':
		vUrl = vUrl + 'comments' 
	else:
		vUrl = vUrl + 'feed'
	logging.warning(vUrl)		
	try:
		result = requests.post(vUrl, headers=vHeaders, data=data)
		vFbPostId = eval(result.text)['id']
		logging.warning('FbPostId = ' + str(vFbPostId))
		return vFbPostId
	except Exception as err:
		logging.warning('FATAL:' + str(err))
		sys.exit(0) 

#def dynamodbStore(table, key_attr, key_value, sort_key_attr, sort_key_value, fb_post_attr, fb_post_id):
def dynamodbStore(dynamodb_info,fb_post_id):
	logging.warning('In dynamodbStore:')
	logging.warning(dynamodb_info)
	dmo_c = boto3.client('dynamodb')
	dmo_r = boto3.resource('dynamodb')
	table=dmo_r.Table(dynamodb_info['table'])
	try:
		response = table.update_item(Key={dynamodb_info['key_attr']:dynamodb_info['key_value'], dynamodb_info['sort_key_attr']: dynamodb_info['sort_key_value'] },
				UpdateExpression="set "  +  dynamodb_info['fb_post_attr'] + " = :v",
				ExpressionAttributeValues={
				":v" : fb_post_id
			},
			ReturnConsumedCapacity='TOTAL'
			)
		logging.warning(response)
	except ClientError as err:
		logging.warning(str(err))
	return 0


def lambda_handler(event,context):
    logging.basicConfig(level=logging.WARNING, format = '%(asctime)s - %(levelname)s - %(message)s' )
    data = eval(event['Records'][0]['Sns']['Message'])
    #data = {"comment_after_post": "battery started at 2017-01-13 23:33:47", "fb_post_data": {"message": "Insight started ... \nCarrier : RAK\nPipeline Name : PSS-BDP-DEV-DP-ATT-INSIGHTS-SCHEDULED\nEmr Ip : 100.104.117.243\nEmr Name : df-05297832BTBYRX0WVYLF_@EmrClusterObj_2017-01-08T21:21:17"}, "fbTokenS3FilePath": "s3://pss-bdp-dev-files/fbtokens/fb_token.txt", "fb_node_id": "1374429862578535", "dynamodb": {"key_value": "RAK", "sort_key_attr": "skey", "comment_key_value": "20170113_j-3FBEM1N1Y16V5_battery", "key_attr": "key", "fb_post_attr_for_comment_after_post": "fbPostId", "sort_key_value": "20170113_j-3FBEM1N1Y16V5_emr", "table": "PSS_BDP_DEV_JOB_STATUS_REPORT", "fb_post_attr": "fbPostId"}, "post_type": "post"}

    logging.warning(data)
    #data={"fb_post_data" : { "message" : "this is test from lambda" },"fb_node_id" : "1808415652727018","post_type" : "post"}
    vFbPostId = fbPost(data['fbTokenS3FilePath'],data['fb_node_id'],data['fb_post_data'],data['post_type'])

    if data.has_key('dynamodb'):
    	dynamodbStore(data['dynamodb'],vFbPostId)

	if data.has_key('comment_after_post'):
		logging.warning('Adding comment after post ...')
		data['dynamodb']['fb_post_attr'] = data['dynamodb']['fb_post_attr_for_comment_after_post']
		data['dynamodb']['sort_key_value'] = data['dynamodb']['comment_key_value']
		data['fb_post_data'] = { "message" : data['comment_after_post'] }
		vFbCommentPostId = fbPost(data['fbTokenS3FilePath'],vFbPostId,data['fb_post_data'],'comment')
		logging.warning('Done')
		logging.warning('Updating dynamodb record ...')
		if data.has_key('dynamodb'):
			dynamodbStore(data['dynamodb'],vFbCommentPostId)
		logging.warning('Done')	

    return 0
'''    
if __name__ == "__main__":
	event = { "fbTokenS3FilePath" : "s3://pss-bdp-poc/ahmad/fb_token.txt" , "fb_post_data" : { "message" : "this is test from lambda" },"fb_node_id" : "1808415652727018","post_type" : "post", "dynamodb" : { "table" : "PSS_BDP_POC_JOB_STATUS_REPORT", "key_attr" : "carrier", "key_value" : "rak", "sort_key_attr":"dt", "sort_key_value":"20170105_j-xxxxxx", "fb_post_attr":"bufbPostId"}}
	context = 'test'
	lambda_handler(event,context)
'''