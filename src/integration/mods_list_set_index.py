import json
import tomllib
import os
import shutil

from pathlib import PureWindowsPath, Path

# Like the CLI, only doing this because it's not an conventionally distributed module.
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f"{script_directory}/../")


if __name__ == "__main__":
    script_directory = os.path.dirname(os.path.realpath(__file__))

    INDEX_DIRECTORY_PATH = path_to_posix(f"{script_directory}/../../data/index")
    DATA_PATH = f"{script_directory}/../../data"
    MOD_LIST_PATH = f"{DATA_PATH}/mods.json"

    mods_indexed: dict = {}

    if os.path.exists(INDEX_DIRECTORY_PATH):
        index_subdirectories = os.listdir(INDEX_DIRECTORY_PATH)

    with open(MOD_LIST_PATH, "r", encoding="utf-8") as mod_list_file:
        mod_list_string = mod_list_file.read()
        mod_list_dictionary = json.loads(mod_list_string)

    for index_subdirectory in index_subdirectories:
        for index_file in os.listdir(f"{INDEX_DIRECTORY_PATH}/{index_subdirectory}"):
            index_file_path = path_to_posix(
                f"{INDEX_DIRECTORY_PATH}/{index_subdirectory}/{index_file}"
            )

            with open(index_file_path, "r", encoding="utf-8") as index_file_data:
                index_file_string = index_file_data.read()

                index_file_dictionary = tomllib.loads(index_file_string)

                mods_indexed.update(
                    {index_file_dictionary["filename"]: index_file_path}
                )

    # To do: Replace this with a common function that yields the mods.
    for mod_category in mod_list_dictionary:
        if mod_list_dictionary[mod_category]:
            for mod in mod_list_dictionary[mod_category]:
                mod_path = (
                    f"{mod_category}/{os.path.basename(mods_indexed[mod['filename']])}"
                )

                mod.update({"index": mod_path})

    if os.path.isfile(MOD_LIST_PATH):
        shutil.copyfile(MOD_LIST_PATH, f"{MOD_LIST_PATH}.bak")
        mod_list_string = json.dumps(mod_list_dictionary, indent=4)

        with open(MOD_LIST_PATH, "w", encoding="utf-8") as mod_list_file:
            mod_list_file.write(mod_list_string)
