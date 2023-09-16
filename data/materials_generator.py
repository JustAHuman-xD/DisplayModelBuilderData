import json
import os

new_materials = []
parent_files = {}
files_to_save = set()
files_to_remove = set()

models_directory = "data/models/"
parents_directory = "data/parents/"
textures_directory = "data/textures/"

def processModel(file_path, process_set, add_to_materials):
    if (file_path in parent_files):
        return
    
    process_set.add(file_path)

    if add_to_materials:
        material_key = file_path[file_path.rfind("/") + 1:file_path.rfind(".json")]

        if (not material_key in new_materials):
            new_materials.append(material_key)

def check_parent(json_file):
    if (not "parent" in json_file):
        return False

    parent = json_file["parent"]
    parent_path = models_directory + parent[parent.rfind("/") + 1:] + ".json"

    if (parent_path in parent_files or parent.find("block/cube") != -1):
        return True
    
    if (parent == ("block/block")):
        return False
    
    with open(parent_path, "r") as parent_file:
        return check_parent(json.load(parent_file))

            
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

    # The same as above but for parents
    if (not os.path.isdir(parents_directory)):
        if (os.path.exists(parents_directory)):
            os.remove(parents_directory)

        os.mkdir(parents_directory)

    # Time to start actually making materials.json :D
    # The steps to this are pretty simple, go through all of the models provided, read the json file and check if its a cube model, if it aint, throw it and all relevant textures away
    for file_name in os.listdir(models_directory):

        file_path = models_directory + file_name

        if (not os.path.isfile(file_path)):
            files_to_remove.add(file_path)
            continue

        with open(file_path, "r") as file:
            json_file = json.load(file)

            if (not "parent" in json_file):
                processModel(file_path, files_to_remove, False)
                continue

            parent = json_file["parent"]

            if (not check_parent(json_file)):
                processModel(file_path, files_to_remove, False)
                continue

            parent_path = parent[parent.rfind("/") + 1:] + ".json"
            parent_files[models_directory + parent_path] = parents_directory + parent_path
            files_to_save.add(models_directory + parent_path)

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
            new_materials.append(new_key)
            new_materials.remove(old_key)

            if (old_key in files_to_save):
                files_to_save.remove(old_key)
                files_to_save.add(new_key)

            if (old_key in files_to_remove):
                files_to_remove.remove(old_key)
                files_to_remove.add(new_key)

            old_path = models_directory + old_key + ".json"
            new_path = models_directory + new_key + ".json"

            if (os.path.exists(old_path)):
                if (os.path.exists(new_path)):
                    os.remove(new_path)
                os.rename(old_path, new_path)

        # Handle Removals
        for key in removals:
            if (not key in new_materials):
                continue

            new_materials.remove(key)

            model_key = models_directory + key + ".json"

            if (model_key in files_to_save):
                files_to_save.remove(model_key)

            if (model_key in files_to_remove):
                files_to_remove.remove(model_key)
            
            if (os.path.exists(model_key)):
                os.remove(model_key)

    # Remove those marked to remove
    for path in files_to_remove:
        if (path in files_to_save or path[path.rfind("/") + 1:path.rfind(".json")] in new_materials):
            continue

        if (os.path.exists(path)):
            os.remove(path)

    # Now that we've done all that, we can start to reformat the files, we will also keep track of what textures we actually need to save when doing this!
    textures_to_save = []
    for file_name in os.listdir(models_directory):

        file_path = models_directory + file_name
        json_file = None
        
        with open(file_path, "r") as file:
            json_file = json.load(file)

            if ("parent" in json_file):
                parent = json_file["parent"]
                json_file["parent"] = parent[parent.rfind("/") + 1:] + ".json"
            
            if ("textures" in json_file and not file_path in parent_files):
                textures = json_file["textures"]
                new_textures = {}

                for key in textures:
                    path = textures[key]
                    texture = path[path.rfind("/") + 1:] + ".png"
                    new_textures[key] = texture
                    textures_to_save.append(texture)
                
                json_file["textures"] = new_textures

        with open(file_path, "w") as file:
            file.write(json.dumps(json_file, indent=4))

    # Remove any unused textures
    for file_name in os.listdir(textures_directory):
        file_path = textures_directory + file_name

        if (not file_name in textures_to_save and os.path.exists(file_path)):
            os.remove(file_path)

    # Almost last we move the parent fiiles
    for old_path in parent_files:
        new_path = parent_files[old_path]
        if (os.path.exists(old_path) and not os.path.exists(new_path)):
            os.rename(old_path, new_path)
    
    # And finally actually write to materials.json
    with open("data/materials.json", "w") as file:
        file.write(json.dumps(new_materials, indent=4))

generate_materials()