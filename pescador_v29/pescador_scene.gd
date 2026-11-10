@tool
extends Node3D
## Configura o Pescador para ficar fiel a folha de referencia, sem alterar o GLB:
## corretivo dos ombros, cabelo cacheado, camuflado ajustado, calca escura,
## lentes escuras e uma animacao de repouso com as maos semifechadas.

const Corrective = preload("shoulder_corrective.gd")
const NormalShader = preload("shoulder_normals.gdshader")
const PantsShader = preload("pants_darken.gdshader")
const HairCurls = preload("hair_curls.gd")

## Arquivos na mesma pasta deste script. Sao carregados como recursos importados,
## para funcionar tambem no jogo exportado.
const CLOTH_TEXTURE_FILE := "pescador_v29_Roupa_ajustada.png"
const HEAD_TEXTURE_FILE := "pescador_v29_Rosto_ajustado.png"
const HAIR_TEXTURE_FILE := "hair_curls_albedo.png"
const PANTS_MASK_FILE := "pants_mask.png"
## Tom das lentes medido na referencia.
const LENS_COLOR := Color(0.075, 0.06, 0.065)
## Repouso da referencia: Idle com os dedos parcialmente fechados.
const REFERENCE_IDLE := "Idle_Referencia"
const FINGER_CURL := 0.85
const GRIP_SAMPLE := 0.75
## Na referencia a palma fica virada para a coxa. No repouso do rig ela fica
## virada para tras: o giro abaixo, em graus, e dividido entre antebraco e mao.
const FOREARM_TWIST_DEGREES := 35.0
const HAND_TWIST_DEGREES := 50.0
## Bracos um pouco mais junto do tronco, como na referencia.
const ARM_IN_DEGREES := 2.5

var _cloth_texture: Texture2D = null
var _head_texture: Texture2D = null
var _hair_texture: Texture2D = null
var _pants_mask: Texture2D = null
var _skeleton: Skeleton3D = null
var _player: AnimationPlayer = null

func _ready() -> void:
    var base_dir: String = (get_script() as Script).resource_path.get_base_dir()
    _cloth_texture = _load_texture(base_dir.path_join(CLOTH_TEXTURE_FILE))
    _head_texture = _load_texture(base_dir.path_join(HEAD_TEXTURE_FILE))
    _hair_texture = _load_texture(base_dir.path_join(HAIR_TEXTURE_FILE))
    _pants_mask = _load_texture(base_dir.path_join(PANTS_MASK_FILE))
    _configure(self)
    _add_reference_idle()

func _load_texture(path: String) -> Texture2D:
    if not ResourceLoader.exists(path):
        push_warning("Pescador: textura nao encontrada, usando o padrao: " + path)
        return null
    return load(path) as Texture2D

func _configure(node: Node) -> void:
    if node is Skeleton3D:
        _skeleton = node
        if node.get_node_or_null("ShoulderCorrective") == null:
            var modifier = Corrective.new()
            modifier.name = "ShoulderCorrective"
            node.add_child(modifier)
        HairCurls.attach(node, _hair_texture)
    if node is AnimationPlayer:
        _player = node
    if node is MeshInstance3D and node.mesh != null:
        for surface in range(node.mesh.get_surface_count()):
            var original: Material = node.mesh.surface_get_material(surface)
            if not (original is StandardMaterial3D):
                continue
            if original.resource_name.begins_with("ShoulderCloth"):
                var material := ShaderMaterial.new()
                material.shader = NormalShader
                material.set_shader_parameter("albedo_texture", _cloth_or(original.albedo_texture))
                node.set_surface_override_material(surface, material)
            elif original.resource_name == "Lentes fumê":
                var lens := original.duplicate() as StandardMaterial3D
                lens.albedo_texture = null
                lens.albedo_color = LENS_COLOR
                lens.roughness = 0.12
                lens.metallic_specular = 0.8
                node.set_surface_override_material(surface, lens)
            elif original.resource_name == "Rosto e acessórios" and _head_texture != null:
                var head := original.duplicate() as StandardMaterial3D
                head.albedo_texture = _head_texture
                node.set_surface_override_material(surface, head)
            elif original.resource_name == "Pescador":
                var body := ShaderMaterial.new()
                body.shader = PantsShader
                body.set_shader_parameter("albedo_texture", _cloth_or(original.albedo_texture))
                # Sem a mascara, o shader deixa a calca como no atlas original.
                if _pants_mask != null:
                    body.set_shader_parameter("pants_mask", _pants_mask)
                node.set_surface_override_material(surface, body)
    for child in node.get_children():
        _configure(child)

func _cloth_or(fallback: Texture2D) -> Texture2D:
    return _cloth_texture if _cloth_texture != null else fallback

## Cria "Idle_Referencia": copia do Idle com os dedos a meio caminho da pegada
## do Grip_Rod, como as maos semifechadas da folha de referencia.
## As animacoes originais nao sao alteradas.
func _add_reference_idle() -> void:
    if _player == null or _skeleton == null:
        return
    if _player.has_animation(REFERENCE_IDLE):
        return
    if not _player.has_animation("Idle") or not _player.has_animation("Grip_Rod"):
        return
    var idle: Animation = _player.get_animation("Idle")
    var grip: Animation = _player.get_animation("Grip_Rod")
    var pose := idle.duplicate(true) as Animation
    for g in range(grip.get_track_count()):
        if grip.track_get_type(g) != Animation.TYPE_ROTATION_3D:
            continue
        var path: NodePath = grip.track_get_path(g)
        var bone_name: String = path.get_concatenated_subnames()
        if not (bone_name.begins_with("finger_") or bone_name.begins_with("thumb_")):
            continue
        var bone: int = _skeleton.find_bone(bone_name)
        if bone < 0:
            continue
        var closed: Quaternion = grip.rotation_track_interpolate(g, grip.length * GRIP_SAMPLE)
        var track: int = pose.find_track(path, Animation.TYPE_ROTATION_3D)
        if track < 0:
            # O importador remove trilhas iguais ao repouso: recria a partir do repouso.
            track = pose.add_track(Animation.TYPE_ROTATION_3D)
            pose.track_set_path(track, path)
            var rest: Quaternion = _skeleton.get_bone_rest(bone).basis.get_rotation_quaternion()
            pose.rotation_track_insert_key(track, 0.0, rest.slerp(closed, FINGER_CURL))
            continue
        for key in range(pose.track_get_key_count(track)):
            var open: Quaternion = pose.track_get_key_value(track, key)
            pose.track_set_key_value(track, key, open.slerp(closed, FINGER_CURL))
    for side in ["R", "L"]:
        var direction := 1.0 if side == "R" else -1.0
        _rotate_bone(pose, "upper_arm." + side, Vector3.BACK, direction * ARM_IN_DEGREES)
        _twist_bone(pose, "forearm_twist." + side, "hand." + side, direction * FOREARM_TWIST_DEGREES)
        _twist_bone(pose, "hand." + side, "finger_middle_01." + side, direction * HAND_TWIST_DEGREES)
    for library_name in _player.get_animation_library_list():
        var library: AnimationLibrary = _player.get_animation_library(library_name)
        if library.has_animation("Idle"):
            library.add_animation(REFERENCE_IDLE, pose)
            return

## Gira `bone_name` em torno do proprio eixo (a direcao ate `child_name`).
func _twist_bone(pose: Animation, bone_name: String, child_name: String, degrees: float) -> void:
    var child: int = _skeleton.find_bone(child_name)
    if child < 0:
        return
    _rotate_bone(pose, bone_name, _skeleton.get_bone_rest(child).origin.normalized(), degrees)

## Soma uma rotacao a `bone_name` em todas as chaves da animacao. Cria a trilha
## se a animacao nao tiver uma.
func _rotate_bone(pose: Animation, bone_name: String, axis: Vector3, degrees: float) -> void:
    var bone: int = _skeleton.find_bone(bone_name)
    if bone < 0:
        return
    var extra := Quaternion(axis, deg_to_rad(degrees))
    # Usa o mesmo caminho de no das trilhas que a animacao ja tem.
    var prefix := ""
    for existing in range(pose.get_track_count()):
        if pose.track_get_type(existing) == Animation.TYPE_ROTATION_3D:
            prefix = String(pose.track_get_path(existing).get_concatenated_names())
            break
    if prefix == "":
        return
    var path := NodePath(prefix + ":" + bone_name)
    var track: int = pose.find_track(path, Animation.TYPE_ROTATION_3D)
    if track < 0:
        track = pose.add_track(Animation.TYPE_ROTATION_3D)
        pose.track_set_path(track, path)
        var rest: Quaternion = _skeleton.get_bone_rest(bone).basis.get_rotation_quaternion()
        pose.rotation_track_insert_key(track, 0.0, rest * extra)
        return
    for key in range(pose.track_get_key_count(track)):
        var value: Quaternion = pose.track_get_key_value(track, key)
        pose.track_set_key_value(track, key, value * extra)
