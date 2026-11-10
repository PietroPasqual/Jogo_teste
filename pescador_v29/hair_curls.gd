@tool
extends Node
## Cabelo cacheado do Pescador: touca continua presa ao osso "head" por
## BoneAttachment3D, com textura de tufos (recorte alfa) na borda inferior.
## Nao altera a malha do GLB, os pesos nem o rig.

const COLS := 44
const ROWS := 14
const CENTER := Vector3(0.0, 0.1, -0.012)
const RADII := Vector3(0.106, 0.1, 0.108)
## Alargamento da metade inferior, para a massa de cabelo da referencia
## aparecer dos lados do rosto e na nuca.
const LOWER_FLARE := 0.27
const PHI_TOP := 0.32
const PHI_BOTTOM := 2.12
const TILES_AROUND := 2.0
## Cor usada quando a textura nao pode ser carregada (media medida na referencia).
const FALLBACK_COLOR := Color(0.08, 0.057, 0.057)

static func attach(skeleton: Skeleton3D, texture: Texture2D) -> void:
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
    hair.mesh = _build_cap(texture)
    attachment.add_child(hair)

static func _build_cap(texture: Texture2D) -> ArrayMesh:
    var points: Array = []
    for r in range(ROWS + 1):
        var row_points: Array = []
        var t := float(r) / float(ROWS)
        var phi := lerpf(PHI_TOP, PHI_BOTTOM, t)
        var flare := 1.0 + LOWER_FLARE * sin(PI * clampf((t - 0.2) / 0.8, 0.0, 1.0))
        for c in range(COLS + 1):
            var theta := TAU * float(c) / float(COLS)
            var dir := Vector3(sin(phi) * sin(theta), cos(phi), sin(phi) * cos(theta))
            # Ondulacao suave da superficie: a textura cuida dos tufos finos.
            var curl := 1.0 + 0.05 * sin(theta * 11.0 + phi * 3.0) + 0.03 * sin(theta * 23.0 + phi * 7.0)
            var p := CENTER + Vector3(dir.x * RADII.x * flare, dir.y * RADII.y, dir.z * RADII.z * flare) * curl
            # Recua a frente abaixo da linha dos olhos para deixar o rosto livre.
            if p.z > 0.02 and absf(p.x) < 0.095 and p.y < 0.14:
                p -= dir * 0.05
            row_points.append(p)
        points.append(row_points)

    var st := SurfaceTool.new()
    st.begin(Mesh.PRIMITIVE_TRIANGLES)
    for r in range(ROWS):
        for c in range(COLS):
            _add_vertex(st, points[r][c], _uv(r, c))
            _add_vertex(st, points[r + 1][c], _uv(r + 1, c))
            _add_vertex(st, points[r][c + 1], _uv(r, c + 1))
            _add_vertex(st, points[r][c + 1], _uv(r, c + 1))
            _add_vertex(st, points[r + 1][c], _uv(r + 1, c))
            _add_vertex(st, points[r + 1][c + 1], _uv(r + 1, c + 1))
    st.generate_normals()
    st.set_material(_material(texture))
    return st.commit()

static func _uv(r: int, c: int) -> Vector2:
    return Vector2(float(c) / float(COLS) * TILES_AROUND, float(r) / float(ROWS))

static func _material(texture: Texture2D) -> StandardMaterial3D:
    var mat := StandardMaterial3D.new()
    if texture != null:
        mat.albedo_texture = texture
        mat.albedo_color = Color(1, 1, 1)
        mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
        mat.alpha_scissor_threshold = 0.5
    else:
        mat.albedo_color = FALLBACK_COLOR
    mat.roughness = 0.95
    mat.cull_mode = BaseMaterial3D.CULL_DISABLED
    return mat

static func _add_vertex(st: SurfaceTool, p: Vector3, uv: Vector2) -> void:
    st.set_uv(uv)
    st.add_vertex(p)
