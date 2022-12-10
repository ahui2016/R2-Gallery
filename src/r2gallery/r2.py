import boto3
from botocore.config import Config

from .const import Use_Proxy, Http_Proxy


def get_bucket(s3, cfg):
    return s3.Bucket(cfg["bucket_name"])


def get_s3(cfg):
    return boto3.resource(
        's3',
        endpoint_url=cfg["endpoint_url"],
        aws_access_key_id=cfg["aws_access_key_id"],
        aws_secret_access_key=cfg["aws_secret_access_key"],
        config=Config(proxies=get_proxies(cfg)),
    )


def get_proxies(cfg):
    if cfg[Use_Proxy]:
        return dict(http=cfg[Http_Proxy], https=cfg[Http_Proxy])
    return None