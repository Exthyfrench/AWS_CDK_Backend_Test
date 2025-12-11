from aws_cdk import (
    Stack,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_iam as iam,
)
from constructs import Construct


class ApiGatewayStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, agent_id: str, agent_alias_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create IAM role for Lambda
        lambda_role = iam.Role(self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "LambdaBasicExecution": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            resources=[f"arn:aws:logs:{self.region}:{self.account}:*"]
                        )
                    ]
                ),
                "BedrockInvokePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["bedrock:InvokeAgent"],
                            resources=[f"arn:aws:bedrock:{self.region}:{self.account}:agent-alias/{agent_id}/*"]
                        )
                    ]
                )
            }
        )

        # Create Lambda function
        invoke_agent_lambda = _lambda.Function(self, "InvokeAgentLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="invoke_agent.handler",
            role=lambda_role,
            environment={
                "AGENT_ID": agent_id,
                "AGENT_ALIAS_ID": agent_alias_id
            }
        )

        # Create API Gateway
        api = apigateway.RestApi(self, "AgentApi",
            rest_api_name="AgentApi",
            description="API for invoking Bedrock Agent"
        )

        # Add resource and method
        invoke_resource = api.root.add_resource("invoke")
        invoke_method = invoke_resource.add_method("POST",
            integration=apigateway.LambdaIntegration(invoke_agent_lambda),
            api_key_required=True,
            method_responses=[
                apigateway.MethodResponse(status_code="200")
            ]
        )

        # Create API Key
        api_key = apigateway.ApiKey(self, "AgentApiKey",
            api_key_name="AgentApiKey",
            value="test-api-key-12345"  # For testing purposes
        )

        # Create Usage Plan
        usage_plan = apigateway.UsagePlan(self, "AgentUsagePlan",
            name="AgentUsagePlan",
            api_stages=[
                apigateway.UsagePlanPerApiStage(
                    api=api,
                    stage=api.deployment_stage
                )
            ]
        )
        usage_plan.add_api_key(api_key)

        # Outputs
        CfnOutput(self, "ApiEndpoint", value=api.url)
        CfnOutput(self, "ApiKeyId", value=api_key.key_id)