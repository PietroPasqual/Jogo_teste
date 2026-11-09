shader_type spatial;
// Escurece a calca cargo para o preto com camuflagem sutil da referencia.
// Afeta apenas vertices abaixo da cintura (y do modelo) e dentro das pernas (|x| pequeno).
// Nao altera a malha nem a textura base: so o albedo na etapa de fragmento.

uniform sampler2D albedo_texture : source_color, filter_linear_mipmap;
uniform float waist_y = 0.96;
uniform float leg_half_width = 0.17;
uniform float darken = 0.7;
uniform vec3 pants_tint = vec3(0.075, 0.07, 0.065);
uniform float roughness_value = 0.93;

varying float v_y;
varying float v_x;

void vertex() {
	v_y = VERTEX.y;
	v_x = VERTEX.x;
}

void fragment() {
	vec3 base = texture(albedo_texture, UV).rgb;
	float below_waist = 1.0 - smoothstep(waist_y - 0.02, waist_y + 0.02, v_y);
	float in_legs = 1.0 - smoothstep(leg_half_width - 0.02, leg_half_width + 0.02, abs(v_x));
	vec3 pants = pants_tint + base * 0.3;
	ALBEDO = mix(base, pants, darken * below_waist * in_legs);
	ROUGHNESS = roughness_value;
}
