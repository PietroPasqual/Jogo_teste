@tool
extends Node3D
const Corrective = preload("shoulder_corrective.gd")
const NormalShader = preload("shoulder_normals.gdshader")
const HairCurls = preload("hair_curls.gd")
## Textura da roupa com contraste e nitidez ajustados para o camuflado da referencia.
const CLOTH_TEXTURE_PATH := "res://pescador_v29/pescador_v29_Roupa_ajustada.png"
const PantsShader = preload("pants_darken.gdshader")

var _cloth_texture: Texture2D = null

func _ready() -> void:
    _cloth_texture = _load_cloth_texture()
    _configure(self)

func _load_cloth_texture() -> Texture2D:
    var image := Image.load_from_file(CLOTH_TEXTURE_PATH)
    if image == null:
        return null
    return ImageTexture.create_from_image(image)

func _configure(node: Node) -> void:
    if node is Skeleton3D and node.get_node_or_null("ShoulderCorrective") == null:
        var modifier = Corrective.new()
        modifier.name = "ShoulderCorrective"
        node.add_child(modifier)
    if node is Skeleton3D:
        HairCurls.attach(node)
    if node is MeshInstance3D and node.mesh != null:
        for surface in range(node.mesh.get_surface_count()):
            var original: Material = node.mesh.surface_get_material(surface)
            if original is StandardMaterial3D and original.resource_name.begins_with("ShoulderCloth"):
                var material := ShaderMaterial.new()
                material.shader = NormalShader
                material.set_shader_parameter("albedo_texture", _cloth_or(original.albedo_texture))
                node.set_surface_override_material(surface, material)
            elif original is StandardMaterial3D and original.resource_name == "Lentes fumê":
                var lens := original.duplicate() as StandardMaterial3D
                lens.albedo_texture = null
                lens.albedo_color = Color(0.03, 0.03, 0.035)
                lens.roughness = 0.12
                lens.metallic_specular = 0.8
                node.set_surface_override_material(surface, lens)
            elif original is StandardMaterial3D and original.resource_name == "Pescador":
                var body := ShaderMaterial.new()
                body.shader = PantsShader
                body.set_shader_parameter("albedo_texture", _cloth_or(original.albedo_texture))
                node.set_surface_override_material(surface, body)
    for child in node.get_children():
        _configure(child)

func _cloth_or(fallback: Texture2D) -> Texture2D:
    return _cloth_texture if _cloth_texture != null else fallback
