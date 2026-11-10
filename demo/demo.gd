extends Node3D
var _player: AnimationPlayer
const CLIPS = ["Shoulder_Abduction", "Shoulder_Stress", "Rig_Mobility", "Grip_Rod", "Idle", "Idle_Referencia"]

func find_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node
    for child in node.get_children():
        var player := find_player(child)
        if player != null:
            return player
    return null

func _ready() -> void:
    $Camera.look_at(Vector3(0, 1.0, 0))
    _player = find_player($Pescador)
    if _player != null:
        for clip in CLIPS:
            if _player.has_animation(clip):
                _player.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
        # Comeca no repouso da referencia (maos semifechadas).
        _player.play(CLIPS[5] if _player.has_animation(CLIPS[5]) else CLIPS[4])
    var layer := CanvasLayer.new()
    add_child(layer)
    var label := Label.new()
    label.position = Vector2(20,16)
    label.text = "PESCADOR V29 | 1: Abrir braços | 2: Alcance e torção | 3: Mobilidade | 4: Pega | 5: Repouso | 6: Repouso da referência\nEspaço: pausar | Setas: girar o personagem"
    label.add_theme_color_override("font_outline_color",Color.BLACK)
    label.add_theme_constant_override("outline_size",6)
    layer.add_child(label)

func _unhandled_key_input(event: InputEvent) -> void:
    var key := event as InputEventKey
    if key == null or not key.is_pressed() or key.is_echo() or _player == null:
        return
    if key.keycode >= KEY_1 and key.keycode <= KEY_6:
        var index: int = key.keycode-KEY_1
        if not _player.has_animation(CLIPS[index]):
            return
        _player.stop()
        var skeleton = _player.get_node("../Pescador/Skeleton3D") as Skeleton3D
        if skeleton != null:
            skeleton.reset_bone_poses()
        _player.play(CLIPS[index])
    elif key.keycode == KEY_SPACE:
        if _player.is_playing(): _player.pause()
        else: _player.play()
    elif key.keycode == KEY_LEFT:
        $Pescador.rotation.y -= PI/8.0
    elif key.keycode == KEY_RIGHT:
        $Pescador.rotation.y += PI/8.0
