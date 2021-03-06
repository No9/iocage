"""snapshot module for the cli."""
import datetime
import subprocess as su

import click

import iocage.lib.ioc_common as ioc_common
import iocage.lib.ioc_json as ioc_json
import iocage.lib.ioc_list as ioc_list

__rootcmd__ = True


@click.command(name="snapshot", help="Snapshots the specified jail.")
@click.argument("jail")
@click.option("--name", "-n", help="The snapshot name. This will be what comes"
                                   " after @", required=False)
def cli(jail, name):
    """Get a list of jails and print the property."""
    jails, paths = ioc_list.IOCList("uuid").list_datasets()
    pool = ioc_json.IOCJson().json_get_value("pool")
    date = datetime.datetime.utcnow().strftime("%F_%T")

    _jail = {tag: uuid for (tag, uuid) in jails.items() if
             uuid.startswith(jail) or tag == jail}

    if len(_jail) == 1:
        tag, uuid = next(iter(_jail.items()))
        path = paths[tag]
    elif len(_jail) > 1:
        ioc_common.logit({
            "level"  : "ERROR",
            "message": f"Multiple jails found for {jail}:"
        })
        for t, u in sorted(_jail.items()):
            ioc_common.logit({
                "level"  : "ERROR",
                "message": f"  {u} ({t})"
            })
        exit(1)
    else:
        ioc_common.logit({
            "level"  : "ERROR",
            "message": f"{jail} not found!"
        })
        exit(1)

    # If they don't supply a snapshot name, we will use the date.
    if not name:
        name = date

    # Looks like foo/iocage/jails/df0ef69a-57b6-4480-b1f8-88f7b6febbdf@BAR
    conf = ioc_json.IOCJson(path).json_load()

    if conf["template"] == "yes":
        target = f"{pool}/iocage/templates/{tag}@{name}"
    else:
        target = f"{pool}/iocage/jails/{uuid}@{name}"

    try:
        su.check_call(["zfs", "snapshot", "-r", target], stderr=su.PIPE)
        ioc_common.logit({
            "level"  : "INFO",
            "message": f"Snapshot: {target} created."
        })
    except su.CalledProcessError:
        ioc_common.logit({
            "level"  : "ERROR",
            "message": "Snapshot already exists!"
        })
        exit(1)
