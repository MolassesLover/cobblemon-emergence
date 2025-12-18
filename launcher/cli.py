#!/usr/bin/env python3

"""
The command-line for the Cobblemon Emergence launcher. This file serves as its
entrypoint, and should not be imported for use as a library.
"""

import argparse
import os
import tomllib
import sys
import shutil
import json
import hashlib

from pathlib import PureWindowsPath, Path
from dataclasses import dataclass

import requests


@dataclass
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


# https://stackoverflow.com/a/75292055
def path_to_posix(path):
    """
    Returns a path formatted to follow Unix conventions.
    """

    return PureWindowsPath(
        os.path.normpath(PureWindowsPath(path).as_posix())
    ).as_posix()


def query_free_space() -> float:
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


def mod_dictionary_list_append(dictionary_list: list[str], mod_dictionary: dict):
    dictionary_list.append(mod["filename"])

    return dictionary_list


if __name__ == "__main__":
    # Get the current script directory in order to obtain the index files.
    # To do: Ensure there are other search paths for the index files.
    script_directory = os.path.dirname(os.path.realpath(__file__))

    free_space_requirement: float = 0.5  # This value is replaced by the config file.
    free_space = query_free_space()
    index_files = None

    INDEX_DIRECTORY = path_to_posix(f"{script_directory}/../data/index")
    DATA_PATH = f"{script_directory}/../data"
    CONFIG_PATH = path_to_posix(f"{DATA_PATH}/launcher.json")
    MOD_LIST_PATH = path_to_posix(f"{DATA_PATH}/mods.json")
    TEMP_DIRECTORY_WIN32 = path_to_posix(f"{Path.home()}/AppData/Local/Temp")
    TEMP_DIRECTORY_UNIX = path_to_posix("/var/tmp")  # Hopefully compatible enough.

    mods_local_current: list = []
    installation_target_directories: list = []

    mods: dict = {"client": [], "core": [], "server": []}

    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("-c", "--client", help="The client mod directory.")
    argument_parser.add_argument("-s", "--server", help="The server mod directory.")

    argument_group_actions = argument_parser.add_mutually_exclusive_group(required=True)

    argument_group_actions.add_argument(
        "-u",
        "--update",
        help="Update mod files; download new files, delete old ones.",
        action="store_true",
    )
    argument_group_actions.add_argument(
        "-x", "--check", help="Check for updates to the modpack.", action="store_true"
    )

    arguments = argument_parser.parse_args()

    if not arguments.client and not arguments.server:
        argument_parser.print_help()
        exit_error(
            "At least one of either the client or server mod directory must be specified."
        )

    if arguments.client:
        installation_target_directories.append(arguments.client)
    if arguments.server:
        installation_target_directories.append(arguments.server)

    for installation_target in installation_target_directories:
        for local_mod_path in os.listdir(installation_target):
            if os.path.isfile(f"{installation_target}/{local_mod_path}"):
                mods_local_current.append(local_mod_path)

    # To do: Check if the temp directory has appropriate read/write mode.

    with open(MOD_LIST_PATH, "r", encoding="utf-8") as mod_list_file:
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

    print()

    # Open the config file, get the modpack size.
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_file_string = config_file.read()
        config_file_dictionary = json.loads(config_file_string)

        free_space_requirement = config_file_dictionary["modpack_size_gb"]

    if free_space < free_space_requirement:
        exit_error(
            f"Insufficient storage on device, expected at least {free_space_requirement} gb"
        )

    if os.path.exists(INDEX_DIRECTORY):
        index_subdirectories = os.listdir(INDEX_DIRECTORY)
    else:
        exit_error(
            f"Could not find Modrinth index file directory: `{Colors.YELLOW}{INDEX_DIRECTORY}{Colors.RESET}`"
        )

    temp_directory_path: str = ""

    # Make Windows use the right temp directory, and have a few sanity checks to ensure compatibility.
    match sys.platform:
        case "win32":
            temp_directory_path = temp_environment_setup(TEMP_DIRECTORY_WIN32)
        case "linux":
            temp_directory_path = temp_environment_setup(TEMP_DIRECTORY_UNIX)
        case "freebsd":
            temp_directory_path = temp_environment_setup(TEMP_DIRECTORY_UNIX)
        case "darwin":
            temp_directory_path = temp_environment_setup(TEMP_DIRECTORY_UNIX)
        case _:
            exit_error(
                "Unsupported platform, can't create the temp directory for cache."
            )

    mods_latest: list = []
    mods_latest_files: list = []

    if arguments.client:
        mods_latest: list = mod_list_dictionary["core"] + mod_list_dictionary["client"]
    elif arguments.server:
        mods_latest: list = mod_list_dictionary["core"] + mod_list_dictionary["server"]
    else:
        exit_error("Unknown mod installation target.")

    for mod in mods_latest:
        mods_latest_files.append(mod["filename"])

        if not mod["filename"] in mods_local_current:
            log_message_info(
                f"[ {Colors.YELLOW}⧗{Colors.RESET} ] Installing mod '{Colors.BLUE}{mod["name"]}{Colors.RESET}'"
            )

            with open(
                f"{INDEX_DIRECTORY}/{mod["index"]}", "r", encoding="utf-8"
            ) as index_file_data:
                index_file_string = index_file_data.read()

                index_file_dictionary = tomllib.loads(index_file_string)

                mod_url = index_file_dictionary["download"]["url"]

                mod_download_destination_path = (
                    f"{temp_directory_path}/{index_file_dictionary['filename']}"
                )

                print(mod_download_destination_path)

                with requests.get(mod_url, stream=True) as mod_request:
                    with open(mod_download_destination_path, "wb") as mod_file_stream:
                        shutil.copyfileobj(mod_request.raw, mod_file_stream)

                with open(mod_download_destination_path, "rb") as mod_file:
                    mod_file_hash = hashlib.sha512(mod_file.read()).hexdigest()
                    print(mod_file_hash)

                mod_file_hash_expected = index_file_dictionary["download"]["hash"]

                if mod_file_hash == mod_file_hash_expected:
                    log_message_info(
                        f"[ {Colors.GREEN}✔{Colors.RESET} ] Installed mod '{Colors.BLUE}{mod["name"]}{Colors.RESET}'"
                    )
                else:
                    exit_error(
                        f"Hash mismatch for mod {mod['name']}.\n:: Got: {mod_file_hash}\n ::Expected: {mod_file_hash_expected}"
                    )

                mods_downloaded.append(mod["filename"])

                log_message_info("Moving mod into installation directory.")

                shutil.move(
                    mod_download_destination_path,
                    f"{installation_target}/{index_file_dictionary['filename']}",
                )
        else:
            log_message_info(f"[ {Colors.GREEN}✔{Colors.RESET} ] Mod '{Colors.BLUE}{mod["name"]}{Colors.RESET}' already installed and up to date.")

    for mod_local in mods_local_current:
        if not mod_local in mods_latest_files:
            log_message_info(f"Deleting file {mod_local}")                

            os.remove(f"{installation_target}/{mod_local}")