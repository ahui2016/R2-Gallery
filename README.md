# R2-Gallery

个人独立相册，其中图片储存采用 Cloudflare R2 实现。


## Photo

- 文件名只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)
- 文件名包括后缀名, 不包括目录
- 文件名请尽量不要太长
- toml 里的文件名不可手动更改
- 自动获取简单描述的第一行作为照片的标题
- 简单描述采用纯文本格式, 有字数限制, 建议不要写太长
- 如果有较长的描述, 可以写在 story 里, 采用 Markdown 格式
- checksum, 用来判断 notes/story 有无变更

## Album

- 使用 `r2g album -new NAME` 命令新建相册
- 每个相册一个文件夹
- 上述命令里的 NAME 是相册的文件夹名称  
  - 只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)  
  - 并且应尽量短
- 在相册文件夹内有一个 album.toml 文件
- 可在 album.toml 文件里填写相册标题, 相册标题可以使用任何字符
- 相册简介采用纯文本格式, 第一行是相册标题
- 如果有较长的描述, 可以写在 story 里, 采用 Markdown 格式
- ctime, 相册创建时间
- utime, 相册更新时间 (比如添加照片, 就会更新该时间)
- r2_html, 相册网页的 R2 地址 (自动获取)
- checksum, 用来判断 notes/story 有无变更
- sort_by(排序方法): 按创建时间/按更新时间/由列表指定等共 5 种排序方式
- 采用 SortBy.List 以外的方式时, photos 列表可以为空
- 采用 SortBy.List 方式时, 必须填写 photos 列表
- 采用 SortBy.List 方式时, 只显示列表中的照片, 未列出的就不会显示
  (但照片本身仍可被公开访问, 只是不出现在相册中)
- 采用 SortBy.List 以外的方式时, 使用命令
  `r2g album --rewrite-sortby-list -name NAME`
  可以自动填充 photos 列表 (目的是方便后续改为 SortBy.List 方式)
- photos(照片文件名列表), 只在采用 SortBy.List 方式时才生效
- 采用 SortBy.List 方式时, 如果添加照片, 则自动添加到列表头部
- cover, 指定一个照片文件名作为相册封面, 留空则采用第一张


## 建议使用终端文本编辑器

本软件的大部分操作都需要在终端输入命令, 有时需要稍稍修改一下 toml,
这种情况下如果切换到文本编辑器去操作, 会感觉优点麻烦, 因此建议使用类似
Vim/Emacs 的终端文本编辑器, 就很方便.

我找到了 [micro](https://github.com/zyedidia/micro), 它类似 Vim/Emacs
并且更轻, 也更易学易用, 优点:

- 启动速度飞快, 感觉非常轻巧.
- 非常易学易用, 支持鼠标选择, 以及用 Ctrl-C / Ctrl-V 来复制黏贴.  
  支持 Ctrl-S 保存 / Ctrl-A 全选等符合现代习惯的快捷键.

