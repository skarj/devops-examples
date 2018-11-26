from stacker.blueprints.base import Blueprint
from troposphere import Output, Ref, Template, AccountId, Join
from troposphere.s3 import Bucket
from troposphere.ecr import Repository
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
        
        self.enable_ecr('imagefetcher')

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


    def enable_ecr(self, name):
    # https://docs.aws.amazon.com/codebuild/latest/userguide/sample-docker.html
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
                            # TODO: fix this
                            Principal=Principal("AWS", Join("", ["arn:aws:iam::", AccountId, ":user/stacker"])),
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
