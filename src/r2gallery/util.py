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
    Dot_Toml, Picture_Toml, DateTime, DateTimeOriginal, MB, ImageDateTimeFormat, \
    ImageWidth, ImageLength, Orientation
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
    albums = get_all_albums(gallery)
    for album_path in albums:
        update_album(album_path, gallery)


def resize_all_albums_pics(gallery:Gallery):
    albums = get_all_albums(gallery)
    for album_path in albums:
        resize_oversize_pics(album_path, gallery)


def check_all_albums_pic_names(gallery:Gallery):
    """
    :return: 零表示没有重复的文件名, 大于零表示有重复的文件名
    """
    album_paths = get_all_albums(gallery)
    albums = {}
    for album_path in album_paths:
        names = check_album_pic_names(album_path)
        if names:
            albums[album_path.name] = names

    if len(albums) > 0:
        print_double_names(albums)

    return len(albums)


def print_double_names(albums:dict):
    print("请修改以下文件名, 使每个文件名都是唯一 (不分大小写, 不管后缀名)")
    for album_name, pic_names in albums.items():
        for pic_name in pic_names:
            print(f"{album_name}/{pic_name}")


def get_all_albums(gallery:Gallery):
    albums = []
    for album_name in gallery.albums:
        album_path = CWD.joinpath(album_name)
        if not album_path.exists():
            print(f"相册不存在: {album_name}")
            continue
        albums.append(album_path)
    return albums


def update_album(album_path:Path, gallery:Gallery):
    files = album_path.glob("*.*")
    pics = [pic for pic in files if pic.is_file() and pic.name != Album_Toml]

    oversize_pics = get_oversize_pics(pics, gallery)
    if oversize_pics:
        print_oversize_pics(oversize_pics)
        return

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


def check_album_pic_names(album_path:Path) -> list[str]:
    """找出同一相册内的同名图片 (不分大小写, 不管后缀名)"""
    files = album_path.glob("*.*")
    pics = [pic for pic in files if pic.is_file() and pic.name != Album_Toml]

    count = {}
    for pic in pics:
        stem = pic.stem.lower()
        if stem in count:
            item = count[stem]
            item[0] += 1
            item[1].append(pic.name)
        else:
            count[stem] = [1, [pic.name]]

    names = []
    for item in count.values():
        if item[0] > 1:
            names.extend(item[1])

    return names


def resize_oversize_pics(album_path:Path, gallery:Gallery):
    files = album_path.glob("*.*")
    pics = [pic for pic in files if pic.is_file() and pic.name != Album_Toml]
    oversize_pics = get_oversize_pics(pics, gallery)
    for pic in oversize_pics:
        img = open_image(pic)
        exif = img.getexif()
        img = resize_image(img, gallery)
        pic_path = pic.with_suffix(gallery.thumb_suffix())
        img.save(pic_path, gallery.image_output_format, exif=reset_exif(exif))
        print(f"Resize to {pic_path}")


def reset_exif(exif):
    """resize后, 图片的宽, 高, 方向可能发生变化"""
    exif[Orientation] = 1
    if ImageWidth in exif:
        del exif[ImageWidth]
    if ImageLength in exif:
        del exif[ImageLength]
    return exif


def print_oversize_pics(oversize_pics):
    if oversize_pics:
        print("以下图片体积超过上限，请手动缩小图片，或使用 `r2g --force-resize` 自动缩小图片。")
        print(f"另外，可在 {Gallery_Toml_Path} 文件中修改图片体积上限（包括高度、宽度、占用空间）。")
        for pic in oversize_pics:
            print(pic)


def get_oversize_pics(pics:list[Path], gallery:Gallery) -> list:
    oversize_pics = []
    for pic in pics:
        img = open_image(pic)
        if img is None:
            continue
        if is_image_oversize(img, pic, gallery):
            oversize_pics.append(pic)
    return oversize_pics


def get_image_datetime(img:Image):
    exif = img.getexif()
    if DateTimeOriginal in exif:
        dt = arrow.get(exif[DateTimeOriginal], ImageDateTimeFormat)
        return dt.to("local").format(model.RFC3339)
    if DateTime in exif:
        dt = arrow.get(exif[DateTime], ImageDateTimeFormat)
        return dt.to("local").format(model.RFC3339)
    return model.now()


def create_pic_toml_if_not_exists(img:Image, pic_path:Path, album_path:Path):
    pic_toml_name = pic_path.with_suffix(Dot_Toml).name
    pic_toml_path = album_path.joinpath(Metadata, pic_toml_name)
    if not pic_toml_path.exists():
        pic = Picture.default(pic_path, get_image_datetime(img))
        render_picture_toml(pic_toml_path, pic)


def create_thumb_if_not_exists(
        img:Image, pic_path:Path, album_path:Path, gallery:Gallery):
    thumb_name = pic_path.with_suffix(gallery.thumb_suffix()).name
    thumb_path = album_path.joinpath(Thumbs, thumb_name)
    if not thumb_path.exists():
        create_thumb(img, thumb_path, gallery)


def create_thumb(img:Image, thumb_path:Path, gallery:Gallery):
    img = ImageOps.exif_transpose(img)
    img = ImageOps.fit(img, gallery.thumbnail_size())
    img.save(thumb_path, gallery.image_output_format)
    print(f"Create thumbnail {thumb_path}")


def resize_image(img:Image, gallery:Gallery):
    """
    :return: Image | None
    """
    img = ImageOps.exif_transpose(img)
    changed = False
    width, height = float(img.size[0]), float(img.size[1])
    width_max, height_max = float(gallery.image_width_max), float(gallery.image_height_max)
    if height > height_max:
        ratio = height_max / height
        width = width * ratio
        height = height_max
        changed = True
    if width > width_max:
        ratio = width_max / width
        height = height * ratio
        width = width_max
        changed = True
    if changed:
        size = round(width), round(height)
        img = img.resize(size)
    return img


def is_image_oversize(img:Image, file:Path, gallery:Gallery):
    filesize = file.lstat().st_size
    width, height = img.size
    if width > gallery.image_width_max \
            or height > gallery.image_height_max \
            or filesize > gallery.image_size_max * MB:
        return True
    return False


def open_image(file):
    """
    :return: Image | None
    """
    try:
        img = Image.open(file)
    except OSError:
        img = None
    return img


def rename_pic(name:str, pic_path:Path):
    pass


def print_err(err):
    """如果有错误就打印, 没错误就忽略."""
    if err:
        print(f"Error: {err}", file=sys.stderr)


def print_err_exist(ctx, err):
    """若有错误则打印并结束程序, 无错误则忽略."""
    if err:
        print(f"Error: {err}", file=sys.stderr)
        ctx.exit()
