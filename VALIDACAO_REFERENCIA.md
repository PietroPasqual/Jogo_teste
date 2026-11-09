# Validação do modelo Pescador V29 contra a referência

## O que foi verificado (arquivos)

- `pescador_v29/pescador_v29.glb`: glTF 2.0, 1 malha com 5 primitivas, 4 materiais
  (`Pescador`, `Rosto e acessórios`, `Lentes fumê`, `ShoulderCloth`), 2 texturas embutidas
  (`Roupa` 1536×1792 e `Rosto` 2048×1360), 1 skin com 68 ossos e 5 animações
  (`Idle`, `Grip_Rod`, `Rig_Mobility`, `Shoulder_Abduction`, `Shoulder_Stress`).
- Hierarquia de ossos: 15 articulações de dedos por mão, `clavicle`, `upper_arm`/`forearm`/`hand`,
  `thigh`/`shin`/`foot`, `neck`, `head`, 6 auxiliares de ombro (`shoulder_deform_*`).
- Prévia `previa_maos_v29.webp`: comparação V28 × V29 das mãos, sem alteração de malha além das mãos.

## Limitações desta validação

- O Godot 4.4.1 não está disponível no ambiente, então `demo/validate.gd` (validação nativa de
  ossos, ângulos e áreas das seções) **não foi executado**. Os números de `validacao/` são os
  do autor do modelo e não foram reproduzidos aqui.
- A comparação com a referência é visual (texturas e prévia), não medição de pixels.

## Diferenças observadas em relação à referência

Referência: folha de modelo (4 vistas + close-ups) e cena in-game com o pescador segurando um peixe.

| Área | Referência | Modelo V29 | Status |
|---|---|---|---|
| Chapéu bucket camuflado com logo de peixe | Camuflagem nítida, logo claro na frente | Presente na textura `Roupa` e na prévia | Conferir nitidez da camuflagem |
| Óculos escuros | Lentes pretas, reflexo marcado | Material `Lentes fumê`, rugosidade 0.38 | Conferir reflexo |
| Cabelo cacheado | Cachos visíveis nas têmporas e na nuca | Massa escura, com borrões nas laterais do atlas `Rosto` | **Diferente** – cachos pouco definidos |
| Rosto (bigode, cavanhaque) | Traços bem definidos | Traços presentes, mas testa e olhos com faixas esticadas no atlas | **Diferente** – textura com distorção |
| Camuflagem da jaqueta | Blocos pretos/cinza com contraste forte | Blocos com contraste mais baixo e desfoque | **Diferente** – menor contraste |
| Detalhes vermelhos/brancos nos ombros (`ShoulderCloth`) | Padrão vermelho e branco nítido | Presente, porém com manchas menos definidas | **Diferente** – padrão menos nítido |
| Logo de peixe nas costas e no bolso | Presente | Presente na textura `Roupa` | Igual |
| Cinto, tiras e bolso peitoral | Presentes | Presentes na textura `Roupa` | Igual |
| Calça cargo com bolsos laterais | Presentes | Presentes | Igual |
| Tênis escuros com sola branca | Presentes | Presentes | Conferir sola branca |

## Próximos passos para ficar idêntico à referência

1. Refazer a textura `Rosto` com cabelo cacheado definido e corrigir o esticamento de testa e olhos.
2. Aumentar o contraste e a nitidez da camuflagem na textura `Roupa`, principalmente nos ombros.
3. Rodar `demo/validate.gd` no Godot 4.4.1 para confirmar que o rig não mudou.
4. Comparar renders no Godot com as vistas da referência, lado a lado.

Nenhuma alteração de malha, osso ou textura foi feita nesta etapa. Este commit apenas salva o pacote do modelo.

## Validação nativa executada (Godot 4.4.1, Xvfb)

- Import do pacote (`godot --headless --import`): OK.
- `demo/validate.gd`: **NATIVE_VALIDATION_PASS**, 68 ossos, erro máximo de posição 0,00000018 m, erro angular máximo 0,00098 rad, razão de área das seções entre 0,99999950 e 1,00000007.
- Renders das vistas da referência (`validacao/renders_godot_4_4_1/`), gerados por `validacao/render_views.gd` com a cena oficial `PescadorCorrigido.tscn`: frente, lado, costas, 3/4 e close-ups de cabeça.

### Achados dos renders

- **Rosto:** o bloco esticado do atlas não aparece no personagem montado. O rosto renderiza correto. O "esticamento" é só o desdobramento UV, então não é um defeito visível.
- **Cabelo:** existe, com mechas e cachos na nuca e nas laterais, mas o volume e a definição dos cachos são menores que na referência. Na frente, o cabelo fica achatado sob o chapéu.
- **Cartões de cabelo no atlas:** estão nas duas miniaturas do canto inferior direito da textura `Rosto`. Ajustar o volume da silhueta depende principalmente da geometria, não só da textura.

## Ajuste de malha do cabelo (cachos)

- Novo `pescador_v29/hair_curls.gd`: 64 blocos de cabelo presos ao osso `head` por `BoneAttachment3D`, nunca alterando a malha do GLB, os pesos nem o rig.
- `pescador_v29/pescador_scene.gd` chama `HairCurls.attach` para cada `Skeleton3D`.
- Renders atualizados em `validacao/renders_godot_4_4_1/`. Na nuca e nas laterais, o volume agora aparece abaixo da aba do chapéu. A frente do rosto fica limpa.
- Limitação da etapa anterior: os blocos pareciam bolinhas separadas.

## Cabelo em touca contínua (etapa 2)

- `hair_curls.gd` agora gera uma malha contínua em forma de touca (44×14 vértices), presa ao osso `head`, com ondulação de cachos na borda e cor levemente variável.
- Recuo das laterais: o volume de "fone de ouvido" na altura das orelhas sumiu, e a frente abaixo da linha dos olhos fica livre.
- Ainda falta: a textura de cachos da referência. A superfície está lisa demais para bater com a massa cacheada, então a silhueta ainda não está igual.
- Próximo passo: cartões com textura de cachos (alpha) sobre a touca, ou ondulação de maior frequência com normal map.

## Cabelo com textura de cachos (etapa 3)

- `pescador_v29/hair_curls_albedo.png`: textura 512×256 gerada por script, com cachos escuros na borda inferior e falhas transparentes entre eles. A parte de cima fica sólida.
- `hair_curls.gd` aplica a textura na touca com UVs (2 repetições ao redor da cabeça) e recorte alfa. A cor do vértice fica branca para não escurecer a textura.
- Renders: na nuca, o cabelo agora tem massa e textura cacheada. Na vista 3/4, os cachos aparecem nas laterais, sob a aba do chapéu.
- Ainda diferente da referência: a textura usa círculos e não cachos reais, então o detalhe é mais uniforme que o da folha de referência. A cor também é um pouco mais escura.
- Próximo passo: refinar a textura para cachos com formas irregulares, e revisar a cor do cabelo contra a amostra da referência.

## Cabelo com cachos irregulares (etapa 4)

- `hair_curls_albedo.png` refeita com cachos de contorno irregular (polígonos em estrela), realce pequeno em cada cacho e paleta mais escura, perto da cor do cabelo da referência.
- Renders: a nuca mostra textura cacheada irregular, com aspecto de massa crespa. Nas laterais, os cachos aparecem acima da orelha, sob a aba do chapéu.
- Ainda diferente da referência: a coroa fica mais uniforme que a folha de referência, e não há uma medição de cor contra a amostra. A comparação continua visual.

## Cabelo com coroa texturizada (etapa 5)

- `hair_curls_albedo.png`: a parte superior da textura agora tem cachos pequenos e de baixo contraste. Antes era uma cor lisa.
- Renders: a coroa aparece texturizada sob a aba do chapéu, e a nuca mantém a massa cacheada. A frente do rosto continua limpa.
- Ainda diferente da referência: o cabelo é mais uniforme que a folha de referência, e a comparação de cor segue visual.

## Camuflagem e ombros (etapa 6)

- A textura `Roupa` embutida no GLB é idêntica ao `pescador_v29_Roupa.jpg` solto. Por isso a correção não altera o GLB: o `pescador_scene.gd` aplica em tempo de execução a versão `pescador_v29_Roupa_ajustada.png`.
- Ajuste da versão: contraste ×1,18, saturação ×1,08 e nitidez (unsharp mask). Uma primeira tentativa com saturação ×1,3 deixou o rosto alaranjado e foi descartada.
- Aplicada no material `Pescador` (corpo) e no `ShoulderCloth` (ombros, pelo shader).
- Renders: o padrão vermelho e branco dos ombros ficou mais nítido, e o camuflado ganhou contraste. O corpo continua escuro, como na referência.
- Ainda não verificado: os óculos (material `Lentes fumê`) e a sola branca do tênis. Ficaram para a próxima etapa.

## Óculos e tênis (etapa 7)

- Óculos (`Lentes fumê`): o material usava a textura `Rosto`, que dava um cinza com reflexo fraco. Agora, em tempo de execução, as lentes usam cor preta (0,03), rugosidade 0,12 e especularidade metálica 0,8, o que dá o preto brilhante da referência. Verificado no close-up da frente.
- Tênis: a sola branca nas bordas aparece nos renders das vistas dos pés. Confere com a referência. Nenhuma alteração foi feita.
- Novas vistas `feet_front` e `feet_side` adicionadas a `validacao/render_views.gd`.
- Diferença observada: a calça tem manchas de camuflagem mais evidentes que a calça preta cargo da referência. Não foi corrigida nesta etapa.
