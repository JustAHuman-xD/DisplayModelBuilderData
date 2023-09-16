import json
import os

new_materials = []
parent_files = {}
files_to_save = set()
files_to_remove = set()

current_directory = os.getcwd()
models_directory = os.path.join(current_directory, "data/models")
parents_directory = os.path.join(current_directory, "data/parents")
textures_directory = os.path.join(current_directory, "data/textures")

def processModel(file_path, process_set, generate):
    process_set.add(file_path)

    json_file = None

    with open(file_path, "r") as file:
        json_file = json.load(file)

        if (not "textures" in json_file):
            return

        textures = json_file["textures"]
        new_textures = {}
        
        for key in textures:
            path = textures[key]

            # If this doesn't happen I'm confused but then I don't have the file anyways so we just continue
            if (not path.startswith("minecraft:block/")):
                continue

            texture = path[16:] + ".png"
            texture_path = os.path.join(textures_directory, texture)
            new_textures[key] = texture
            process_set.add(texture_path)

            if (generate):
                material_key = file_path[file_path.find("models\\") + 7:file_path.find(".json")]

                if (not material_key in new_materials):
                    new_materials.append(material_key)

        json_file["textures"] = new_textures

    with open(file_path, "w") as file:
        file.write(json.dumps(json_file, indent=4))

def check_parent(json_file):
    parent = json_file["parent"]

    if (parent.startswith("minecraft:block/cube")):
        return True
    return 
            
def generate_materials():
    # We need the models directory, create it if it doesn't exist
    if (not os.path.isdir(models_directory)):
        # If there is some file there remove it
        if (os.path.exists(models_directory)):
            os.remove(models_directory)

        # Creates The Directory
        os.mkdir(models_directory)

    # The same as above but for textures
    if (not os.path.isdir(textures_directory)):
        if (os.path.exists(textures_directory)):
            os.remove(textures_directory)

        os.mkdir(textures_directory)

    # Time to start actually making materials.json :D
    # The steps to this are pretty simple, go through all of the models provided, read the json file and check if its a cube model, if it aint, throw it and all relevant textures away
    for file_name in os.listdir(models_directory):

        file_path = os.path.join(models_directory, file_name)

        if (not os.path.isfile(file_path)):
            files_to_remove.add(file_path)
            continue

        json_file = None

        with open(file_path, "r") as file:
            json_file = json.load(file)

            if (not "parent" in json_file):
                processModel(file_path, files_to_remove, False)
                continue

            parent = json_file["parent"]

            if (not check_parent(json_file)):
                processModel(file_path, files_to_remove, False)
                continue

            parent_path = parent[16:] + ".json"
            parent_files[os.path.join(models_directory, parent_path)] = os.path.join(parents_directory, parent_path)
            files_to_save.add(parent_path)

            json_file["parent"] = parent_path
        
        with open(file_path, "w") as file:
            file.write(json.dumps(json_file, indent=4))

        processModel(file_path, files_to_save, True)

    # Handle any special cases
    with open("data/special_cases.json", "r") as file:
        special_cases = json.load(file)
        remappings = special_cases["remappings"]
        removals = special_cases["removals"]

        # Handle Remappings
        for old_key in remappings:
            if (not old_key in new_materials):
                continue

            new_key = remappings[old_key]
            new_materials[new_key] = new_materials[old_key]
            new_materials.pop(old_key)

            if (old_key in files_to_save):
                files_to_save.remove(old_key)
                files_to_save.add(new_key)

            if (old_key in files_to_remove):
                files_to_remove.remove(old_key)
                files_to_remove.add(new_key)

            old_path = os.path.join(models_directory, old_key + ".json")
            new_path = os.path.join(models_directory, new_key + ".json")
            if (os.path.exists(old_path) and not os.path.exists(new_path)):
                os.rename(old_path, new_path)

        # Handle Removals
        for key in removals:
            if (not key in new_materials):
                continue

            new_materials.pop(key)

            if (key in files_to_save):
                files_to_save.remove(key)

            if (key in files_to_remove):
                files_to_remove.remove(key)
            
            file_path = os.path.join(models_directory, key + ".json")
            if (os.path.exists(file_path)):
                os.remove(file_path)

    # Move parent fiiles
    for old_path in parent_files:
        new_path = parent_files[old_path]
        if (os.path.exists(old_path) and not os.path.exists(new_path)):
            os.rename(old_path, new_path)

    # Remove those not marked to save
    for path in files_to_remove:
        if (path in files_to_save):
            continue

        if (os.path.exists(path)):
            os.remove(path)

    # Remove any unused textures
    for file_name in os.listdir(textures_directory):
        file_path = os.path.join(textures_directory, file_name)

        if (not file_path in files_to_save and os.path.exists(file_path)):
            os.remove(file_path)
    
    # Actually write to materials.json
    with open("data/materials.json", "w") as file:
        file.write(json.dumps(new_materials, indent=4))


generate_materials()