import re
from dataclasses import dataclass, asdict
from enum import Enum, auto

import arrow


RFC3339 = "YYYY-MM-DD HH:mm:ssZZ"

Filename_Forbid_Pattern = re.compile(r"[^._0-9a-zA-Z\-]")
"""文件名只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)。"""

Short_Notes_Limit = 512
"""简单描述的长度上限，单位: UTF8字符"""


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
