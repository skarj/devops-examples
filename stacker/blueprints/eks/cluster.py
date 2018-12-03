from stacker.blueprints.base import Blueprint
from troposphere.iam import Role, Policy as IamPolicy
from troposphere.ec2 import SecurityGroupRule, SecurityGroup

from troposphere import (
    Output, Ref, Template,
    AccountId, Region, Join,
    GetAtt, Tags
)

from awacs.sts import AssumeRole
from awacs.aws import Allow, Policy, Statement, Principal


class EKSCluster(Blueprint):
    """
    EKS Cluster Resources
     * IAM Role to allow EKS service to manage other AWS services
     * EC2 Security Group to allow networking traffic with EKS cluster
     * EKS Cluster
    """
    VARIABLES = {}


    def create_template(self):
        t = self.template
        t.add_description("Stack for EKS infrastructure")

        variables = self.get_variables()

        ref_stack_id = Ref('AWS::StackId')
        ref_region = Ref('AWS::Region')
        ref_stack_name = Ref('AWS::StackName')

        clustername = self.context.namespace.replace("-", "")

        self.create_eks_role()
        self.create_eks_security_group(clustername)


    def create_eks_security_group(self, clustername):
        t = self.template
        t.add_description("Cluster communication with worker nodes")

        self.ClusterSecurityGroup = t.add_resource(
            SecurityGroup(
                "{}ClusterSecurityGroup".format(clustername),
                GroupDescription='Enable SSH access via port 22',
                SecurityGroupEgress=[
                    SecurityGroupRule(
                        IpProtocol='-1',
                        FromPort='0',
                        ToPort='0',
                        CidrIp='0.0.0.0/0'
                    )
                ],
                SecurityGroupIngress=[
                    SecurityGroupRule(
                        Description='Allow pods to communicate with the cluster API Server',
                        IpProtocol='tcp',
                        FromPort='443',
                        ToPort='443',
                        SourceSecurityGroupId=Ref(self.VPC)
                    ),
                    SecurityGroupRule(
                        Description='Allow workstation to communicate with the cluster API Server',
                        IpProtocol='tcp',
                        FromPort='443',
                        ToPort='443',
                        cidr_blocks= ["${local.workstation-external-cidr}"] ### FF
                    )
                ],
                VpcId=Ref(self.VPC)
            ))


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
