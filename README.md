# picopic-backend-optimization-service

This is an image optimization service for the Picopic backend.

It consists of [AWS Lambda](https://aws.amazon.com/lambda/) functions
for uploading images to [Amazon S3](https://aws.amazon.com/s3/), then
downloading the optimized images, using S3 pre-signed URLs.

The infrastructure for the backend can be found in the [picopic-backend-infrastructure][1]
repository.

[1]: https://github.com/jmp/picopic-backend-infrastructure