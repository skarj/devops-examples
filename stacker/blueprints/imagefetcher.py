# https://docs.aws.amazon.com/codebuild/latest/userguide/sample-docker.html

from stacker.blueprints.base import Blueprint
from troposphere import Output, Ref, Template
from troposphere.s3 import Bucket
from troposphere.ecr import Repository
from awacs.aws import Allow, Policy, AWSPrincipal, Statement
import awacs.ecr as ecr
import awacs.iam as iam

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


    def allow_ecr(self, basename):
        t = self.template

        t.add_resource(
            Repository(
                'MyRepository',
                RepositoryName='test-repository',
                RepositoryPolicyText=Policy(
                    Version='2008-10-17',
                    Statement=[
                        Statement(
                            Sid='AllowPushPull',
                            Effect=Allow,
                            Principal=AWSPrincipal([
                                iam.ARN(account='123456789012', resource='user/Bob')
                            ]),
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
                        Statement(
                            Sid='AllowCreate',
                            Effect=Allow,
                            Principal=AWSPrincipal([
                                iam.ARN(account='123456789012', resource='user/Alice'),
                            ]),
                            Action=[
                                ecr.CreateRepository,
                            ],
                        ),
                    ]
                ),
            )
        )
