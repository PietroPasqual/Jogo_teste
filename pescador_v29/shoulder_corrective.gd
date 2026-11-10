@tool
extends SkeletonModifier3D
## Continuous shoulder volume controls. Runs after AnimationMixer/Skeleton posing.
const FRACTIONS = [0.25, 0.5, 0.75]
## Volume extra do ombro com os bracos abaixados. O valor original (0.0546) criava
## ombreiras salientes que nao existem na folha de referencia; com 0.0 o ombro fica
## arredondado como na referencia. Bracos levantados nao mudam (o volume ja sumia).
const BULGE = 0.0
const CHAINS = [
    {"arm": "upper_arm.R", "side": "R", "root": Vector3(-0.0928822588, 0.0214941176, -0.0271998918), "end": Vector3(-0.1523660863, -0.0882602175, -0.0204386175), "pivot": Vector3(-0.1218105000, 0.0042000000, -0.0043701000), "outward": Vector3(-1.0000000000, 0.0000000000, 0.0000000000), "sections": [Vector3(-0.1645189439, 0.0122564384, -0.0261434427), Vector3(-0.1983213341, -0.0122858883, -0.0238192546), Vector3(-0.1895912041, -0.0473767958, -0.0214950666)]},
    {"arm": "upper_arm.L", "side": "L", "root": Vector3(0.0909932100, 0.0206062500, -0.0164193225), "end": Vector3(0.1479575737, -0.0881558825, -0.0202652537), "pivot": Vector3(0.1218105000, 0.0042000000, -0.0043701000), "outward": Vector3(1.0000000000, 0.0000000000, 0.0000000000), "sections": [Vector3(0.1618217610, 0.0113854464, -0.0170202493), Vector3(0.1948041376, -0.0130460706, -0.0183422881), Vector3(0.1854382018, -0.0478419604, -0.0196643270)]}
]
var _bindings: Array[Dictionary] = []

func _ready() -> void:
    _cache_bones()

func _cache_bones() -> void:
    _bindings.clear()
    var skeleton: Skeleton3D = get_skeleton()
    if skeleton == null:
        return
    for chain in CHAINS:
        var source: int = skeleton.find_bone(chain["arm"])
        var targets: Array[int] = []
        for suffix in ["25", "50", "75"]:
            targets.append(skeleton.find_bone("shoulder_deform_" + suffix + "." + chain["side"]))
        if source >= 0 and not targets.has(-1):
            _bindings.append({"source": source, "targets": targets, "data": chain})

func _process_modification() -> void:
    var skeleton: Skeleton3D = get_skeleton()
    if skeleton == null:
        return
    if _bindings.is_empty():
        _cache_bones()
    for binding in _bindings:
        var data: Dictionary = binding["data"]
        var q: Quaternion = skeleton.get_bone_pose_rotation(binding["source"]).normalized()
        var pivot: Vector3 = data["pivot"]
        var root_point: Vector3 = data["root"]
        var outward: Vector3 = data["outward"]
        var end_point: Vector3 = pivot + q * (data["end"] - pivot)
        var end_axis: Vector3 = q * Vector3.DOWN
        var span: float = root_point.distance_to(end_point) * 0.45
        var c1: Vector3 = root_point + outward * span
        var c2: Vector3 = end_point - end_axis * span
        var fade: float = 1.0 - maxf(0.0, outward.dot(end_axis))
        var side_sign: float = -1.0 if data["side"] == "R" else 1.0
        var end_turn := Quaternion(Vector3(0,0,1), -side_sign * PI * 0.5)
        for k in range(3):
            var a: float = FRACTIONS[k]
            var b: float = 1.0 - a
            var frame: Quaternion = Quaternion.IDENTITY.slerp(q * end_turn, a)
            var bind_frame := Quaternion(Vector3(0,0,1), -side_sign * PI * 0.5 * a)
            var partial: Quaternion = (frame * bind_frame.inverse()).normalized()
            var target: Vector3 = b*b*b*root_point + 3.0*b*b*a*c1 + 3.0*b*a*a*c2 + a*a*a*end_point
            target += outward * BULGE * sin(PI*a) * fade
            var default_center: Vector3 = pivot + partial * (data["sections"][k] - pivot)
            var index: int = binding["targets"][k]
            skeleton.set_bone_pose_rotation(index, partial)
            skeleton.set_bone_pose_position(index, skeleton.get_bone_rest(index).origin + target - default_center)
