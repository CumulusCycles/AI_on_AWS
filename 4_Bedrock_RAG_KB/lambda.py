import json
import os
import boto3

# --- Config: KB and model from env (no hardcoding) ---
KNOWLEDGE_BASE_ID = os.environ['KNOWLEDGE_BASE_ID']
FOUNDATION_MODEL_ARN = os.environ['FOUNDATION_MODEL_ARN']

SERVICE_NAME = 'bedrock-agent-runtime'
client = boto3.client(SERVICE_NAME)


def _get_query(event):
    """Extract the query string from a Lambda event.

    Checks in order: event['query'], event['queryStringParameters']['query'],
    then event['body'] (parsed as JSON if a string).

    Args:
        event: Lambda invocation event (dict).

    Returns:
        str: The query value, or empty string if not found.
    """
    # 1. Direct invoke: event['query']
    if 'query' in event:
        return event['query']
    # 2. API Gateway GET: queryStringParameters
    if 'queryStringParameters' in event and event['queryStringParameters']:
        return event['queryStringParameters'].get('query', '')
    # 3. API Gateway POST: body (JSON)
    if 'body' in event and event['body']:
        body = event['body']
        if isinstance(body, str):
            body = json.loads(body)
        return body.get('query', '')
    return ''


def lambda_handler(event, _context):
    """Query a Bedrock knowledge base with RAG and return the generated answer and sources.

    Accepts query via event['query'], event['body'] (JSON), or event['queryStringParameters']['query'].

    Returns:
        dict: statusCode, query, generated_response, s3_locations (list of cited S3 URIs)
    """
    # 1. Get query from event (direct / queryString / body)
    query = _get_query(event)

    # 2. RAG: retrieve from KB + generate with foundation model (one call)
    rag_response = client.retrieve_and_generate(
        input={
            'text': query
        },
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                'modelArn': FOUNDATION_MODEL_ARN
            }
        }
    )

    print(f"RAG response: {rag_response}")

    # 3. Collect cited S3 URIs from citations
    citations = rag_response.get('citations', [])
    s3_locations = []
    for citation in citations:
        for ref in citation.get('retrievedReferences', []):
            loc = ref.get('location', {}).get('s3Location', {}).get('uri')
            if loc and loc not in s3_locations:
                s3_locations.append(loc)
    response_text = rag_response['output']['text']

    # 4. Return query, answer, and source locations
    response = {
        'statusCode': 200,
        'query': query,
        'generated_response': response_text,
        's3_locations': s3_locations
    }
    
    print(f"Response: {response}")
    
    return response
        