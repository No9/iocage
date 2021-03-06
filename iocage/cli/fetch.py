"""fetch module for the cli."""
import json
import os

import click

import iocage.lib.ioc_common as ioc_common
import iocage.lib.ioc_fetch as ioc_fetch

__rootcmd__ = True


def validate_count(ctx, param, value):
    """Takes a string, removes the commas and returns an int."""
    if isinstance(value, str):
        try:
            value = value.replace(",", "")

            return int(value)
        except ValueError:
            ioc_common.logit({
                "level"  : "ERROR",
                "message": f"({value} is not a valid  integer."
            })
            exit(1)
    else:
        return int(value)


@click.command(name="fetch", help="Fetch a version of FreeBSD for jail usage.")
@click.option("--http", "-h", default=False,
              help="Have --server define a HTTP server instead.", is_flag=True)
@click.option("--file", "-f", "_file", default=False,
              help="Use a local file directory for root-dir instead of FTP or"
                   " HTTP.", is_flag=True)
@click.option("--files", "-F", multiple=True,
              help="Specify the files to fetch from the mirror.")
@click.option("--server", "-s", default="ftp.freebsd.org",
              help="FTP server to login to.")
@click.option("--user", "-u", default="anonymous", help="The user to use.")
@click.option("--password", "-p", default="anonymous@",
              help="The password to use.")
@click.option("--auth", "-a", default=None, help="Authentication method for "
                                                 "HTTP fetching. Valid "
                                                 "values: basic, digest")
@click.option("--verify/--noverify", "-V/-NV", default=True,
              help="Enable or disable verifying SSL cert for HTTP fetching.")
@click.option("--release", "-r", help="The FreeBSD release to fetch.")
@click.option("--plugin-file", "-P", help="The plugin file to use.")
@click.option("--plugins", help="List all available plugins for creation.",
              is_flag=True)
@click.argument("props", nargs=-1)
@click.option("--count", "-c", callback=validate_count, default="1")
@click.option("--root-dir", "-d", help="Root directory " +
                                       "containing all the RELEASEs.")
@click.option("--update/--noupdate", "-U/-NU", default=True,
              help="Decide whether or not to update the fetch to the latest "
                   "patch level.")
@click.option("--eol/--noeol", "-E/-NE", default=True,
              help="Enable or disable EOL checking with upstream.")
def cli(http, _file, server, user, password, auth, verify, release, plugins,
        plugin_file, root_dir, props, count, update, eol, files):
    """CLI command that calls fetch_release()"""
    freebsd_version = ioc_common.checkoutput(["freebsd-version"])
    arch = os.uname()[4]

    if not files:
        if arch == "arm64":
            files = ("MANIFEST", "base.txz", "doc.txz")
        else:
            files = ("MANIFEST", "base.txz", "lib32.txz", "doc.txz")

    if "HBSD" in freebsd_version:
        if server == "ftp.freebsd.org":
            hardened = True
        else:
            hardened = False
    else:
        hardened = False

    if plugins or plugin_file:
        if plugin_file:
            try:
                with open(plugin_file) as f:
                    json.load(f)
            except FileNotFoundError:
                ioc_common.logit({
                    "level"  : "ERROR",
                    "message": "File was not found!"
                })
                exit(1)
            except json.decoder.JSONDecodeError:
                ioc_common.logit({
                    "level"  : "ERROR",
                    "message": "Invalid JSON file supplied, please supply a "
                               "correctly formatted JSON file."
                })
                exit(1)

        ip = [x for x in props if x.startswith("ip4_addr") or x.startswith(
            "ip6_addr")]
        if not ip:
            ioc_common.logit({
                "level"  : "ERROR",
                "message": "An IP address is needed to fetch a plugin!\n"
                           "Please specify ip(4|6)"
                           "_addr=\"INTERFACE|IPADDRESS\"!"
            })
            exit(1)
        if plugins:
            ioc_fetch.IOCFetch(release=None, http=http, _file=_file,
                               verify=verify, hardened=hardened,
                               update=update, eol=eol,
                               files=files).fetch_plugin_index(props)
            exit()

        if count == 1:
            ioc_fetch.IOCFetch("", server, user, password, auth, root_dir,
                               http=http, _file=_file, verify=verify,
                               hardened=hardened, update=update, eol=eol,
                               files=files).fetch_plugin(
                plugin_file, props, 0)
        else:
            for j in range(1, count + 1):
                ioc_fetch.IOCFetch("", server, user, password, auth, root_dir,
                                   http=http, _file=_file, verify=verify,
                                   hardened=hardened, update=update,
                                   eol=eol, files=files).fetch_plugin(
                    plugin_file, props, j)
    else:
        ioc_fetch.IOCFetch(release, server, user, password, auth, root_dir,
                           http=http,
                           _file=_file, verify=verify, hardened=hardened,
                           update=update,
                           eol=eol, files=files).fetch_release()
