

from aws_cdk import core as cdk
# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import (core, aws_ecr as ecr, aws_ec2 as ec2)
from aws_cdk.aws_ec2 import (GatewayVpcEndpoint, GatewayVpcEndpointAwsService,
                             InterfaceVpcEndpointAwsService, InterfaceVpcEndpoint,)


class CommonResourcesStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        deploy_env = kwargs.pop("deploy_env", "prod")
        super().__init__(scope, construct_id, **kwargs)
        self.ecr_repo = ecr.Repository(
            self,
            f'cdk-ecs-sample-ecr-repo-{deploy_env.lower()}',
            repository_name=f"cdk-ecs-sample-ecr-repo-{deploy_env.lower()}"  # Important: keep teh name lowercase
        )
        # Our network in the cloud
        self.vpc = ec2.Vpc(
            self,
            f"SampleAppVpc{deploy_env}",
            max_azs=2,  # default is all AZs in region
            nat_gateways=0,  # Save costs and gain in performance and security
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        # Add VPC endpoints for ECR, S3 and CloudWatch to avoid using NAT GWs
        self.s3_private_link = GatewayVpcEndpoint(
            self,
            f"SampleAppS3GWEndpoint{deploy_env}",
            vpc=self.vpc,
            service=GatewayVpcEndpointAwsService.S3
        )
        self.ecr_api_private_link = InterfaceVpcEndpoint(
            self,
            f"SampleAppECRapiEndpoint{deploy_env}",
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.ECR,
            open=True,
            private_dns_enabled=True
        )
        self.ecr_dkr_private_link = InterfaceVpcEndpoint(
            self,
            f"SampleAppECRdkrEndpoint{deploy_env}",
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.ECR_DOCKER,
            open=True,
            private_dns_enabled=True
        )
        cloudwatch_private_link = InterfaceVpcEndpoint(
            self,
            f"SampleAppCloudWatchEndpoint{deploy_env}",
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            open=True,
            private_dns_enabled=True
        )
