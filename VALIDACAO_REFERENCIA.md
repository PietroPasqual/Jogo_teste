# Validação do Pescador V29 contra a referência

Estado em 10/11/2026, com Godot 4.4.1 (Compatibility). Todas as verificações abaixo foram
executadas, e os relatórios estão em `validacao/`.

## Resultado

| Verificação | Resultado | Relatório |
|---|---|---|
| Malha do `.glb` (geometria, pesos, UVs, animações, texturas) | Passou, sem erros nem avisos | `validation_report_glb.json` |
| Rig no motor (68 ossos, poses, seções do ombro, 6 animações, mapa de ossos) | Passou | `validation_report_godot_4_4_1.json` |
| Cores contra a folha de referência (6 regiões) | Todas dentro da tolerância | `color_report.json` |
| Demo (`project.godot`) | Abre e roda sem erros | — |

### Malha do `.glb`

- 5 primitivas, 71.157 vértices no total e 18.916 triângulos. Nenhum triângulo degenerado.
- Normais unitárias, UVs dentro de 0..1, pesos somando 1 em todos os vértices, nenhum vértice sem peso.
- 68 ossos, 5 animações com tempos em ordem e rotações unitárias, 2 texturas embutidas íntegras.
- Altura do personagem: 1,886 m, com os pés em y = 0.
- No `.glb`, só o UV de 1.336 vértices da roupa foi alterado (ver "Textura refeita"). Posições, normais, pesos, ossos, animações e o tamanho do arquivo são idênticos ao original da V29.

### Rig no motor

- Erro máximo de posição dos ossos: 0,00000018 m. Erro máximo de ângulo: 0,00098 rad.
- Seções do ombro sem esticar: razão de área entre 0,9999995 e 1,0000003.
- As 5 animações originais e a `Idle_Referencia` foram amostradas em 12 instantes cada, sem valores inválidos.
- Texturas do cabelo e da roupa carregadas como recursos importados, então funcionam no jogo exportado.

### Cores medidas (mediana RGB, folha de referência × render)

| Região | Referência | Modelo | Diferença máxima |
|---|---|---|---|
| Rosto | 158, 94, 62 | 166, 100, 66 | 8 |
| Mãos | 162, 98, 70 | 173, 109, 76 | 11 |
| Cabelo | 20, 14, 15 | 19, 12, 12 | 3 |
| Lentes | 18, 15, 17 | 17, 12, 14 | 3 |
| Calça | 30, 25, 28 | 29, 24, 24 | 4 |
| Vermelho do casaco | 140, 28, 34 | 151, 29, 37 | 11 |

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
  6 cm em torno de cada junta, sem cortes duros. Os pesos e os ossos do `.glb` não foram alterados.
- **Defeito encontrado e corrigido:** com o braço fora do lugar, aparecia uma placa cinza com um
  triângulo cor de pele na lateral do tronco e do quadril. Não era da malha: essas faces laterais
  amostram uma coluna de poucos pixels na borda do desenho, onde a folha tem fundo e mão. O atlas
  ajustado agora refaz essas colunas com a cor da roupa.
- **Mapa de ossos humanoide:** `pescador_v29/pescador_bone_map.tres` mapeia 53 ossos para o perfil
  humanoide do Godot, para reaproveitar animações de outras bibliotecas. O validador confere que
  cada osso mapeado existe e que os lados não estão trocados. O mapa não foi testado com uma
  biblioteca de animações externa.

## Diferenças que continuam

O modelo está próximo da referência, mas não idêntico. O que ainda difere:

- **Chapéu:** a aba é mais larga e mais caída que a da referência, e o logo de peixe fica mais alto.
- **Capuz:** mais baixo e menos volumoso atrás do pescoço.
- **Cabelo:** a silhueta é mais lisa. A referência tem cachos mais volumosos e recortados.
- **Proporções:** os braços ficam mais afastados do corpo e as pernas mais abertas, por causa da pose de repouso do rig.
- **Bolsos da calça:** menos destacados que os bolsos cargo da referência.

Essas diferenças são da geometria do `.glb`. Corrigi-las exige remodelar a malha em um programa
de modelagem (por exemplo, o Blender), o que não foi feito aqui.

## Arquivos

- `validacao/imagens/comparacao/`: referência × render, lado a lado.
- `validacao/imagens/renders/`: vistas e poses renderizadas.
- `validacao/godot_4_4_1.json` e `validacao/ajuste_das_maos.json`: relatórios originais do autor da V29.
- `validacao/expected.json`: poses esperadas pelo autor, usadas por `validate_rig.gd`.
