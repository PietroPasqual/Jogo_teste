shader_type spatial;
render_mode cull_disabled;
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_disable;
void fragment() {
    ALBEDO = texture(albedo_texture, UV).rgb;
    vec3 face_normal = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));
    if (dot(face_normal, VIEW) < 0.0) {
        face_normal = -face_normal;
    }
    NORMAL = face_normal;
    ROUGHNESS = 0.93;
    METALLIC = 0.0;
    SPECULAR = 0.0;
}
