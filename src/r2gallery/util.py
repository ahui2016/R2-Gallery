import os
import shutil
import sys

import arrow
import jinja2
from PIL import Image, ImageOps

from . import model, r2
from .const import *
from .model import Gallery, Album, Picture, PictureData, AlbumData, SortBy, GalleryData

"""
【关于返回值】
本项目的返回值有时采用 (result, err) 的形式,
err 是 str|None, 有内容表示有错误, 空字符串或 None 表示没错误.
"""

loader = jinja2.FileSystemLoader(Templates_Path)
jinja_env = jinja2.Environment(
    loader=loader, autoescape=jinja2.select_autoescape()
)

# tmplfile 可能没用
# 将templates 文件夹内除了 tmplfile 之外的全部文件都复制到 output 文件夹
_tmplfile = dict(
    gallery_toml            = Gallery_Toml,
    album_toml              = Album_Toml,
    picture_toml            = Picture_Toml,
    index_list_html         = Index_List_HTML,
    index_story_html        = "index_story.html",
    index_single_html       = "index_single.html",
    album_index_list_html   = Album_Index_List_HTML,
    album_index_story_html  = "album_index_story.html",
    album_index_single_html = "album_index_single.html",
    pic_html                = "pic.html",
    pics_id_list_js         = Pics_Id_List_JS,
)


def render_write(tmpl_name:str, output_path:Path, data:dict):
    tmpl = jinja_env.get_template(tmpl_name)
    rendered = tmpl.render(data)
    print(f"render and write {output_path}")
    output_path.write_text(rendered, encoding="utf-8")


def render_gallery_toml(gallery:Gallery):
    render_write(Gallery_Toml, Gallery_Toml_Path, dict(data=gallery))


def render_album_toml(album:Album, name:str):
    toml_path = CWD.joinpath(name, Album_Toml)
    render_write(Album_Toml, toml_path, dict(data=album))


def render_picture_toml(toml_path:Path, pic:Picture):
    render_write(Picture_Toml, toml_path, dict(data=pic))


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
    Output_R2_Path.mkdir()
    copy_templates()
    render_gallery_toml(Gallery.default(CWD.name))
    r2.add_to_r2_files([Index_HTML])
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
    if err := model.check_filename(name):
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
    album = Album.default(name)
    render_album_toml(album, name)
    gallery.add_album(name)
    render_gallery_toml(gallery)
    print("相册创建成功。")
    print(f"请用文本编辑器打开 {album_toml_path} 填写相册相关信息。")
    return None


def render_all(albums_pics:dict, gallery:Gallery, force=False):
    update_gallery = render_all_albums(albums_pics, gallery, force)
    if not force:
        force = update_gallery
    render_gallery_index(gallery, force)
    r2.add_to_r2_files([Index_HTML])


def render_gallery_index(gallery:Gallery, force:bool):
    local_output_path  = Output_Local_Path.joinpath(Index_HTML)
    local_output_path2 = Output_Local_Path.joinpath(Index2_HTML)
    web_output_path    = Output_Web_Path.joinpath(Index_HTML)
    web_output_path2   = Output_Web_Path.joinpath(Index2_HTML)
    r2_output_path     = Output_R2_Path.joinpath(Index_HTML)
    r2_output_path2    = Output_R2_Path.joinpath(Index2_HTML)

    force = render_index_html(
        "local", gallery.index_html_name(), local_output_path, gallery, force)
    render_index_html(
        "web", gallery.index_html_name(), web_output_path, gallery, force)
    render_index_html(
        "r2", gallery.index_html_name(), r2_output_path, gallery, force)
    render_index_html(
        "local", Index_List_HTML, local_output_path2, gallery, force)
    render_index_html(
        "web", Index_List_HTML, web_output_path2, gallery, force)
    render_index_html(
        "r2", Index_List_HTML, r2_output_path2, gallery, force)


def update_all_albums(albums_pics:dict, gallery:Gallery):
    """返回 True 表示有错, 返回 False 表示无错."""
    for album, pics in albums_pics.items():
        if update_album(pics, Path(album), gallery):
            return True
    return False


def render_all_albums(
        albums_pics:dict,
        gallery:Gallery,
        force=False
) -> bool:
    """:return: True 表示需要重新渲染 gallery 首页."""
    update_gallery = False
    for album_folder, pics in albums_pics.items():
        album_path = Path(album_folder)
        album = Album.loads(album_path.joinpath(Album_Toml))
        album_data = album.to_data(album_path, gallery.bucket_url)
        pics_sorted = sort_pics(pics, album, album_path)

        local_album_folder = Output_Local_Path.joinpath(album_data.name)
        local_album_folder.mkdir(exist_ok=True)
        web_album_folder = Output_Web_Path.joinpath(album_data.name)
        web_album_folder.mkdir(exist_ok=True)
        r2_album_folder = Output_R2_Path.joinpath(album_data.name)
        r2_album_folder.mkdir(exist_ok=True)

        # 渲染相册内的图片
        pics_data_list = render_album_pics(
            pics_sorted,
            local_album_folder,
            web_album_folder,
            r2_album_folder,
            album_data,
            gallery.to_data()
        )

        # 渲染相册索引页
        update_gallery = render_album_index_html(
            local_album_folder,
            web_album_folder,
            r2_album_folder,
            gallery,
            album,
            album_data,
            pics_data_list,
            force=force,
        )

        # 添加待上传的文件 到 r2_files.json
        obj_names = [pic.r2_html for pic in pics_data_list]
        pics_js_name = f"{album_data.name}/{Pics_Id_List_JS}"
        obj_names.extend([album_data.r2_html, pics_js_name])
        r2.add_to_r2_files(obj_names)

    return update_gallery


def sort_pics(pics_paths:list[Path], album:Album, album_path:Path) -> list[Path]:
    sort_by = SortBy[album.sort_by]
    if sort_by is SortBy.List:
        return [album_path.joinpath(filename) for filename in album.pictures]

    pairs = pics_with_ctime(pics_paths)
    if sort_by is SortBy.CTimeDesc:
        pairs = sorted(pairs, key=lambda pair: pair[1], reverse=True)
    else:
        pairs = sorted(pairs, key=lambda pair: pair[1])

    return [pair[0] for pair in pairs]


def pics_with_ctime(pics_paths:list):
    """:return: (pic_path, ctime)"""
    pairs = []
    for pic_path in pics_paths:
        pic = Picture.loads(get_pic_toml_path(pic_path))
        pairs.append((pic_path, pic.ctime))
    return pairs


def resize_all_albums_pics(albums_pics:dict, gallery:Gallery):
    for pics in albums_pics.values():
        resize_oversize_pics(pics, gallery)


def check_all_albums_cover(albums_pics:dict):
    """:return: err:str | None"""
    for album_folder, pics in albums_pics.items():
        album_path = Path(album_folder)
        album_name = album_path.name
        album = Album.loads(album_path.joinpath(Album_Toml))
        if not album.cover:
            return f"每个相册都必须指定封面, 请向相册 {album_name} 添加图片。" \
                   f"添加图片后执行 'r2g -update' 会自动指定封面。" \
                   f"若想手动指定封面, 可修改 '{album_name}/album.toml' 中的 cover 项目。"

        pics_name_list = [pic.name for pic in pics]
        if album.cover not in pics_name_list:
            return f"找不到封面图片: {album.cover}\n" \
                   f"请修改 '{album_name}/album.toml' 中的 cover, " \
                   f"确保 cover 指定的图片存在于相册文件夹 {album_name} 内。"
    return None


def check_all_double_names(albums_pics:dict):
    """
    :return: 零表示没有重复的文件名, 大于零表示有重复的文件名
    """
    albums = {}
    for album, pics in albums_pics.items():
        names = get_double_names(pics)
        if names:
            albums[Path(album).name] = names

    if len(albums) > 0:
        err = "请修改以下文件名, 使每个文件名都是唯一 (不分大小写, 不管后缀名)"
        print_bad_names(albums, err)

    return len(albums)


def check_all_bad_names(albums_pics:dict):
    """
    :return: 零表示没有不符合要求的文件名, 大于零表示有不符合要求的文件名
    """
    albums = {}
    for album, pics in albums_pics.items():
        names = get_bad_pic_names(pics)
        if names:
            albums[Path(album).name] = names

    if len(albums) > 0:
        err = "请修改以下文件名, \n" \
              "文件名只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)\n" \
              "不能使用空格，请用下划线或短横线代替空格。\n" \
              "并且不可使用 'index' 作为文件名。\n"
        print_bad_names(albums, err)

    return len(albums)


def print_bad_names(albums:dict, err:str):
    print(err)
    for album_name, pic_names in albums.items():
        for pic_name in pic_names:
            print(f"{album_name}/{pic_name}")


def pic_paths_to_pic_data(pic_paths:list[Path]) -> list[PictureData]:
    pic_data_list = []
    for pic_path in pic_paths:
        toml_path = get_pic_toml_path(pic_path)
        pic_data = Picture.loads(toml_path).to_data(pic_path)
        pic_data_list.append(pic_data)
    return pic_data_list


def get_all_albums_pictures(gallery:Gallery):
    """获取全部相册的全部图片的 Path"""
    albums = get_all_albums(gallery)
    albums_pics = {}
    for album_path in albums:
        albums_pics[str(album_path)] = get_pic_files(album_path)
    return albums_pics


def get_pic_files(album_path:Path):
    """获取指定相册内全部图片的 Path"""
    files = album_path.glob("*.*")
    pics = [pic for pic in files if pic.is_file() and pic.name != Album_Toml]
    return pics


def get_all_albums(gallery:Gallery):
    """获取全部相册的 Path"""
    albums = []
    for album_name in gallery.albums:
        album_path = CWD.joinpath(album_name)
        if not album_path.exists():
            print(f"相册不存在: {album_name}")
            continue
        albums.append(album_path)
    return albums


def update_album(pics:list, album_path:Path, gallery:Gallery) -> bool:
    """返回 True 表示有错, 返回 False 表示无错."""
    oversize_pics = get_oversize_pics(pics, gallery)
    if oversize_pics:
        print_oversize_pics(oversize_pics)
        return True

    new_pics = []
    new_files_set = set()
    for pic_path in pics:
        img = open_image(pic_path)
        if img is None:
            print(f"Not Image: {pic_path.name}")
        else:
            if create_pic_toml_if_not_exists(img, pic_path):
                new_pics.append(pic_path.name)
                thumb_path = create_thumb_if_not_exists(img, pic_path, album_path, gallery)
                new_files_set.add(str(thumb_path))
                new_files_set.add(str(pic_path))

    r2.add_pics_to_r2_waiting(new_files_set)
    update_album_pictures(new_pics, album_path)
    return False


def update_album_pictures(new_pics:list[str], album_path:Path):
    """添加图片到相册. TODO: 删除图片."""
    if not new_pics:
        return
    album_toml_path = album_path.joinpath(Album_Toml)
    album = Album.loads(album_toml_path)
    album.pictures = new_pics + album.pictures
    if not album.cover:
        album.cover = new_pics[0]
    render_album_toml(album, album_path.name)


def get_double_names(pics:list) -> list[str]:
    """找出同一相册内的同名图片 (不分大小写, 不管后缀名)"""
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


def get_bad_pic_names(files:list[Path]) -> list[str]:
    """找出相册内不符合要求的图片文件名"""
    bad_id_list = ["index"]
    bad_names = []
    for file in files:
        if file.stem.lower() in bad_id_list:
            bad_names.append(file.name)
        if model.check_filename(file.name):
            bad_names.append(file.name)
    return bad_names


def resize_oversize_pics(pics:list, gallery:Gallery):
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


def get_pic_toml_path(pic_path:Path) -> Path:
    pic_toml_name = pic_path.with_suffix(Dot_Toml).name.lower()
    return pic_path.parent.joinpath(Metadata, pic_toml_name)


def create_pic_toml_if_not_exists(img:Image, pic_path:Path):
    """
    :return: True 表示这是新图片, 否则返回 False
    """
    pic_toml_path = get_pic_toml_path(pic_path)
    if not pic_toml_path.exists():
        pic = Picture.default(pic_path, get_image_datetime(img))
        render_picture_toml(pic_toml_path, pic)
        return True
    return False


def create_thumb_if_not_exists(
        img:Image, pic_path:Path, album_path:Path, gallery:Gallery) -> Path:
    thumb_name = pic_path.with_suffix(gallery.thumb_suffix()).name.lower()
    thumb_path = album_path.joinpath(Thumbs, thumb_name)
    create_thumb(img, thumb_path, gallery)
    return thumb_path


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


def render_index_html(
        output_type:str,
        tmpl_name:str,
        output_path:Path,
        gallery:Gallery,
        force=False
) -> bool:
    """返回 True 表示执行了渲染。"""
    checksum = gallery.make_checksum()
    if gallery.checksum != checksum:
        gallery.checksum = checksum
        render_gallery_toml(gallery)
        force = True

    if force:
        render_write(tmpl_name, output_path, dict(
            output_type=output_type,
            gallery=gallery.to_data(),
            albums=gallery.get_albumdata(),
        ))

    return force


def render_album_index_html(
        local_output_folder:Path,
        web_output_folder:Path,
        r2_output_folder:Path,
        gallery:Gallery,
        album:Album,
        album_data:AlbumData,
        pics_data_list:list[PictureData],
        force=False
) -> bool:
    """:return: True 表示需要重新渲染 gallery 首页."""
    update_gallery = False
    checksum = album.make_checksum()
    if album.checksum != checksum:
        album.checksum = checksum
        render_album_toml(album, album_data.name)
        force = True
        update_gallery = True

    if force:
        local_output_path    = local_output_folder.joinpath(Index_HTML)
        local_output_path2   = local_output_folder.joinpath(Index2_HTML)
        web_output_path      = web_output_folder.joinpath(Index_HTML)
        web_output_path2     = web_output_folder.joinpath(Index2_HTML)
        r2_output_path       = r2_output_folder.joinpath(Index_HTML)
        r2_output_path2      = r2_output_folder.joinpath(Index2_HTML)
        local_js_output_path = local_output_folder.joinpath(Pics_Id_List_JS)
        web_js_output_path   = web_output_folder.joinpath(Pics_Id_List_JS)
        r2_js_output_path    = r2_output_folder.joinpath(Pics_Id_List_JS)
        gallery_data         = gallery.to_data()

        data = dict(gallery=gallery_data, album=album_data, pictures=pics_data_list,)
        render_write(album.index_html_name(), r2_output_path, data)
        render_write(Album_Index_List_HTML, r2_output_path2, data)

        data["parent_dir"]=f"../../{album_data.name}/"
        render_write(album.index_html_name(), local_output_path, data)
        render_write(Album_Index_List_HTML, local_output_path2, data)

        data["parent_dir"]=f"{gallery.bucket_url}{album_data.name}/"
        render_write(album.index_html_name(), web_output_path, data)
        render_write(Album_Index_List_HTML, web_output_path2, data)

        pics_id_list = [pic.file_id for pic in pics_data_list]
        pics_id_data = dict(pics=pics_id_list)
        render_write(Pics_Id_List_JS, local_js_output_path, pics_id_data)
        render_write(Pics_Id_List_JS, web_js_output_path, pics_id_data)
        render_write(Pics_Id_List_JS, r2_js_output_path, pics_id_data)

    return update_gallery


def render_album_pics(
        pics_paths:list[Path],
        local_album_folder:Path,
        web_album_folder:Path,
        r2_album_folder:Path,
        album:AlbumData,
        gallery:GalleryData,
        force=False
) -> list[PictureData]:
    """返回 PictureData 有用."""
    pic_data_list = []
    for pic_path in pics_paths:
        pic_data = render_pic_html(
            pic_path, local_album_folder, web_album_folder, r2_album_folder,
            album, gallery, force)
        pic_data_list.append(pic_data)
    return pic_data_list


def render_pic_html(
        pic_path:Path,
        local_album_folder:Path,
        web_album_folder:Path,
        r2_album_folder:Path,
        album:AlbumData,
        gallery:GalleryData,
        force=False
) -> PictureData:
    """返回 PictureData 有用."""
    pic_toml_path = get_pic_toml_path(pic_path)
    pic = Picture.loads(pic_toml_path)
    pic_data = pic.to_data(pic_path)
    checksum = pic.make_checksum()
    if pic.checksum != checksum:
        pic.checksum = checksum
        render_picture_toml(pic_toml_path, pic)
        force = True

    if force:
        pic_html_name = f"{pic_data.file_id}{Dot_HTML}"
        local_output_path = local_album_folder.joinpath(pic_html_name)
        web_output_path = web_album_folder.joinpath(pic_html_name)
        r2_output_path = r2_album_folder.joinpath(pic_html_name)

        data = dict(pic=pic_data, album=album, gallery=gallery)
        render_write(Pic_HTML, r2_output_path, data)
        data["parent_dir"] = f"../../{album.name}/"
        render_write(Pic_HTML, local_output_path, data)
        data["parent_dir"] = f"{gallery.bucket_url}{album.name}/"
        render_write(Pic_HTML, web_output_path, data)

    return pic_data


def delete_pic_or_album(filepath:Path, gallery:Gallery, bucket):
    if filepath.is_file():
        if err := check_pic_in_album(filepath):
            print(err)
            return
        pic_id = filepath.stem.lower()
        thumb_path = filepath.parent.joinpath(Thumbs, pic_id+Dot_JPEG)
        toml_path = filepath.parent.joinpath(Metadata, pic_id+Dot_Toml)
        delete_pic(filepath, thumb_path, toml_path, bucket)
        album_toml_path = filepath.parent.joinpath(Album_Toml)
        album = Album.loads(album_toml_path)
        album.delete_pic(filepath.name)
        render_album_toml(album, filepath.name)
    else:
        if not is_album_in_gallery(filepath):
            print(f"不在图库内: {filepath}")
            return
        if filepath.name in Not_Album_Folders:
            print(f"不是相册: {filepath}")
            return
        delete_album(filepath, gallery, bucket)


def delete_album(album_path:Path, gallery:Gallery, bucket):
    r2.delete_album(album_path.name, bucket)
    output_local_path = Output_Local_Path.joinpath(album_path.name)
    output_web_path = Output_Web_Path.joinpath(album_path.name)
    output_r2_path = Output_R2_Path.joinpath(album_path.name)
    for folder in [album_path, output_local_path, output_web_path, output_r2_path]:
        if folder.exists():
            print(f"Delete {folder}")
            shutil.rmtree(folder)
    gallery.delete_album(album_path.name)
    render_gallery_toml(gallery)


def delete_pic(pic_path:Path, thumb_path:Path, toml_path:Path, bucket):
    r2_waiting = r2.get_r2_waiting()
    r2_files = r2.get_r2_files()
    parts = pic_path.parts
    pic_id = toml_path.stem
    album_folder = parts[-2]
    pic_obj_name = "/".join(parts[-2:])
    thumb_obj_name = "/".join(thumb_path.parts[-3:])
    html_obj_name = f"{album_folder}/{pic_id + Dot_HTML}"
    local_html_path = Output_Local_Path.joinpath(html_obj_name)
    web_html_path = Output_Web_Path.joinpath(html_obj_name)
    r2_html_path = Output_R2_Path.joinpath(html_obj_name)

    objects_to_delete = set()
    if str(pic_path) not in r2_waiting:
        objects_to_delete.add(pic_obj_name)
    if str(thumb_path) not in r2_waiting:
        objects_to_delete.add(thumb_obj_name)
    if r2_files.get(html_obj_name, ""):
        objects_to_delete.add(html_obj_name)
        r2.delete_from_r2_files(html_obj_name, r2_files)

    r2.delete_objects(objects_to_delete, bucket)

    paths_to_delete = [pic_path, thumb_path, toml_path, local_html_path,
                       web_html_path, r2_html_path]
    for file in paths_to_delete:
        if file.exists():
            print(f"Delete {file}")
            file.unlink()
        else:
            print(f"File Not Exists: {file}")


def check_pic_in_album(filepath:Path) -> str:
    if not is_pic_in_album(filepath):
        return f"不在相册内: {filepath}"
    if filepath.suffix == Dot_Toml:
        return f"不是图片: {filepath}"
    return ""


def check_album_in_gallery(album_path:Path) -> str:
    if not is_album_in_gallery(album_path):
        return f"不在当前图库内: {album_path}"
    if album_path.name in [Output_Local, Output_Web, Output_R2, Templates]:
        return f"不是相册: {album_path}"
    return ""


def is_pic_in_album(pic_path:Path) -> bool:
    """返回 False 表示该图片文件不在相册中"""
    album_folder = pic_path.parts[-2]
    my_pic_path = CWD.joinpath(album_folder, pic_path.name)
    return my_pic_path.samefile(pic_path)


def is_album_in_gallery(album_path:Path) -> bool:
    """返回 False 表示该相册文件夹不在图库内"""
    my_album_path = CWD.joinpath(album_path.name)
    return my_album_path.samefile(album_path)


def set_use_proxy(sw:str, gallery:Gallery):
    use_proxy = False
    if sw.lower() in ["1", "on", "true"]:
        use_proxy = True

    gallery.use_proxy = use_proxy
    render_gallery_toml(gallery)
    print(f"设置成功\nuse proxy = {use_proxy}\nhttp proxy = {gallery.http_proxy}")

    if not gallery.http_proxy and use_proxy:
        print(f"未设置 proxy, 请用文本编辑器打开 {Gallery_Toml_Path} 填写 http proxy")



def print_err(err:str):
    """如果有错误就打印, 没错误就忽略."""
    if err:
        print(f"Error: {err}", file=sys.stderr)


def print_err_exist(ctx, err:str):
    """若有错误则打印并结束程序, 无错误则忽略."""
    if err:
        print(f"Error: {err}", file=sys.stderr)
        ctx.exit()
