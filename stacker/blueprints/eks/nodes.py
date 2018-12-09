from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import EC2KeyPairKeyName, EC2ImageId

from troposphere import (
    Output, Ref, Template,
    Join, Split, GetAtt
)

from troposphere.iam import Role, InstanceProfile
from troposphere.policies import UpdatePolicy, AutoScalingRollingUpdate
from troposphere.ec2 import (
    SecurityGroupIngress,
    SecurityGroupEgress,
    SecurityGroup
)
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, Tag
from awacs.aws import Allow, Policy, Statement, Principal
from awacs import sts
import awacs.iam as iam
import awacs.ec2 as ec2


class EKSNodes(Blueprint):
    """
    EKS Worker Nodes Resources
     * IAM role allowing Kubernetes actions to access other AWS services
     * EC2 Security Group to allow networking traffic
     * AutoScaling Launch Configuration to configure worker instances
     * AutoScaling Group to launch worker instances
    """
    VARIABLES = {
        "VpcId": {
            "type": str,
            "description": "ID of VPC in which resources will be created"
        },
        "KeyName": {
            "type": EC2KeyPairKeyName,
            "description": "EC2 Key Pair for SSH access to the instances"
        },
        "NodeImageId": {
            "type": EC2ImageId,
            "description": "AMI id for the node instances",
            "default": "ami-dea4d5a1"
        }, 
        "NodeInstanceType": {
            "type": str,
            "description": "EC2 instance type for the node instances",
            "default": "t2.medium",
            "allowed_values": ['t2.small', 't2.medium', 't2.large', 't2.xlarge'],
            "constraint_description": "must be a valid EC2 instance type"
        },
        "NodeAutoScalingGroupMinSize": {
            "type": int,
            "description": "Minimum size of Node Group ASG",
            "default": 1
        },
        "NodeAutoScalingGroupMaxSize": {
            "type": int,
            "description": "Maximum size of Node Group ASG",
            "default": 3
        },
        "ClusterName": {
            "type": str,
            "description": "The cluster name provided when the cluster was created"
        },
        "ClusterSecurityGroup": {
            "type": str,
            "description": "Cluster control plane security group for communication with worker nodes"
        },
        "NodeGroupName": {
            "type": str,
            "description": "Unique identifier for the Node Group",
            "default": "one"
        },
    }


    def create_template(self):
        t = self.template
        t.add_description("Amazon EKS - Node Group")
        t.add_version("2010-09-09")

        variables = self.get_variables()
        vpc_id = variables["VpcId"]
        cluster_sg = variables["ClusterSecurityGroup"]
        asg_min_size = variables["NodeAutoScalingGroupMinSize"]
        asg_max_size = variables["NodeAutoScalingGroupMaxSize"]
        subnet_ids = variables["NodeAutoScalingGroupMaxSize"]

        basename = "{}Eks".format(self.context.namespace).replace("-", "")

        node_instance_profile = self.create_node_instance_pofile(basename)

        node_security_group = self.create_node_security_group(
            basename,
            vpc_id,
            cluster_sg
        )

        launch_configuration = self.create_node_launch_configuration()

        self.create_node_auto_scaling_group(
            basename,
            launch_configuration,
            asg_min_size,
            asg_max_size,
            subnet_ids
        )


    def create_node_instance_pofile(self, basename):
        t = self.template

        role = t.add_resource(Role(
            "{}NodeInstanceRole".format(basename),
            Version='2012-10-17',
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Action=[sts.AssumeRole],
                        Effect=Allow,
                        Principal=Principal("Service", ["eks.amazonaws.com"])
                    )
                ]
            ),
            Path="/",
            ManagedPolicyArns=[
                "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
                "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
                "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
            ]
        ))

        return t.add_resource(InstanceProfile(
            "{}NodeInstanceProfile".format(basename),
            Roles=[Ref(role)]
        ))


    def create_node_security_group(self, basename, vpc_id, cluster_sg):
        t = self.template

        security_group = t.add_resource(
            SecurityGroup(
                "{}NodeSecurityGroup".format(basename),
                GroupDescription='Allow the cluster control plane to communicate with worker Kubelet and pods',
                VpcId=vpc_id
            ))

        t.add_resource(SecurityGroupIngress(
            "{}NodeSecurityGroupIngress".format(basename),
            Description='Allow node to communicate with each other',
            GroupId=GetAtt(security_group, "GroupId"),
            SourceSecurityGroupId=GetAtt(security_group, "GroupId"),
            IpProtocol='-1',
            FromPort='0',
            ToPort='65535'
        ))

        t.add_resource(SecurityGroupIngress(
            "{}NodeSecurityGroupFromControlPlaneIngress".format(basename),
            Description='Allow worker Kubelets and pods to receive communication from the cluster control plane',
            GroupId=GetAtt(security_group, "GroupId"),
            SourceSecurityGroupId=GetAtt(cluster_sg, "GroupId"),
            IpProtocol='-1',
            FromPort='1025',
            ToPort='65535'
        ))

        t.add_resource(SecurityGroupIngress(
            "{}ClusterControlPlaneSecurityGroupIngress".format(basename),
            Description='Allow pods to communicate with the cluster API Server',
            GroupId=GetAtt(cluster_sg, "GroupId"),
            SourceSecurityGroupId=GetAtt(security_group, "GroupId"),
            IpProtocol='tcp',
            FromPort='443',
            ToPort='443'
        ))

        t.add_resource(SecurityGroupEgress(
            "{}ControlPlaneEgressToNodeSecurityGroup".format(basename),
            Description='Allow the cluster control plane to communicate with worker Kubelet and pods',
            GroupId=GetAtt(cluster_sg, "GroupId"),
            DestinationSecurityGroupId=GetAtt(security_group, "GroupId"),
            IpProtocol='tcp',
            FromPort='1025',
            ToPort='65535'
        ))

        return security_group


    def create_node_auto_scaling_group(self, basename, launch_config,
                                        min_size, max_size, subnet_ids):
        t = self.template

        t.add_resource(AutoScalingGroup(
            "{}NodeAutoScalingGroup".format(basename),
            DesiredCapacity=max_size,
            LaunchConfigurationName=Ref(launch_config),
            MinSize=min_size,
            MaxSize=max_size,
            VPCZoneIdentifier=subnet_ids,
            Tags=[
                Tag("Name", "{}Node".format(basename), True),
                Tag("kubernetes.io/cluster/{}".format(basename), 'shared', True) # shared?
            ],
            UpdatePolicy=UpdatePolicy(
                AutoScalingReplacingUpdate=AutoScalingRollingUpdate(
                    MinInstancesInService='1',
                    MaxBatchSize='1'
                )
            )
        ))


    def create_node_launch_configuration(self):
        t = self.template
