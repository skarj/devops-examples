from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString
from troposphere import Output, Ref, Template, AccountId, Region, Join, GetAtt, Tags
from troposphere.iam import Role, Policy as IamPolicy
from troposphere.ec2 import SecurityGroupRule, SecurityGroup, \
    VPC, Subnet, InternetGateway, VPCGatewayAttachment, RouteTable, Route, SubnetRouteTableAssociation
from awacs.sts import AssumeRole
from awacs.aws import Allow, Policy, Statement, Principal

# https://github.com/skarj/terraform-aws-eks/blob/master/vpc.tf

class EKSVPC(Blueprint):
    """
    VPC Resources
     * VPC
     * Subnets
     * Internet Gateway
     * Route Table
    """
    VARIABLES = {
        "Namespace": {
            "type": str,
            "description": ""
        },
        "BaseCidr": {
            "type": CFNString,
            "description": "The 'base' of the CIDR string, in XX.YY format"
        },
    }


    def create_template(self):
        t = self.template
        t.add_description("Stack for EKS VPC")

        variables = self.get_variables()
        namespace = variables["Namespace"]

        clustername = "{}Eks".format(namespace).replace("-", "")

        self.create_vpc(clustername)
        self.create_subnet(clustername)
        self.create_internet_gateway(clustername)
        self.create_gateway_attachment()
        self.create_route_table(clustername)
        self.add_route()


    def create_vpc(self, clustername):
        t = self.template

        self.VPC = t.add_resource(
            VPC(
                '{}Vpc'.format(clustername),
                CidrBlock='10.0.0.0/16',
                Tags=Tags(
                    Name=clustername # tags
                )
            )
        )


    def create_subnet(self, clustername):  # Count 2
        t = self.template

        self.subnet = t.add_resource(
            Subnet(
                '{}Subnet'.format(clustername),
                CidrBlock='10.0.0.0/24',
                VpcId=Ref(self.VPC),
                Tags=Tags(
                    Name=clustername # tags
                )
            )
        )


    def create_internet_gateway(self, clustername):
        t = self.template

        self.internetGateway = t.add_resource(
            InternetGateway(
                '{}InternetGateway'.format(clustername),
                Tags=Tags(
                    Name=clustername # tags
                )
            )
        )


    def create_gateway_attachment(self):
        t = self.template

        self.gatewayAttachment = t.add_resource(
            VPCGatewayAttachment(
                'AttachGateway',
                VpcId=Ref(self.VPC),
                InternetGatewayId=Ref(self.internetGateway)
            )
        )


    def create_route_table(self, clustername):
        t = self.template

        self.routeTable = t.add_resource(
            RouteTable(
                '{}RouteTable'.format(clustername),
                VpcId=Ref(self.VPC),
                Tags=Tags(
                    Name=clustername # tags
                )
            )
        )


    def add_route(self):
        t = self.template

        self.route = t.add_resource(
            Route(
                'Route',
                DependsOn='AttachGateway',
                GatewayId=Ref('InternetGateway'),
                DestinationCidrBlock='0.0.0.0/0',
                RouteTableId=Ref(self.routeTable),
            )
        )


    def create_route_table_association(self):  # count
        t = self.template

        self.subnetRouteTableAssociation = t.add_resource(
            SubnetRouteTableAssociation(
                'SubnetRouteTableAssociation',
                SubnetId=Ref(self.subnet),
                RouteTableId=Ref(self.routeTable),
            )
        )
