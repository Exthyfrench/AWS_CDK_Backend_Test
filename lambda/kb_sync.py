import json
import boto3
import os

def handler(event, context):
    client = boto3.client('bedrock-agent')
    
    data_source_id = os.environ['DATA_SOURCE_ID']
    knowledge_base_id = os.environ['KNOWLEDGE_BASE_ID']
    
    try:
        response = client.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Ingestion job started successfully',
                'ingestionJob': response['ingestionJob']
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }