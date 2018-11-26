from stacker.blueprints.base import Blueprint

from troposphere import Output, Ref, Template
from troposphere.s3 import Bucket

class Imagefetcher(Blueprint):
    """
    Blueprint for imagefetcher infrastructure.
    """
    VARIABLES = {
        "Namespace": {
            "type": str,
            "description": ""
        }
    }

    def create_template(self):
        t = self.template
        t.add_description("Stack for imagefetcher infrastructure")

        variables = self.get_variables()

        namespace = variables["Namespace"]
        basename = "{}Images".format(namespace).replace("-", "")

        images_bucket = self.create_images_bucket(basename)

        t.add_output(Output(
            "{}Bucket".format(basename),
            Value=Ref(images_bucket))
        )

    def create_images_bucket(self, basename):
        t = self.template

        bucket = t.add_resource(Bucket(
            "{}Bucket".format(basename)
        ))

        return bucket
