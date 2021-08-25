import bpy
import os
from . import materials, nodeutils, imageutils, properties, params, utils, vars


def connect_tearline_material(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_character_cache(obj, mat)
    parameters = chr_cache.basic_parameters
    obj_cache = chr_cache.get_object_cache(obj)
    mat_cache = chr_cache.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader = nodeutils.reset_shader(nodes, links, "Tearline Shader", "basic_tearline", None)

    nodeutils.set_node_input(shader, "Base Color", (1.0, 1.0, 1.0, 1.0))
    nodeutils.set_node_input(shader, "Metallic", 1.0)
    nodeutils.set_node_input(shader, "Specular", 1.0)
    nodeutils.set_node_input(shader, "Roughness", parameters.tearline_roughness)
    nodeutils.set_node_input(shader, "Alpha", parameters.tearline_alpha)
    shader.name = utils.unique_name("eye_tearline_shader")
    materials.set_material_alpha(mat, props.blend_mode)
    mat.shadow_method = "NONE"


def connect_eye_occlusion_material(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_character_cache(obj, mat)
    parameters = chr_cache.basic_parameters
    obj_cache = chr_cache.get_object_cache(obj)
    mat_cache = chr_cache.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader = nodeutils.reset_shader(nodes, links, "Eye Occlusion Shader", "basic_eye_occlusion", None)

    shader.name = utils.unique_name("eye_occlusion_shader")
    nodeutils.set_node_input(shader, "Base Color", (0,0,0,1))
    nodeutils.set_node_input(shader, "Metallic", 0.0)
    nodeutils.set_node_input(shader, "Specular", 0.0)
    nodeutils.set_node_input(shader, "Roughness", 1.0)
    nodeutils.reset_cursor()

    # groups
    group = nodeutils.get_node_group("eye_occlusion_mask")
    occ_node = nodeutils.make_node_group_node(nodes, group, "Eye Occulsion Alpha", "eye_occlusion_mask")
    # values
    nodeutils.set_node_input(occ_node, "Strength", parameters.eye_occlusion)
    nodeutils.set_node_input(occ_node, "Hardness", parameters.eye_occlusion_power)
    # links
    nodeutils.link_nodes(links, occ_node, "Alpha", shader, "Alpha")

    materials.set_material_alpha(mat, props.blend_mode)
    mat.shadow_method = "NONE"


def connect_basic_eye_material(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_character_cache(obj, mat)
    parameters = chr_cache.basic_parameters
    obj_cache = chr_cache.get_object_cache(obj)
    mat_cache = chr_cache.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader = nodeutils.reset_shader(nodes, links, "Eye Shader", "basic_eye", None)

    # Base Color
    #
    nodeutils.reset_cursor()
    diffuse_image =  imageutils.find_material_image(mat, "DIFFUSE")
    if diffuse_image is not None:
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "(DIFFUSE)")
        nodeutils.advance_cursor(1.0)
        hsv_node = nodeutils.make_shader_node(nodes, "ShaderNodeHueSaturation", 0.6)
        hsv_node.label = "HSV"
        hsv_node.name = utils.unique_name("eye_basic_hsv")
        nodeutils.set_node_input(hsv_node, "Value", parameters.eye_brightness)
        # links
        nodeutils.link_nodes(links, diffuse_node, "Color", hsv_node, "Color")
        nodeutils.link_nodes(links, hsv_node, "Color", shader, "Base Color")

    # Metallic
    #
    nodeutils.reset_cursor()
    metallic_node = nodeutils.make_value_node(nodes, "Eye Metallic", "eye_metallic", 0.0)
    nodeutils.link_nodes(links, metallic_node, "Value", shader, "Metallic")

    # Specular
    #
    nodeutils.reset_cursor()
    specular_node = nodeutils.make_value_node(nodes, "Eye Specular", "eye_specular", parameters.eye_specular)
    nodeutils.link_nodes(links, specular_node, "Value", shader, "Specular")

    # Roughness
    #
    nodeutils.reset_cursor()
    roughness_node = nodeutils.make_value_node(nodes, "Eye Roughness", "eye_roughness", parameters.eye_roughness)
    nodeutils.link_nodes(links, roughness_node, "Value", shader, "Roughness")

    # Alpha
    #
    nodeutils.set_node_input(shader, "Alpha", 1.0)

    # Normal
    #
    nodeutils.reset_cursor()
    normal_image = imageutils.find_material_image(mat, "SCLERANORMAL")
    if normal_image is not None:
        strength_node = nodeutils.make_value_node(nodes, "Normal Strength", "eye_normal", parameters.eye_normal)
        normal_node = nodeutils.make_image_node(nodes, normal_image, "(SCLERANORMAL)")
        nodeutils.advance_cursor()
        normalmap_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        nodeutils.link_nodes(links, strength_node, "Value", normalmap_node, "Strength")
        nodeutils.link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        nodeutils.link_nodes(links, normalmap_node, "Normal", shader, "Normal")

    # Clearcoat
    #
    nodeutils.set_node_input(shader, "Clearcoat", 1.0)
    nodeutils.set_node_input(shader, "Clearcoat Roughness", 0.15)
    mat.use_screen_refraction = False

    return

def connect_basic_material(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_character_cache(obj, mat)
    parameters = chr_cache.basic_parameters
    obj_cache = chr_cache.get_object_cache(obj)
    mat_cache = chr_cache.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader = nodeutils.reset_shader(nodes, links, "Basic Shader", "basic", None)

    # Base Color
    #
    nodeutils.reset_cursor()
    diffuse_image = imageutils.find_material_image(mat, "DIFFUSE")
    ao_image = imageutils.find_material_image(mat, "AO")
    diffuse_node = ao_node = None
    if (diffuse_image is not None):
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "(DIFFUSE)")
        if ao_image is not None:

            if mat_cache.is_skin() or mat_cache.is_nails():
                prop = "skin_ao"
                ao_strength = parameters.skin_ao
            elif mat_cache.is_hair():
                prop = "hair_ao"
                ao_strength = parameters.hair_ao
            else:
                prop = "default_ao"
                ao_strength = parameters.default_ao

            fac_node = nodeutils.make_value_node(nodes, "Ambient Occlusion Strength", prop, ao_strength)
            ao_node = nodeutils.make_image_node(nodes, ao_image, "ao_tex")
            nodeutils.advance_cursor(1.5)
            nodeutils.drop_cursor(0.75)
            mix_node = nodeutils.make_mixrgb_node(nodes, "MULTIPLY")
            nodeutils.link_nodes(links, diffuse_node, "Color", mix_node, "Color1")
            nodeutils.link_nodes(links, ao_node, "Color", mix_node, "Color2")
            nodeutils.link_nodes(links, fac_node, "Value", mix_node, "Fac")
            nodeutils.link_nodes(links, mix_node, "Color", shader, "Base Color")
        else:
            nodeutils.link_nodes(links, diffuse_node, "Color", shader, "Base Color")

    # Metallic
    #
    nodeutils.reset_cursor()
    metallic_image = imageutils.find_material_image(mat, "METALLIC")
    metallic_node = None
    if metallic_image is not None:
        metallic_node = nodeutils.make_image_node(nodes, metallic_image, "(METALLIC)")
        nodeutils.link_nodes(links, metallic_node, "Color", shader, "Metallic")

    # Specular
    #
    nodeutils.reset_cursor()
    specular_image = imageutils.find_material_image(mat, "SPECULAR")
    mask_image = imageutils.find_material_image(mat, "SPECMASK")

    prop = "none"
    spec = 0.5
    if mat_cache.is_skin() or mat_cache.is_nails():
        prop = "skin_specular"
        spec = parameters.skin_specular
    elif mat_cache.is_hair():
        prop = "hair_specular"
        spec = parameters.hair_specular
    elif mat_cache.is_scalp() or mat_cache.is_eyelash():
        prop = "scalp_specular"
        spec = parameters.scalp_specular
    elif mat_cache.is_teeth():
        prop = "teeth_specular"
        roughness = parameters.teeth_specular
    elif mat_cache.is_tongue():
        prop = "tongue_specular"
        roughness = parameters.tongue_specular

    specular_node = mask_node = mult_node = None
    if specular_image is not None:
        specular_node = nodeutils.make_image_node(nodes, specular_image, "(SPECULAR)")
        nodeutils.link_nodes(links, specular_node, "Color", shader, "Specular")
    # always make a specular value node for skin or if there is a mask (but no map)
    elif prop != "none":
        specular_node = nodeutils.make_value_node(nodes, "Specular Strength", prop, spec)
        nodeutils.link_nodes(links, specular_node, "Value", shader, "Specular")
    if mask_image is not None:
        mask_node = nodeutils.make_image_node(nodes, mask_image, "(SPECMASK)")
        nodeutils.advance_cursor()
        mult_node = nodeutils.make_math_node(nodes, "MULTIPLY")
        if specular_node.type == "VALUE":
            nodeutils.link_nodes(links, specular_node, "Value", mult_node, 0)
        else:
            nodeutils.link_nodes(links, specular_node, "Color", mult_node, 0)
        nodeutils.link_nodes(links, mask_node, "Color", mult_node, 1)
        nodeutils.link_nodes(links, mult_node, "Value", shader, "Specular")

    # Roughness
    #
    nodeutils.reset_cursor()
    roughness_image = imageutils.find_material_image(mat, "ROUGHNESS")
    roughness_node = None
    if roughness_image is not None:
        roughness_node = nodeutils.make_image_node(nodes, roughness_image, "(ROUGHNESS)")

        if mat_cache.is_skin():
            prop = "skin_roughness"
            roughness = parameters.skin_roughness
        elif mat_cache.is_teeth():
            prop = "teeth_roughness"
            roughness = parameters.teeth_roughness
        elif mat_cache.is_tongue():
            prop = "tongue_roughness"
            roughness = parameters.tongue_roughness
        else:
            prop = "none"
            roughness = 1

        if mat_cache.material_type.startswith("SKIN"):
            nodeutils.advance_cursor()
            remap_node = nodeutils.make_shader_node(nodes, "ShaderNodeMapRange")
            remap_node.name = utils.unique_name(prop)
            nodeutils.set_node_input(remap_node, "To Min", roughness)
            nodeutils.link_nodes(links, roughness_node, "Color", remap_node, "Value")
            nodeutils.link_nodes(links, remap_node, "Result", shader, "Roughness")
        elif mat_cache.material_type.startswith("TEETH") or mat_cache.material_type == "TONGUE":
            nodeutils.advance_cursor()
            rmult_node = nodeutils.make_math_node(nodes, "MULTIPLY", 1, roughness)
            rmult_node.name = utils.unique_name(prop)
            nodeutils.link_nodes(links, roughness_node, "Color", rmult_node, 0)
            nodeutils.link_nodes(links, rmult_node, "Value", shader, "Roughness")
        else:
            nodeutils.link_nodes(links, roughness_node, "Color", shader, "Roughness")

    # Emission
    #
    nodeutils.reset_cursor()
    emission_image = imageutils.find_material_image(mat,"EMISSION")
    emission_node = None
    if emission_image is not None:
        emission_node = nodeutils.make_image_node(nodes, emission_image, "(EMISSION)")
        nodeutils.link_nodes(links, emission_node, "Color", shader, "Emission")

    # Alpha
    #
    nodeutils.reset_cursor()
    alpha_image = imageutils.find_material_image(mat, "ALPHA")
    alpha_node = None
    if alpha_image is not None:
        alpha_node = nodeutils.make_image_node(nodes, alpha_image, "(ALPHA)")
        dir,file = os.path.split(alpha_image.filepath)
        if "_diffuse" in file.lower() or "_albedo" in file.lower():
            nodeutils.link_nodes(links, alpha_node, "Alpha", shader, "Alpha")
        else:
            nodeutils.link_nodes(links, alpha_node, "Color", shader, "Alpha")
    elif diffuse_node:
        nodeutils.link_nodes(links, diffuse_node, "Alpha", shader, "Alpha")

    # material alpha blend settings
    if obj_cache.is_hair() or mat_cache.is_eyelash():
        materials.set_material_alpha(mat, "HASHED")
    elif shader.inputs["Alpha"].default_value < 1.0:
        materials.set_material_alpha(mat, props.blend_mode)
    else:
        materials.set_material_alpha(mat, "OPAQUE")

    # Normal
    #
    nodeutils.reset_cursor()
    normal_image = imageutils.find_material_image(mat, "NORMAL")
    bump_image = imageutils.find_material_image(mat,"BUMP")
    normal_node = bump_node = normalmap_node = bumpmap_node = None
    if normal_image is not None:
        normal_node = nodeutils.make_image_node(nodes, normal_image, "(NORMAL)")
        nodeutils.advance_cursor()
        normalmap_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        nodeutils.link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        nodeutils.link_nodes(links, normalmap_node, "Normal", shader, "Normal")
    if bump_image is not None:

        if mat_cache.is_hair() or mat_cache.is_eyelash() or mat_cache.is_scalp():
            prop = "hair_bump"
            bump_strength = parameters.hair_bump
        else:
            prop = "default_bump"
            bump_strength = parameters.default_bump

        bump_strength_node = nodeutils.make_value_node(nodes, "Bump Strength", prop, bump_strength / 1000)
        bump_node = nodeutils.make_image_node(nodes, bump_image, "(BUMP)")
        nodeutils.advance_cursor()
        bumpmap_node = nodeutils.make_shader_node(nodes, "ShaderNodeBump", 0.7)
        nodeutils.advance_cursor()
        nodeutils.link_nodes(links, bump_strength_node, "Value", bumpmap_node, "Distance")
        nodeutils.link_nodes(links, bump_node, "Color", bumpmap_node, "Height")
        if normal_image is not None:
            nodeutils.link_nodes(links, normalmap_node, "Normal", bumpmap_node, "Normal")
        nodeutils.link_nodes(links, bumpmap_node, "Normal", shader, "Normal")

    return


def update_basic_material(mat, cache, prop):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_character_cache(None, mat)
    parameters = chr_cache.basic_parameters
    scope = locals()

    if mat is not None and mat.node_tree is not None:

        nodes = mat.node_tree.nodes
        for node in nodes:

            for prop_info in params.BASIC_PROPS:

                prop_name = prop_info[3]
                prop_node = prop_info[2]
                if prop_node == "":
                    prop_node = prop_name

                if prop_node in node.name and (prop == "ALL" or prop == prop_name):
                    prop_dir = prop_info[0]
                    prop_socket = prop_info[1]

                    try:
                        if len(prop_info) == 5:
                            prop_eval = prop_info[4]
                        else:
                            prop_eval = "parameters." + prop_name

                        prop_value = eval(prop_eval, None, scope)

                        if prop_dir == "IN":
                            nodeutils.set_node_input(node, prop_socket, prop_value)
                        elif prop_dir == "OUT":
                            nodeutils.set_node_output(node, prop_socket, prop_value)
                    except Exception as e:
                        utils.log_error("update_basic_materials(): Unable to evaluate or set: " + prop_eval, e)