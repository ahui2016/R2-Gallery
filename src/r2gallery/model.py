import hashlib
import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import arrow
import tomli
import mistune

from .const import Gallery_Toml_Path, RFC3339, Metadata, Dot_Toml, CWD, \
    Album_Toml, Dot_JPEG, Index_HTML, Dot_HTML, Thumbs

Filename_Forbid_Pattern = re.compile(r"[^._0-9a-zA-Z\-]")
"""文件名只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)。"""

Short_Notes_Limit = 512
"""简单描述的长度上限，单位: UTF8字符"""

Title_Limit = 32
"""从简介中提取标题时, 标题的长度上限, 单位: UTF8字符"""


class SortBy(Enum):
    """相册内的图片的排序方法"""
    CTime     = auto()  # 按图片拍摄或发布日期排序
    CTimeDesc = auto()  # 按图片拍摄或发布日期排序(倒序)
    List      = auto()  # 用列表指定顺序


def sort_by_from(text:str):
    n = len(text)
    if n <= len("List"):
        return SortBy.List
    elif n >= len("CTimeDesc"):
        return SortBy.CTimeDesc
    else:
        return SortBy.CTime


class Frontpage(Enum):
    """图库/相册首页的展示方式"""
    Story  = auto()  # 展示简介, 故事及列表
    Single = auto()  # 只展示一张图片
    List   = auto()  # 只展示列表


# 注意! 本软件暂时只能使用 JPEG, 原本打算让用户自由选择格式,
# 但后来想暂时先保持简单, 以后看情况再考虑让用户选择.
class ImageFormat(Enum):
    """缩小图片或生成缩略图时, 输出的图片格式"""
    WebP = auto()
    JPEG = auto()


def now():
    return arrow.now().format(RFC3339)


@dataclass
class PictureData:
    """用于生成前端 HTML"""
    file_id       : str  # 文件名作为 id (不含后缀名, 转小写)
    filename      : str  # 图片文件名, 包括后缀, 不包括文件夹
    title         : str  # 提取自 Picture.notes 的第一行
    notes         : str  # 提取自 Picture.notes (不含第一行)
    story         : str  # Picture.story 转换为 HTML
    ctime         : str  # 相当于 Picture.ctime
    r2_html       : str  # 图片页面的 R2 对象名
    r2_pic_name   : str  # 图片本身的 R2 对象名
    r2_thumb_name : str  # 缩略图的 R2 对象名


@dataclass
class Picture:
    notes    : str  # 简单描述 (纯文本格式, 第一行是图片标题)
    story    : str  # 图片的故事 (Markdown 格式)
    ctime    : str  # 拍摄或创作或发布日期
    checksum : str  # sha1, 用来判断 notes/story 有无变更

    @classmethod
    def default(cls, file:Path, ctime:str=None):
        if ctime is None:
            ctime = now()
        file_id = file.stem.lower()
        return Picture(
            notes=file_id,
            story="",
            ctime=ctime,
            checksum="",
        )

    @classmethod
    def loads(cls, toml_path:Path):
        """Loads TOML to a Picture."""
        data = tomli_loads(toml_path)
        pic = Picture(**data)
        pic.notes = pic.notes.strip()
        pic.story = pic.story.strip()
        return pic

    def make_checksum(self):
        text = self.notes + self.story + self.ctime
        return text_checksum(text)

    def title(self):
        """图片允许没有标题/简介"""
        pic_title, _, _ = split_notes(self.notes)
        return pic_title

    def to_data(self, pic_path:Path) -> PictureData:
        """pic_name 是图片文件名, 包括后缀, 不包括文件夹."""
        title, notes, _ = split_notes(self.notes)
        file_id = pic_path.stem.lower()
        pic_name = pic_path.name
        album_folder = pic_path.parent.name
        return PictureData(
            file_id=file_id,
            filename=pic_name,
            title=title,
            notes=notes,
            story=mistune.html(self.story),
            ctime=self.ctime,
            r2_html=f"{album_folder}/{file_id+Dot_HTML}",
            r2_pic_name=f"{album_folder}/{pic_name}",
            r2_thumb_name=f"{album_folder}/{Thumbs}/{file_id+Dot_JPEG}",
        )


@dataclass
class AlbumData:
    """用于生成前端 HTML"""
    name               : str  # 相册文件夹名称 (只能使用半角英数, 建议尽量简短)
    author             : str  # 相当于 Album.author
    title              : str  # 提取自 Album.notes 的第一行
    notes              : str  # 提取自 Album.notes (不含第一行)
    story              : str  # Album.story 转换为 HTML
    sort_by            : str  # 相当于 Album.sort_by
    r2_html            : str  # R2 HTML object name
    cover_thumb_r2     : str  # Album.cover 的缩略图文件名
    cover_thumb_web    : str  # Album.cover 的缩略图网址
    cover_thumb_local  : str  # Album.cover 的缩略图本地路径
    cover_title        : str  # 提取自 Album.cover 的 notes


@dataclass
class Album:
    author     : str  # 作者, 留空表示跟随图库作者
    notes      : str  # 相册简介 (纯文本格式, 第一行是相册标题)
    story      : str  # 相册的故事 (Markdown 格式)
    sort_by    : str  # 相册内照片排序, 可选择 SortBy 里的五种排序方式
    pictures   : list # 图片文件名列表
    cover      : str  # 封面 (指定一个图片文件名)
    frontpage  : str  # 默认 Frontpage.Story
    checksum   : str  # sha1, 用来判断相册首页 HTML 要不要更新

    @classmethod
    def default(cls, foldername):
        return Album(
            author="",
            notes=foldername,
            story="",
            sort_by=SortBy.CTimeDesc.name,
            pictures=[],
            cover="",
            frontpage=Frontpage.Story.name,
            checksum="",
        )

    @classmethod
    def loads(cls, toml_path:Path):
        """Loads TOML to an Album."""
        data = tomli_loads(toml_path)
        album = Album(**data)
        album.notes = album.notes.strip()
        album.story = album.story.strip()
        album.frontpage = album.frontpage.capitalize()
        album.sort_by = sort_by_from(album.sort_by).name
        return album

    def delete_pic(self, pic_name:str):
        if pic_name in self.pictures:
            self.pictures.remove(pic_name)
        if pic_name == self.cover:
            if len(self.pictures) > 0:
                self.cover = self.pictures[0]
            else:
                self.cover = ""

    def make_checksum(self):
        pictures = ''.join(self.pictures)
        text = self.author + self.notes + self.story + self.sort_by + pictures \
               + self.cover + self.frontpage
        return text_checksum(text)

    def index_html_name(self):
        return f"album_index_{self.frontpage.lower()}.html"

    def to_data(self, album_path:Path, bucket_url:str) -> AlbumData:
        foldername = album_path.name
        title, notes, err = split_notes(self.notes)
        if err:
            title = foldername
        if not self.cover:
            cover_thumb_name = ""
            cover_title = ""
        else:
            cover_toml_name = Path(self.cover).with_suffix(Dot_Toml).name
            cover_toml_path = album_path.joinpath(Metadata, cover_toml_name)
            cover_thumb_name = cover_toml_path.with_suffix(Dot_JPEG).name
            cover_title = Picture.loads(cover_toml_path).title()
        return AlbumData(
            name=foldername,
            author=self.author,
            title=title,
            notes=notes,
            story=mistune.html(self.story),
            sort_by=self.sort_by,
            r2_html=f"{foldername}/{Index_HTML}",
            cover_thumb_r2=f"{foldername}/thumbs/{cover_thumb_name}",
            cover_thumb_web=f"{bucket_url}{foldername}/thumbs/{cover_thumb_name}",
            cover_thumb_local=f"../{foldername}/thumbs/{cover_thumb_name}",
            cover_title=cover_title,
        )


@dataclass
class GalleryData:
    author       : str  # 相当于 Gallery.author
    title        : str  # 提取自 Gallery.notes 的第一行
    notes        : str  # 提取自 Gallery.notes (不含第一行)
    story        : str  # Gallery.story 转换为 HTML
    frontpage    : str  # 相当于 Gallery.frontpage
    bucket_url   : str  # 相当于 Gallery.bucket_url


@dataclass
class Gallery:
    author    : str   # 图库作者 (默认:佚名)
    notes     : str   # 图库简介 (纯文本格式, 第一行是图库标题)
    story     : str   # 图库的故事 (Markdown 格式)
    frontpage : str   # 可选择 Frontpage 里的三种展示方式
    albums    : list  # 相册列表
    checksum  : str   # sha1, 用来判断图库首页 HTML 要不要更新
    use_proxy : str   # 是否使用 http proxy
    http_proxy : str  # 默认 http://127.0.0.1:1081

    image_width_max     : int  # 图片宽度上限, 单位: 像素
    image_height_max    : int  # 图片高度上限, 单位: 像素
    image_size_max      : int  # 图片体积上限, 单位: MB
    image_output_format : str  # 缩小图片或生成缩略图时输出的图片格式
    thumb_size          : int  # 缩略图边长 (缩略图总是正方形)

    endpoint_url          : str  # 以下 5 项是 Cloudflare R2 信息
    aws_access_key_id     : str
    aws_secret_access_key : str
    bucket_name           : str
    bucket_url            : str

    @classmethod
    def default(cls, title:str):
        author = "佚名"
        return Gallery(
            author=author,
            notes=title,
            story="",
            frontpage=Frontpage.Story.name,
            albums=[],
            checksum="",
            use_proxy="",
            http_proxy="http://127.0.0.1:1081",
            image_width_max=1000,
            image_height_max=1000,
            image_size_max=2,
            image_output_format=ImageFormat.JPEG.name,
            thumb_size=128,
            endpoint_url='https://<accountid>.r2.cloudflarestorage.com',
            aws_access_key_id = '<access_key_id>',
            aws_secret_access_key = '<access_key_secret>',
            bucket_name = '<bucket_name>',
            bucket_url = '<bucket_url>',
        )

    @classmethod
    def loads(cls):
        """Loads the Gallery config from Gallery_Toml_Path."""
        data = tomli_loads(Gallery_Toml_Path)
        gallery = Gallery(**data)
        gallery.notes = gallery.notes.strip()
        gallery.story = gallery.story.strip()
        gallery.frontpage = gallery.frontpage.capitalize()
        bucket_url = gallery.bucket_url
        gallery.bucket_url = bucket_url.rstrip("/") + "/"
        return gallery

    def r2_html_url(self) -> str:
        """R2 首页的完整网址"""
        return f"{self.bucket_url}{Index_HTML}"

    def to_data(self) -> GalleryData:
        title, notes, err = split_notes(self.notes)
        if err:
            title = err
        return GalleryData(
            author=self.author,
            title=title,
            notes=notes,
            story=mistune.html(self.story),
            frontpage=self.frontpage,
            bucket_url=self.bucket_url,
        )

    def title(self):
        """
        :return: (result, err)
        """
        gallery_title, _, err = split_notes(self.notes)
        return gallery_title, err

    def make_checksum(self):
        albums = ''.join(self.albums)
        text = self.author + self.notes + self.story + self.frontpage + albums
        return text_checksum(text)

    def add_album(self, album_name:str):
        self.albums.insert(0, album_name)

    def thumbnail_size(self):
        """用于 PIL.Image.thumbnail(size)"""
        return self.thumb_size, self.thumb_size

    def thumb_suffix(self):
        return f".{self.image_output_format.lower()}"

    def index_html_name(self):
        return f"index_{self.frontpage.lower()}.html"

    def delete_album(self, album_folder:str):
        if album_folder in self.albums:
            self.albums.remove(album_folder)

    def get_albumdata(self):
        albums = []
        for album_name in self.albums:
            album_path = CWD.joinpath(album_name)
            album_toml_path = album_path.joinpath(Album_Toml)
            album = Album.loads(album_toml_path)
            albums.append(album.to_data(album_path, self.bucket_url))
        return albums


def text_checksum(text:str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()


def tomli_loads(file) -> dict:
    """正确处理 utf-16"""
    with open(file, "rb") as f:
        text = f.read()
        try:
            text = text.decode()  # Default encoding is 'utf-8'.
        except UnicodeDecodeError:
            text = text.decode("utf-16").encode("utf-8").decode("utf-8")
        return tomli.loads(text)


def split_notes(text:str) -> (str, str, str|None):
    """
    :return: (标题, 简介, 错误)
    """
    title, notes = split_first_line(text)
    err = None
    if not title:
        err = "未填写notes"
    return title, notes, err


def split_first_line(text:str) -> (str, str):
    """将 text 分成两部分, 第一部分是第一行, 其余是第二部分.
    其中第一行还有长度限制.

    注意, 有可能返回空字符串."""
    parts = text.split("\n", maxsplit=1)
    if len(parts) < 2:
        parts.append("")
    head, tail = parts[0], parts[1].strip()
    if len(head) > Title_Limit:
        head = head[:Title_Limit]
    return head, tail


def check_filename(name: str):
    """
    :return: 有错返回 err: str, 无错返回空字符串。
    """
    if Filename_Forbid_Pattern.search(name) is None:
        return False
    else:
        return "文件名/文件夹名只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)" \
               "\n注意：不能使用空格，请用下划线或短横线代替空格。"
