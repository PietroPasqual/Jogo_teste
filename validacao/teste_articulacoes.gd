extends SceneTree
## Teste de esforco das articulacoes: aplica poses fortes direto nos ossos e
## renderiza cada uma em dois angulos, para conferir a deformacao da malha.
## Rodar na raiz do repositorio: godot --path . -s validacao/teste_articulacoes.gd
## As imagens saem em validacao/imagens/articulacoes/.

const OUT := "res://validacao/imagens/articulacoes/"
## Rotacoes em graus (x, y, z) por osso. Os ossos tem repouso sem rotacao, entao
## os eixos sao os do modelo: X para o lado, Y para cima, Z para a frente.
const POSES := {
	"cotovelos_dobrados": {
		"bones": {"forearm.R": Vector3(-110, 0, 0), "forearm.L": Vector3(-110, 0, 0)},
		"target": Vector3(0, 1.2, 0), "dist": 2.2},
	"bracos_a_frente": {
		"bones": {"upper_arm.R": Vector3(-90, 0, 0), "upper_arm.L": Vector3(-90, 0, 0)},
		"target": Vector3(0, 1.3, 0.1), "dist": 2.4},
	"bracos_acima": {
		"bones": {"upper_arm.R": Vector3(0, 0, -150), "upper_arm.L": Vector3(0, 0, 150)},
		"target": Vector3(0, 1.5, 0), "dist": 2.8},
	"arremesso": {
		"bones": {"upper_arm.R": Vector3(-150, 0, -20), "forearm.R": Vector3(-70, 0, 0), "upper_arm.L": Vector3(-40, 0, 10), "forearm.L": Vector3(-60, 0, 0), "chest": Vector3(-8, -15, 0)},
		"target": Vector3(0, 1.4, 0), "dist": 2.8},
	"agachado": {
		"bones": {"thigh.R": Vector3(-95, 0, 0), "thigh.L": Vector3(-95, 0, 0), "shin.R": Vector3(115, 0, 0), "shin.L": Vector3(115, 0, 0), "foot.R": Vector3(-20, 0, 0), "foot.L": Vector3(-20, 0, 0)},
		"target": Vector3(0, 0.75, 0.1), "dist": 3.0},
	"passo_largo": {
		"bones": {"thigh.R": Vector3(-45, 0, 0), "shin.R": Vector3(50, 0, 0), "thigh.L": Vector3(30, 0, 0), "shin.L": Vector3(25, 0, 0), "upper_arm.L": Vector3(-35, 0, 0), "upper_arm.R": Vector3(30, 0, 0), "forearm.L": Vector3(-40, 0, 0), "forearm.R": Vector3(-25, 0, 0)},
		"target": Vector3(0, 0.95, 0), "dist": 3.6},
	"tronco_inclinado": {
		"bones": {"spine_lower": Vector3(15, 0, 0), "spine": Vector3(15, 0, 0), "chest": Vector3(15, 0, 0), "upper_chest": Vector3(10, 0, 0), "neck": Vector3(-15, 0, 0)},
		"target": Vector3(0, 1.2, 0.1), "dist": 2.8},
	"tronco_torcido": {
		"bones": {"spine_lower": Vector3(0, 12, 0), "spine": Vector3(0, 12, 0), "chest": Vector3(0, 12, 0), "upper_chest": Vector3(0, 10, 0), "neck": Vector3(0, 25, 0), "head": Vector3(0, 30, 0)},
		"target": Vector3(0, 1.3, 0), "dist": 2.6},
	"cabeca": {
		"bones": {"neck": Vector3(15, 30, 0), "head": Vector3(20, 35, 10)},
		"target": Vector3(0, 1.6, 0), "dist": 1.3},
	"torcao_do_punho": {
		"bones": {"forearm.R": Vector3(-90, 0, 0), "forearm.L": Vector3(-90, 0, 0), "hand.R": Vector3(0, 90, 0), "hand.L": Vector3(0, -90, 0)},
		"target": Vector3(0, 1.1, 0.25), "dist": 1.6},
	"torcao_do_tornozelo": {
		"bones": {"foot.R": Vector3(0, 45, 0), "foot.L": Vector3(0, -45, 0)},
		"target": Vector3(0, 0.2, 0.05), "dist": 1.5},
	"punhos": {
		"bones": {"forearm.R": Vector3(-90, 0, 0), "forearm.L": Vector3(-90, 0, 0), "hand.R": Vector3(-60, 0, 0), "hand.L": Vector3(60, 0, 0)},
		"target": Vector3(0, 1.1, 0.25), "dist": 1.6},
}
const YAWS := [20.0, 100.0]

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
	var skeleton := find_type(model, "Skeleton3D") as Skeleton3D
	var player := find_type(model, "AnimationPlayer") as AnimationPlayer
	player.stop()
	player.active = false
	for pose_name in POSES:
		var pose: Dictionary = POSES[pose_name]
		skeleton.reset_bone_poses()
		for bone_name in pose["bones"]:
			var bone: int = skeleton.find_bone(bone_name)
			if bone < 0:
				push_error("osso ausente: " + bone_name)
				continue
			var e: Vector3 = pose["bones"][bone_name]
			var rotation := Quaternion.from_euler(Vector3(deg_to_rad(e.x), deg_to_rad(e.y), deg_to_rad(e.z)))
			skeleton.set_bone_pose_rotation(bone, skeleton.get_bone_rest(bone).basis.get_rotation_quaternion() * rotation)
		for y in range(YAWS.size()):
			var yaw := deg_to_rad(YAWS[y])
			var target: Vector3 = pose["target"]
			var dist: float = pose["dist"]
			cam.fov = 30.0
			cam.position = target + Vector3(sin(yaw) * dist, 0.15, cos(yaw) * dist)
			cam.look_at(target, Vector3.UP)
			cam.current = true
			await process_frame
			await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("%s%s_%d.png" % [OUT, pose_name, y])
		print("POSE ", pose_name)
	quit()
