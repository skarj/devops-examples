from stacker.blueprints.base import Blueprint
from troposphere import Output, Ref, Template, AccountId, Region, Join, GetAtt
from troposphere.s3 import Bucket
from troposphere.iam import Role, Policy as IamPolicy
from awacs.sts import AssumeRole
from awacs.aws import Allow, Policy, Statement, Principal


class EKSCluster(Blueprint):
    """
    EKS Cluster Resources
     * IAM Role to allow EKS service to manage other AWS services
     * EC2 Security Group to allow networking traffic with EKS cluster
     * EKS Cluster
    """
    VARIABLES = {
        "Namespace": {
            "type": str,
            "description": ""
        },
    }


    def create_template(self):
        t = self.template
        t.add_description("Stack for EKS infrastructure")

        variables = self.get_variables()
        namespace = variables["Namespace"]

        basename = namespace.replace("-", "")

        self.create_eks_role()


    def create_eks_role(self):
        t = self.template

        self.eks_role = t.add_resource(Role(
            "EKScluster",
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["eks.amazonaws.com"])
                    )
                ]
            ),
            ManagedPolicyArns=[
                "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
                "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
            ],
            Policies=[
                IamPolicy(
                    PolicyName="EKSClusterPolicy",
                    PolicyDocument={
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Action": [
                                    "iam:CreateServiceLinkedRole"
                                ],
                                "Resource": ["arn:aws:iam::*:role/aws-service-role/*"],
                                "Effect": "Allow"
                            },
                            {
                                "Action": [
                                    "ec2:DescribeAccountAttributes",
                                    "ec2:DescribeInternetGateways"
                                ],
                                "Resource": ["*"],
                                "Effect": "Allow"
                            },
                        ]
                    }
                ),
            ]
        ))
