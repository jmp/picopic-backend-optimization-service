import * as cdk from '@aws-cdk/core';
import * as apigw from '@aws-cdk/aws-apigatewayv2';
import * as integrations from '@aws-cdk/aws-apigatewayv2-integrations';
import * as s3 from '@aws-cdk/aws-s3';
import * as lambda from '@aws-cdk/aws-lambda';
import * as python from '@aws-cdk/aws-lambda-python';

export class OptimizationServiceStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const bucket = new s3.Bucket(this, 'PicopicImageOptimizationBucket', {
      bucketName: 'picopic-images',
      cors: [{
        allowedOrigins: ['https://picopic.io'],
        allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.POST],
        allowedHeaders: ['*'],
      }],
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [{
        abortIncompleteMultipartUploadAfter: cdk.Duration.days(1),
        expiration: cdk.Duration.days(1),
        enabled: true,
      }],
    });

    const createUploadUrlFunction = new python.PythonFunction(this, 'PicopicCreateUploadUrlFunction', {
      entry: 'functions/create-upload-url',
      environment: {BUCKET: bucket.bucketName},
      timeout: cdk.Duration.seconds(10),
      runtime: lambda.Runtime.PYTHON_3_8,
    });
    bucket.grantPut(createUploadUrlFunction);

    const createDownloadUrlFunction = new python.PythonFunction(this, 'PicopicCreateDownloadUrlFunction', {
      entry: 'functions/create-download-url',
      environment: {BUCKET: bucket.bucketName},
      timeout: cdk.Duration.seconds(10),
      runtime: lambda.Runtime.PYTHON_3_8,
      memorySize: 1024,
    });
    bucket.grantReadWrite(createDownloadUrlFunction);

    const httpApi = apigw.HttpApi.fromHttpApiAttributes(this, 'PicopicHttpApiGateway', {
      httpApiId: cdk.Fn.importValue('PicopicHttpApiId')
    });

    new apigw.HttpRoute(this, 'PicopicGetUploadUrlRoute', {
      httpApi,
      routeKey: apigw.HttpRouteKey.with('/upload-url', apigw.HttpMethod.GET),
      integration: new integrations.LambdaProxyIntegration({
        handler: createUploadUrlFunction,
      }),
    });

    new apigw.HttpRoute(this, 'PicopicGetDownloadUrlRoute', {
      httpApi,
      routeKey: apigw.HttpRouteKey.with('/download-url/{key}', apigw.HttpMethod.GET),
      integration: new integrations.LambdaProxyIntegration({
        handler: createDownloadUrlFunction,
      }),
    });
  }
}
