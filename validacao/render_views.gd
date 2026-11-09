extends SceneTree

# Renderiza as vistas da folha de referencia com a cena oficial PescadorCorrigido.tscn.
const VIEWS := [
	{"name": "front", "yaw": 0.0, "target": Vector3(0, 1.0, 0), "dist": 4.2, "fov": 30.0},
	{"name": "side", "yaw": 90.0, "target": Vector3(0, 1.0, 0), "dist": 4.2, "fov": 30.0},
	{"name": "back", "yaw": 180.0, "target": Vector3(0, 1.0, 0), "dist": 4.2, "fov": 30.0},
	{"name": "three_quarter", "yaw": 45.0, "target": Vector3(0, 1.0, 0), "dist": 4.2, "fov": 30.0},
	{"name": "head_front", "yaw": 0.0, "target": Vector3(0, 1.63, 0), "dist": 0.9, "fov": 28.0},
	{"name": "head_side", "yaw": 90.0, "target": Vector3(0, 1.63, 0), "dist": 0.9, "fov": 28.0},
	{"name": "head_back", "yaw": 180.0, "target": Vector3(0, 1.63, 0), "dist": 0.9, "fov": 28.0},
	{"name": "head_three_quarter", "yaw": 45.0, "target": Vector3(0, 1.63, 0), "dist": 0.9, "fov": 28.0},
]

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var model = load("res://pescador_v29/PescadorCorrigido.tscn").instantiate()
	root.add_child(model)

	var world := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.17, 0.17, 0.19)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.75, 0.75, 0.75)
	world.environment = env
	root.add_child(world)

	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, 30, 0)
	key.light_energy = 1.1
	root.add_child(key)

	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-20, -150, 0)
	fill.light_energy = 0.4
	root.add_child(fill)

	var cam := Camera3D.new()
	root.add_child(cam)

	for view in VIEWS:
		var yaw := deg_to_rad(view["yaw"])
		var target: Vector3 = view["target"]
		var dist: float = view["dist"]
		cam.fov = view["fov"]
		cam.position = target + Vector3(sin(yaw) * dist, 0.0, cos(yaw) * dist)
		cam.look_at(target, Vector3.UP)
		cam.current = true
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		var img := root.get_texture().get_image()
		img.save_png("res://render_" + view["name"] + ".png")
		print("RENDERED ", view["name"])
	quit()
