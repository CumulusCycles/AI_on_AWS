const {
  BedrockAgentClient,
  StartIngestionJobCommand,
  GetIngestionJobCommand,
} = require('@aws-sdk/client-bedrock-agent');

exports.handler = async (event) => {
  const { KnowledgeBaseId, DataSourceId, Region } = event.ResourceProperties || {};
  if (event.RequestType === 'Delete') {
    return { PhysicalResourceId: event.PhysicalResourceId || 'none' };
  }
  const client = new BedrockAgentClient({ region: Region });
  const { ingestionJob } = await client.send(
    new StartIngestionJobCommand({
      knowledgeBaseId: KnowledgeBaseId,
      dataSourceId: DataSourceId,
    })
  );
  const jobId = ingestionJob.ingestionJobId;
  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 10000));
    const { ingestionJob: job } = await client.send(
      new GetIngestionJobCommand({
        knowledgeBaseId: KnowledgeBaseId,
        dataSourceId: DataSourceId,
        ingestionJobId: jobId,
      })
    );
    if (job.status === 'COMPLETE') return { PhysicalResourceId: jobId };
    if (job.status === 'FAILED')
      throw new Error('Ingestion failed: ' + (job.failureReasons || []).join(', '));
  }
  throw new Error('Ingestion timed out after 300s');
};
