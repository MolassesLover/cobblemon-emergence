#!/usr/bin/env python3

"""
The core module for Cobblemon Emergence's launcher and development utilities.
"""

import os
import tomllib
import sys
import shutil
import json
import hashlib

from pathlib import PureWindowsPath, Path
from dataclasses import dataclass

import requests


class Colors:
    """
    A few ANSI escape codes in order to output colours to the terminal.
    """

    RESET = "\033[0m"
    RED = "\033[0;31m"
    YELLOW = "\033[0;33m"
    GREEN = "\033[0;32m"
    BLUE = "\033[0;34m"


def log_message_info(message_string):
    """
    One of the logging functions. Prints a formatted message.
    """

    print(f":: {message_string}")


def log_message_warning(message_string):
    """
    One of the logging functions. Prints a formatted warning message.
    """

    print(f":: {Colors.YELLOW}Warning{Colors.RESET}: {message_string}")


def log_message_error(message_string):
    """
    One of the logging functions. Prints a formatted error message.
    """

    print(f":: {Colors.RED}Error{Colors.RESET}: {message_string}")


def exit_error(message_string_error):
    """
    Print out an error message, and exit with error code -1.
    """

    log_message_error(message_string_error)

    sys.exit(-1)


def temp_directory_path_query(
    temp_directory_win32: str, temp_directory_unix: str
) -> str:
    # Make Windows use the right temp directory, and have a few sanity checks to ensure compatibility.
    match sys.platform:
        case "win32":
            temp_directory_path = temp_environment_setup(temp_directory_win32)
        case "linux":
            temp_directory_path = temp_environment_setup(temp_directory_unix)
        case "freebsd":
            temp_directory_path = temp_environment_setup(temp_directory_unix)
        case "darwin":
            temp_directory_path = temp_environment_setup(temp_directory_unix)
        case _:
            exit_error(
                "Unsupported platform, can't create the temp directory for cache."
            )

    return temp_directory_path


# https://stackoverflow.com/a/75292055
def path_to_posix(path):
    """
    Returns a path formatted to follow Unix conventions.
    """

    return PureWindowsPath(
        os.path.normpath(PureWindowsPath(path).as_posix())
    ).as_posix()


def free_space_query() -> float:
    """
    Obtain the amount of space available to the root directory in gigabytes.
    This is used to ensure there is enough space for all the mods.

    Returns the available space as a float.
    """

    match sys.platform:
        case "win32":
            # This is bad, this path should be chosen manually on initial setup.
            path = "C:/"
        case _:
            path = "/"

    file_system_stat = shutil.disk_usage(path)

    available_gigabytes = file_system_stat.free / 1024 / 1024 / 1024

    return available_gigabytes


def free_space_query_required(config_path) -> float:
    # Open the config file, get the modpack size.
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_file_string = config_file.read()
        config_file_dictionary = json.loads(config_file_string)

        free_space_requirement = config_file_dictionary["modpack_size_gb"]

    return free_space_requirement


def free_space_validate(free_space, free_space_requirement):
    if free_space < free_space_requirement:
        exit_error(
            f"Insufficient storage on device, expected at least {free_space_requirement} gb"
        )


def temp_environment_setup(temp_directory: str) -> str:
    """
    Create the necessary temp directory for cached mod files.
    """

    if os.path.exists(temp_directory):
        log_message_info(
            f"Using temp directory: `{Colors.YELLOW}{temp_directory}{Colors.RESET}`"
        )
    else:
        exit_error(
            f"Could not find temp directory: `{Colors.YELLOW}{temp_directory}{Colors.RESET}`"
        )

    temp_directory_path = f"{temp_directory}/molasses.love/cobblemon-emergence"

    os.makedirs(temp_directory_path, exist_ok=True)

    return temp_directory_path


def mod_list_read(mod_list_path, mods) -> dict:
    with open(mod_list_path, "r", encoding="utf-8") as mod_list_file:
        mod_list_string = mod_list_file.read()
        mod_list_dictionary = json.loads(mod_list_string)

        for mod_category in mod_list_dictionary:
            if mod_list_dictionary[mod_category]:
                print(f"\n[{Colors.YELLOW}{mod_category.upper()}{Colors.RESET}]")

                for mod in mod_list_dictionary[mod_category]:
                    log_message_info(
                        f"Found mod '{Colors.BLUE}{mod['name']}{Colors.RESET}' in latest list."
                    )

                    match mod_category:
                        case "client":
                            mod_dictionary_list_append(mods["client"], mod)
                        case "core":
                            mod_dictionary_list_append(mods["core"], mod)
                        case "server":
                            mod_dictionary_list_append(mods["server"], mod)
                        case _:
                            exit_error(f"Found unsupported mod category {mod_category}")

    return mod_list_dictionary


def index_query_subdirectories(index_directory) -> list[str]:
    index_subdirectories = []

    if os.path.exists(index_directory):
        index_subdirectories = os.listdir(index_directory)
    else:
        exit_error(
            f"Could not find Modrinth index file directory: `{Colors.YELLOW}{index_directory}{Colors.RESET}`"
        )

    return index_subdirectories


def mod_dictionary_list_append(dictionary_list: list[str], mod_dictionary: dict):
    """
    Append a mod's filename to a list.
    """

    dictionary_list.append(mod_dictionary["filename"])

    return dictionary_list


def mod_download_and_verify(
    mod_url: str,
    mod_download_desination_path: str,
    index_file_dictionary: dict,
    mod_dictionary: dict,
):
    """
    Download a mod using a Requests stream, and verify its contents using a
    SHA512 hash.
    """

    with requests.get(mod_url, stream=True, timeout=5) as mod_request:
        with open(mod_download_desination_path, "wb") as mod_file_stream:
            shutil.copyfileobj(mod_request.raw, mod_file_stream)

    with open(mod_download_desination_path, "rb") as mod_file:
        mod_file_hash = hashlib.sha512(mod_file.read()).hexdigest()

    mod_file_hash_expected = index_file_dictionary["download"]["hash"]

    if mod_file_hash == mod_file_hash_expected:
        log_message_info(
            f"[ {Colors.YELLOW}⧗{Colors.RESET} ] Downloaded mod '{Colors.BLUE}{mod_dictionary["name"]}{Colors.RESET}'"
        )
    else:
        exit_error(
            f"Hash mismatch for mod {mod_dictionary['name']}.\n:: Got: {mod_file_hash}\n ::Expected: {mod_file_hash_expected}"
        )


def mods_update(
    mod_list_dictionary: dict,
    temp_directory_path: str,
    index_directory: str,
    client_directory_path: str,
    server_directory_path: str,
):
    mods_local_current: list = []
    mods_latest: list = []
    mods_latest_files: list = []

    for mod_category in mod_list_dictionary:
        match mod_category:
            case "client":
                installation_target = client_directory_path
            case "server":
                installation_target = server_directory_path
            case _:
                continue

        if not installation_target:
            continue

        mods_latest: list = (
            mod_list_dictionary["core"] + mod_list_dictionary[mod_category]
        )

        mods_local_current = os.listdir(installation_target)

        for mod in mods_latest:
            mods_latest_files.append(mod["filename"])

            if not mod["filename"] in mods_latest_files:
                log_message_info(
                    f"Mod '{Colors.BLUE}{mod['filename']}{Colors.RESET}' not in '{mod_category}', skipping."
                )

                continue

            if not mod["filename"] in mods_local_current:
                log_message_info(
                    f"[ {Colors.YELLOW}⧗{Colors.RESET} ] Installing mod '{Colors.BLUE}{mod["name"]}{Colors.RESET}'"
                )

                with open(
                    f"{index_directory}/{mod["index"]}", "r", encoding="utf-8"
                ) as index_file_data:
                    index_file_string = index_file_data.read()

                    _index_file_dictionary = tomllib.loads(index_file_string)

                    _mod_url = _index_file_dictionary["download"]["url"]

                    _mod_download_destination_path = (
                        f"{temp_directory_path}/{_index_file_dictionary['filename']}"
                    )

                    mod_download_and_verify(
                        _mod_url,
                        _mod_download_destination_path,
                        _index_file_dictionary,
                        mod,
                    )

                    log_message_info(f"Moving {_mod_download_destination_path} to {installation_target}/{_index_file_dictionary['filename']}")

                    shutil.move(
                        _mod_download_destination_path,
                        f"{installation_target}/{_index_file_dictionary['filename']}",
                    )

                    log_message_info(
                        f"[ {Colors.GREEN}✔{Colors.RESET} ] Installed mod '{Colors.BLUE}{mod["name"]}{Colors.RESET}'."
                    )
            else:
                log_message_info(
                    f"[ {Colors.GREEN}✔{Colors.RESET} ] Mod '{Colors.BLUE}{mod["name"]}{Colors.RESET}' already installed and up to date."
                )

        for mod_local in mods_local_current:
            if not mod_local in mods_latest_files:
                if os.path.isfile(f"{installation_target}/{mod_local}"):
                    log_message_info(f"Deleting file {mod_local}")

                    os.remove(f"{installation_target}/{mod_local}")
