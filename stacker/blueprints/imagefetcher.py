from stacker.blueprints.base import Blueprint
from troposphere import Output, Ref, Template, AccountId, Region, Join, GetAtt
from troposphere.s3 import Bucket
from troposphere.iam import Role, Policy as IamPolicy
from troposphere.ecr import Repository
from troposphere.codebuild import Artifacts, Environment, Source, Project
from awacs.sts import AssumeRole
from awacs.aws import Allow, Policy, AWSPrincipal, Statement, Principal
import awacs.ecr as ecr
import awacs.logs as logs


class Imagefetcher(Blueprint):
    """
    Blueprint for imagefetcher infrastructure.
    """
    VARIABLES = {
        "Namespace": {
            "type": str,
            "description": ""
        }
    }


    def create_template(self):
        t = self.template
        t.add_description("Stack for imagefetcher infrastructure")

        variables = self.get_variables()

        namespace = variables["Namespace"]
        basename = "{}Images".format(namespace).replace("-", "")

        images_bucket = self.create_images_bucket(basename)

        self.create_codebuild_role('imagefetcher')
        self.create_container_registry('imagefetcher')
        self.create_codebuild_project('imagefetcher')

        t.add_output(Output(
            "{}Bucket".format(basename),
            Value=Ref(images_bucket))
        )


    def create_images_bucket(self, basename):
        t = self.template

        bucket = t.add_resource(Bucket(
            "{}Bucket".format(basename)
        ))

        return bucket


    def create_codebuild_role(self, name):
        t = self.template

        # Strange role name
        self.codebuild_role = t.add_resource(Role(
            "{}Codebuild".format(name).replace("-", ""),
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["codebuild.amazonaws.com"])
                    )
                ]
            ),
            Policies=[IamPolicy(
                PolicyName="{}Codebuild".format(name).replace("-", ""),
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            "Resource": [
                                # Fix this
                                Join("", ["arn:aws:logs:", Region, ":", AccountId,
                                          ":log-group:/aws/codebuild/", "imagefetcher"]),
                                Join("", ["arn:aws:logs:", Region, ":", AccountId,
                                          ":log-group:/aws/codebuild/", "imagefetcher:*"])
                            ],
                            "Effect": "Allow"
                        }
                    ]
                }
            )]
        ))


    def create_container_registry(self, name):
        t = self.template

        t.add_resource(
            Repository(
                "{}Registry".format(name),
                RepositoryName=name,
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


    def create_codebuild_project(self, name):
        t = self.template

        t.add_version('2010-09-09')

        artifacts = Artifacts(Type='NO_ARTIFACTS')

        environment = Environment(
            ComputeType='BUILD_GENERAL1_SMALL',
            Image='aws/codebuild/docker:17.09.',
            Type='LINUX_CONTAINER',
            EnvironmentVariables=[
                {'Name': 'AWS_DEFAULT_REGION', 'Value': Region},
                {'Name': 'AWS_ACCOUNT_ID', 'Value': AccountId},
                {'Name': 'IMAGE_REPO_NAME', 'Value': '{}Registry'.format(name)}, # Fix this
                {'Name': 'IMAGE_TAG', 'Value': 'latest'}
            ],
        )

        source = Source(
            Location='https://github.com/skarj/devops-callenge.git',
            Type='GITHUB'
        )

        project = Project(
            "{}Project".format(name),
            Name=name,
            Artifacts=artifacts,
            Environment=environment,
            ServiceRole=GetAtt(self.codebuild_role, "Arn"),
            Source=source,
        )

        t.add_resource(project)
