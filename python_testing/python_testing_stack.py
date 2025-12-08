import json
from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_kms as kms,
    aws_s3 as s3,
    aws_opensearchserverless as opensearchserverless,
    CfnOutput,
)
from constructs import Construct

class PythonTestingStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a KMS key
        kms_key = kms.Key(self, "MyKmsKey")

        # Create an S3 bucket encrypted with the KMS key
        bucket = s3.Bucket(self, "MyBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key
        )

        # Encryption security policy for OpenSearch Serverless
        encryption_policy = opensearchserverless.CfnSecurityPolicy(self, "EncryptionPolicy",
            name="encryption-policy",
            type="encryption",
            policy=json.dumps({
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": ["collection/my-collection"],
                        "Encryption": {
                            "KmsKeyId": kms_key.key_id
                        }
                    }
                ],
                "AWSOwnedKey": False
            })
        )

        # Network security policy for OpenSearch Serverless
        network_policy = opensearchserverless.CfnSecurityPolicy(self, "NetworkPolicy",
            name="network-policy",
            type="network",
            policy=json.dumps([
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": ["collection/my-collection"]
                        }
                    ],
                    "AllowFromPublic": True
                }
            ])
        )

        # OpenSearch Serverless collection
        collection = opensearchserverless.CfnCollection(self, "MyCollection",
            name="my-collection",
            type="VECTORSEARCH"
        )

        # Outputs
        CfnOutput(self, "KmsKeyArn", value=kms_key.key_arn)
        CfnOutput(self, "S3BucketArn", value=bucket.bucket_arn)
        CfnOutput(self, "OpenSearchCollectionArn", value=collection.attr_arn)
