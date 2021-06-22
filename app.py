#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

# For consistency with TypeScript code, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core

from pipeline_stack import SampleAppPipelineStack
from cdk_ecs_python_sample.cdk_ecs_python_sample_stack import SampleAppStack


app = core.App()
# Create staging resources
stage_backend = SampleAppStack(
    app,
    "SampleAppStackStage",
    task_cpu=256,
    task_desired_count=1,  # Keep it small in staging to save costs
    task_memory_mib=512,
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    env=core.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=core.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
)
SampleAppPipelineStack(
    app,
    "SampleAppPipelineStackStage",
    env=core.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    backend=stage_backend,
    source_branch="development",
    deploy_env="Stage"
)

# Create Production resources
prod_backend = SampleAppStack(
    app,
    "SampleAppStackProd",
    task_cpu=512,
    task_desired_count=2,  # 2 tasks in 2 AZ minimum for High Availability
    task_memory_mib=1024,
    env=core.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)
SampleAppPipelineStack(
    app,
    "SampleAppPipelineStackProd",
    env=core.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    backend=prod_backend,
    source_branch="master",
    deploy_env="Prod",

)
app.synth()
