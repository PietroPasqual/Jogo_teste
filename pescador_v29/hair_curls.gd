@tool
extends Node
## Cabelo cacheado do Pescador: uma malha continua em forma de touca, presa ao
## osso "head" por BoneAttachment3D. Nao altera a malha do GLB, os pesos nem o rig.
## A borda inferior e as laterais recebem ondulacao para lembrar cachos.

const SEED := 20260907
const COLS := 44
const ROWS := 14
const CENTER := Vector3(0.0, 0.1, -0.012)
const RADII := Vector3(0.098, 0.1, 0.106)
const PHI_TOP := 0.32
const PHI_BOTTOM := 2.12

static func attach(skeleton: Skeleton3D) -> void:
    if skeleton == null or skeleton.find_bone("head") < 0:
        return
    if skeleton.get_node_or_null("HairCurls") != null:
        return
    var attachment := BoneAttachment3D.new()
    attachment.name = "HairCurls"
    attachment.bone_name = "head"
    skeleton.add_child(attachment)
    var hair := MeshInstance3D.new()
    hair.name = "HairCap"
    hair.mesh = _build_cap()
    attachment.add_child(hair)

static func _build_cap() -> ArrayMesh:
    var rng := RandomNumberGenerator.new()
    rng.seed = SEED
    var points: Array = []
    var colors: Array = []
    for r in range(ROWS + 1):
        var row_points: Array = []
        var row_colors: Array = []
        var t := float(r) / float(ROWS)
        var phi := lerpf(PHI_TOP, PHI_BOTTOM, t)
        for c in range(COLS + 1):
            var theta := TAU * float(c) / float(COLS)
            var dir := Vector3(sin(phi) * sin(theta), cos(phi), sin(phi) * cos(theta))
            # Ondulacao de cachos: mais forte na borda inferior.
            var curl := 1.0 + 0.07 * sin(theta * 11.0 + phi * 3.0) + 0.05 * sin(theta * 23.0 + phi * 7.0) + 0.035 * sin(theta * 41.0 - phi * 11.0)
            curl += 0.12 * t * absf(sin(theta * 19.0)) + rng.randf_range(-0.045, 0.045)
            var p := CENTER + Vector3(dir.x * RADII.x, dir.y * RADII.y, dir.z * RADII.z) * curl
            # Recua a frente abaixo da linha dos olhos para deixar o rosto livre.
            if p.z > 0.02 and absf(p.x) < 0.095 and p.y < 0.14:
                p -= dir * 0.03
            row_points.append(p)
            var shade := rng.randf_range(-0.012, 0.012)
            row_colors.append(Color(0.075 + shade, 0.06 + shade, 0.05 + shade))
        points.append(row_points)
        colors.append(row_colors)

    var st := SurfaceTool.new()
    st.begin(Mesh.PRIMITIVE_TRIANGLES)
    for r in range(ROWS):
        for c in range(COLS):
            _add_vertex(st, points[r][c], colors[r][c])
            _add_vertex(st, points[r + 1][c], colors[r + 1][c])
            _add_vertex(st, points[r][c + 1], colors[r][c + 1])
            _add_vertex(st, points[r][c + 1], colors[r][c + 1])
            _add_vertex(st, points[r + 1][c], colors[r + 1][c])
            _add_vertex(st, points[r + 1][c + 1], colors[r + 1][c + 1])
    st.generate_normals()
    var mat := StandardMaterial3D.new()
    mat.vertex_color_use_as_albedo = true
    mat.roughness = 0.95
    mat.cull_mode = BaseMaterial3D.CULL_DISABLED
    st.set_material(mat)
    return st.commit()

static func _add_vertex(st: SurfaceTool, p: Vector3, color: Color) -> void:
    st.set_color(color)
    st.add_vertex(p)
