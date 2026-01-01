import boto3
import logging
import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from exceptions import TextractError

logger = logging.getLogger(__name__)


class TextractService:
    def __init__(self, region_name: str = "us-east-1", s3_bucket: Optional[str] = None):
        self.client = boto3.client('textract', region_name=region_name)
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.region_name = region_name
        self.s3_bucket = s3_bucket
    
    def _analyze_document_sync(self, document_bytes: bytes, is_pdf: bool = False) -> Dict[str, Any]:
        """Analyze document using Textract (sync for images, async for PDFs)."""
        try:
            if is_pdf:
                # For PDFs, use asynchronous API
                return self._analyze_pdf_sync(document_bytes)
            else:
                # For images, use synchronous API
                response = self.client.analyze_document(
                    Document={'Bytes': document_bytes},
                    FeatureTypes=['FORMS', 'TABLES']
                )
                return self._process_textract_response(response)
        except ClientError as e:
            error_msg = f"Textract ClientError: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise TextractError(error_msg) from e
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise TextractError(error_msg) from e
    
    def _analyze_pdf_sync(self, document_bytes: bytes) -> Dict[str, Any]:
        """Analyze PDF using asynchronous Textract API. Requires S3 for PDFs."""
        s3_key = None
        try:
            # For PDFs, we need to upload to S3 first
            if not self.s3_bucket:
                raise TextractError(
                    "S3 bucket not configured. PDF processing requires an S3 bucket. "
                    "Set TEXTRACT_S3_BUCKET environment variable."
                )
            
            # Upload PDF to S3 temporarily
            s3_key = f"textract-temp/{uuid.uuid4()}.pdf"
            logger.info(f"Uploading PDF to S3: s3://{self.s3_bucket}/{s3_key}")
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=document_bytes,
                ContentType='application/pdf'
            )
            logger.info(f"PDF uploaded to S3 successfully")
            
            # Start asynchronous document analysis using S3 location
            response = self.client.start_document_analysis(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': self.s3_bucket,
                        'Name': s3_key
                    }
                },
                FeatureTypes=['FORMS', 'TABLES']
            )
            job_id = response['JobId']
            logger.info(f"Started Textract job: {job_id}")
            
            # Poll for completion
            max_attempts = 60  # 5 minutes max (5 second intervals)
            attempt = 0
            
            all_blocks = []
            
            while attempt < max_attempts:
                time.sleep(5)  # Wait 5 seconds between checks
                response = self.client.get_document_analysis(JobId=job_id)
                status = response['JobStatus']
                
                if status == 'SUCCEEDED':
                    logger.info(f"Textract job {job_id} completed successfully")
                    # Collect all blocks (handle pagination for multi-page PDFs)
                    all_blocks.extend(response.get('Blocks', []))
                    
                    # Check if there are more pages
                    next_token = response.get('NextToken')
                    while next_token:
                        logger.info(f"Fetching next page for job {job_id}")
                        response = self.client.get_document_analysis(JobId=job_id, NextToken=next_token)
                        all_blocks.extend(response.get('Blocks', []))
                        next_token = response.get('NextToken')
                    
                    # Create a response-like dict with all blocks
                    full_response = {'Blocks': all_blocks}
                    return self._process_textract_response(full_response)
                    
                elif status == 'FAILED':
                    error_msg = response.get('StatusMessage', 'Unknown error')
                    logger.error(f"Textract job {job_id} failed: {error_msg}")
                    raise TextractError(f"Textract job failed: {error_msg}")
                elif status in ['IN_PROGRESS', 'PARTIAL_SUCCESS']:
                    attempt += 1
                    logger.debug(f"Textract job {job_id} still in progress (attempt {attempt}/{max_attempts})")
                    continue
                else:
                    raise TextractError(f"Unknown job status: {status}")
            
            raise TextractError("Textract job timed out")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            full_error = f"Textract PDF ClientError [{error_code}]: {error_msg}"
            logger.error(full_error, exc_info=True)
            raise TextractError(full_error) from e
        except Exception as e:
            error_msg = f"Error processing PDF: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise TextractError(error_msg) from e
        finally:
            # Clean up S3 object
            if s3_key:
                try:
                    self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
                    logger.info(f"Cleaned up S3 object: s3://{self.s3_bucket}/{s3_key}")
                except Exception as e:
                    logger.warning(f"Failed to delete S3 object {s3_key}: {str(e)}")
    
    def _process_textract_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process Textract response into structured format."""
        blocks = response.get('Blocks', [])
        
        result = {
            "full_text": "",
            "forms": [],
            "tables": [],
            "key_value_pairs": []
        }
        
        # Build text from LINE blocks
        lines = [block for block in blocks if block['BlockType'] == 'LINE']
        result["full_text"] = "\n".join([line.get('Text', '') for line in lines])
        
        # Extract key-value pairs from FORMS
        key_value_map = {}
        for block in blocks:
            if block['BlockType'] == 'KEY_VALUE_SET':
                entity_type = block.get('EntityTypes', [])
                if 'KEY' in entity_type:
                    key_value_map[block['Id']] = {
                        'key': self._get_text(block, blocks),
                        'value_id': None
                    }
                elif 'VALUE' in entity_type:
                    for key_id, kv in key_value_map.items():
                        if kv['value_id'] is None:
                            relationships = block.get('Relationships', [])
                            for rel in relationships:
                                if rel['Type'] == 'CHILD' and key_id in rel.get('Ids', []):
                                    kv['value_id'] = block['Id']
                                    kv['value'] = self._get_text(block, blocks)
                                    break
        
        result["key_value_pairs"] = [
            {"key": kv['key'], "value": kv.get('value', '')}
            for kv in key_value_map.values() if kv.get('value')
        ]
        
        # Extract tables
        tables = []
        for block in blocks:
            if block['BlockType'] == 'TABLE':
                table_data = self._extract_table(block, blocks)
                if table_data:
                    tables.append(table_data)
        
        result["tables"] = tables
        
        return result
    
    async def analyze_document(self, document_bytes: bytes, is_pdf: bool = False) -> Dict[str, Any]:
        """Analyze document using Textract (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._analyze_document_sync,
            document_bytes,
            is_pdf
        )
    
    def _get_text(self, block: Dict, blocks: List[Dict]) -> str:
        """Extract text from a block by following relationships."""
        text = ""
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship.get('Ids', []):
                        child = next((b for b in blocks if b['Id'] == child_id), None)
                        if child and child['BlockType'] == 'WORD':
                            text += child.get('Text', '') + " "
        return text.strip()
    
    def _extract_table(self, table_block: Dict, blocks: List[Dict]) -> Dict[str, Any]:
        """Extract table structure from table block."""
        cells = []
        for relationship in table_block.get('Relationships', []):
            if relationship['Type'] == 'CHILD':
                for cell_id in relationship.get('Ids', []):
                    cell = next((b for b in blocks if b['Id'] == cell_id), None)
                    if cell and cell['BlockType'] == 'CELL':
                        cell_text = self._get_text(cell, blocks)
                        cells.append({
                            "text": cell_text,
                            "row_index": cell.get('RowIndex', 0),
                            "column_index": cell.get('ColumnIndex', 0)
                        })
        
        # Organize into rows
        rows = {}
        for cell in cells:
            row_idx = cell['row_index']
            if row_idx not in rows:
                rows[row_idx] = []
            rows[row_idx].append(cell)
        
        # Sort cells in each row by column index
        for row_idx in rows:
            rows[row_idx].sort(key=lambda x: x['column_index'])
        
        table_data = {
            "rows": [
                [cell['text'] for cell in rows[row_idx]]
                for row_idx in sorted(rows.keys())
            ]
        }
        
        return table_data

