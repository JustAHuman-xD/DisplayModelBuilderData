import json
import os

new_materials = {}
parent_files = {}
files_to_save = set()
files_to_remove = set()

current_directory = os.getcwd()
models_directory = os.path.join(current_directory, "data/models")
parents_directory = os.path.join(current_directory, "data/parents")
textures_directory = os.path.join(current_directory, "data/textures")

def processModel(filepath, process_set, generate):
    process_set.add(filepath)

    with open(filepath, "r") as file:
        jsonFile = json.load(file)

        if (not "textures" in jsonFile):
            return

        textures = jsonFile["textures"]
        
        #print("textures: " + str(textures))
        for key in textures:
            path = textures[key]

            # If this doesn't happen I'm confused but then I don't have the file anyways so we just continue
            if (not path.startswith("minecraft:block/")):
                continue

            texture = path[16:] + ".png"
            texturePath = os.path.join(textures_directory, texture)
            process_set.add(texturePath)

            if (generate):
                material_key = filepath[filepath.find("models\\") + 7:filepath.find(".json")]
                material_textures = list()

                if (material_key in new_materials):
                    material_textures = new_materials[material_key]
                
                material_textures.append("data/textures/" +texture)
                new_materials[material_key] = material_textures
            
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
    for filename in os.listdir(models_directory):

        filepath = os.path.join(models_directory, filename)

        if (not os.path.isfile(filepath)):
            files_to_remove.add(filepath)
            continue

        with open(filepath, "r") as file:
            jsonFile = json.load(file)

            if (not "parent" in jsonFile):
                processModel(filepath, files_to_remove, False)
                continue

            parent = jsonFile["parent"]

            if (not parent.startswith("minecraft:block/cube")):
                processModel(filepath, files_to_remove, False)
                continue

            parent_path = parent[16:] + ".json"
            parent_files[os.path.join(models_directory, parent_path)] = os.path.join(parents_directory, parent_path)
            files_to_save.add(parent_path)

        processModel(filepath, files_to_save, True)

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
            
            filepath = os.path.join(models_directory, key + ".json")
            if (os.path.exists(filepath)):
                os.remove(filepath)

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
    for filename in os.listdir(textures_directory):
        filepath = os.path.join(textures_directory, filename)

        if (not filepath in files_to_save and os.path.exists(filepath)):
            os.remove(filepath)
    
    # Actually write to materials.json
    with open("data/materials.json", "w") as file:
        file.write(json.dumps(new_materials, indent=4))


generate_materials()