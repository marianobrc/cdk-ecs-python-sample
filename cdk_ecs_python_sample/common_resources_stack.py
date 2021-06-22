

from aws_cdk import core as cdk
# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import (core, aws_ecr as ecr,)


class CommonResourcesStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        deploy_env = kwargs.pop("deploy_env", "prod")
        super().__init__(scope, construct_id, **kwargs)
        self.ecr_repo = ecr.Repository(
            self,
            f'cdk-ecs-sample-ecr-repo-{deploy_env.lower()}',
            repository_name=f"cdk-ecs-sample-ecr-repo-{deploy_env.lower()}"  # Important: keep teh name lowercase
        )
