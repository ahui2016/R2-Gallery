import json
from typing import Iterable

import boto3
from botocore.config import Config

from .const import Use_Proxy, Http_Proxy, R2_Files_JSON_Path, R2_Waiting_JSON_Path


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


def add_pics_to_r2_waiting(new_pics:Iterable):
    waiting = get_r2_waiting()
    waiting["add"] = waiting["add"].intersection(new_pics)
    write_r2_waiting(waiting)


def write_r2_waiting(waiting:dict):
    waiting["add"] = list(waiting["add"])
    waiting["delete"] = list(waiting["delete"])
    R2_Waiting_JSON_Path.write_text(json.dumps(waiting))


def get_r2_waiting() -> dict:
    if R2_Waiting_JSON_Path.exists():
        waiting = json.loads(R2_Waiting_JSON_Path.read_text())
        waiting["add"] = set(waiting["add"])
        waiting["delete"] = set(waiting["delete"])
        return waiting
    return dict(add=set(), delete=set())


def write_r2_files_json(r2_files:dict):
    data = json.dumps(r2_files)
    R2_Files_JSON_Path.write_text(data)


def get_r2_files() -> dict:
    if R2_Files_JSON_Path.exists():
        return json.loads(R2_Files_JSON_Path.read_text())
    return {}


def add_to_r2_files(obj_names: list):
    r2_files = get_r2_files()
    for obj_name, checksum in obj_names:
        r2_files[obj_name] = checksum
    write_r2_files_json(r2_files)
