from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import EC2VPCId, EC2SubnetIdList

from troposphere import (
    Output, Ref, Template,
    AccountId, Region, Join,
    GetAtt, Tags, Split
)

from troposphere.iam import Role, Policy as IamPolicy
from troposphere.ec2 import SecurityGroupRule, SecurityGroup
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
    """
    VARIABLES = {
        "VpcId": {
            "type": str,
            "description": "ID of VPC in which DHW resources will be created"
        },
        "PublicSubnets": {
            "type": str,
            "description": ""
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

        basename = self.context.namespace.replace("-", "")

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
        t = self.template

        security_group = t.add_resource(
            SecurityGroup(
                "{}ClusterSecurityGroup".format(basename),
                GroupDescription='Cluster communication with worker nodes',
                # SecurityGroupEgress=[
                #     SecurityGroupRule(
                #         IpProtocol='-1',
                #         FromPort='0',
                #         ToPort='0',
                #         CidrIp='0.0.0.0/0'
                #     )
                # ],
                # SecurityGroupIngress=[
                #     SecurityGroupRule(
                #         Description='Allow pods to communicate with the cluster API Server',
                #         IpProtocol='tcp',
                #         FromPort='443',
                #         ToPort='443',
                #         SourceSecurityGroupId=vpc_id
                #     ),
                #     SecurityGroupRule(
                #         Description='Allow workstation to communicate with the cluster API Server',
                #         IpProtocol='tcp',
                #         FromPort='443',
                #         ToPort='443',
                #         cidr_blocks= [workstation-external-cidr]
                #     )
                # ],
                VpcId=vpc_id
            ))

        return security_group


    def create_eks_role(self, basename):
        t = self.template

        t.add_description("Allows EKS to manage clusters")

        eks_role = t.add_resource(Role(
            "{}EKSClusterRole".format(basename),
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

        return eks_role


    def create_eks_cluster(self, basename, role, security_group, subnets, version):
        t = self.template

        cluster = t.add_resource(Cluster(
            "{}EKSCluster".format(basename),
            ResourcesVpcConfig=ResourcesVpcConfig(
                SecurityGroupIds=[Ref(security_group)],
                # Subnets specified must be in at least two different AZs
                SubnetIds=Split(",", subnets)
            ),
            RoleArn=GetAtt(role, "Arn"),
            Version=version
        ))

        return cluster
