from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString

from troposphere import (
    Output, Ref, GetAtt,
    Template, Join, Tags
)

from troposphere.ec2 import (
    VPC, Subnet, InternetGateway,
    VPCGatewayAttachment, RouteTable,
    Route, SubnetRouteTableAssociation,
    EIP, NatGateway
)


class EKSVPC(Blueprint):
    """
    VPC Resources
     * VPC
     * Subnets
     * Internet Gateway
     * NAT Gateway
     * Route Tables
    """
    VARIABLES = {
        "VPCCIDR": {
            "type": CFNString,
            "default": "10.0.0.0/16",
            "description": "VPC CIDR Block"
        },
        "PrivateSubnetCIDR": {
            "type": CFNString,
            "default": "10.0.0.0/19",

            "description": "CIDR Block for the Private Subnet"
        },
        "PublicSubnetCIDR": {
            "type": CFNString,
            "default": "10.0.128.0/20",
            "description": "CIDR Block for the Public Subnet"
        },
    }


    def create_template(self):
        t = self.template

        t.add_description("Stack for EKS VPC")

        variables = self.get_variables()
        vpc_cidr = variables["VPCCIDR"].ref
        private_subnet_cidr = variables["PrivateSubnetCIDR"].ref
        public_subnet_cidr = variables["PublicSubnetCIDR"].ref

        clustername = "{}Eks".format(self.context.namespace).replace("-", "")

        vpc, public_subnet, private_subnet = self.create_vpc(
            clustername,
            vpc_cidr,
            public_subnet_cidr,
            private_subnet_cidr
        )

        nat_eip = self.create_nat_gateway(
            clustername,
            vpc,
            public_subnet,
            private_subnet
        )

        self.create_internet_gateway(
            clustername,
            vpc,
            public_subnet
        )

        t.add_output(
            Output(
                "VPCID", Value=Ref(vpc)
            )
        )

        t.add_output(
            Output(
                "NATEIP", Value=Ref(nat_eip)
            )
        )

        t.add_output(
            Output(
                "PublicSubnetID", Value=Ref(public_subnet)
            )
        )

        t.add_output(
            Output(
                "PrivateSubnetID", Value=Ref(private_subnet)
            )
        )


    def create_vpc(self, clustername, vpc_cidr, public_subnet_cidr, private_subnet_cidr):
        t = self.template

        vpc = t.add_resource(
            VPC(
                '{}Vpc'.format(clustername),
                EnableDnsSupport=False,
                EnableDnsHostnames=False,
                CidrBlock=vpc_cidr,
                Tags=Tags({
                    "Name": clustername,
                    "kubernetes.io/cluster/{}".format(clustername): "shared"
                })
            )
        )

        public_subnet = t.add_resource(
            Subnet(
                '{}PublicSubnet'.format(clustername),
                CidrBlock=public_subnet_cidr,
                VpcId=Ref(vpc),
                MapPublicIpOnLaunch=True,
                Tags=Tags({
                    "Name": "{} public subnet".format(clustername),
                    "Network": "Public",
                    "kubernetes.io/cluster/{}".format(clustername): "shared"
                })
            )
        )

        private_subnet = t.add_resource(
            Subnet(
                '{}PrivateSubnet'.format(clustername),
                CidrBlock=private_subnet_cidr,
                VpcId=Ref(vpc),
                Tags=Tags({
                    "Name": "{} private subnet".format(clustername),
                    "Network": "Private",
                    "kubernetes.io/cluster/{}".format(clustername): "shared"
                })
            )
        )

        return vpc, public_subnet, private_subnet


    def create_nat_gateway(self, clustername, vpc, public_subnet, private_subnet):
        t = self.template

        nat_eip = t.add_resource(
            EIP(
                '{}NatEIP'.format(clustername),
                Domain="vpc",
                DependsOn='{}VPCGatewayAttachment'.format(clustername)
            )
        )

        nat_gateway = t.add_resource(
            NatGateway(
                '{}NatGateway'.format(clustername),
                AllocationId=GetAtt(nat_eip, "AllocationId"),
                SubnetId=Ref(public_subnet),
                DependsOn='{}VPCGatewayAttachment'.format(clustername)
            )
        )

        PrivateSubnetRouteTable = t.add_resource(
            RouteTable(
                '{}PrivateRouteTable'.format(clustername),
                VpcId=Ref(vpc),
                Tags=Tags({
                    "Name": "{} private subnets".format(clustername),
                    "Network": "Private",
                    "kubernetes.io/role/internal-elb": "1"
                })
            )
        )

        t.add_resource(
            Route(
                '{}PrivateSubnetRoute'.format(clustername),
                DependsOn='{}VPCGatewayAttachment'.format(clustername),
                DestinationCidrBlock='0.0.0.0/0',
                RouteTableId=Ref(PrivateSubnetRouteTable),
                NatGatewayId=Ref(nat_gateway)
            )
        )

        t.add_resource(
            SubnetRouteTableAssociation(
                '{}PrivateSubnetRouteTableAssociation'.format(clustername),
                SubnetId=Ref(private_subnet),
                RouteTableId=Ref(PrivateSubnetRouteTable),
            )
        )

        return nat_eip


    def create_internet_gateway(self, clustername, vpc, public_subnet):
        t = self.template

        internetGateway = t.add_resource(
            InternetGateway(
                '{}InternetGateway'.format(clustername),
                Tags=Tags(
                    Name=clustername,
                    Network="Public"
                )
            )
        )

        t.add_resource(
            VPCGatewayAttachment(
                '{}VPCGatewayAttachment'.format(clustername),
                VpcId=Ref(vpc),
                InternetGatewayId=Ref(internetGateway)
            )
        )

        PublicSubnetRouteTable = t.add_resource(
            RouteTable(
                '{}PublicRouteTable'.format(clustername),
                VpcId=Ref(vpc),
                Tags=Tags(
                    Name="{} public subnets".format(clustername),
                    Network="Public"
                )
            )
        )

        t.add_resource(
            Route(
                '{}PublicSubnetRoute'.format(clustername),
                DependsOn='{}VPCGatewayAttachment'.format(clustername),
                DestinationCidrBlock='0.0.0.0/0',
                RouteTableId=Ref(PublicSubnetRouteTable),
                GatewayId=Ref(internetGateway)
            )
        )

        t.add_resource(
            SubnetRouteTableAssociation(
                '{}PublicSubnetRouteTableAssociation'.format(clustername),
                SubnetId=Ref(public_subnet),
                RouteTableId=Ref(PublicSubnetRouteTable),
            )
        )
