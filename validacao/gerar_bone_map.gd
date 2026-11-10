extends SceneTree
## Gera pescador_v29/pescador_bone_map.tres: o mapa dos ossos do Pescador para o
## perfil humanoide do Godot (SkeletonProfileHumanoid), usado para reaproveitar
## animacoes de outras bibliotecas (retargeting).
## Rodar na raiz do repositorio: godot --path . --headless -s validacao/gerar_bone_map.gd

const OUT := "res://pescador_v29/pescador_bone_map.tres"
## No modelo, ".L" fica em +X: e o lado esquerdo do personagem, que olha para +Z.
const SIDES := {"Left": "L", "Right": "R"}
const CENTER := {
	"Root": "root_motion", "Hips": "root", "Spine": "spine_lower", "Chest": "chest",
	"UpperChest": "upper_chest", "Neck": "neck", "Head": "head",
}
const LIMBS := {
	"Shoulder": "clavicle", "UpperArm": "upper_arm", "LowerArm": "forearm", "Hand": "hand",
	"UpperLeg": "thigh", "LowerLeg": "shin", "Foot": "foot", "Toes": "toes",
	"ThumbMetacarpal": "thumb_01", "ThumbProximal": "thumb_02", "ThumbDistal": "thumb_03",
}
const FINGERS := {"Index": "finger_index", "Middle": "finger_middle", "Ring": "finger_ring", "Little": "finger_little"}
const PHALANGES := {"Proximal": "01", "Intermediate": "02", "Distal": "03"}

func _initialize() -> void:
	var map := BoneMap.new()
	map.profile = SkeletonProfileHumanoid.new()
	for profile_bone in CENTER:
		map.set_skeleton_bone_name(profile_bone, CENTER[profile_bone])
	for side in SIDES:
		var suffix: String = "." + SIDES[side]
		for part in LIMBS:
			map.set_skeleton_bone_name(side + part, LIMBS[part] + suffix)
		for finger in FINGERS:
			for phalanx in PHALANGES:
				map.set_skeleton_bone_name(side + finger + phalanx, "%s_%s%s" % [FINGERS[finger], PHALANGES[phalanx], suffix])
	var error := ResourceSaver.save(map, OUT)
	print("BONE_MAP ", "ok" if error == OK else "erro %d" % error)
	quit(0 if error == OK else 1)
