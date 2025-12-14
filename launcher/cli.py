#!/usr/bin/env python3

"""
The command-line for the Cobblemon Emergence launcher. This file serves as its
entrypoint, and should not be imported for use as a library.
"""

import os
import tomllib
import sys
import shutil
import json

from pathlib import PureWindowsPath, Path
from dataclasses import dataclass


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


def temp_environment_setup(temp_directory: str):
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

    os.makedirs(f"{temp_directory}/molasses.love/cobblemon-emergence", exist_ok=True)


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

    # To do: Check if the temp directory has appropriate read/write mode.

    with open(MOD_LIST_PATH, 'r', encoding='utf-8') as mod_list_file:
        mod_list_string = mod_list_file.read()
        mod_list_dictionary = json.loads(mod_list_string)

        for mod in mod_list_dictionary:
            print(mod["filename"])

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
        index_files = os.listdir(INDEX_DIRECTORY)
    else:
        exit_error(
            f"Could not find Modrinth index file directory: `{Colors.YELLOW}{INDEX_DIRECTORY}{Colors.RESET}`"
        )

    # Make Windows use the right temp directory, and have a few sanity checks to ensure compatibility.
    match sys.platform:
        case "win32":
            temp_environment_setup(TEMP_DIRECTORY_WIN32)
        case "linux":
            temp_environment_setup(TEMP_DIRECTORY_UNIX)
        case "freebsd":
            temp_environment_setup(TEMP_DIRECTORY_UNIX)
        case "darwin":
            temp_environment_setup(TEMP_DIRECTORY_UNIX)
        case _:
            exit_error(
                "Unsupported platform, can't create the temp directory for cache."
            )

    # Iterate through all the index files, read their data into a dictionary, and update the modpack.
    if index_files:
        for index_file in index_files:
            index_file_path = path_to_posix(f"{INDEX_DIRECTORY}/{index_file}")

            log_message_info(
                f"Reading: `{Colors.GREEN}{os.path.basename(index_file_path)}{Colors.RESET}`"
            )

            with open(index_file_path, "r", encoding="utf-8") as index_file_data:
                index_file_string = index_file_data.read()

                index_file_dictionary = tomllib.loads(index_file_string)

                print(
                    f":: Checking: '{Colors.BLUE}{index_file_dictionary['name']}{Colors.RESET}'"
                )

                # To do:
                # - Check if the modpack has changed since the last update.
                # - Download missing files.
                # - Remove old files.
    else:
        exit_error("No index files listed. Is the index directory empty?")
