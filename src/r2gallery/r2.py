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
    write_r2_waiting(waiting.union(new_pics))


def write_r2_waiting(waiting:set):
    R2_Waiting_JSON_Path.write_text(json.dumps(list(waiting)))


def get_r2_waiting() -> set:
    """:return: set(pic_path:str)"""
    if R2_Waiting_JSON_Path.exists():
        waiting = json.loads(R2_Waiting_JSON_Path.read_text())
        return set(waiting)
    return set()


def write_r2_files_json(r2_files:dict):
    data = json.dumps(r2_files)
    R2_Files_JSON_Path.write_text(data)


def get_r2_files() -> dict:
    if R2_Files_JSON_Path.exists():
        return json.loads(R2_Files_JSON_Path.read_text())
    return {}


def add_to_r2_files(obj_names: list[str]):
    """obj_names 是 obj_name 的列表.

    新的 obj_name 添加到 r2_files 时, checksum 是空字符串。
    如果 obj_name 已经在 r2_files 中, 则其 checksum 保持不变.
    (等上传时才更新 checksum)
    """
    r2_files = get_r2_files()
    for obj_name in obj_names:
        checksum = r2_files.get(obj_name, "")
        r2_files[obj_name] = checksum
    write_r2_files_json(r2_files)


def update_r2_files(new_r2_files:dict):
    old_r2_files = get_r2_files()
    for obj_name, checksum in new_r2_files.items():
        old_r2_files[obj_name] = checksum
    write_r2_files_json(old_r2_files)


def delete_from_r2_files(name:str, r2_files:dict):
    del r2_files[name]
    write_r2_files_json(r2_files)


def delete_album_from_r2_files(album_folder:str, r2_files:dict[str, str]):
    remains = dict()
    for obj_name in r2_files.keys():
        if not obj_name.startswith(album_folder+"/"):
            remains[obj_name] = r2_files[obj_name]
    write_r2_files_json(remains)


def rename_obj(old_name:str, new_name:str, bucket):
    print(f"Rename Cloudflare R2 object '{old_name}' to '{new_name}'")
    copy_source = {
        "Bucket": bucket.name,
        "Key": old_name
    }
    bucket.copy(copy_source, new_name)
    bucket.delete_objects(Delete={"Objects": [dict(Key=old_name)]})


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
    for pic_path in r2_waiting:
        print(f"upload -> {pic_path}")
        if upload_pic(pic_path, bucket):
            success.add(pic_path)
        else:
            print(f"上传失败: {pic_path}")
            break
    r2_waiting.difference_update(success)
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


def delete_objects(obj_names:set[str], bucket):
    """返回删除失败的 obj name"""
    objects = [dict(Key=obj_name) for obj_name in obj_names]
    resp = bucket.delete_objects(Delete={"Objects": objects})
    deleted = [obj["Key"] for obj in resp["Deleted"]]
    print_delete_result(obj_names, deleted)


def delete_album(album_folder:str, bucket):
    objects = get_objects_by_prefix(album_folder, bucket)
    obj_list = [dict(Key=obj.key) for obj in objects]
    if obj_list:
        resp = bucket.delete_objects(Delete={"Objects": obj_list})
        deleted = [obj["Key"] for obj in resp["Deleted"]]
        obj_names = [obj.key for obj in objects]
        print_delete_result(set(obj_names), deleted)
    delete_album_from_r2_files(album_folder, get_r2_files())


def print_delete_result(obj_names:set, deleted:list):
    if len(deleted) > 0:
        print(f"Deleted from R2: {', '.join(deleted)}")
    failed = obj_names.difference(deleted)
    if len(failed) > 0:
        print(f"未删除云端文件: {', '.join(failed)}")


def file_checksum(filepath:Path) -> str:
    text = filepath.read_text()
    return hashlib.sha1(text.encode()).hexdigest()


def get_objects_by_prefix(prefix, bucket):
    return bucket.objects.filter(Prefix=prefix)

