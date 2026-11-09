@tool
extends Node3D
const Corrective = preload("shoulder_corrective.gd")
const NormalShader = preload("shoulder_normals.gdshader")
const HairCurls = preload("hair_curls.gd")

func _ready() -> void:
    _configure(self)

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
                material.set_shader_parameter("albedo_texture", original.albedo_texture)
                node.set_surface_override_material(surface, material)
    for child in node.get_children():
        _configure(child)
