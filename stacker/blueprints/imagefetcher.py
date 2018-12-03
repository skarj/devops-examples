from stacker.blueprints.base import Blueprint
from troposphere.s3 import Bucket
from troposphere.iam import Role, Policy as IamPolicy
from troposphere.ecr import Repository

from troposphere.codebuild import (
    Artifacts, Environment, Source, Project
)

from troposphere import (
    Output, Ref, Template, AccountId
    Region, Join, GetAtt
)

from awacs.sts import AssumeRole
from awacs.aws import Allow, Policy, Statement, Principal
import awacs.ecr as ecr
import awacs.logs as logs


class Imagefetcher(Blueprint):
    """
    Imagefetcher resources
    """
    VARIABLES = {
        "GithubRepo": {
            "type": str,
            "description": "Github repository URL"
        }
    }


    def create_template(self):
        t = self.template
        t.add_description("Stack for imagefetcher infrastructure")

        variables = self.get_variables()
        github_repo = variables["GithubRepo"]

        basename = self.context.namespace.replace("-", "")

        images_bucket = self.create_images_bucket(basename)
        self.create_codebuild_role(basename)
        self.create_container_registry(basename)
        self.create_codebuild_project(basename, github_repo)

        t.add_output(Output(
            "{}Bucket".format(basename),
            Value=Ref(images_bucket))
        )


    def create_images_bucket(self, basename):
        t = self.template

        bucket = t.add_resource(Bucket(
            "{}ImagesBucket".format(basename)
        ))

        return bucket


    def create_codebuild_role(self, basename):
        t = self.template

        self.codebuild_role = t.add_resource(Role(
            "{}Codebuild".format(basename),
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["codebuild.amazonaws.com"])
                    )
                ]
            ),
            Policies=[
                IamPolicy(
                    PolicyName="{}Codebuild".format(basename),
                    PolicyDocument={
                        # recreate using awacs
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Action": [
                                    "logs:CreateLogGroup",
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents",
                                ],
                                "Resource": [
                                    Join("", ["arn:aws:logs:", Region, ":", AccountId,
                                            ":log-group:/aws/codebuild/", basename]),
                                    Join("", ["arn:aws:logs:", Region, ":", AccountId,
                                            ":log-group:/aws/codebuild/", basename, ":*"])
                                ],
                                "Effect": "Allow"
                            },
                            {
                                "Action": [
                                    "ecr:GetAuthorizationToken"
                                ],
                                "Resource": ["*"],
                                "Effect": "Allow"
                            },
                            {
                                "Action": [
                                    "ecr:InitiateLayerUpload"
                                ],
                                "Resource": ["*"],
                                "Effect": "Allow"
                            }
                        ]
                    }
                )
            ]
        ))


    def create_container_registry(self, basename):
        t = self.template

        t.add_resource(
            Repository(
                "{}Registry".format(basename),
                RepositoryName=basename,
                RepositoryPolicyText=Policy(
                    Version='2008-10-17',
                    Statement=[
                        Statement(
                            Sid='AllowPushPull',
                            Effect=Allow,
                            Principal=Principal("AWS", GetAtt(self.codebuild_role, "Arn")),
                            Action=[
                                ecr.GetDownloadUrlForLayer,
                                ecr.BatchGetImage,
                                ecr.BatchCheckLayerAvailability,
                                ecr.PutImage,
                                ecr.InitiateLayerUpload,
                                ecr.UploadLayerPart,
                                ecr.CompleteLayerUpload,
                            ],
                        ),
                    ]
                ),
            )
        )


    def create_codebuild_project(self, basename, github_repo):
        t = self.template

        t.add_version('2010-09-09')

        artifacts = Artifacts(Type='NO_ARTIFACTS')

        environment = Environment(
            ComputeType='BUILD_GENERAL1_SMALL',
            Image='aws/codebuild/docker:17.09.0',
            Type='LINUX_CONTAINER',
            EnvironmentVariables=[
                {'Name': 'AWS_DEFAULT_REGION', 'Value': Region},
                {'Name': 'AWS_ACCOUNT_ID', 'Value': AccountId},
                {'Name': 'IMAGE_REPO_NAME', 'Value': basename},
                {'Name': 'IMAGE_TAG', 'Value': 'latest'}
            ],
        )

        source = Source(
            Location=github_repo,
            Type='GITHUB'
        )

        project = Project(
            "{}Project".format(basename),
            Name=basename,
            Artifacts=artifacts,
            Environment=environment,
            ServiceRole=GetAtt(self.codebuild_role, "Arn"),
            Source=source,
        )

        t.add_resource(project)
