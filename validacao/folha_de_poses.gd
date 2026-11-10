extends SceneTree
# Folha de contato: uma animacao em N instantes, em dois angulos.
func _initialize() -> void:
	call_deferred("run")
func find_type(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found = find_type(child, kind)
		if found != null: return found
	return null
func run() -> void:
	var args := OS.get_cmdline_user_args()
	var clip: String = args[0]
	var count: int = int(args[1])
	var out: String = args[2]
	var yaws: Array = [0.0, 90.0] if args.size() < 4 else Array(args[3].split(",")).map(func(v): return float(v))
	var target := Vector3(0, 1.0, 0) if args.size() < 5 else Vector3(0, float(args[4]), 0)
	var dist := 4.4 if args.size() < 6 else float(args[5])
	var model = load("res://pescador_v29/PescadorCorrigido.tscn").instantiate()
	root.add_child(model)
	var world := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.3, 0.3, 0.34)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 1, 1)
	world.environment = env
	root.add_child(world)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, 30, 0)
	key.light_energy = 0.6
	root.add_child(key)
	var cam := Camera3D.new()
	root.add_child(cam)
	await process_frame
	var player := find_type(model, "AnimationPlayer") as AnimationPlayer
	var skeleton := find_type(model, "Skeleton3D") as Skeleton3D
	var length: float = player.get_animation(clip).length
	for i in range(count):
		skeleton.reset_bone_poses()
		player.play(clip)
		player.seek(length * float(i) / float(count), true)
		player.pause()
		for y in range(yaws.size()):
			var yaw := deg_to_rad(yaws[y])
			cam.fov = 30.0
			cam.position = target + Vector3(sin(yaw) * dist, 0.0, cos(yaw) * dist)
			cam.look_at(target, Vector3.UP)
			cam.current = true
			await process_frame
			await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("%s/%s_%02d_%d.png" % [out, clip, i, y])
	quit()
