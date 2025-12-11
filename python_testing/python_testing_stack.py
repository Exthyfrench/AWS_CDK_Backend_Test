from aws_cdk import (
    # Duration,
    Stack,
    RemovalPolicy,
    # aws_sqs as sqs,
    aws_kms as kms,
    aws_s3 as s3,
    aws_opensearchserverless as opensearchserverless,
    aws_bedrock as bedrock,
    aws_iam as iam,
    aws_logs as logs,
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

        # Create an OpenSearch Serverless collection
        collection = opensearchserverless.CfnCollection(self, "MyOpenSearchCollection",
            name="my-opensearch-collection",
            type="SEARCH"
        )

        # Create IAM role for Bedrock Knowledge Base
        bedrock_role = iam.Role(self, "BedrockKnowledgeBaseRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonOpenSearchServiceFullAccess"),
            ]
        )

        # Allow the role to use the KMS key
        kms_key.grant_encrypt_decrypt(bedrock_role)

        # Grant the role read access to the S3 bucket
        bucket.grant_read(bedrock_role)

        # Create Bedrock Knowledge Base
        knowledge_base = bedrock.CfnKnowledgeBase(self, "MyKnowledgeBase",
            name="my-knowledge-base",
            role_arn=bedrock_role.role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0:8k"
                )
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configuration=bedrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn=collection.attr_arn,
                    vector_index_name="bedrock-knowledge-base-index",
                    field_mapping=bedrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        vector_field="vector",
                        text_field="text",
                        metadata_field="metadata"
                    )
                )
            ),
            description="Knowledge base using OpenSearch Serverless"
        )

        # Create S3 Data Source for Knowledge Base
        data_source = bedrock.CfnDataSource(self, "MyDataSource",
            knowledge_base_id=knowledge_base.attr_knowledge_base_id,
            name="my-s3-data-source",
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=bucket.bucket_arn,
                    inclusion_prefixes=["documents/"]  # Assuming documents are in this prefix
                ),
                type="S3"
            ),
            description="S3 data source for ingesting documents into the knowledge base"
        )

        # Create Bedrock Guardrail
        guardrail = bedrock.CfnGuardrail(self, "TestGuardrail",
            name="TestGuardrail",
            description="Guardrail to prevent foul language, PII, PHI, and inappropriate content",
            blocked_input_messaging="I cannot respond to that request.",
            blocked_outputs_messaging="I cannot provide that response.",
            word_policy_config=bedrock.CfnGuardrail.WordPolicyConfigProperty(
                words_config=[],
                managed_word_lists_config=[
                    bedrock.CfnGuardrail.ManagedWordsConfigProperty(
                        type="PROFANITY"
                    )
                ]
            ),
            sensitive_information_policy_config=bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty(
                pii_entities_config=[
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="NAME",
                        action="BLOCK"
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="EMAIL",
                        action="BLOCK"
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="PHONE",
                        action="BLOCK"
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="ADDRESS",
                        action="BLOCK"
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="SSN",
                        action="BLOCK"
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="DRIVER_ID",
                        action="BLOCK"
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="BANK_ACCOUNT",
                        action="BLOCK"
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="CREDIT_DEBIT_CARD",
                        action="BLOCK"
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="MEDICAL_RECORD_NUMBER",
                        action="BLOCK"
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="HEALTH_INSURANCE_ID",
                        action="BLOCK"
                    )
                ]
            ),
            topic_policy_config=bedrock.CfnGuardrail.TopicPolicyConfigProperty(
                topics_config=[
                    bedrock.CfnGuardrail.TopicConfigProperty(
                        name="Adult Content",
                        definition="Content related to sexual or explicit topics",
                        type="DENY"
                    )
                ]
            )
        )

        # Create Bedrock Agent
        agent = bedrock.CfnAgent(self, "Testbedrockagent",
            agent_name="Testbedrockagent",
            description="An AI assistant for handling queries and tasks for humans",
            instruction="You are a helpful assistant than answers qestions based on the provided knowledge and can perform actions when needed",
            foundation_model="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
            agent_resource_role_arn=bedrock_role.role_arn,
            guardrail_configuration=bedrock.CfnAgent.GuardrailConfigurationProperty(
                guardrail_identifier=guardrail.attr_guardrail_id,
                guardrail_version="DRAFT"
            )
        )

        # Associate Knowledge Base with Agent using property override
        agent.add_property_override("KnowledgeBaseAssociations", [
            {
                "KnowledgeBaseId": knowledge_base.attr_knowledge_base_id,
                "Description": "Association between agent and knowledge base"
            }
        ])

        # Create Agent Alias
        agent_alias = bedrock.CfnAgentAlias(self, "TestAgentAlias",
            agent_id=agent.attr_agent_id,
            agent_alias_name="Test",
            description="Alias for invoking the Testbedrockagent"
        )

        # Create CloudWatch Log Group for Agent Logging
        agent_log_group = logs.LogGroup(self, "AgentLogGroup",
            log_group_name="/aws/bedrock/agents/Testbedrockagent",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Outputs
        CfnOutput(self, "KmsKeyArn", value=kms_key.key_arn)
        CfnOutput(self, "S3BucketArn", value=bucket.bucket_arn)
        CfnOutput(self, "OpenSearchCollectionArn", value=collection.attr_arn)
        CfnOutput(self, "KnowledgeBaseId", value=knowledge_base.attr_knowledge_base_id)
        CfnOutput(self, "DataSourceId", value=data_source.attr_data_source_id)
        CfnOutput(self, "AgentId", value=agent.attr_agent_id)
        CfnOutput(self, "AgentAliasId", value=agent_alias.attr_agent_alias_id)
        CfnOutput(self, "AgentLogGroupName", value=agent_log_group.log_group_name)
