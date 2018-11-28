from stacker.blueprints.base import Blueprint
from troposphere import Output, Ref, Template, AccountId, Region, Join, GetAtt, Tags
from troposphere.iam import Role, Policy as IamPolicy
from troposphere.ec2 import SecurityGroupRule, SecurityGroup, \
    VPC, Subnet, InternetGateway, RouteTable, SubnetRouteTableAssociation
from awacs.sts import AssumeRole
from awacs.aws import Allow, Policy, Statement, Principal

# https://github.com/skarj/terraform-aws-eks/blob/master/vpc.tf

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

        ref_stack_id = Ref('AWS::StackId')
        ref_region = Ref('AWS::Region')
        ref_stack_name = Ref('AWS::StackName')

        clustername = namespace.replace("-", "")

        self.create_eks_role()
        self.create_vpc(ref_stack_id)
        self.create_eks_security_group(clustername)


    def create_vpc(self, ref_stack_id):
        t = self.template

        self.VPC = t.add_resource(
            VPC(
                'VPC',
                CidrBlock='10.0.0.0/16',
                Tags=Tags(
                    Application=ref_stack_id # tags
                )
            )
        )


    def create_subnet(self, ref_stack_id):  # Count 2
        t = self.template

        self.subnet = t.add_resource(
            Subnet(
                'Subnet',
                CidrBlock='10.0.0.0/24',
                VpcId=Ref(self.VPC),
                Tags=Tags(
                    Application=ref_stack_id # tags
                )
            )
        )


    def create_internetGateway(self, ref_stack_id):
        t = self.template
        self.internetGateway = t.add_resource(
            InternetGateway(
                'InternetGateway',
                Tags=Tags(
                    Application=ref_stack_id # tags
                )
            )
        )


    def create_route_table(self, ref_stack_id):
        t = self.template

        self.routeTable = t.add_resource(
            RouteTable(
                'RouteTable',
                VpcId=Ref(VPC),
                Tags=Tags(
                    Application=ref_stack_id
                )
            )
        )


    def create_route_table_association(self, ref_stack_id):  # count
        t = self.template

        self.subnetRouteTableAssociation = t.add_resource(
            SubnetRouteTableAssociation(
                'SubnetRouteTableAssociation',
                SubnetId=Ref(self.subnet),
                RouteTableId=Ref(self.routeTable),
            )
        )


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
