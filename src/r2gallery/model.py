import hashlib
import re
from dataclasses import dataclass
from enum import Enum, auto

import arrow
import tomli

from .const import Gallery_Toml_Path

RFC3339 = "YYYY-MM-DD HH:mm:ssZZ"

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


class Frontpage(Enum):
    """图库首页的展示方式"""
    Story  = auto()  # 展示图库简介, 故事及相册列表
    Single = auto()  # 只展示最新的一张图片
    List   = auto()  # 只展示相册列表


class ImageFormat(Enum):
    """缩小图片或生成缩略图时, 输出的图片格式"""
    WebP = auto()
    JPEG = auto()


def now():
    return arrow.now().format(RFC3339)


@dataclass
class Picture:
    filename : str  # 文件名 (只能使用半角英数, 建议尽量简短)
    notes    : str  # 简单描述 (纯文本格式, 第一行是图片标题)
    story    : str  # 图片的故事 (Markdown 格式)
    ctime    : str  # 拍摄或创作或发布日期
    checksum : str  # sha1, 用来判断 notes/story 有无变更
    r2_url   : str  # 图片的 R2 地址 (自动获取)
    r2_html  : str  # 图片网页的 R2 地址 (自动获取)

    @classmethod
    def default(cls, filename):
        pic = Picture(
            filename=filename,
            notes=filename,
            story="",
            ctime=now(),
            checksum="",
            r2_url="",
            r2_html="",
        )
        pic.update_checksum()
        return pic

    def update_checksum(self):
        """当 notes, story, ctime 的内容有变化时, 更新 checksum."""
        text = self.notes + self.story + self.ctime
        checksum = text_checksum(text)
        if checksum != self.checksum:
            self.checksum = checksum


@dataclass
class Album:
    foldername : str   # 相册文件夹名称 (只能使用半角英数, 建议尽量简短)
    author     : str   # 作者, 留空表示跟随图库作者
    notes      : str   # 相册简介 (纯文本格式, 第一行是相册标题)
    story      : str   # 相册的故事 (Markdown 格式)
    sort_by    : str   # 相册内照片排序, 可选择 SortBy 里的五种排序方式
    pictures   : list  # 图片文件名列表
    cover      : str   # 封面 (指定一个图片文件名)
    checksum   : str   # sha1, 用来判断相册首页 HTML 要不要更新
    r2_html    : str   # 相册网页的 R2 地址 (自动获取)

    @classmethod
    def default(cls, foldername):
        album = Album(
            foldername=foldername,
            author="",
            notes=foldername,
            story="",
            sort_by=SortBy.CTimeDesc.name,
            pictures=[],
            cover="",
            checksum="",
            r2_html=""
        )
        album.update_checksum()
        return album

    def update_checksum(self):
        """当 author, notes, story, sort_by, pictures, cover
        的内容有变化时, 更新 checksum."""
        pictures = ''.join(self.pictures)
        text = self.author + self.notes + self.story + self.sort_by + pictures + self.cover
        checksum = text_checksum(text)
        if checksum != self.checksum:
            self.checksum = checksum


@dataclass
class Gallery:
    author    : str   # 图库作者 (默认:佚名)
    notes     : str   # 图库简介 (纯文本格式, 第一行是图库标题)
    story     : str   # 图库的故事 (Markdown 格式)
    frontpage : str   # 可选择 Frontpage 里的三种展示方式
    albums    : list  # 相册列表
    checksum  : str   # sha1, 用来判断图库首页 HTML 要不要更新
    r2_html   : str   # 图库首页的 R2 地址 (自动获取)

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
        gallery = Gallery(
            author=author,
            notes=title,
            story="",
            frontpage=Frontpage.Story.name,
            albums=[],
            checksum="",
            r2_html="",
            image_width_max=1000,
            image_height_max=1000,
            image_size_max=2,
            image_output_format=ImageFormat.WebP.name,
            thumb_size=128,
            endpoint_url='https://<accountid>.r2.cloudflarestorage.com',
            aws_access_key_id = '<access_key_id>',
            aws_secret_access_key = '<access_key_secret>',
            bucket_name = '<bucket_name>',
            bucket_url = '<bucket_url>',
        )
        gallery.update_checksum()
        return gallery

    @classmethod
    def loads(cls):
        """Loads the Gallery config from Gallery_Toml_Path."""
        data = tomli_loads(Gallery_Toml_Path)
        ga = Gallery(**data)
        ga.notes = ga.notes.strip()
        ga.story = ga.story.strip()
        return ga

    def title(self):
        """
        :return: (result, err)
        """
        return get_title(self.notes)

    def update_checksum(self):
        """当 author, notes, story, frontpage, albums
        的内容有变化时, 更新 checksum."""
        albums = ''.join(self.albums)
        text = self.author + self.notes + self.story + self.frontpage + albums
        checksum = text_checksum(text)
        if checksum != self.checksum:
            self.checksum = checksum

    def add_album(self, album_name:str):
        self.albums.insert(0, album_name)
        self.update_checksum()

    def thumbnail_size(self):
        """用于 PIL.Image.thumbnail(size)"""
        return self.thumb_size, self.thumb_size


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


def get_title(text:str):
    """
    :return: (result, err)
    """
    line = get_first_line(text)
    if not line:
        return None, "必须填写简介(标题)"
    if len(line) >= Title_Limit:
        return line[:Title_Limit], None
    return line, None


def get_first_line(text:str):
    """
    :return: str, 注意有可能返回空字符串。
    """
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def check_pathname(name: str):
    """
    :return: 有错返回 err: str, 无错返回空字符串。
    """
    if Filename_Forbid_Pattern.search(name) is None:
        return False
    else:
        return "文件名只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)" \
               "\n注意：不能使用空格，请用下划线或短横线代替空格。"
