#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import {OptimizationServiceStack} from './lib/optimization-service-stack';

const app = new cdk.App();
new OptimizationServiceStack(app, 'PicopicOptimizationServiceStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
