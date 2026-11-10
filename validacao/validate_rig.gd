extends SceneTree
## Validacao nativa do Pescador (Godot 4.4.1). Rodar na raiz do repositorio:
##   godot --path . -s validacao/validate_rig.gd
##
## Confere, contra validacao/expected.json (dados do autor da V29):
##  1. 68 ossos e poses de Idle/Grip_Rod dentro da tolerancia do autor.
##     Os 6 ossos shoulder_deform_* sao reportados a parte: o volume do ombro
##     (BULGE) foi zerado de proposito para seguir a folha de referencia.
##  2. Secoes do ombro sem esticar (razao de area ~1).
##  3. Todas as animacoes, amostradas no tempo, sem valores invalidos.
##  4. Ajustes de cena aplicados: cabelo, texturas importadas (exportaveis),
##     materiais e a animacao Idle_Referencia.

const POSITION_TOLERANCE := 0.0001
const ANGLE_TOLERANCE := 0.002
const AREA_MIN := 0.999
const AREA_MAX := 1.001
const ANIMATIONS := ["Idle", "Grip_Rod", "Rig_Mobility", "Shoulder_Abduction", "Shoulder_Stress", "Idle_Referencia"]
const SAMPLES_PER_ANIMATION := 12

var latest: Dictionary = {}
var skeleton: Skeleton3D
var failures: Array[String] = []

func find_type(node: Node, kind: String) -> Node:
	if node.is_class(kind):
		return node
	for child in node.get_children():
		var found = find_type(child, kind)
		if found != null:
			return found
	return null

func _initialize() -> void:
	call_deferred("validate")

func collect_pose() -> void:
	latest.clear()
	for i in range(skeleton.get_bone_count()):
		latest[skeleton.get_bone_name(i)] = skeleton.get_bone_global_pose(i)

func ring_area(points: PackedVector3Array) -> float:
	var sum := Vector3.ZERO
	for i in range(points.size()):
		sum += points[i].cross(points[(i + 1) % points.size()])
	return sum.length() * 0.5

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		print("FALHA: ", message)

func settle() -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw

func validate() -> void:
	var expected: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://validacao/expected.json"))
	var scene = load("res://pescador_v29/PescadorCorrigido.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	skeleton = find_type(scene, "Skeleton3D") as Skeleton3D
	var player = find_type(scene, "AnimationPlayer") as AnimationPlayer
	check(skeleton != null, "Skeleton3D nao encontrado")
	check(player != null, "AnimationPlayer nao encontrado")
	if skeleton == null or player == null:
		finish({})
		return
	var modifier = skeleton.get_node_or_null("ShoulderCorrective") as SkeletonModifier3D
	check(modifier != null, "ShoulderCorrective nao foi adicionado ao esqueleto")
	if modifier == null:
		finish({})
		return
	modifier.modification_processed.connect(collect_pose)
	print("OSSOS=", skeleton.get_bone_count())
	check(skeleton.get_bone_count() == 68, "esperados 68 ossos, encontrados %d" % skeleton.get_bone_count())

	# 1 e 2: poses do autor.
	var max_position := 0.0
	var max_angle := 0.0
	var max_shoulder_shift := 0.0
	var min_area := 2.0
	var max_area := 0.0
	var rows: Array = []
	for pose in expected["poses"]:
		player.play(pose["clip"])
		player.seek(pose["time"], true)
		player.pause()
		await settle()
		check(not latest.is_empty(), "o corretivo de ombro nao processou a pose %s" % pose["clip"])
		var p_error := 0.0
		var q_error := 0.0
		var shoulder_shift := 0.0
		for bone_name in pose["bones"]:
			var ref: Dictionary = pose["bones"][bone_name]
			var trans: Transform3D = latest[bone_name]
			var p := Vector3(ref["p"][0], ref["p"][1], ref["p"][2])
			var q := Quaternion(ref["q"][0], ref["q"][1], ref["q"][2], ref["q"][3])
			var dp := trans.origin.distance_to(p)
			var dq := trans.basis.get_rotation_quaternion().angle_to(q)
			if String(bone_name).begins_with("shoulder_deform_"):
				shoulder_shift = maxf(shoulder_shift, dp)
			else:
				p_error = maxf(p_error, dp)
				q_error = maxf(q_error, dq)
		max_position = maxf(max_position, p_error)
		max_angle = maxf(max_angle, q_error)
		max_shoulder_shift = maxf(max_shoulder_shift, shoulder_shift)
		for ring in expected["rings"]:
			var index: int = skeleton.find_bone(ring["bone"])
			var rest_inverse := skeleton.get_bone_global_rest(index).affine_inverse()
			var transform: Transform3D = latest[ring["bone"]] * rest_inverse
			var a := PackedVector3Array()
			var b := PackedVector3Array()
			for row in ring["points"]:
				var point := Vector3(row[0], row[1], row[2])
				a.append(point)
				b.append(transform * point)
			var ratio := ring_area(b) / ring_area(a)
			min_area = minf(min_area, ratio)
			max_area = maxf(max_area, ratio)
		rows.append({"clip": pose["clip"], "time": pose["time"], "max_bone_position_error_m": p_error, "max_bone_angle_error_rad": q_error, "shoulder_deform_shift_m": shoulder_shift})
		print("POSE ", pose["clip"], " ", pose["time"], " erro_posicao=", p_error, " erro_angulo=", q_error, " ombro_auxiliar=", shoulder_shift)
	check(max_position < POSITION_TOLERANCE, "erro de posicao dos ossos %.9f m acima da tolerancia" % max_position)
	check(max_angle < ANGLE_TOLERANCE, "erro de angulo dos ossos %.6f rad acima da tolerancia" % max_angle)
	check(min_area > AREA_MIN and max_area < AREA_MAX, "secoes do ombro esticaram: razao de area %.6f a %.6f" % [min_area, max_area])
	check(max_shoulder_shift < 0.08, "ossos auxiliares do ombro deslocaram %.4f m, mais que o esperado" % max_shoulder_shift)

	# 3: todas as animacoes sem valores invalidos.
	var animation_rows: Array = []
	for clip in ANIMATIONS:
		check(player.has_animation(clip), "animacao ausente: %s" % clip)
		if not player.has_animation(clip):
			continue
		var length: float = player.get_animation(clip).length
		var finite := true
		var max_reach := 0.0
		for s in range(SAMPLES_PER_ANIMATION):
			skeleton.reset_bone_poses()
			player.play(clip)
			player.seek(length * float(s) / float(SAMPLES_PER_ANIMATION), true)
			player.pause()
			await settle()
			for bone_name in latest:
				var t: Transform3D = latest[bone_name]
				if not t.is_finite():
					finite = false
				max_reach = maxf(max_reach, t.origin.length())
		check(finite, "animacao %s gerou transformacao invalida (NaN/inf)" % clip)
		check(max_reach < 3.0, "animacao %s levou um osso a %.2f m da origem" % [clip, max_reach])
		animation_rows.append({"clip": clip, "length_s": length, "finite": finite, "max_bone_distance_m": max_reach})
		print("ANIM ", clip, " duracao=", length, " ok=", finite, " alcance=", max_reach)

	# 4: ajustes de cena.
	var hair := skeleton.get_node_or_null("HairCurls/HairCap") as MeshInstance3D
	check(hair != null and hair.mesh != null, "cabelo (HairCurls/HairCap) nao foi criado")
	var hair_texture_ok := false
	if hair != null and hair.mesh != null:
		var hair_material := hair.mesh.surface_get_material(0) as StandardMaterial3D
		hair_texture_ok = hair_material != null and hair_material.albedo_texture != null and hair_material.albedo_texture.resource_path != ""
	check(hair_texture_ok, "textura do cabelo nao veio de um recurso importado (falharia no jogo exportado)")
	var body: MeshInstance3D = null
	for candidate in skeleton.get_children():
		if candidate is MeshInstance3D and candidate.mesh != null and candidate.mesh.get_surface_count() >= 4:
			body = candidate
	check(body != null, "malha do corpo nao encontrada no esqueleto")
	var overrides: Dictionary = {}
	var cloth_imported := false
	if body != null and body.mesh != null:
		for surface in range(body.mesh.get_surface_count()):
			var original := body.mesh.surface_get_material(surface)
			var override := body.get_surface_override_material(surface)
			var name := original.resource_name if original != null else "?"
			overrides[name] = override != null
			if override is ShaderMaterial and name == "Pescador":
				var texture := (override as ShaderMaterial).get_shader_parameter("albedo_texture") as Texture2D
				cloth_imported = texture != null and texture.resource_path.ends_with("pescador_v29_Roupa_ajustada.png")
	check(overrides.get("Pescador", false), "material do corpo sem o ajuste de calca/camuflado")
	check(overrides.get("ShoulderCloth", false), "material do ombro sem o shader de normais")
	check(overrides.get("Lentes fumê", false), "lentes sem o ajuste de cor")
	check(cloth_imported, "textura ajustada da roupa nao veio de um recurso importado (falharia no jogo exportado)")

	finish({
		"engine": Engine.get_version_info()["string"],
		"bones": skeleton.get_bone_count(),
		"poses": rows,
		"max_position_error_m": max_position,
		"max_rotation_error_rad": max_angle,
		"shoulder_deform_max_shift_m": max_shoulder_shift,
		"section_area_ratio_min": min_area,
		"section_area_ratio_max": max_area,
		"animations": animation_rows,
		"hair_texture_imported": hair_texture_ok,
		"cloth_texture_imported": cloth_imported,
		"material_overrides": overrides,
	})

func finish(report: Dictionary) -> void:
	report["failures"] = failures
	report["passed"] = failures.is_empty()
	var file := FileAccess.open("res://validacao/validation_report_godot_4_4_1.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	if failures.is_empty():
		print("RIG_VALIDATION_PASS")
		quit()
	else:
		push_error("Validacao do rig falhou: %d problema(s)" % failures.size())
		quit(1)
