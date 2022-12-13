import click

from . import __version__, util, r2
from .const import Gallery_Toml_Path
from .util import print_err, print_err_exist, get_gallery

"""
【关于返回值】
本项目的返回值有时采用 (result, err) 的形式,
err 是 str|None, 有内容表示有错误, 空字符串或 None 表示没错误.
"""

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def show_info(ctx):
    gallery = get_gallery(ctx)
    title, err = gallery.title()
    print_err_exist(ctx, err)

    print()
    print(f"[r2g]     {__file__}")
    print(f"[version] {__version__}")
    print(f"[repo]    https://github.com/ahui2016/R2-Gallery")
    print()
    print(f"[Gallery] {title}")
    print(f"[Author]  {gallery.author}")
    print(f"[Albums]  {len(gallery.albums)}")
    print()
    print("[R2 Home Page]")
    print(gallery.r2_html_url())
    print()
    print(f"[Image Width Max    ] {gallery.image_width_max} px")
    print(f"[Image Height Max   ] {gallery.image_height_max} px")
    print(f"[Image Size Max     ] {gallery.image_size_max} MB")
    print(f"[Image Output Format] {gallery.image_output_format}")
    print(f"[Thumbnail Size     ] {gallery.thumb_size}")
    print()
    print(f"[use proxy] {gallery.use_proxy}")
    proxy = gallery.http_proxy
    if not proxy and gallery.use_proxy:
        proxy = f"\n未设置 proxy, 请用文本编辑器打开 '{Gallery_Toml_Path}' 填写 http proxy"
    print(f"[http proxy] {proxy}")


@click.group(invoke_without_command=True)
@click.help_option("-h", "--help")
@click.option(
    "info", "-i", "-info", "-v", "-V",
    is_flag=True,
    help="Show information about the gallery.",
)
@click.option(
    "-update",
    is_flag=True,
    help="Add or remove toml files of all pictures."
)
@click.option(
    "--force-resize",
    is_flag=True,
    help="Force resize all oversize pictures."
)
@click.option("--use-proxy", help="Set '1' or 'on' or 'true' to use proxy.")
@click.pass_context
def cli(ctx, info, update, force_resize, use_proxy):
    """R2-Gallery: 个人独立相册，采用 Cloudflare R2 作为图片储存。

    https://github.com/ahui2016/R2-Gallery/
    """
    if info:
        show_info(ctx)
        ctx.exit()

    if use_proxy:
        gallery = get_gallery(ctx)
        util.set_use_proxy(use_proxy, gallery)
        ctx.exit()

    if update:
        gallery = get_gallery(ctx)
        albums_pics = util.get_all_albums_pictures(gallery)
        if util.check_all_bad_names(albums_pics) > 0:
            ctx.exit()
        if util.check_all_double_names(albums_pics) > 0:
            ctx.exit()
        if util.update_all_albums(albums_pics, gallery):
            ctx.exit()

        err = util.check_all_albums_cover(albums_pics)
        print_err_exist(ctx, err)

        util.render_all(albums_pics, gallery)
        ctx.exit()

    if force_resize:
        click.confirm("注意，强制缩小图片有可能覆盖原图，请先备份原图。确认执行吗？", abort=True)
        gallery = get_gallery(ctx)
        albums_pics = util.get_all_albums_pictures(gallery)
        util.resize_all_albums_pics(albums_pics, gallery)
        ctx.exit()

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()


# 以上是主命令
# ########## #
# 以下是子命令


@cli.command(context_settings=CONTEXT_SETTINGS, name="init")
@click.pass_context
def init_command(ctx):
    """Initialize your gallery.

    初始化图库。请在一个空文件夹内执行 'r2g init'。
    """
    err = util.init_gallery()
    print_err(err)
    ctx.exit()


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option("name", "-new", help="Create a new album.")
@click.pass_context
def album(ctx, name):
    """Operations about albums.

    关于相册的操作。
    """
    gallery = get_gallery(ctx)

    if name:
        err = util.create_album(name, gallery)
        print_err(err)
        ctx.exit()

    click.echo(ctx.get_help())
    ctx.exit()


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option("all_files", "-all", is_flag=True, help="Upload pictures and assets.")
@click.option("-pics", is_flag=True, help="Upload pictures.")
@click.option("-assets", is_flag=True, help="Upload assets.")
@click.pass_context
def upload(ctx, all_files, pics, assets):
    """Upload pictures or static files.

    上传图片或 HTML/CSS 等文件。
    """
    gallery = get_gallery(ctx)

    if all_files:
        bucket = r2.get_bucket(gallery)
        r2.upload_pics(bucket)
        r2.upload_assets(bucket)
    elif pics:
        bucket = r2.get_bucket(gallery)
        r2.upload_pics(bucket)
    elif assets:
        bucket = r2.get_bucket(gallery)
        r2.upload_assets(bucket)
    else:
        click.echo(ctx.get_help())
    ctx.exit()
