import argparse
import os
import re
import sys
import unreal

PROP_ALBEDO = "Albedo"
PROP_AO = "AO"
PROP_DISPLACEMENT = "Displacement"
PROP_NORMAL = "Normal"
PROP_ROUGHNESS = "Roughness"
PROP_SPECULAR = "Specular"

NODE_POS_X = -360

FILE_TYPES = [
    "_" + PROP_ALBEDO + ".jpg",
    "_" + PROP_AO + ".jpg",
    "_" + PROP_DISPLACEMENT + ".jpg",
    "_" + PROP_NORMAL + ".jpg",
    "_" + PROP_ROUGHNESS + ".jpg",
    "_" + PROP_SPECULAR + ".jpg",
]

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="the path of input folder")
    parser.add_argument("-o", "--output", type=str, help="the name of destination asset folder")
    parser.add_argument("-f", "--filter", type=str, default=None, help="filter string for selection target folder (REGEX)")

    print "arguments:"
    print args
    return parser.parse_args(args)

def get_asset_path(output, dir):
    return "/Game/" + output + "/" + dir

def get_material_property(texture_name):
    if "_" + PROP_ALBEDO + "_" in texture_name:
        return unreal.MaterialProperty.MP_BASE_COLOR
    elif "_" + PROP_AO + "_" in texture_name:
        return unreal.MaterialProperty.MP_AMBIENT_OCCLUSION
    # TODO: DISPLACEMENT のプロパティがない？
    # elif "_" + PROP_DISPLACEMENT + "_" in texture_name:
    #     return unreal.MaterialProperty.MP_WORLD_DISPLACEMENT
    elif "_" + PROP_NORMAL + "_" in texture_name:
        return unreal.MaterialProperty.MP_NORMAL
    elif "_" + PROP_ROUGHNESS + "_" in texture_name:
        return unreal.MaterialProperty.MP_ROUGHNESS
    elif "_" + PROP_SPECULAR + "_" in texture_name:
        return unreal.MaterialProperty.MP_SPECULAR
    else:
        return None

def get_target_directories(input_path, filter=None):
    files = os.listdir(input_path)
    if filter is not None:
        regex = re.compile(filter)
        files = [f for f in files if regex.match(f) is not None]
    files_dir = [f for f in files if os.path.isdir(os.path.join(input_path, f))]
    return files_dir

def get_node_y_pos(property):
    Y_LEN = 240
    if property == unreal.MaterialProperty.MP_BASE_COLOR:
        return Y_LEN * (-2)
    elif property == unreal.MaterialProperty.MP_METALLIC:
        return Y_LEN * (-1)
    elif property == unreal.MaterialProperty.MP_SPECULAR:
        return Y_LEN * (0)
    elif property == unreal.MaterialProperty.MP_ROUGHNESS:
        return Y_LEN * (1)
    elif property == unreal.MaterialProperty.MP_NORMAL:
        return Y_LEN * (2)
    elif property == unreal.MaterialProperty.MP_AMBIENT_OCCLUSION:
        return Y_LEN * (3)
    # TODO: DISPLACEMENT のプロパティがない？
    # elif "_" + PROP_DISPLACEMENT + "_" in texture_name:
    #     return unreal.MaterialProperty.MP_WORLD_DISPLACEMENT
    else:
        return 0

def import_textures(input_path, dir, output):
    def contains(file_name):
        for x in FILE_TYPES:
            if x in file_name:
                return True
        return False

    files = os.listdir(os.path.join(input_path, dir))
    files = [f for f in files if contains(f)]

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    tasks = []
    for f in files:
        task = unreal.AssetImportTask()
        task.automated = True
        task.destination_name = "T_" + f
        task.destination_path = get_asset_path(output, dir)
        task.filename = os.path.join(input_path, dir, f)
        tasks.append(task)
    asset_tools.import_asset_tasks(tasks)

def add_material_expression(material, texture_name):
    class_name = unreal.MaterialExpressionTextureSample
    property = get_material_property(texture_name)
    if property is None:
        print "add_material_expression(): MaterialProperty not found."
        return
    exp = unreal.MaterialEditingLibrary.create_material_expression(material, class_name, NODE_POS_X, get_node_y_pos(property))
    exp.texture = unreal.EditorAssetLibrary.load_asset(texture_name)
    # Normal の場合は sampler_type の変更が必要
    if property == unreal.MaterialProperty.MP_NORMAL:
        exp.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    unreal.MaterialEditingLibrary.connect_material_property(exp, "RGB", property)

def create_material(dir, output):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    path = get_asset_path(output, dir)
    tex_names = unreal.EditorAssetLibrary.list_assets(path)
    
    material = asset_tools.create_asset("M_" + dir, path, unreal.Material, None)
    for tex in tex_names:
        add_material_expression(material, tex)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    input_dirs = get_target_directories(args.input, args.filter)
    
    for d in input_dirs:
        import_textures(args.input, d, args.output)
        create_material(d, args.output)