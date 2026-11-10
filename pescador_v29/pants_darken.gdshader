shader_type spatial;
// Escurece a calca cargo para o preto com camuflagem sutil da referencia.
// A regiao da calca vem de uma mascara fixa no espaco UV (pants_mask.png), calculada
// na pose de repouso. Por isso nao muda com a animacao, e os tenis ficam de fora.
// Nao altera a malha nem a textura base: so o albedo na etapa de fragmento.

uniform sampler2D albedo_texture : source_color, filter_linear_mipmap;
uniform sampler2D pants_mask : hint_default_black, filter_linear;
uniform float darken = 0.7;
uniform vec3 pants_tint : source_color = vec3(0.075, 0.07, 0.065);
uniform float roughness_value = 0.93;

void fragment() {
	vec3 base = texture(albedo_texture, UV).rgb;
	float legs = texture(pants_mask, UV).r;
	vec3 pants = pants_tint + base * 0.3;
	ALBEDO = mix(base, pants, darken * legs);
	ROUGHNESS = roughness_value;
}
