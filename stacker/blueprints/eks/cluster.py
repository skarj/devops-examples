from stacker.blueprints.base import Blueprint

from troposphere import (
    Output, Ref, Template,
    Join, Split, GetAtt
)

from troposphere.iam import Role
from troposphere.ec2 import SecurityGroup
from troposphere.eks import Cluster, ResourcesVpcConfig

from awacs.aws import Allow, Policy, Statement, Principal
from awacs import sts
import awacs.iam as iam
import awacs.ec2 as ec2


class EKSCluster(Blueprint):
    """
    EKS Cluster Resources
     * IAM Role to allow EKS service to manage other AWS services
     * EC2 Security Group to allow networking traffic with EKS cluster
     * EKS Cluster

    It is possible to specify only public or private subnets when create cluster:
        Private-only: Everything runs in a private subnet and Kubernetes
            cannot create internet-facing load balancers for pods.
        Public-only: Everything runs in a public subnet, including your worker nodes.
    """
    VARIABLES = {
        "VpcId": {
            "type": str,
            "description": "ID of VPC in which resources will be created"
        },
        "PublicSubnets": {
            "type": str,
            "description": "List of public vpc subnets"
        },
        "PrivateSubnets": {
            "type": str,
            "description": "List of private vpc subnets"
        },
        "ClusterVersion": {
            "type": str,
            "default": "1.10",
            "description": "Version of Kubernetes cluster"
        }
    }


    def create_template(self):
        t = self.template
        t.add_description("Stack for EKS infrastructure")

        variables = self.get_variables()
        vpc_id = variables["VpcId"]
        cluster_version = variables["ClusterVersion"]
        public_subnets = variables["PublicSubnets"]

        basename = "{}Eks".format(self.context.namespace).replace("-", "")

        eks_role = self.create_eks_role(basename)
        eks_security_group = self.create_eks_security_group(basename, vpc_id)

        eks_cluser = self.create_eks_cluster(
            basename,
            eks_role,
            eks_security_group,
            public_subnets,
            cluster_version
        )

        t.add_output(
            Output(
                "ClusterName", Value=Ref(eks_cluser)
            )
        )

        t.add_output(
            Output(
                "ClusterArn", Value=GetAtt(eks_cluser, "Arn")
            )
        )

        t.add_output(
            Output(
                "ClusterEndpoint", Value=GetAtt(eks_cluser, "Endpoint")
            )
        )

        t.add_output(
            Output(
                "ClusterControlPlaneSecurityGroup", Value=Ref(eks_security_group)
            )
        )


    def create_eks_security_group(self, basename, vpc_id):
        # https://docs.aws.amazon.com/en_us/eks/latest/userguide/create-public-private-vpc.html#vpc-create-sg
        t = self.template

        return t.add_resource(
            SecurityGroup(
                "{}ControlPlaneSecurityGroup".format(basename),
                GroupDescription='Cluster communication with worker nodes',
                VpcId=vpc_id
            ))


    def create_eks_role(self, basename):
        t = self.template

        t.add_description("Allows EKS to manage clusters")

        return t.add_resource(Role(
            "{}ClusterRole".format(basename),
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Action=[sts.AssumeRole],
                        Effect=Allow,
                        Principal=Principal("Service", ["eks.amazonaws.com"])
                    )
                ]
            ),
            ManagedPolicyArns=[
                "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
                "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
            ]
        ))


    def create_eks_cluster(self, basename, role, security_group, subnets, version):
        t = self.template

        return t.add_resource(Cluster(
            "{}Cluster".format(basename),
            ResourcesVpcConfig=ResourcesVpcConfig(
                SecurityGroupIds=[Ref(security_group)],
                # Subnets specified must be in at least two different AZs
                SubnetIds=Split(",", subnets)
            ),
            RoleArn=GetAtt(role, "Arn"),
            Version=version
        ))
