from aws_cdk import core as cdk, aws_route53

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core
from aws_cdk import (core, aws_ec2 as ec2, aws_ecs as ecs, aws_iam as iam, aws_ecr as ecr,
                     aws_ecs_patterns as ecs_patterns)
from aws_cdk.aws_ec2 import (GatewayVpcEndpoint, GatewayVpcEndpointAwsService,
                             InterfaceVpcEndpointAwsService, GatewayVpcEndpointProps, InterfaceVpcEndpoint,
                             InterfaceVpcEndpointProps)
from aws_cdk.aws_iam import ServicePrincipal


class SampleAppStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # The repository where images of this app will be stored
        self.ecr_repo = ecr.Repository(self, 'cdk-ecs-sample-ecr-repo')

        # Our network in the cloud
        self.vpc = ec2.Vpc(
            self,
            "SampleAppVpc",
            max_azs=2,  # default is all AZs in region
            nat_gateways=0,  # Save costs and gain in performance and security
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        # Add VPC endpoints for ECR, S3 and CloudWatch to avoid using NAT GWs
        self.s3_private_link = GatewayVpcEndpoint(
            self,
            "SampleAppS3GWEndpoint",
            vpc=self.vpc,
            service=GatewayVpcEndpointAwsService.S3
        )
        self.ecr_api_private_link = InterfaceVpcEndpoint(
            self,
            "SampleAppECRapiEndpoint",
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.ECR,
            open=True,
            private_dns_enabled=True
        )
        self.ecr_dkr_private_link = InterfaceVpcEndpoint(
            self,
            "SampleAppECRdkrEndpoint",
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.ECR_DOCKER,
            open=True,
            private_dns_enabled=True
        )
        cloudwatch_private_link = InterfaceVpcEndpoint(
            self,
            "SampleAppCloudWatchEndpoint",
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            open=True,
            private_dns_enabled=True
        )

        cluster = ecs.Cluster(self, "SampleAppCluster", vpc=self.vpc)
        # Allow ECS tasks to pull images from ECR while provisioning
        # ecs_task_execution_role = iam.Role(
        #     self, "SampleAppEcsTaskExecutionRole",
        #     assumed_by=ServicePrincipal('ecs-tasks.amazonaws.com'),
        #     managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")]
        # )
        # Create the load balancer, ECS service and tasks
        self.container_name = "ecs-sample-app"
        self.alb_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "SampleAppBackendAPIService",
            #domain_name="api.quick-pay.com",
            #certificate=aws_route53.IHostedZone,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cluster=cluster,  # Required
            cpu=256,  # Default is 256
            desired_count=1,  # Default is 1
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("./backend/"),
                # image=ecs.ContainerImage.from_ecr_repository(
                #     repository=ecr.Repository.from_repository_arn(
                #         self,
                #         "SampleAppECRSourceRepo",
                #         repository_arn="arn:aws:ecr:us-east-1:675985711616:repository/ecs-python-sample"
                #     ),
                #     tag="latest"
                # ),
                container_port=5000,
                container_name=self.container_name
                #execution_role=ecs_task_execution_role,
                #task_role=ecs_task_execution_role
            ),
            memory_limit_mib=512,  # Default is 512
            public_load_balancer=True
        )
