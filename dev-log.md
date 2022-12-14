# 开发日志

## TODO

- 每个相册可单独设置展示方式: 缩略图 or 单图(index2.html)
  - 生成图库/相册的 list.html
- 优化: 减少重复读写 toml 的次数
- PictureData.r2_pic_name, PictureData.r2_thumb_name 可能没用
- util.pic_paths_to_pic_data() 可能没用

## 2022-12-14

- 合并 html templates (local, web, r2 三合一)

## 2022-12-13

- r2_files.json:
  记录已上传到 R2 的 html/css 等文件的 checksum, 以便判断是否需要更新.
- 生成 output_r2 版本的网页
- 上传 output_r2 内的文件

## 2022-12-12

- `r2g -info` 显示 http proxy
- `r2g upload -pics` 上传图片
- 生成 output_web 版本的网页 (添加文件到 r2_waiting.json)

## 2022-12-11

- 添加待上传的文件到 r2_files.json
- 添加待上传的图片到 r2_waiting.json
- 渲染 output_web 的 HTML 文件

## 2022-12-10

- r2_waiting.json: 记录待上传和待删除的图片
- r2_files.json: 记录 HTML/CSS 等文件的 checksum

## 2022-12-09

- 禁止图片名称: index
- http proxy

## 2022-12-08

- 图片的 HTML 页面 (local_pic.html)
- 下一页 (如何高效地获得下一张图片的网址?)
- 图片允许没有标题

## 概念

### 添加图片

执行 `r2g -update` 时 (在 render 阶段) 自动找出新图片,
没有 toml 文件的图片就是新图片, 对于一张新图片, 要做以下处理:

- 生成同名 (不同后缀名) 的 toml 文件
- 生成缩略图
- 添加图片文件名到 album.toml
- 添加图片的 HTML 到 r2_files.json
- 添加图片路径到 r2_waiting["upload"]
- 添加缩略图路径到 r2_waiting["upload"]
- 等执行 `r2g upload -all` 时才上传 r2_waiting["upload"]
- 执行 `r2g upload -all` 时更新 r2_files.json 里的 checksum

### 删除图片

r2_waiting["delete"]

### Frontpage

- 图库/相册首页是 index.html, 该网页内容会根据 frontpage 设定而变化
- 另外图库/相册还有一个 list.html 页面, 内容固定为相册/图片列表
