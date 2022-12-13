import hashlib
import json
from pathlib import Path
from typing import Iterable

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError

from .const import R2_Files_JSON_Path, R2_Waiting_JSON_Path, Thumbs, Output_R2_Path


def get_bucket(cfg):
    s3 = get_s3(cfg)
    return s3.Bucket(cfg.bucket_name)


def get_s3(cfg):
    return boto3.resource(
        's3',
        endpoint_url=cfg.endpoint_url,
        aws_access_key_id=cfg.aws_access_key_id,
        aws_secret_access_key=cfg.aws_secret_access_key,
        config=Config(proxies=get_proxies(cfg)),
    )


def get_proxies(cfg):
    if cfg.use_proxy:
        return dict(http=cfg.http_proxy, https=cfg.http_proxy)
    return None


def add_pics_to_r2_waiting(new_pics:Iterable):
    waiting = get_r2_waiting()
    waiting["upload"] = waiting["upload"].union(new_pics)
    write_r2_waiting(waiting)


def write_r2_waiting(waiting:dict):
    waiting["upload"] = list(waiting["upload"])
    waiting["delete"] = list(waiting["delete"])
    R2_Waiting_JSON_Path.write_text(json.dumps(waiting))


def get_r2_waiting() -> dict:
    if R2_Waiting_JSON_Path.exists():
        waiting = json.loads(R2_Waiting_JSON_Path.read_text())
        waiting["upload"] = set(waiting["upload"])
        waiting["delete"] = set(waiting["delete"])
        return waiting
    return dict(upload=set(), delete=set())


def write_r2_files_json(r2_files:dict):
    data = json.dumps(r2_files)
    R2_Files_JSON_Path.write_text(data)


def get_r2_files() -> dict:
    if R2_Files_JSON_Path.exists():
        return json.loads(R2_Files_JSON_Path.read_text())
    return {}


def add_to_r2_files(obj_names: list[str]):
    """obj_names 是 obj_name 的列表.

    将待上传的 obj_name 添加到 r2_files, checksum 是空字符串。
    注意: 待上传的 obj_name 对应的 checksum 总是空字符串,
    只有当上传时, 才更新真实的 checksum.
    """
    r2_files = get_r2_files()
    for obj_name in obj_names:
        r2_files[obj_name] = ""
    write_r2_files_json(r2_files)


def update_r2_files(new_r2_files:dict):
    old_r2_files = get_r2_files()
    for obj_name, checksum in new_r2_files.items():
        old_r2_files[obj_name] = checksum
    write_r2_files_json(old_r2_files)


def upload_file(file:str, obj_name:str, bucket) -> bool:
    """返回 False 表示上传失败。"""
    success = True
    try:
        bucket.upload_file(file, obj_name)
    except BotoCoreError as err:
        print(err)
        success = False
    return success


def upload_pic(pic_path:str, bucket):
    """返回 False 表示上传失败。"""
    parts = Path(pic_path).parts
    if parts[-2] == Thumbs:
        obj_name = "/".join(parts[-3:])
    else:
        obj_name = "/".join(parts[-2:])
    return upload_file(pic_path, obj_name, bucket)


def upload_pics(bucket):
    """上传图片及其缩略图到 Cloudflare R2"""
    r2_waiting = get_r2_waiting()
    success = set()
    for pic_path in r2_waiting["upload"]:
        print(f"upload -> {pic_path}")
        if upload_pic(pic_path, bucket):
            success.add(pic_path)
        else:
            print(f"上传失败: {pic_path}")
            break
    r2_waiting["upload"] = r2_waiting["upload"].difference(success)
    write_r2_waiting(r2_waiting)


def upload_assets(bucket):
    """上传 HTML/CSS 等文件到 Cloudflare R2"""
    r2_files = get_r2_files()
    success = {}
    for obj_name in r2_files:
        filepath = Output_R2_Path.joinpath(obj_name)
        checksum = file_checksum(filepath)
        if r2_files[obj_name] == checksum:
            continue

        print(f"upload -> {filepath}")
        if upload_file(str(filepath), obj_name, bucket):
            success[obj_name] =checksum
        else:
            print(f"上传失败: {filepath}")
    update_r2_files(success)


def file_checksum(filepath:Path) -> str:
    text = filepath.read_text()
    return hashlib.sha1(text.encode()).hexdigest()
