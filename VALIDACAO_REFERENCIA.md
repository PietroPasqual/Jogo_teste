# Validação do Pescador V29 contra a referência

Estado em 10/11/2026, com Godot 4.4.1 (Compatibility). Todas as verificações abaixo foram
executadas, e os relatórios estão em `validacao/`.

## Resultado

| Verificação | Resultado | Relatório |
|---|---|---|
| Malha do `.glb` (geometria, pesos, UVs, animações, texturas) | Passou, sem erros nem avisos | `validation_report_glb.json` |
| Rig no motor (68 ossos, poses, seções do ombro, 6 animações, mapa de ossos) | Passou | `validation_report_godot_4_4_1.json` |
| Cores contra a folha de referência (6 regiões) | Todas dentro da tolerância | `color_report.json` |
| Silhueta contra a folha de referência (frente, lado, costas) | Frente dentro de 10%, exceto as mãos (ver abaixo) | `silhouette_report.json` |
| Demo (`project.godot`) | Abre e roda sem erros | — |

### Malha do `.glb`

- 5 primitivas, 66.833 vértices no total e 17.960 triângulos. Nenhum triângulo degenerado.
- Normais unitárias, UVs dentro de 0..1, pesos somando 1 em todos os vértices, nenhum vértice sem peso.
- 68 ossos, 5 animações com tempos em ordem e rotações unitárias, 2 texturas embutidas íntegras.
- Altura do personagem: 1,886 m, com os pés em y = 0.
- O `.glb` foi remodelado (ver "Remodelagem da malha"): mãos novas, mangas, tênis, aba do chapéu e capuz. O esqueleto, os pesos das partes mantidas e as animações são os originais da V29.

### Rig no motor

- Erro máximo de posição dos ossos: 0,00000018 m. Erro máximo de ângulo: 0,00098 rad.
- Seções do ombro sem esticar: razão de área entre 0,9999995 e 1,0000003.
- As 5 animações originais e a `Idle_Referencia` foram amostradas em 12 instantes cada, sem valores inválidos.
- Texturas do cabelo e da roupa carregadas como recursos importados, então funcionam no jogo exportado.

### Cores medidas (mediana RGB, folha de referência × render)

| Região | Referência | Modelo | Diferença máxima |
|---|---|---|---|
| Rosto | 158, 94, 62 | 166, 100, 66 | 8 |
| Mãos | 162, 98, 70 | 169, 106, 74 | 8 |
| Cabelo | 20, 14, 15 | 19, 12, 12 | 3 |
| Lentes | 18, 15, 17 | 17, 12, 14 | 3 |
| Calça | 30, 25, 28 | 29, 24, 24 | 4 |
| Vermelho do casaco | 140, 28, 34 | 149, 28, 35 | 9 |

Tolerância usada: 22 por canal (escala 0–255).

## O que foi corrigido nesta revisão

A comparação lado a lado com a folha de referência (`validacao/imagens/comparacao/`) mostrou
problemas que as etapas anteriores não tinham pegado:

1. **Ombreiras salientes.** O corretivo de ombro somava 5,5 cm de volume com os braços abaixados,
   o que criava "ombreiras" que não existem na referência. O volume (`BULGE`) foi zerado.
   Com os braços levantados nada muda, porque esse volume já sumia nessa pose.
2. **Texturas que falhariam no jogo exportado.** A roupa e o cabelo eram lidos com
   `Image.load_from_file`, e o Godot avisava que isso não funciona após exportar. Agora são
   recursos importados, com caminho relativo à pasta do script.
3. **Calça dependia da pose.** O shader escurecia por posição do vértice, então a região mudava
   com a animação e pegava os tênis. Agora usa uma máscara fixa no espaço UV (`pants_mask.png`),
   calculada pelos pesos dos ossos das pernas.
4. **Cabelo.** A textura tinha pontos claros e as lentes estavam mais pretas que a referência.
   O cabelo foi refeito com tufos recortados nos tons medidos, com mais volume nas laterais.
5. **Tom das mãos.** O ajuste de contraste alterava a pele das mãos. Os tons de pele do atlas
   agora são preservados.
6. **Mãos abertas.** A referência tem as mãos semifechadas. A cena cria a animação
   `Idle_Referencia`, igual ao `Idle` com os dedos parcialmente fechados.
7. **Iluminação dos renders.** As texturas já trazem o sombreado da referência pintado. Com luz
   forte, o modelo ficava mais claro que a folha. Os renders e a demo usam luz quase neutra.

O volume do ombro também foi a única mudança que afeta os dados do autor: os 6 ossos auxiliares
`shoulder_deform_*` ficam 5,46 cm mais para dentro do que em `validacao/expected.json`. Isso é
intencional, e o validador reporta esse valor à parte.

## Textura refeita

A textura da roupa é a própria folha de referência projetada sobre o corpo, e o mapa UV não
acompanha a silhueta do desenho. Isso causava três defeitos, agora corrigidos:

1. **Riscos em topos de ombro, barras, laterais de bolso e solas.** 554 triângulos tinham os três
   vértices sobre uma mesma linha do atlas, então apareciam como borrões riscados.
   `corrigir_uv_glb.py` aponta cada grupo para uma amostra de cor sólida própria (384 amostras,
   em uma área livre do atlas). É a única mudança no `.glb`.
2. **Roupa amostrando o fundo e a pele da folha.** O atlas ajustado troca esses pixels pela cor
   da roupa vizinha.
3. **Capuz por trás escuro e com manchas esverdeadas.** A faixa correspondente do atlas `Rosto`
   foi repintada com o camuflado do próprio capuz (`pescador_v29_Rosto_ajustado.png`).

Os atlas originais continuam no repositório. Tudo é gerado por
`validacao/ferramentas/gerar_texturas.py`.

**Limite que continua:** a resolução. O corpo inteiro ocupa cerca de 285 pixels de largura por
vista no atlas (uns 425 pixels por metro), então de perto o camuflado fica suave. Melhorar isso
exige pintar um atlas novo em resolução maior, não só tratar o existente.

## Articulações e animações

`validacao/teste_articulacoes.gd` aplica 12 poses fortes direto nos ossos (cotovelos a 110°,
agachamento, braços à frente e acima, arremesso, passo largo, tronco inclinado e torcido, cabeça,
punhos, torção de punho e de tornozelo) e renderiza cada uma em dois ângulos
(`validacao/imagens/articulacoes/`).

- **Resultado:** cotovelos, joelhos, ombros, quadril, tronco, pescoço, punhos e tornozelos
  dobram sem quebras, buracos nem vértices soltos. Os pesos se misturam numa faixa de cerca de
  6 cm em torno de cada junta, sem cortes duros. O teste foi repetido depois da remodelagem,
  com as mãos novas.
- **Defeito encontrado e corrigido:** com o braço fora do lugar, aparecia uma placa cinza com um
  triângulo cor de pele na lateral do tronco e do quadril. Não era da malha: essas faces laterais
  amostram uma coluna de poucos pixels na borda do desenho, onde a folha tem fundo e mão. O atlas
  ajustado agora refaz essas colunas com a cor da roupa.
- **Mapa de ossos humanoide:** `pescador_v29/pescador_bone_map.tres` mapeia 53 ossos para o perfil
  humanoide do Godot, para reaproveitar animações de outras bibliotecas. O validador confere que
  cada osso mapeado existe e que os lados não estão trocados. O mapa não foi testado com uma
  biblioteca de animações externa.

## Remodelagem da malha

A comparação anterior era só de cores. Sobrepondo a silhueta do modelo à da folha
(`validacao/imagens/silhueta/`), as diferenças de forma ficaram mensuráveis, e a malha do `.glb`
foi alterada para reduzi-las.

### Mãos (`remodelar_maos.py`)

As mãos originais eram lisas, com dedos finos, abertas e com a palma virada para trás. Na folha
elas são blocos facetados, em punho solto, com a palma virada para a coxa.

- A malha das mãos foi reconstruída do zero a partir das posições dos ossos: palma e cinco dedos
  em blocos chanfrados de faces planas, 2.624 vértices e 1.360 triângulos (eram 6.948 e 2.316).
- Cada falange é presa ao seu osso, com mistura de pesos nas juntas. As animações de dedos
  (`Grip_Rod`, `Rig_Mobility`) continuam funcionando sem alteração.
- Três tons de pele por face, tirados das amostras de pele do próprio atlas, desenham as facetas
  e separam os dedos.
- A animação `Idle_Referencia` fecha os dedos em punho solto e gira antebraço e mão (35° + 50°)
  para a palma ficar virada para a coxa.

### Corpo e cabeça (`remodelar_corpo.py`)

- **Mangas:** 15% mais cheias do cotovelo ao punho, e braços 2,5° mais junto do tronco na
  `Idle_Referencia`. O vão entre braço e tronco, que a folha não tem, praticamente fechou.
- **Tênis:** mais largos, altos e compridos, como as botas da folha.
- **Aba do chapéu:** era ondulada e caía mais de um lado. Agora é reta, firme e quase circular,
  um pouco mais alta na frente para mostrar a franja e os óculos.
- **Capuz:** 6% mais alto atrás e dos lados, junto da nuca.
- **Cabelo:** mais volume lateral sob a aba.

O ombro não foi tocado, porque o corretivo de ombro foi calculado para a forma original.

### Largura da silhueta, vista de frente (modelo ÷ referência)

| Altura | Razão |
|---|---|
| Copa do chapéu | 0,92 |
| Aba do chapéu | 0,97 |
| Rosto | 0,90 |
| Ombros | 1,04 |
| Peito | 1,06 |
| Cintura | 1,04 |
| Mãos | 0,82 |
| Coxas | 1,01 |
| Joelhos | 1,04 |
| Canelas | 0,99 |
| Pés | 1,04 |

A largura na altura das mãos ficou 18% menor: os punhos do modelo ficam um pouco mais altos e
mais junto das coxas que os da folha.

Na vista de costas as razões ficam entre 0,93 e 1,28, e na de lado entre 0,81 e 1,20. Na folha,
a figura de costas é desenhada mais estreita que a de frente, então um mesmo modelo 3D não
consegue coincidir com as duas ao mesmo tempo. A vista de frente foi a usada como alvo.

## Diferenças que continuam

O modelo está mais próximo da referência, mas não idêntico. O que ainda difere:

- **Textura:** o camuflado é a própria folha projetada sobre o corpo, em baixa resolução (cerca
  de 425 pixels por metro). De perto fica suave, sem os polígonos nítidos da folha. Um filtro
  para deixar as facetas chapadas foi testado e descartado, porque apagava o logo e as fivelas.
- **Mãos:** são blocos facetados, mas mais simples que as da folha, que têm facetas esculpidas à mão.
- **Rosto:** o queixo do modelo é mais longo e estreito, e os óculos são maiores.
- **Capuz:** menos volumoso que o da folha, que forma um rolo grosso em volta do pescoço.
- **Cabelo:** silhueta mais lisa que os cachos recortados da folha.
- **Bolsos da calça:** menos destacados que os bolsos cargo da folha.
- **Vista lateral:** as costas e o capuz do modelo avançam cerca de 2 cm além da folha.

O que resta é escultura fina (rosto, capuz, bolsos) e pintura de textura. Isso pede um programa
de modelagem, como o Blender, e uma textura nova pintada em resolução maior.

## Arquivos

- `validacao/imagens/comparacao/`: referência × render, lado a lado.
- `validacao/imagens/silhueta/`: silhueta do modelo com o contorno da referência por cima.
- `validacao/imagens/articulacoes/`: poses do teste de esforço.
- `validacao/imagens/renders/`: vistas e poses renderizadas.
- `validacao/godot_4_4_1.json` e `validacao/ajuste_das_maos.json`: relatórios originais do autor da V29.
- `validacao/expected.json`: poses esperadas pelo autor, usadas por `validate_rig.gd`.
