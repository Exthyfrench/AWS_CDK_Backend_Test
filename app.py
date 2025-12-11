#!/usr/bin/env python3
import os

import aws_cdk as cdk

from python_testing.python_testing_stack import PythonTestingStack
from python_testing.api_gateway_stack import ApiGatewayStack


app = cdk.App()
main_stack = PythonTestingStack(app, "PythonTestingStack")
api_stack = ApiGatewayStack(app, "ApiGatewayStack",
    agent_id=main_stack.agent.attr_agent_id,
    agent_alias_id=main_stack.agent_alias.attr_agent_alias_id
)

app.synth()
