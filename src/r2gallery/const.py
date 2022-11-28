from pathlib import Path

# 这里主要是一些字符串的常量
# 定义字符串常量后, 在写代码时就有自动补全, 很方便, 也能减少 typo

Templates    = "templates"
Output_Local = "output_local"
Output_Web   = "output_web"
Gallery_Toml = "gallery.toml"
Album_Toml   = "album.toml"

CWD               = Path.cwd().resolve()
Templates_Path    = CWD.joinpath(Templates)
Output_Local_Path = CWD.joinpath(Output_Local)
Output_Web_Path   = CWD.joinpath(Output_Web)
Gallery_Toml_Path = CWD.joinpath(Gallery_Toml)
