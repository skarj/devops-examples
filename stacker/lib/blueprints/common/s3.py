
from troposphere import NoValue
from troposphere.s3 import Bucket, BucketEncryption, \
    ServerSideEncryptionByDefault, ServerSideEncryptionRule, \
    VersioningConfiguration


def create_bucket(resource_name, bucket_name=NoValue,
                  access_control="Private", kms_key_id=NoValue,
                  versioning=True, disable_encryption=True):

    encryption_rules = [ServerSideEncryptionRule(
        ServerSideEncryptionByDefault=ServerSideEncryptionByDefault(
            KMSMasterKeyID=kms_key_id,
            SSEAlgorithm="aws:kms",
        )
    )]

    bucket_encryption = BucketEncryption(
        ServerSideEncryptionConfiguration=encryption_rules
    ) if not disable_encryption else NoValue

    versioning_config = VersioningConfiguration(Status="Enabled") \
        if versioning else NoValue

    return Bucket(
        resource_name,
        BucketName=bucket_name,
        AccessControl=access_control,
        BucketEncryption=bucket_encryption,
        VersioningConfiguration=versioning_config,
    )
