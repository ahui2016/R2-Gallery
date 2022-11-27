import os
import shutil
import sys
from pathlib import Path

import jinja2

from .const import CWD, Templates_Path, Output_Local_Path, Output_Web_Path, \
    Gallery_Toml, Gallery_Toml_Path, Templates
from .model import Gallery

"""
【关于返回值】
本项目的返回值有时采用 (result, err) 的形式,
err 是 str|None, 有内容表示有错误, 空字符串或 None 表示没错误.
"""

loader = jinja2.FileSystemLoader(Templates_Path)
jinja_env = jinja2.Environment(
    loader=loader, autoescape=jinja2.select_autoescape()
)

# 将templates 文件夹内除了 tmplfile 之外的全部文件都复制到 output 文件夹
tmplfile = dict(
    gallery_toml = Gallery_Toml,
)

def render_gallery_toml(cfg):
    tmpl = jinja_env.get_template(tmplfile['gallery_toml'])
    rendered = tmpl.render(dict(cfg=cfg))
    print(f"render and write {Gallery_Toml_Path}")
    Gallery_Toml_Path.write_text(rendered, encoding="utf-8")


def folder_not_empty(folder):
    return True if os.listdir(folder) else False


def init_gallery():
    """在一个空文件夹中初始化一个图库.

    :return: 有错返回 err: str, 无错返回空字符串。
    """
    if folder_not_empty(CWD):
        return f"Folder Not Empty: {CWD}"

    Output_Local_Path.mkdir()
    Output_Web_Path.mkdir()
    copy_templates()
    render_gallery_toml(Gallery.default(CWD.name))
    print(f"请用文本编辑器打开 {Gallery_Toml_Path} 填写图库相关信息。")
    return ""


def get_gallery(ctx):
    if is_gallery_folder():
        gallery = Gallery.loads()
        return gallery

    print("请先进入图库根目录, 或使用 'r2g init' 命令新建图库")
    ctx.exit()


def is_gallery_folder():
    """检查当前文件夹是否图库根目录"""
    return Templates_Path.exists() \
        and Output_Web_Path.exists() \
        and Output_Web_Path.exists() \
        and Gallery_Toml_Path.exists()


def copy_templates():
    src_folder = Path(__file__).parent.joinpath(Templates)
    shutil.copytree(src_folder, Templates_Path)


def print_err(err):
    """如果有错误就打印, 没错误就忽略."""
    if err:
        print(f"Error: {err}", file=sys.stderr)


def print_err_exist(ctx, err):
    """若有错误则打印并结束程序, 无错误则忽略."""
    if err:
        print(f"Error: {err}", file=sys.stderr)
        ctx.exit()
