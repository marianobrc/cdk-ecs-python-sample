#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

# For consistency with TypeScript code, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core

from common_resources_stack import CommonResourcesStack
from pipeline_stack import SampleAppPipelineStack
from cdk_ecs_python_sample.cdk_ecs_python_sample_stack import SampleAppStack


app = core.App()
# Create staging resources
common_resources_stage = CommonResourcesStack(
    app,
    "CommonResourcesStackStage",
    deploy_env="Stage",
    env=core.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)
stage_backend = SampleAppStack(
    app,
    "SampleAppStackStage",
    ecr_repo=common_resources_stage.ecr_repo,
    task_cpu=256,
    task_desired_count=1,  # Keep it small in staging to save costs
    task_memory_mib=512,
    env=core.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
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
common_resources_prod = CommonResourcesStack(
    app,
    "CommonResourcesStackProd",
    deploy_env="Prod",
    env=core.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)
prod_backend = SampleAppStack(
    app,
    "SampleAppStackProd",
    ecr_repo=common_resources_prod.ecr_repo,
    task_cpu=512,
    task_desired_count=2,  # 2 tasks in 2 AZ minimum for High Availability
    task_memory_mib=1024,
    deploy_env="Prod",
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
