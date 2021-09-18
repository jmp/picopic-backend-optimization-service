# picopic-backend-optimization-service

[![build](https://github.com/jmp/picopic-backend-optimization-service/actions/workflows/build.yml/badge.svg)](https://github.com/jmp/picopic-backend-optimization-service/actions/workflows/build.yml)
[![e2e-tests](https://github.com/jmp/picopic-e2e-tests/actions/workflows/e2e-tests.yml/badge.svg?event=workflow_dispatch)](https://github.com/jmp/picopic-e2e-tests/actions/workflows/e2e-tests.yml)

This is an image optimization service for [Picopic](https://github.com/jmp/picopic).

It consists of [AWS Lambda](https://aws.amazon.com/lambda/) functions
for uploading images to [Amazon S3](https://aws.amazon.com/s3/), then
downloading the optimized images, using S3 pre-signed URLs.

The infrastructure for the backend can be found in the [picopic-backend-infrastructure][1]
repository.

## How it works

Optimizing an image file happens in two steps:

1. Upload an unoptimized image file to an S3 bucket
2. Download an optimized image file from the S3 bucket

A user cannot upload files directly to an S3 bucket, because that would
not be very secure. Instead, the user will do this using [a presigned URL][2].
A presigned URL is a short-lived URL that can be used to upload or download
a file from S3.

The image optimization service exposes two endpoints through the API gateway:

* `/upload-url` for creating a presigned URL for upload
* `/download-url/<key>` for creating a presigned URL for download

To upload an image file to S3, the frontend will send a request to the
`/upload-url` endpoint. The API gateway will forward the request to a
Lambda function that will generate a short-lived presigned URL. This
presigned URL is then returned to the client in the HTTP response. The
presigned URL allows the client to upload a file that meets certain criteria, like maximum
file size. The presigned URL will also contain key for the uploaded file.
The key identifies the file (or *object*) in S3. 

Once the unoptimized image has been uploaded to S3, the client will
send a request to the `/download-url/<key>` endpoint with the object key
received earlier. The API gateway will forward this to a Lambda function
that starts optimizing the image. Once the optimization is complete, the
function will generate a short-lived presigned URL that allows the client
to download the image file from S3. This URL is then sent to the client
in the HTTP response. Using the presigned URL, the client can download
the final, optimized image.

[1]: https://github.com/jmp/picopic-backend-infrastructure
[2]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html