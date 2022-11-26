import os

from .const import CWD, Templates_Path, Output_Local_Path, Output_Web_Path, \
    Gallery_Toml_Path


def folder_not_empty(folder):
    return True if os.listdir(folder) else False


def init_gallery():
    """在一个空文件夹中初始化一个图库.

    :return: 有错返回 err: str, 无错返回空字符串。
    """
    if folder_not_empty(CWD):
        return f"Folder Not Empty: {CWD}"

    Templates_Path.mkdir()
    Output_Local_Path.mkdir()
    Output_Web_Path.mkdir()
    




def is_gallery_folder():
    """检查当前文件夹是否图库根目录"""
    return Templates_Path