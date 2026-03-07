const { DynamoDBClient, PutItemCommand } = require('@aws-sdk/client-dynamodb');

exports.handler = async (event) => {
  if (event.RequestType !== 'Create') {
    return { PhysicalResourceId: event.PhysicalResourceId || 'SeedPolicies' };
  }
  const { TableName, Policies } = event.ResourceProperties;
  const client = new DynamoDBClient({});
  for (const policy of Policies) {
    try {
      await client.send(
        new PutItemCommand({
          TableName,
          Item: policy,
          ConditionExpression: 'attribute_not_exists(policy_id)',
        })
      );
    } catch (e) {
      if (e.name !== 'ConditionalCheckFailedException') throw e;
    }
  }
  return { PhysicalResourceId: 'SeedPolicies' };
};
