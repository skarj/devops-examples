from stacker.blueprints.base import Blueprint

from troposphere import AccountId, Join, Output, Ref, Region, StackName
from troposphere.ssm import Parameter
from troposphere.iam import ManagedPolicy

#from ..common.policy import create_policy_images_bucket
from ..common.s3 import create_bucket
#from ..common.utils import get_role_arn

class Imagefetcher(Blueprint):
    """
    Blueprint for imagefetcher infrastructure.
    """
    VARIABLES = {
        "Namespace": {
            "type": str,
            "description": ""
        },
        "AllowedRoles": {
            "default": [],
            "type": list,
            "description": "IAM Roles that will have "
                           "permissions to download images "
                           "from bucket"
        }
    }

    def create_template(self):
        t = self.template
        t.add_description("Stack for imagefetcher infrastructure")

        variables = self.get_variables()
  
        namespace = variables["Namespace"]
        basename = "{}Images".format(namespace).replace("-", "")
        
        images_bucket = self.create_images_bucket(
            basename, namespace)
        
        t.add_output(Output(
            "{}Bucket".format(basename),
            Value=Ref(images_bucket))
        )
           