from stacker.blueprints.base import Blueprint
from troposphere.s3 import Bucket
from troposphere.iam import Role, Policy as IamPolicy
from troposphere.ecr import Repository

from troposphere.codebuild import (
    Artifacts, Environment, Source, Project
)

from troposphere import (
    Output, Ref, AccountId,
    Region, Join, GetAtt
)

from awacs.sts import AssumeRole
from awacs.aws import Allow, Policy, Statement, Principal
import awacs.ecr as ecr
import awacs.logs as logs


class Imagefetcher(Blueprint):
    """
    Imagefetcher resources
     * S3 Bucket
    """
    VARIABLES = {
        "GithubRepo": {
            "type": str,
            "description": "Github repository URL"
        },
        "ClusterName": {
            "type": str,
            "description": "The cluster name provided when the cluster was created",
        },
        "NodeInstanceRole": {
            "type": str,
            "description": "Arn of node role",
        }
    }


    def create_template(self):
        t = self.template
        t.set_description("Stack for imagefetcher infrastructure")

        variables = self.get_variables()
        github_repo = variables["GithubRepo"]
        cluster_name = variables["ClusterName"]
        node_role_arn = variables["NodeInstanceRole"]
        basename = self.context.namespace.replace("-", "")

        images_bucket = self.create_images_bucket(basename)

        codebuild_role = self.create_codebuild_role(basename)

        self.create_container_registry(
            basename,
            codebuild_role
        )

        self.create_codebuild_project(
            basename,
            codebuild_role,
            github_repo
        )

        t.add_output(Output(
            "{}Bucket".format(basename),
            Value=Ref(images_bucket))
        )

        t.add_output(
            Output(
                "Kubeconfig", Value=Join("\n",[
                    "", "=============================================", "",
                    "To configure kubectl run:", "",
                    "aws eks update-kubeconfig --name {}".format(cluster_name), "",
                    "To check kubernetes cluster run:", "",
                    "kubectl get svc",
                    "", "=============================================",
                ])
            )
        )

        t.add_output(
            Output(
                "JoinNodes", Value=Join("\n",[
                    "", "=============================================", "",
                    'To enable worker nodes to join cluster run "kubectl apply -f aws-auth-cm.yaml":', "",
                    "apiVersion: v1",
                    "kind: ConfigMap",
                    "metadata:",
                    "  name: aws-auth",
                    "  namespace: kube-system",
                    "data:",
                    "  mapRoles: |",
                    "    - rolearn: {}".format(node_role_arn),
                    "      username: system:node:{{EC2PrivateDNSName}}",
                    "      groups:",
                    "        - system:bootstrappers",
                    "        - system:nodes",
                    "", "=============================================",
                ])
            )
        )


    def create_images_bucket(self, basename):
        t = self.template

        bucket = t.add_resource(Bucket(
            "{}ImagesBucket".format(basename)
        ))

        return bucket


    def create_codebuild_role(self, basename):
        t = self.template

        codebuild_role = t.add_resource(Role(
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
                    PolicyDocument=Policy(
                        Version='2012-10-17',
                        Statement=[
                            Statement(
                                Action=[
                                    logs.CreateLogGroup,
                                    logs.CreateLogStream,
                                    logs.PutLogEvents
                                ],
                                Effect=Allow,
                                Resource=[
                                    Join("", ["arn:aws:logs:", Region, ":", AccountId,
                                            ":log-group:/aws/codebuild/", basename]),
                                    Join("", ["arn:aws:logs:", Region, ":", AccountId,
                                            ":log-group:/aws/codebuild/", basename, ":*"])
                                ]
                            ),
                            Statement(
                                Action=[
                                    ecr.GetAuthorizationToken
                                ],
                                Effect=Allow,
                                Resource=["*"]
                            ),
                            Statement(
                                Action=[
                                    ecr.InitiateLayerUpload
                                ],
                                Effect=Allow,
                                Resource=["*"],
                            )
                        ]
                    )
                )
            ]
        ))

        return codebuild_role


    def create_container_registry(self, basename, service_role):
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
                            Principal=Principal("AWS", GetAtt(service_role, "Arn")),
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


    def create_codebuild_project(self, basename, service_role, github_repo):
        t = self.template

        t.set_version('2010-09-09')

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
            ServiceRole=GetAtt(service_role, "Arn"),
            Source=source,
        )

        t.add_resource(project)
