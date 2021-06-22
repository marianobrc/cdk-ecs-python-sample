from aws_cdk import core as cdk, aws_route53

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core
from aws_cdk import (core, aws_ecs as ecs, aws_ecs_patterns as ecs_patterns)


class SampleAppStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        vpc = kwargs.pop("vpc")
        deploy_env = kwargs.pop("deploy_env", "prod")
        task_cpu = kwargs.pop("task_cpu", 256)
        task_desired_count = kwargs.pop("task_desired_count", 2)
        task_memory_mib = kwargs.pop("task_memory_mib", 1024)
        super().__init__(scope, construct_id, **kwargs)

        cluster = ecs.Cluster(self, f"SampleAppCluster{deploy_env}", vpc=vpc)

        # Create the load balancer, ECS service and tasks
        self.container_name = "ecs-sample-app"
        self.alb_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, f"SampleAppBackendAPI{deploy_env}",
            #domain_name="api.quick-pay.com",
            #certificate=aws_route53.IHostedZone,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cluster=cluster,  # Required
            cpu=task_cpu,  # Default is 256
            memory_limit_mib=task_memory_mib,  # Default is 512
            desired_count=task_desired_count,  # Default is 1
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("./backend/"),
                container_port=5000,
                container_name=self.container_name
            ),
            public_load_balancer=True
        )
