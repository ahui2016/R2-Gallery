import os
import shutil
import sys
from pathlib import Path

import arrow
import jinja2
from PIL import Image, ImageOps, ExifTags

from . import model
from .const import CWD, Templates_Path, Output_Local_Path, Output_Web_Path, \
    Gallery_Toml, Gallery_Toml_Path, Templates, Album_Toml, Metadata, Thumbs, \
    Dot_Toml, Picture_Toml, DateTime, DateTimeOriginal
from .model import Gallery, Album, Picture

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
    album_toml   = Album_Toml,
    picture_toml = Picture_Toml,
)


def render_toml(tmpl_name:str, toml_path:Path, data):
    tmpl = jinja_env.get_template(tmplfile[tmpl_name])
    rendered = tmpl.render(dict(data=data))
    print(f"render and write {toml_path}")
    toml_path.write_text(rendered, encoding="utf-8")


def render_gallery_toml(gallery:Gallery):
    render_toml('gallery_toml', Gallery_Toml_Path, gallery)


def render_album_toml(toml_path:Path, album:Album):
    render_toml('album_toml', toml_path, album)


def render_picture_toml(toml_path:Path, pic:Picture):
    render_toml('picture_toml', toml_path, pic)


def folder_not_empty(folder):
    return True if os.listdir(folder) else False


def init_gallery():
    """在一个空文件夹中初始化一个图库.

    :return: 有错返回 err: str, 无错返回 falsy 值。
    """
    if folder_not_empty(CWD):
        return f"Folder Not Empty: {CWD}"

    Output_Local_Path.mkdir()
    Output_Web_Path.mkdir()
    copy_templates()
    render_gallery_toml(Gallery.default(CWD.name))
    print("图库创建成功。")
    print(f"请用文本编辑器打开 {Gallery_Toml_Path} 填写图库相关信息。")
    return None


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


def create_album(name:str, gallery:Gallery):
    if err := model.check_pathname(name):
        return err

    album_path = CWD.joinpath(name)
    if album_path.exists():
        return f"文件夹已存在: {name}"

    album_path.mkdir()
    album_toml_path = album_path.joinpath(Album_Toml)
    metadata_path = album_path.joinpath(Metadata)
    thumbs_path = album_path.joinpath(Thumbs)
    thumbs_path.mkdir()
    metadata_path.mkdir()
    render_album_toml(album_toml_path, Album.default(name))
    gallery.add_album(name)
    render_gallery_toml(gallery)
    print("相册创建成功。")
    print(f"请用文本编辑器打开 {album_toml_path} 填写相册相关信息。")
    return None


def update_all_albums(gallery:Gallery):
    for album_name in gallery.albums:
        album_path = CWD.joinpath(album_name)
        if not album_path.exists():
            print(f"相册不存在: {album_name}")
            continue
        update_album(album_path, gallery)


def update_album(album_path:Path, gallery:Gallery):
    files = album_path.glob("*.*")
    pics = [pic for pic in files if pic.is_file() and pic.name != Album_Toml]
    for pic in pics:
        img = open_image(pic)
        if img is None:
            print(f"Not Image: {pic.name}")
        else:
            exif = img.getexif()
            print(f"exif: {exif}")
            for k in exif.keys():
                if type(k) == int:
                    print(f"{ExifTags.TAGS[k]}({k}): {exif[k]}")
                else:
                    print(f"{k}: {exif[k]}")
            create_pic_toml_if_not_exists(img, pic, album_path)
            create_thumb_if_not_exists(img, pic, album_path, gallery)


def get_image_datetime(img:Image):
    exif = img.getexif()
    if DateTimeOriginal in exif:
        dt = arrow.get(exif[DateTimeOriginal], model.ImageDateTimeFormat)
        return dt.to("local").format(model.RFC3339)
    if DateTime in exif:
        dt = arrow.get(exif[DateTime], model.ImageDateTimeFormat)
        return dt.to("local").format(model.RFC3339)
    return model.now()


def create_pic_toml_if_not_exists(img:Image, pic_path:Path, album_path:Path):
    pic_toml_name = pic_path.with_suffix(Dot_Toml).name
    pic_toml_path = album_path.joinpath(Metadata, pic_toml_name)
    if not pic_toml_path.exists():
        pic = Picture.default(pic_path.name, get_image_datetime(img))
        render_picture_toml(pic_toml_path, pic)


def create_thumb_if_not_exists(
        img:Image, pic_path:Path, album_path:Path, gallery:Gallery):
    suffix = f".{gallery.image_output_format.lower()}"
    thumb_name = pic_path.with_suffix(suffix).name
    thumb_path = album_path.joinpath(Thumbs, thumb_name)
    if not thumb_path.exists():
        create_thumb(img, thumb_path, gallery)


# https://pillow.readthedocs.io/en/stable/handbook/tutorial.html
def create_thumb(img:Image, thumb_path:Path, gallery:Gallery):
    img = ImageOps.exif_transpose(img)
    img = ImageOps.fit(img, gallery.thumbnail_size())
    img.save(thumb_path, gallery.image_output_format)
    print(f"Create thumbnail {thumb_path}")


def resize_image(img:Image, pic_path:Path, gallery:Gallery):
    pass

def open_image(file):
    """
    :return: Image | None
    """
    try:
        img = Image.open(file)
    except OSError:
        img = None
    return img

def print_err(err):
    """如果有错误就打印, 没错误就忽略."""
    if err:
        print(f"Error: {err}", file=sys.stderr)


def print_err_exist(ctx, err):
    """若有错误则打印并结束程序, 无错误则忽略."""
    if err:
        print(f"Error: {err}", file=sys.stderr)
        ctx.exit()
