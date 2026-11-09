# Pescador V29 — mais volume nas mãos

Copie a pasta `pescador_v29` inteira para a raiz do seu projeto e instancie:

`res://pescador_v29/PescadorCorrigido.tscn`

Use essa cena para manter a correção automática dos ombros da V27. Testado no Godot 4.4.1, Compatibility. A cena requer SkeletonModifier3D, disponível a partir do Godot 4.3.

## Ajuste desta versão

A V29 dá mais volume à palma e aos dedos. O comprimento de 14,2 cm foi mantido. A largura passou de aproximadamente 8,7 para 9,6 cm e a espessura máxima de 3,45 para 4,39 cm. A transição no punho permanece gradual, sem alterar o encaixe da manga.

O ajuste é gradual junto ao punho, preservando os vértices de encaixe da manga e a posição dos ossos das mãos. As posições de repouso das 15 articulações dos dedos de cada lado e as matrizes de ligação do esqueleto foram atualizadas para a geometria nova. Os pesos e as conexões da malha foram mantidos.

Rosto, roupa, óculos, ombros, corpo e texturas mantêm os dados da V28. O esqueleto continua com 68 ossos e os seis auxiliares automáticos dos ombros.

## Conferência

Foram conferidos os dados preservados, os pesos e a ligação da malha aos ossos. No Godot 4.4.1 foram testados o repouso e quatro momentos da flexão dos dedos. A prévia compara as duas versões em enquadramentos de mesma escala e mostra a flexão real no motor. Os resultados estão em `validacao/`.

As animações incluídas continuam sendo `Idle`, `Grip_Rod`, `Rig_Mobility`, `Shoulder_Abduction` e `Shoulder_Stress`. O AnimationPlayer está em `Model/AnimationPlayer` dentro da cena corrigida.

O projeto `demo_validacao_godot.zip` deve ser extraído em uma pasta separada. Abra seu `project.godot` para observar os movimentos. Teclas 1 a 5 alternam animações; espaço pausa; setas giram o personagem.
