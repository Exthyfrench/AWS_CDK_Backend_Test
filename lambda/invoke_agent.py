import json
import boto3
import os

def handler(event, context):
    client = boto3.client('bedrock-agent-runtime')
    
    agent_id = os.environ['AGENT_ID']
    agent_alias_id = os.environ['AGENT_ALIAS_ID']
    
    body = json.loads(event.get('body', '{}'))
    input_text = body.get('inputText', '')
    session_id = body.get('sessionId', 'default')
    
    response = client.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id,
        inputText=input_text
    )
    
    # Process the streaming response
    completion = ""
    if 'completion' in response:
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'text' in chunk:
                    completion += chunk['text']
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'response': completion,
            'sessionId': session_id
        })
    }