from aws_cdk.core import Stack, StackProps, Construct, SecretValue
from aws_cdk.pipelines import CdkPipeline, SimpleSynthAction
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codebuild as codebuild
import aws_cdk.aws_codepipeline_actions as codepipeline_actions


class SampleAppPipelineStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        backend = kwargs.pop("backend")
        super().__init__(scope, id, **kwargs)

        # Create an empty Pipeline
        pipeline = codepipeline.Pipeline(
            self,
            "SampleAppCPipelineProd",
            pipeline_name="SampleAppCPipelineProd"
        )

        # Add a source stage to trigger the pipeline on github commits
        source_output = codepipeline.Artifact()
        pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.GitHubSourceAction(
                    action_name="GITHUB_SOURCE_ACTION",
                    output=source_output,
                    oauth_token=SecretValue.secrets_manager(
                        secret_id="/cdk-ecs-sample/prod/github",
                        json_field="GITHUB_TOKEN"
                    ),
                    owner=SecretValue.secrets_manager(
                        secret_id="/cdk-ecs-sample/prod/github",
                        json_field="GITHUB_OWNER"
                    ).to_string(),
                    repo=SecretValue.secrets_manager(
                        secret_id="/cdk-ecs-sample/prod/github",
                        json_field="GITHUB_REPO"
                    ).to_string(),
                    branch="master"
                )
            ]

        )

        # Add a build stage to build docker images and store them in ECR
        build_output = codepipeline.Artifact()
        docker_img_name = backend.ecr_repo.repository_name
        build_spec = codebuild.BuildSpec.from_object(
            {
                "version": '0.2',
                "phases": {
                    "pre_build": {
                        "commands": [
                            'aws --version',
                            '$(aws ecr get-login --region ${AWS_DEFAULT_REGION} --no-include-email |  sed \'s|https://||\')',
                            'COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)',
                            'IMAGE_TAG=${COMMIT_HASH:=latest}'
                        ]
                    },
                    "build": {
                        "commands": [
                            f'docker build -t {docker_img_name}:latest .',
                            f'docker tag {docker_img_name}:latest {docker_img_name}:$IMAGE_TAG',
                        ]
                    },
                    "post_build": {
                        "commands": [
                            f'docker push {docker_img_name}:latest',
                            f'docker push {docker_img_name}:$IMAGE_TAG',
                            'printf "[{\\"name\\":\\"${CONTAINER_NAME}\\",\\"imageUri\\":\\"'+docker_img_name+':latest\\"}]" > imagedefinitions.json'
                        ]
                    }
                },
                "artifacts": {
                    "files": [
                        'imagedefinitions.json'
                    ]
                }
            }
        )
        codebuild_project = codebuild.Project(
            self,
            "SampleAppCodeBuildProject",
            build_spec=build_spec,
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_2_0,
                privileged=True
            ),
            environment_variables={
                "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(value=backend.ecr_repo),
                "CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value=backend.container_name)
            }
        )
        # Grant permissions to codebuild to access the ECR repo
        backend.ecr_repo.grant_pull_push(codebuild_project.grant_principal)
        pipeline.add_stage(
            stage_name="Build",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="CODEBUILD_ACTION",
                    input=source_output,  # Takes the source code from the previous stage
                    outputs=[build_output],
                    project=codebuild_project
                )
            ]
        )

        # Add a Deploy stage to update ECS service & tasks with the new docker images
        pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                codepipeline_actions.EcsDeployAction(
                    action_name="ECS_ACTION",
                    input=build_output,  # Takes the imagedefinitions.json generated in the build stage
                    service=backend.alb_fargate_service.service
                )
            ]
        )
