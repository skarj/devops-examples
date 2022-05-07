from stacker.blueprints.base import Blueprint

from stacker.blueprints.variables.types import (
    EC2KeyPairKeyName,
    EC2ImageId,
    EC2SecurityGroupId,
    EC2VPCId
)

from troposphere.iam import (
    Role,
    InstanceProfile
)

from troposphere.policies import (
    UpdatePolicy,
    CreationPolicy,
    ResourceSignal,
    AutoScalingRollingUpdate
)

from troposphere.autoscaling import (
    AutoScalingGroup,
    LaunchConfiguration,
    BlockDeviceMapping,
    EBSBlockDevice,
    Tag
)

from troposphere import (
    Output, Ref, Region,
    Join,  GetAtt, Tags,
    StackName, Base64
)

from troposphere.ec2 import (
    SecurityGroupIngress,
    SecurityGroupEgress,
    SecurityGroup
)

from awacs.aws import (
    Allow, Policy,
    Statement, Principal
)

from awacs import sts


class EKSNodes(Blueprint):
    """
    EKS Worker Nodes Resources
     * IAM role allowing Kubernetes actions to access other AWS services
     * EC2 Security Group to allow networking traffic
     * AutoScaling Launch Configuration to configure worker instances
     * AutoScaling Group to launch worker instances
    """
    VARIABLES = {
        "KeyName": {
            "type": EC2KeyPairKeyName,
            "description": "The EC2 Key Pair to allow SSH access to the instances"
        },
        "NodeImageId": {
            "type": EC2ImageId,
            "description": "AMI id for the node instances",
            "default": "ami-027792c3cc6de7b5b"
        },
        "NodeInstanceType": {
            "type": str,
            "description": "EC2 instance type for the node instances",
            "default": "t2.medium",
            "allowed_values": ['t2.small', 't2.medium', 't2.large', 't2.xlarge'],
            "constraint_description": "Must be a valid EC2 instance type"
        },
        "NodeAutoScalingGroupMinSize": {
            "type": str,
            "description": "Minimum size of Node Group ASG",
            "default": 1
        },
        "NodeAutoScalingGroupMaxSize": {
            "type": str,
            "description": "Maximum size of Node Group ASG",
            "default": 3
        },
        "NodeVolumeSize": {
            "type": int,
            "description": "Node volume size",
            "default": 20
        },
        "ClusterName": {
            "type": str,
            "description": "The cluster name provided when the cluster was created",
        },
        "BootstrapArguments": {
            "type": str,
            "description": "Arguments to pass to the bootstrap script. See files/bootstrap.sh in https://github.com/awslabs/amazon-eks-ami",
            "default": ""
        },
        "NodeGroupName": {
            "type": str,
            "description": "Unique identifier for the Node Group",
            "default": "one"
        },
        "ControlPlaneSecurityGroup": {
            "type": EC2SecurityGroupId,
            "description": "Cluster control plane security group for communication with worker nodes"
        },
        "VpcId": {
            "type": EC2VPCId,
            "description": "The VPC of the worker instances"
        },
        "PublicSubnets": {
            "type": str,
            "description": "The subnets where workers can be created"
        },
        "PrivateSubnets": {
            "type": str,
            "description": "The subnets where workers can be created"
        }
    }


    def create_template(self):
        t = self.template
        t.set_description("Amazon EKS - Node Group")
        t.set_version("2010-09-09")

        variables = self.get_variables()
        vpc_id = variables["VpcId"].ref
        cluster_sg = variables["ControlPlaneSecurityGroup"].ref
        bootstrap_args = variables["BootstrapArguments"]
        cluster_name = variables["ClusterName"]
        asg_min_size = variables["NodeAutoScalingGroupMinSize"]
        asg_max_size = variables["NodeAutoScalingGroupMaxSize"]
        public_subnets = variables["PublicSubnets"]
        private_subnets = variables["PrivateSubnets"]
        node_ami_id = variables["NodeImageId"].ref
        node_instance_type = variables["NodeInstanceType"]
        node_key_name = variables["KeyName"].ref
        node_security_group = variables["KeyName"]
        node_volume_size = variables["NodeVolumeSize"]

        if private_subnets:
            subnet_ids = private_subnets
        else:
            subnet_ids = public_subnets

        node_security_group = self.create_node_security_group(
            cluster_name,
            vpc_id,
            cluster_sg
        )

        node_instance_role, node_instance_profile = self.create_node_instance_pofile()

        user_data = Base64(Join('', [
            "#!/bin/bash\n",
            "set -o xtrace\n",
            "/etc/eks/bootstrap.sh {0} {1} \n".format(cluster_name, bootstrap_args),
            "/opt/aws/bin/cfn-signal --exit-code $?",
            " --resource NodeGroup",
            " --stack ", StackName,
            " --region ", Region
        ]))

        launch_configuration = self.create_node_launch_configuration(
            node_instance_profile,
            node_ami_id,
            node_instance_type,
            node_key_name,
            node_security_group,
            node_volume_size,
            user_data
        )

        self.create_node_auto_scaling_group(
            cluster_name,
            launch_configuration,
            asg_min_size,
            asg_max_size,
            subnet_ids
        )

        t.add_output(
            Output(
                "NodeInstanceRole",
                Value=GetAtt(node_instance_role, "Arn"),
            )
        )

        t.add_output(
            Output(
                "NodeSecurityGroup", Value=Ref(node_security_group)
            )
        )


    def create_node_instance_pofile(self):
        t = self.template

        role = t.add_resource(Role(
            "NodeInstanceRole",
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Action=[sts.AssumeRole],
                        Effect=Allow,
                        Principal=Principal("Service", ["ec2.amazonaws.com"])
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

        instance_profile = t.add_resource(InstanceProfile(
            "NodeInstanceProfile",
            Path="/",
            Roles=[Ref(role)]
        ))

        return role, instance_profile


    def create_node_security_group(self, cluster_name, vpc_id, cluster_sg):
        t = self.template

        security_group = t.add_resource(
            SecurityGroup(
                "NodeSecurityGroup",
                GroupDescription='Security group for all nodes in the cluster',
                VpcId=vpc_id,
                Tags=Tags({
                    "kubernetes.io/cluster/{}".format(cluster_name): "owned"
                })
            ))

        t.add_resource(SecurityGroupIngress(
            "NodeSecurityGroupIngress",
            Description='Allow node to communicate with each other',
            GroupId=GetAtt(security_group, "GroupId"),
            SourceSecurityGroupId=GetAtt(security_group, "GroupId"),
            IpProtocol='-1',
            FromPort='0',
            ToPort='65535'
        ))

        t.add_resource(SecurityGroupIngress(
            "NodeSecurityGroupFromControlPlaneIngress",
            Description='Allow worker Kubelets and pods to receive communication from the cluster control plane',
            GroupId=GetAtt(security_group, "GroupId"),
            SourceSecurityGroupId=cluster_sg,
            IpProtocol='tcp',
            FromPort='1025',
            ToPort='65535'
        ))

        t.add_resource(SecurityGroupEgress(
            "ControlPlaneEgressToNodeSecurityGroup",
            Description='Allow the cluster control plane to communicate with worker Kubelet and pods',
            GroupId=cluster_sg,
            DestinationSecurityGroupId=GetAtt(security_group, "GroupId"),
            IpProtocol='tcp',
            FromPort='1025',
            ToPort='65535'
        ))

        t.add_resource(SecurityGroupIngress(
            "NodeSecurityGroupFromControlPlaneOn443Ingress",
            Description='Allow pods running extension API servers on port 443 to receive communication from cluster control plane',
            GroupId=GetAtt(security_group, "GroupId"),
            SourceSecurityGroupId=cluster_sg,
            IpProtocol='tcp',
            FromPort='443',
            ToPort='443'
        ))

        t.add_resource(SecurityGroupEgress(
            "ControlPlaneEgressToNodeSecurityGroupOn443",
            Description='Allow the cluster control plane to communicate with pods running extension API servers on port 443',
            GroupId=cluster_sg,
            DestinationSecurityGroupId=GetAtt(security_group, "GroupId"),
            IpProtocol='tcp',
            FromPort='443',
            ToPort='443'
        ))

        t.add_resource(SecurityGroupIngress(
            "ClusterControlPlaneSecurityGroupIngress",
            Description='Allow pods to communicate with the cluster API Server',
            GroupId=cluster_sg,
            SourceSecurityGroupId=GetAtt(security_group, "GroupId"),
            IpProtocol='tcp',
            FromPort='443',
            ToPort='443'
        ))

        return security_group


    def create_node_launch_configuration(self, node_instance_profile,
                            ami_id, instance_type, key_name, security_group,
                            volume_size, user_data):
        t = self.template

        return t.add_resource(LaunchConfiguration(
            "NodeLaunchConfig",
            AssociatePublicIpAddress=True,
            IamInstanceProfile=Ref(node_instance_profile),
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroups=[
                Ref(security_group)
            ],
            BlockDeviceMappings=[
                BlockDeviceMapping(
                    DeviceName="/dev/sda1",
                    Ebs=EBSBlockDevice(
                        VolumeSize=volume_size,
                        VolumeType="gp2",
                        DeleteOnTermination=True,
                    ),
                )
            ],
            UserData=user_data
        ))


    def create_node_auto_scaling_group(self, cluster_name, launch_config,
                                        min_size, max_size, subnet_ids):
        t = self.template

        t.add_resource(AutoScalingGroup(
            "NodeGroup",
            DesiredCapacity=max_size,
            LaunchConfigurationName=Ref(launch_config),
            MinSize=min_size,
            MaxSize=max_size,
            VPCZoneIdentifier=[subnet_ids],
            Tags=[
                Tag("Name", "{}Node".format(cluster_name), True),
                Tag("kubernetes.io/cluster/{}".format(cluster_name), 'owned', True)
            ],
            CreationPolicy=CreationPolicy(
                ResourceSignal=ResourceSignal(
                    Timeout="PT15M",
                    Count=1,
                )
            ),
            UpdatePolicy=UpdatePolicy(
                AutoScalingRollingUpdate=AutoScalingRollingUpdate(
                    MinInstancesInService="0" if max_size == "1" else min_size,
                    MaxBatchSize="1",
                    WaitOnResourceSignals="true",
                    PauseTime="PT15M"
                )
            )
        ))
