from stacker.blueprints.base import Blueprint
from troposphere import Output, Ref, Template, AccountId, Join, GetAtt
from troposphere.s3 import Bucket
from troposphere.iam import Role
from troposphere.ecr import Repository
from troposphere.codebuild import Artifacts, Environment, Source, Project
from awacs.sts import AssumeRole
from awacs.aws import Allow, Policy, AWSPrincipal, Statement, Principal
import awacs.ecr as ecr


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

        self.codebuild_role = t.add_resource(Role(
            "{}CodebuildRole".format(name).replace("-", ""),
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["codebuild.amazonaws.com"])
                    )
                ]
            )
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
            Image='aws/codebuild/java:openjdk-8',
            Type='LINUX_CONTAINER',
            EnvironmentVariables=[
                {'Name': 'APP_NAME', 'Value': 'demo'}
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
