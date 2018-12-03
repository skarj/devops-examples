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
     * Route Table
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
            "description": "IDR Block for the Private Subnet"
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

        self.create_vpc(clustername, vpc_cidr)

        self.create_subnets(
            clustername,
            private_subnet_cidr,
            public_subnet_cidr
        )

        self.create_internet_gateway(clustername)
        self.create_nat_gateway(clustername)
        self.create_route_tables(clustername)

        t.add_output(
            Output(
                "VPCID", Value=Ref(self.VPC)
            )
        )


    def create_vpc(self, clustername, vpc_cidr):
        t = self.template

        self.VPC = t.add_resource(
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


    def create_internet_gateway(self, clustername):
        t = self.template

        self.internetGateway = t.add_resource(
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
                VpcId=Ref(self.VPC),
                InternetGatewayId=Ref(self.internetGateway)
            )
        )


    def create_nat_gateway(self, clustername):
        t = self.template

        nat_eip = t.add_resource(
            EIP(
                '{}NatEIP'.format(clustername),
                Domain="vpc",
                DependsOn='{}VPCGatewayAttachment'.format(clustername)
            )
        )

        self.nat_gateway = t.add_resource(
            NatGateway(
                '{}NatGateway'.format(clustername),
                AllocationId=GetAtt(nat_eip, "AllocationId"),
                SubnetId=Ref(self.PublicSubnet),
                DependsOn='{}VPCGatewayAttachment'.format(clustername)
            )
        )


    def create_subnets(self, clustername, private_subnet, public_subnet):
        t = self.template

        self.PrivateSubnet = t.add_resource(
            Subnet(
                '{}PrivateSubnet'.format(clustername),
                CidrBlock=private_subnet,
                VpcId=Ref(self.VPC),
                Tags=Tags({
                    "Name": "{} private subnet".format(clustername),
                    "Network": "Private",
                    "kubernetes.io/cluster/{}".format(clustername): "shared"
                })
            )
        )

        self.PublicSubnet = t.add_resource(
            Subnet(
                '{}PublicSubnet'.format(clustername),
                CidrBlock=public_subnet,
                VpcId=Ref(self.VPC),
                MapPublicIpOnLaunch=True,
                Tags=Tags({
                    "Name": "{} public subnet".format(clustername),
                    "Network": "Public",
                    "kubernetes.io/cluster/{}".format(clustername): "shared"
                })
            )
        )


    def create_route_tables(self, clustername):
        t = self.template

        PrivateSubnetRouteTable = t.add_resource(
            RouteTable(
                '{}PrivateRouteTable'.format(clustername),
                VpcId=Ref(self.VPC),
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
                NatGatewayId=Ref(self.nat_gateway)
            )
        )

        t.add_resource(
            SubnetRouteTableAssociation(
                '{}PrivateSubnetRouteTableAssociation'.format(clustername),
                SubnetId=Ref(self.PrivateSubnet),
                RouteTableId=Ref(PrivateSubnetRouteTable),
            )
        )

        PublicSubnetRouteTable = t.add_resource(
            RouteTable(
                '{}PublicRouteTable'.format(clustername),
                VpcId=Ref(self.VPC),
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
                GatewayId=Ref(self.internetGateway)
            )
        )

        t.add_resource(
            SubnetRouteTableAssociation(
                '{}PublicSubnetRouteTableAssociation'.format(clustername),
                SubnetId=Ref(self.PublicSubnet),
                RouteTableId=Ref(PublicSubnetRouteTable),
            )
        )
