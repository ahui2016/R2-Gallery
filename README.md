# R2-Gallery

个人独立相册，其中图片储存采用 Cloudflare R2 实现。

## 关于 Cloudflare R2

Cloudflare R2 是一种云储存服务, 本软件用它来储存图片.

- 官方网址 <https://developers.cloudflare.com/r2/platform/pricing/>
- 方便编程, 注册与设置也简单, 正因为如此, 我才能作出这个软件
- 储存在 R2 里的文件, 可以公开访问 (因此才能用来做相册)
- 有一定免费额度, 最重要的的是, 流量免费
- 内含 10GB 免费容量, 流量免费, 注册时需要信用卡或 PayPal  
  (注意: 上传下载等的操作次数超过上限也会产生费用,
   详情以 Cloudflare 官方说明为准).

由于本软件采用了 Cloudflare R2, 因此用户不得不麻烦一点自己去注册账号,
以及填写配置信息, 下面我会详细说明如何操作 (详见后文 "准备工作" 部分).

## 大架构

- 使用本软件可创建一个或多个图库 (Gallery)
- 每个图库可包含一个或多个相册 (Album)
- 每个相册可包含一张或多张图片 (Picture)
- 每个图库/相册/图片都有对应的 toml 文件, 包含了它们的信息 (例如标题/简介)
- 使用 `r2g render` 命令会根据上述 toml 文件生成网页

### 三种输出

使用 `r2g render` 命令生成网页时, 有 3 种不同的输出:

- **本地预览** (文件夹名: output_local):  
  浏览该网页不会产生流量, 方便在本地预览效果, 减少云端流量消费.
- **正常网站** (文件夹名: output_web):  
  即使在本地浏览该网页也会产生流量,
  通常将这个文件夹内的网页发布到网上 (例如 GitHub Pages).
- **Cloudflare R2**:  
  直接将网页上传到云端, 通过在 R2 设置的网址即可访问相册.

具体而言, 当执行 `r2g render -all` 或 `r2g render NAME` 等命令时,
都会同时输出 *本地预览* 与 *正常网站*.

为了节省流量以及避免网络通讯耗费时间, 只有执行 `r2g render --to-cloud`
命令时才会将网页上传到 Cloudflare R2.

建议本地预览确认网页内容符合自己的期望后, 才执行 `r2g render --to-cloud`.

**正常网站** (文件夹 output_web) 相当于一个静态网站,
你可以采用 GitHub Pages 之类的服务将这个文件夹的内容发布到网上.


## Picture

- 文件名只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)
- 文件名包括后缀名, 不包括目录
- 文件名请尽量不要太长
- toml 里的文件名不可手动更改
- 自动获取简单描述的第一行作为图片的标题
- 简单描述采用纯文本格式, 有字数限制, 建议不要写太长
- 如果有较长的描述, 可以写在 story 里, 采用 Markdown 格式
- checksum, 用来判断 notes/story 有无变更

## Album

- 使用命令 `r2g album -new NAME` 新建相册
- 每个相册一个文件夹
- 上述命令里的 NAME 是相册的文件夹名称  
  - 只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)  
  - 并且应尽量短
- 在相册文件夹内有一个 album.toml 文件, 以及 thumbs 和 metadata 文件夹
- 可在 album.toml 文件里填写相册标题, 相册标题可以使用任何字符
- 相册简介采用纯文本格式, 第一行是相册标题
- 如果有较长的描述, 可以写在 story 里, 采用 Markdown 格式
- ctime, 相册创建时间
- utime, 相册更新时间 (比如添加图片, 就会更新该时间)
- r2_html, 相册网页的 R2 地址 (自动获取)
- checksum, 用来判断 notes/story 有无变更
- sort_by(排序方法): 按创建时间/按更新时间/由列表指定等共 5 种排序方式
  - 采用 SortBy.List 以外的方式时, Pictures 列表可以为空
  - 采用 SortBy.List 方式时, 必须填写 Pictures 列表
  - 采用 SortBy.List 方式时, 只显示列表中的图片, 未列出的就不会显示
    (但图片本身仍可被公开访问, 只是不出现在相册中)
  - 采用 SortBy.List 以外的方式时, 使用命令
    `r2g album --rewrite-sortby-list -name NAME`
    可以自动填充 Pictures 列表 (目的是方便后续改为 SortBy.List 方式)
- Pictures (图片文件名列表), 只在采用 SortBy.List 方式时才生效
- 添加图片时, 则自动添加到 Pictures 列表头部
- cover, 指定一个图片文件名作为相册封面, 留空则采用第一张

## Gallery

- author, 图库作者 (必填)
- notes, 图库简介 (纯文本格式, 第一行是图库标题)
- 如果有较长的描述, 可以写在 story 里, 采用 Markdown 格式
- checksum, 用来判断 notes/story 有无变更
- 相册列表排序: 只能手动排序
- 相册列表
  - 相册依次排序
  - 不在列表中的相册不会显示在图库网页中 (但相册本身仍可被公开访问)
- 首页可选择 3 种展示方式
  - 相册列表(封面)
  - 最新单图
  - 相册介绍(notes+story+相册列表)

## r2_static_files.json

记录已上传到 R2 的 html/css 等文件的 checksum, 以便判断是否需要更新.

## 准备工作

为了让你的图片能通过互联网访问, 本软件采用的办法是上传图片到
Cloudflare R2. 因此, 需要先开通 Cloudflare R2.

### 开通 Cloudflare R2

1. 注册账户 <https://www.cloudflare.com/>
2. 启用 R2 服务 <https://developers.cloudflare.com/r2/get-started/>  
   内含 10GB 免费容量, 流量免费, 注册时需要信用卡或 PayPal  
   (注意: 上传下载等的操作次数超过上限也会产生费用,
    详情以 Cloudflare 官方说明为准).
3. 从 dashboard 进入 R2 页面，点击 Create bucket 创建一个数据桶。
   建议 bucket 的名称设为 `my-gallery`
4. 进入新建的 bucket, 点击 Settings,
   在 Public Access 栏内点击 Allow Access,
   该操作成功后可以看到 Public Bucket URL, 请复制保存, 后续有用.

### 生成密钥

(如果已经有密钥, 就不需要再生成了.)

1. 在 R2 页面可以找到 Account ID, 请复制保存, 后续有用.
2. 在 R2 页面点击 Manage R2 API Tokens
3. 点击 Create API Token, 权限选择 Edit, 再点击右下角的 Create API
   Token 按钮, 即可得到 Access Key ID 和 Secret Access Key

**注意**:  
Access Key ID 和 Secret Access Key 只显示一次, 请立即复制保存
(建议保存到密码管理器中)

### 五个重要信息

经过上述操作后, 一共获得了 5 个重要信息, 请妥善保存这些信息:

- bucket 名称 (以下称为 **bucket_name**)
- Public Bucket URL (以下称为 **bucket_url**)
- Account ID (以下称为 **accountid**)
- Access Key ID (以下称为 **access_key_id**)
- Secret Access Key (以下称为 **access_key_secret**)

## 创建一个新图库

安装了 r2g 命令后, 进入任何一个空文件夹内, 执行命令 `rg2 init`
初始化一个图库.

初始化成功后，在当前文件夹 (以下称为 "图库根目录") 内可以看到：

- **templates** (相册网页模板)
- **output_local** (本地网站, 图片地址采用相对路径)
- **output_web** (正常网站, 图片地址是 R2 公开仓库的网址)
- **gallery.toml** (图库作者, 图库简介等)

### 填写图库信息

如上所述, 创建图库后, 会得到一个 gallery.toml 文件,
请用文本编辑器打开 gallery.toml, 其内容大概像这样:

```toml
author = '佚名'
notes = '''
My Gallery
'''
endpoint_url = 'https://<accountid>.r2.cloudflarestorage.com'
aws_access_key_id = '<access_key_id>'
aws_secret_access_key = '<access_key_secret>'
bucket_name = '<bucket_name>'
bucket_url = '<bucket_url>'
```

其中 `<accountid>` 等尖括号的位置要填写正确的值, 一共有 5 个尖括号,
这五个值都可以在上文 `准备工作` 部分找到. (填写时, 不要保留尖括号.)

填写正确的值后保存文件, 配置完成, 可以开始正常使用.

### 注意 bucket_name

每一个图库, 对应一个 bucket_name, 如果在本地新建第二个图库,
那么在 Cloudflare R2 那边也要建立一个新的 bucket,
并获得其 Public Bucket URL.

全部图库的 accountid, access_key_id, access_key_secret 都是通用的,
而 bucket_name 和 bucket_url 是每个图库独立的.

### 填写图库作者与简介等

在上述 gallery.toml 中, 有三个项目涉及图库的作者, 标题, 介绍等信息.

- **author**: 作者名称, 默认佚名, 请改为你的真名或网名
- **notes** (简介):
  - 第一行会被自动提取作为图库的标题
  - 若有更多介绍可从第二行开始写 (参照下面的例子)
  - 有字数限制, 不可超过 512 个字
- **story** (故事):
  - story 与 上面的 notes 一样都是对图库的介绍
  - 不同的是, notes 是纯文本, story 采用 Markdown 格式,
    notes 有字数限制, story 无字数限制
  - 因此, 如果你需要更丰富的格式, 或需要写较多内容, 可以填写 story

示例:

```toml
author = '小帅'
notes = '''
小帅的相册

这里主要是我日常拍的, 旅行拍的照片。
'''
story = '''
## 关于我

一般 story 的标题建议从 `h2` 开始，因为图库标题（**即 notes 的第一行**）
已经占用了 h1
'''
```

## 创建相册

- 使用命令 `r2g album -new NAME` 新建相册
  - 或 `r2g --new-album NAME`
- 其中 NAME 是相册文件夹名称
  - 只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)  
  - 相册文件夹名会成为网址的一部分, 因此建议尽量短一点

### 填写相册信息

使用上述命令创建相册后, 会得到一个新文件夹,
进入该文件夹内, 可以看到一个 album.toml 文件.

- 请在 album.toml 文件里填写相册简介 (默认为相册文件夹名)
- 相册简介采用纯文本格式, 第一行是相册标题
- 如果有较长的描述, 可以写在 story 里, 采用 Markdown 格式
- story 的标题建议从 `h2` 开始 (即最大的标题从 `##` 开始)

### 相册排序

- 新增的相册会被自动添加到 gallery.toml 文件的 albums 列表中
- 如果想调整相册顺序, 可直接编辑 gallery.toml 文件中的 albums 列表
- 你也可以删除列表中的相册文件夹名, 不在列表中的相册不会显示在图库网页中
  (但相册本身仍可被公开访问)

## 添加图片

- 直接复制/剪切图片, 粘贴到相册文件夹中.
- 图片文件名只能使用 0-9, a-z, A-Z, _(下划线), -(短横线), .(点)  
- 图片文件名会成为网址的一部分, 因此建议尽量短一点
- 图片的中文名/标题, 或描述, 可在添加图片后写在对应的 toml 文件里.
- 如果在终端使用 cp 或 mv 命令, 要注意防止覆盖同名文件.
  - 在 Linux 里, 使用 `-i` 开关, 例如 `mv -i src.jpg dest.jpg`
  - 在 Windows 里, 使用 `-cf` 开关, 例如 `mv -cf src.jpg dest.jpg`

### 填写图片信息

添加一张或多张图片到一个或多个相册文件夹后, 在图库根目录执行命令
`r2g -update` 给新增的图片生成同名 toml 文件.

> 注意: `r2g -update` 只处理 gallery.toml 中的 albums 列表中的相册.

- 请在 toml 文件里填写图片简介 (默认为图片文件名)
- 相册简介采用纯文本格式, 第一行是相册标题
- 如果有较长的描述, 可以写在 story 里, 采用 Markdown 格式

填写信息后, 执行命令 `r2g render NAME` (其中 NAME 是相册文件夹名)
或 `r2g render -all` 更新网页.

### 图片体积上限

注意, 本软件并非图片备份软件!

本软件是资源敏感的, 涉及网络传输, 使用了云服务, 如果超过免费额度,
就会产生费用.

因此, 建议限制图片的尺寸与体积. 在 gallery.toml 中有三项相关设定:

- **image_width_max**: 图片宽度上限, 默认 1000 像素
- **image_height_max**: 图片高度上限, 默认 1000 像素
- **image_size_max**: 图片体积上限, 默认 2 MB

### 缩小图片体积

如果添加的图片超过如上所述的体积上限，会报错，此时你可以：

1. 用文本编辑器打开 gallery.toml 修改上限值。
2. 自己另行用图片编辑器缩小图片，使其符合上述宽度、高度、体积要求。
3. 使用命令 `r2g --force-resize` 让本软件执行缩小图片的操作。

注意, 使用命令 `r2g --force-resize` 时, 如果缩小尺寸后的图片文件名与
原图的文件名相同, 就会覆盖原图, 如果文件名不同, 则原图与小图共存,
此时, 请检查小图看看有无问题, 如果没问题请手动删除原图.

如上所述, 由于有可能覆盖原图, 因此请先备份原图.

还要注意, 命令 `r2g --force-resize` 不能正常处理 RAW, NEF 等图片格式.

### 缩略图

添加照片, 执行 `r2g -update` 后, 会生成缩略图在 thumbs 文件夹里.

修改 gallery.toml 中的 `thumb_size` 可设定缩略图的边长 (缩略图总是正方形).

### 封面

- 每个相册都必须指定封面。
- 第一次向相册添加图片时 (复制图片到文件夹内, 然后执行 `r2g -update`)
  会自动指定封面。
- 若想手动指定封面, 可修改 album.toml 中的 cover 项目,
  被指定的封面图片必须存在于该相册内。
- 另外, 也可以删除 gallery.toml 中的 albums 列表中的相册文件夹名,
  不在该列表中的相册可以没有封面。

### 图片排列顺序

有 3 种排序方法: 按创建时间 / 按创建时间倒序 / 由列表指定

- 采用 SortBy.List 以外的方式时, album.toml 中的 pictures 列表可以为空
- 采用 SortBy.List 方式时, 必须填写 album.toml 中的 pictures 列表
- 采用 SortBy.List 方式时, 只显示列表中的图片, 未列出的就不会显示
  (但图片本身仍可被公开访问, 只是不出现在相册中)

## 建议使用终端文本编辑器

本软件的大部分操作都需要在终端输入命令, 有时需要稍稍修改一下 toml,
这种情况下如果切换到文本编辑器去操作, 会感觉优点麻烦, 因此建议使用类似
Vim/Emacs 的终端文本编辑器, 就很方便.

我找到了 [micro](https://github.com/zyedidia/micro), 它类似 Vim/Emacs
并且更轻, 也更易学易用, 优点:

- 启动速度飞快, 感觉非常轻巧.
- 非常易学易用, 支持鼠标选择, 以及用 Ctrl-C / Ctrl-V 来复制黏贴.  
  支持 Ctrl-S 保存 / Ctrl-A 全选等符合现代习惯的快捷键.

