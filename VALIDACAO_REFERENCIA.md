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
