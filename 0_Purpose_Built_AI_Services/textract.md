![Amazon Textract](img/textract.png)

# Amazon Textract: Document Text and Data Extraction

Amazon Textract is a machine learning service that automatically extracts text, forms, and tables from documents using optical character recognition (OCR).

## Features
- Text extraction from documents and images
- Form data extraction (key-value pairs)
- Table extraction with structure preservation
- Identity document analysis
- Receipt and invoice analysis

## Use Cases
- Automating document processing and data entry
- Extracting data from forms and invoices
- Converting scanned documents to searchable text
- Processing insurance claims and medical records
- Digitizing paper-based workflows

## Example
### Using AWS SDK (Python boto3) to extract text, forms, and tables from a document

```python
import boto3

client = boto3.client('textract')

# Read document
with open('document.pdf', 'rb') as document:
    # Analyze document with forms and tables
    response = client.analyze_document(
        Document={'Bytes': document.read()},
        FeatureTypes=['FORMS', 'TABLES']
    )

# Extract text blocks
for block in response['Blocks']:
    if block['BlockType'] == 'LINE':
        print(f"Text: {block['Text']}")
    elif block['BlockType'] == 'KEY_VALUE_SET':
        # KEY_VALUE_SET blocks represent form fields (keys and values)
        # Note: To get the actual text, you need to follow Relationships to child WORD blocks
        if 'KEY' in block.get('EntityTypes', []):
            print(f"Found form key (block ID: {block['Id']})")
```

[Back to menu](README.md)

