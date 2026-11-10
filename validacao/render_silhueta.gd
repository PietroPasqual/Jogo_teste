extends SceneTree
## Renderiza o personagem em projecao ortografica (frente, lado, costas), na pose
## Idle_Referencia, para comparar a silhueta com a folha de referencia.
## Rodar na raiz do repositorio: godot --path . -s validacao/render_silhueta.gd
const OUT := "res://validacao/imagens/silhueta/"
const VIEWS := {"frente": 0.0, "lado": -90.0, "costas": 180.0}
## Altura enquadrada, em metros, e centro vertical. Fixos para as medidas serem comparaveis.
const ALTURA := 2.1
const CENTRO_Y := 0.95

func _initialize() -> void:
	call_deferred("run")

func find_type(node: Node, kind: String) -> Node:
	if node.is_class(kind):
		return node
	for child in node.get_children():
		var found = find_type(child, kind)
		if found != null:
			return found
	return null

func run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var model = load("res://pescador_v29/PescadorCorrigido.tscn").instantiate()
	root.add_child(model)
	var world := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0, 1, 0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 1, 1)
	world.environment = env
	root.add_child(world)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, 30, 0)
	key.light_energy = 0.15
	root.add_child(key)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = ALTURA
	root.add_child(cam)
	await process_frame
	var player := find_type(model, "AnimationPlayer") as AnimationPlayer
	var clip := "Idle_Referencia" if player.has_animation("Idle_Referencia") else "Idle"
	player.play(clip)
	player.seek(0.0, true)
	player.pause()
	for view in VIEWS:
		var yaw := deg_to_rad(VIEWS[view])
		var target := Vector3(0, CENTRO_Y, 0)
		cam.position = target + Vector3(sin(yaw) * 5.0, 0.0, cos(yaw) * 5.0)
		cam.look_at(target, Vector3.UP)
		cam.current = true
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(OUT + view + ".png")
		print("SILHUETA ", view)
	quit()
