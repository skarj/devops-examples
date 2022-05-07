from stacker.blueprints.base import Blueprint

from stacker.blueprints.variables.types import (
    EC2SecurityGroupId
)

from troposphere import (
    Output, Ref, Split, GetAtt
)

from troposphere.eks import (
    Cluster,
    ResourcesVpcConfig
)

from awacs.aws import (
    Allow, Policy,
    Statement, Principal
)

from troposphere.iam import Role
from awacs import sts


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
        "Subnets": {
            "type": str,
            "description": "List of vpc subnets"
        },
        "ClusterVersion": {
            "type": str,
            "default": "1.10",
            "description": "Version of Kubernetes cluster"
        },
        "ControlPlaneSecurityGroup": {
            "type": EC2SecurityGroupId,
            "description": "Cluster control plane security group for communication with worker nodes"
        },
    }


    def create_template(self):
        t = self.template
        t.set_description("Amazon EKS - Cluster")

        variables = self.get_variables()
        cluster_version = variables["ClusterVersion"]
        public_subnets = variables["Subnets"]
        control_plane_sg = variables["ControlPlaneSecurityGroup"].ref
        basename = "{}EKS".format(self.context.namespace).replace("-", "")

        eks_role = self.create_eks_role()

        eks_cluser = self.create_eks_cluster(
            basename,
            eks_role,
            control_plane_sg,
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


    def create_eks_role(self):
        t = self.template

        return t.add_resource(Role(
            "ClusterRole",
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


    def create_eks_cluster(self, basename, role, control_plane_sg, subnets, version):
        t = self.template

        return t.add_resource(Cluster(
            "{}Cluster".format(basename),
            ResourcesVpcConfig=ResourcesVpcConfig(
                # Control plane security group
                SecurityGroupIds=[control_plane_sg],
                # Subnets specified must be in at least two different AZs
                SubnetIds=Split(",", subnets)
            ),
            RoleArn=GetAtt(role, "Arn"),
            Version=version
        ))
