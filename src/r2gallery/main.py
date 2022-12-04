import click

from . import __version__, util
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
    print(f"[Image Width Max    ] {gallery.image_width_max} px")
    print(f"[Image Height Max   ] {gallery.image_height_max} px")
    print(f"[Image Size Max     ] {gallery.image_size_max} MB")
    print(f"[Image Output Format] {gallery.image_output_format}")
    print(f"[Thumbnail Size     ] {gallery.thumb_size}")
    print()


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
@click.pass_context
def cli(ctx, info, update, force_resize):
    """R2-Gallery: 个人独立相册，采用 Cloudflare R2 作为图片储存。

    https://github.com/ahui2016/R2-Gallery/
    """
    if info:
        show_info(ctx)
        ctx.exit()

    if update:
        gallery = get_gallery(ctx)
        albums_pics = util.get_all_albums_pictures(gallery)
        if util.check_all_bad_names(albums_pics) > 0:
            ctx.exit()
        if util.check_all_double_names(albums_pics) > 0:
            ctx.exit()
        util.update_all_albums(albums_pics, gallery)
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
