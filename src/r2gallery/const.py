from pathlib import Path

# 这里主要是一些字符串的常量
# 定义字符串常量后, 在写代码时就有自动补全, 很方便, 也能减少 typo

Templates    = "templates"
Output_Local = "output_local"
Output_Web   = "output_web"
Gallery_Toml = "gallery.toml"
Album_Toml   = "album.toml"
Picture_Toml = "picture.toml"
Metadata     = "metadata"
Thumbs       = "thumbs"

Index_HTML       = "index.html"
Index_Local_HTML = "index_local.html"
Index_Web_HTML   = "index_web.html"

Dot_Toml = ".toml"
Dot_JPEG = ".jpeg"
# Dot_Webp = ".webp"

DateTimeOriginal = 36867
DateTime         = 306
Orientation      = 274
ImageWidth       = 256
ImageLength      = 257

RFC3339 = "YYYY-MM-DD HH:mm:ssZZ"
ImageDateTimeFormat = "YYYY:MM:DD HH:mm:ss"

MB = 1024 * 1024

CWD               = Path.cwd().resolve()
Templates_Path    = CWD.joinpath(Templates)
Output_Local_Path = CWD.joinpath(Output_Local)
Output_Web_Path   = CWD.joinpath(Output_Web)
Gallery_Toml_Path = CWD.joinpath(Gallery_Toml)
