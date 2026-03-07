#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BedrockAgentsStack } from '../lib/bedrock-agents-stack';

const app = new cdk.App();

new BedrockAgentsStack(app, 'BedrockAgentsStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? 'us-east-1',
  },
  description: 'AI Agent Insure — Bedrock Agent, Knowledge Base, Lambda action group',
});
