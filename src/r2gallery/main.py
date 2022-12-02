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
@click.pass_context
def cli(ctx, info, update):
    """R2-Gallery: 个人独立相册，采用 Cloudflare R2 作为图片储存。

    https://github.com/ahui2016/R2-Gallery/
    """
    if info:
        show_info(ctx)
        ctx.exit()

    if update:
        gallery = get_gallery(ctx)
        util.update_all_albums(gallery)
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
