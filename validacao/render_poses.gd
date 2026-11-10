extends SceneTree
## Renderiza poses das animacoes para conferir a deformacao dos ombros e das maos.
## Rodar na raiz do repositorio: godot --path . -s validacao/render_poses.gd
const SHOTS := [
	{"clip": "Idle", "time": 0.0, "yaw": 0.0},
	{"clip": "Idle_Referencia", "time": 0.0, "yaw": 0.0},
	{"clip": "Idle_Referencia", "time": 0.0, "yaw": 90.0},
	{"clip": "Shoulder_Abduction", "time": 0.25, "yaw": 0.0},
	{"clip": "Shoulder_Abduction", "time": 0.5, "yaw": 0.0},
	{"clip": "Shoulder_Abduction", "time": 0.5, "yaw": 180.0},
	{"clip": "Shoulder_Stress", "time": 0.5, "yaw": 0.0},
	{"clip": "Grip_Rod", "time": 0.6, "yaw": 20.0},
	{"clip": "Rig_Mobility", "time": 0.5, "yaw": 0.0},
]
func _initialize() -> void:
	call_deferred("run")
func find_type(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found = find_type(child, kind)
		if found != null: return found
	return null
func run() -> void:
	var model = load("res://pescador_v29/PescadorCorrigido.tscn").instantiate()
	root.add_child(model)
	var world := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.17, 0.17, 0.19)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 1, 1)
	world.environment = env
	root.add_child(world)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, 30, 0)
	key.light_energy = 0.15
	root.add_child(key)
	var cam := Camera3D.new()
	root.add_child(cam)
	await process_frame
	var player := find_type(model, "AnimationPlayer") as AnimationPlayer
	var i := 0
	for shot in SHOTS:
		var anim := player.get_animation(shot["clip"])
		player.play(shot["clip"])
		player.seek(anim.length * float(shot["time"]), true)
		player.pause()
		var yaw := deg_to_rad(shot["yaw"])
		var target := Vector3(0, 1.25, 0)
		cam.fov = 30.0
		cam.position = target + Vector3(sin(yaw) * 3.0, 0.0, cos(yaw) * 3.0)
		cam.look_at(target, Vector3.UP)
		cam.current = true
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://validacao/imagens/renders/pose_%d_%s.png" % [i, shot["clip"]])
		print("POSE ", i, " ", shot["clip"], " len=", anim.length)
		i += 1
	quit()
