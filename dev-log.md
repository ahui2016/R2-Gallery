# 开发日志

## TODO

- 每个相册可单独设置展示方式: 缩略图 or 单图(index2.html)
- 上传图片到 R2
- r2_static_files.json:
  记录已上传到 R2 的 html/css 等文件的 checksum, 以便判断是否需要更新.

## 2022-12-09

- 禁止图片名称: index
- http proxy

## 2022-12-08

- 图片的 HTML 页面 (local_pic.html)
- 下一页 (如何高效地获得下一张图片的网址?)
- 图片允许没有标题

## 概念

### 添加图片

执行 `r2g -update` 时自动找出新图片, 没有 toml 文件的图片就是新图片,
对于一张新图片, 要做以下处理:

- 生成同名 (不同后缀名) 的 toml 文件
- 生成缩略图
- 添加图片文件名到 album.toml
- 添加图片路径到 r2_waiting["add"]
- 添加缩略图路径到 r2_waiting["add"]
- 等执行 `r2g upload -all` 时才上传 r2_waiting["add"]

### 删除图片

r2_waiting["delete"]
