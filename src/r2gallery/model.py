import hashlib
import re
from dataclasses import dataclass, asdict
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


def now():
    return arrow.now().format(RFC3339)


@dataclass
class Picture:
    filename : str  # 文件名 (只能使用半角英数, 建议尽量简短)
    notes    : str  # 简单描述 (纯文本格式, 第一行是图片标题)
    story    : str  # 图片的故事 (Markdown 格式)
    ctime    : str  # 拍摄或发布日期
    r2_url   : str  # 图片的 R2 地址 (自动获取)
    r2_html  : str  # 图片网页的 R2 地址 (自动获取)
    checksum : str  # sha1, 用来判断 notes/story 有无变更


@dataclass
class Album:
    foldername : str   # 相册文件夹名称 (只能使用半角英数, 建议尽量简短)
    author     : str   # 作者, 留空表示跟随图库作者
    notes      : str   # 相册简介 (纯文本格式, 第一行是相册标题)
    story      : str   # 相册的故事 (Markdown 格式)
    ctime      : str   # 相册创建时间
    utime      : str   # 相册更新时间 (比如添加图片, 就会更新该时间)
    r2_html    : str   # 相册网页的 R2 地址 (自动获取)
    checksum   : str   # sha1, 用来判断 notes/story 有无变更
    sort_by    : str   # 可选择 SortBy 里的五种排序方式
    pictures   : list  # 图片文件名列表
    cover      : str   # 封面 (指定一个图片文件名)


@dataclass
class Gallery:
    author    : str   # 图库作者 (默认:佚名)
    notes     : str   # 图库简介 (纯文本格式, 第一行是图库标题)
    story     : str   # 图库的故事 (Markdown 格式)
    r2_html   : str   # 图库首页的 R2 地址 (自动获取)
    checksum  : str   # sha1, 用来判断 notes/story 有无变更
    frontpage : str   # 可选择 Frontpage 里的三种展示方式
    albums    : list  # 相册列表
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
            r2_html="",
            checksum=text_checksum(author + title),
            frontpage=Frontpage.Story.name,
            albums=[],
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
        ga = Gallery(**data)
        ga.notes = ga.notes.strip()
        ga.story = ga.story.strip()
        return ga

    def title(self):
        """
        :return: (result, err)
        """
        return get_title(self.notes)


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
