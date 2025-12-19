#!/usr/bin/env python3

"""
The command-line for the Cobblemon Emergence launcher. This file serves as its
entrypoint, and should not be imported for use as a library.
"""

import argparse
import os
import sys

# Only doing this because it's not an conventionally distributed module.
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f"{script_directory}/../")

from cmecore import *

if __name__ == "__main__":
    # To do: Ensure there are other search paths for the index files.

    INDEX_DIRECTORY_PATH = path_to_posix(f"{script_directory}/../../data/index")
    DATA_PATH = f"{script_directory}/../../data"
    CONFIG_PATH = f"{DATA_PATH}/launcher.json"
    MOD_LIST_PATH = f"{DATA_PATH}/mods.json"
    TEMP_DIRECTORY_WIN32 = path_to_posix(f"{Path.home()}/AppData/Local/Temp")
    TEMP_DIRECTORY_UNIX = "/var/tmp"  # Hopefully compatible enough.

    _temp_directory_path: str = ""

    _mods: dict = {"client": [], "core": [], "server": []}

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

    # To do: Check if the temp directory has appropriate read/write mode.

    _mod_list_dictionary = mod_list_read(MOD_LIST_PATH, _mods)

    _free_space = free_space_query()
    _free_space_requirement = free_space_query_required(CONFIG_PATH)
    free_space_validate(_free_space, _free_space_requirement)

    _temp_directory_path = temp_directory_path_query(
        TEMP_DIRECTORY_WIN32, TEMP_DIRECTORY_UNIX
    )

    mods_update(
        _mod_list_dictionary,
        _temp_directory_path,
        INDEX_DIRECTORY,
        arguments.client,
        arguments.server,
    )
