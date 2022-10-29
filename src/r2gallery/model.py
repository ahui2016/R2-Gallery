import re
from dataclasses import dataclass, asdict
from enum import Enum, auto

import arrow


RFC3339 = "YYYY-MM-DD HH:mm:ssZZ"

Filename_Forbid_Pattern = re.compile(r"[^._0-9a-zA-Z\-]")
"""文件名只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)。"""

Photo_Notes_Limit = 512
"""一张照片的简介的简单描述的长度上限，单位: UTF8字符"""


class SortBy(Enum):
    CTime     = auto()
    CTimeDesc = auto()
    PTime     = auto()
    PTimeDesc = auto()
    List      = auto()  # 用列表指定顺序


def now():
    return arrow.now().format(RFC3339)


# 照片配置: id(filename,不包括相册名), url, 描述, 隐藏, 拍摄日期, 发布日期
@dataclass
class Photo:
    filename : str  # 文件名 (只能使用半角英数, 建议尽量简短)
    notes    : str  # 简单描述 (纯文本格式, 第一行是图片标题)
    story    : str  # 照片的故事 (Markdown 格式)
    ctime    : str  # 拍摄日期
    ptime    : str  # 发布日期
    r2_url   : str  # 照片的 R2 地址 (自动获取)
    r2_html  : str  # 照片网页的 R2 地址 (自动获取)
    checksum : str  # sha1, 用来判断 notes/story 有无变更

@dataclass
class Album:
    foldername : str   # 相册文件夹名称 (只能使用半角英数, 建议尽量简短)
    author     : str   # 作者, 留空表示跟随图库作者
    notes      : str   # 相册简介 (纯文本格式, 第一行是相册标题)
    story      : str   # 相册的故事 (Markdown 格式)
    ctime      : str   # 相册创建时间
    utime      : str   # 相册更新时间 (比如添加照片, 就会更新该时间)
    r2_html    : str   # 相册网页的 R2 地址 (自动获取)
    checksum   : str   # sha1, 用来判断 notes/story 有无变更
    sort_by    : str   # 可选择 SortBy 里的五种排序方式
    photos     : list  # 照片文件名列表
    cover      : str   # 封面 (指定一个照片文件名)

