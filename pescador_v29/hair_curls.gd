@tool
extends Node
## Volume de cachos do cabelo, preso ao osso "head" por BoneAttachment3D.
## Nao altera a malha do GLB nem os pesos: apenas acrescenta blocos de cabelo
## na nuca, nas laterais e sob a aba do chapeu, seguindo a cabeca nas animacoes.

const CURL_COUNT := 64
const SEED := 20260907

static func attach(skeleton: Skeleton3D) -> void:
    if skeleton == null or skeleton.find_bone("head") < 0:
        return
    if skeleton.get_node_or_null("HairCurls") != null:
        return
    var attachment := BoneAttachment3D.new()
    attachment.name = "HairCurls"
    attachment.bone_name = "head"
    skeleton.add_child(attachment)
    var rng := RandomNumberGenerator.new()
    rng.seed = SEED
    var mat := StandardMaterial3D.new()
    mat.albedo_color = Color(0.075, 0.058, 0.05)
    mat.roughness = 0.95
    var mesh := SphereMesh.new()
    mesh.radial_segments = 6
    mesh.rings = 4
    mesh.radius = 0.5
    mesh.height = 1.0
    mesh.material = mat
    var placed := 0
    while placed < CURL_COUNT:
        var angle := rng.randf() * TAU
        var ring := 0.092 + rng.randf() * 0.016
        var pos := Vector3(cos(angle) * ring, rng.randf_range(0.03, 0.12), sin(angle) * ring)
        # Mantem o rosto livre: nada na frente do rosto, abaixo da aba do chapeu.
        if pos.z > 0.02 and absf(pos.x) < 0.1:
            continue
        var curl := MeshInstance3D.new()
        curl.mesh = mesh
        var s := rng.randf_range(0.018, 0.026)
        curl.scale = Vector3(s, s * rng.randf_range(0.8, 1.2), s)
        curl.position = pos
        curl.rotation = Vector3(rng.randf() * TAU, rng.randf() * TAU, rng.randf() * TAU)
        attachment.add_child(curl)
        placed += 1
