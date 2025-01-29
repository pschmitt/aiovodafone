#!/usr/bin/env python3
"""Test script for aiovodafone library."""

import asyncio
import json
import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

import aiohttp
from rich import print_json

from aiovodafone.api import (
    VodafoneStationCommonApi,
    VodafoneStationSercommApi,
    VodafoneStationTechnicolorApi,
)
from aiovodafone.const import DeviceType
from aiovodafone.exceptions import (
    AlreadyLogged,
    CannotAuthenticate,
    CannotConnect,
    GenericLoginError,
    ModelNotSupported,
    VodafoneError,
)

LOGGER = logging.getLogger(__name__)


def get_arguments() -> tuple[ArgumentParser, Namespace]:
    """Get parsed passed in arguments."""
    parser = ArgumentParser(description="aiovodafone library test")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug mode",
    )
    parser.add_argument(
        "--router",
        "-r",
        type=str,
        default="192.168.0.1",
        help="Set router IP address",
    )
    parser.add_argument(
        "--username",
        "-u",
        type=str,
        default="vodafone",
        help="Set router username",
    )
    parser.add_argument(
        "--password",
        "-p",
        type=str,
        help="Set router password",
    )
    parser.add_argument(
        "--configfile",
        "-cf",
        type=str,
        help="Load options from JSON config file. \
        Command line options override those in the file.",
    )

    parser.add_argument(
        "ACTION",
        choices=["dns", "ping", "traceroute"],
        help="Action to perform",
    )

    parser.add_argument("TARGET", help="Target to ping/traceroute/resolve")

    arguments = parser.parse_args()
    # Re-parse the command line
    # taking the options in the optional JSON file as a basis
    if arguments.configfile and Path(arguments.configfile).exists():
        with Path.open(arguments.configfile) as f:
            arguments = parser.parse_args(namespace=Namespace(**json.load(f)))

    return parser, arguments


async def main() -> None:
    """Run main."""
    parser, args = get_arguments()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        LOGGER.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("asyncio").setLevel(logging.INFO)
        logging.getLogger("charset_normalizer").setLevel(logging.INFO)

    if not args.password:
        LOGGER.error("You have to specify a password")
        parser.print_help()
        sys.exit(1)

    async with aiohttp.ClientSession() as session:
        device_type = await VodafoneStationCommonApi.get_device_type(
            args.router,
            session,
        )

    api: VodafoneStationCommonApi
    if device_type == DeviceType.TECHNICOLOR:
        api = VodafoneStationTechnicolorApi(args.router, args.username, args.password)
    elif device_type == DeviceType.SERCOMM:
        api = VodafoneStationSercommApi(args.router, args.username, args.password)
    else:
        LOGGER.error("The device is not a supported Vodafone Station.")
        sys.exit(1)

    try:
        try:
            if device_type == DeviceType.TECHNICOLOR:
                await api.login(force=True)
            else:
                await api.login()
        except ModelNotSupported:
            LOGGER.exception("Model is not supported yet for router %s", api.host)
            raise
        except CannotAuthenticate:
            LOGGER.exception("Cannot authenticate to router %s", api.host)
            raise
        except CannotConnect:
            LOGGER.exception("Cannot connect to router %s", api.host)
            raise
        except AlreadyLogged:
            LOGGER.exception(
                "Only one user at a time can connect to router %s",
                api.host,
            )
            raise
        except GenericLoginError:
            LOGGER.exception("Unable to login to router %s", api.host)
            raise
    except VodafoneError:
        await api.close()
        sys.exit(1)

    rc = 0
    res = None
    if args.ACTION == "dns":
        LOGGER.debug("ping %s", args.TARGET)
        res = await api.dns_resolve(args.TARGET)
    elif args.ACTION == "ping":
        LOGGER.debug("Resolve %s", args.TARGET)
        res = await api.ping(args.TARGET)
    elif args.ACTION == "traceroute":
        LOGGER.debug("Traceroute %s", args.TARGET)
        res = await api.traceroute(args.TARGET)
    else:
        LOGGER.error("Unknown action: %s", args.ACTION)
        rc = 1

    if res:
        print_json(json.dumps(res.get("data")))

    LOGGER.debug("Logout & close session")
    await api.logout()
    await api.close()
    sys.exit(rc)


if __name__ == "__main__":
    asyncio.run(main())
