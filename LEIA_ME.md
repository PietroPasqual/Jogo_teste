# Pescador V29 — modelo para Godot

Personagem pescador rigado (68 ossos), ajustado para ficar fiel à folha de referência.
Este repositório é um projeto Godot 4.4 completo: abra o `project.godot` para ver a demo.

## Como usar no seu jogo

1. Copie a pasta `pescador_v29` inteira para a raiz do seu projeto Godot (4.3 ou mais novo).
2. Instancie a cena `res://pescador_v29/PescadorCorrigido.tscn`.
3. O `AnimationPlayer` fica em `Model/AnimationPlayer`.

Use sempre a cena `PescadorCorrigido.tscn`, não o `.glb` direto. É ela que aplica os ajustes abaixo.

## Animações

| Animação | Uso |
|---|---|
| `Idle_Referencia` | Repouso da folha de referência: punhos soltos, palmas viradas para as coxas, braços junto do tronco. Criada pela cena ao carregar. |
| `Idle` | Repouso original, com as mãos abertas. |
| `Grip_Rod` | Fecha as mãos para segurar a vara. |
| `Rig_Mobility`, `Shoulder_Abduction`, `Shoulder_Stress` | Testes de movimento do rig. |

### Usar animações de outras bibliotecas

O arquivo `pescador_v29/pescador_bone_map.tres` mapeia o esqueleto para o perfil humanoide do
Godot. Para usar: selecione `pescador_v29.glb`, abra a aba Import, clique em Advanced, selecione
o `Skeleton3D` e, em Retarget, escolha esse arquivo como Bone Map. Faça isso em uma cópia do
modelo: o retarget muda a pose de repouso, e o corretivo de ombro foi calculado para a pose original.

## O que a cena ajusta

O `pescador_v29.glb` foi remodelado em relação à V29 original: mãos novas em blocos facetados,
mangas mais cheias, tênis mais encorpados, aba do chapéu reta e capuz mais alto. O esqueleto e
as animações são os originais. Os demais ajustes são aplicados por `pescador_scene.gd` quando a
cena carrega:

- **Cabelo cacheado** (`hair_curls.gd`): touca de cabelo presa ao osso da cabeça.
- **Ombros** (`shoulder_corrective.gd`): corretivo automático, sem a ombreira saliente.
- **Roupa** (`pescador_v29_Roupa_ajustada.png`): atlas refeito, sem riscos nem fundo, com mais contraste.
- **Capuz por trás** (`pescador_v29_Rosto_ajustado.png`): camuflado no lugar do borrão escuro.
- **Calça cargo escura** (`pants_darken.gdshader` + `pants_mask.png`).
- **Lentes escuras** dos óculos.
- **Pose da referência** na animação `Idle_Referencia`.

## Demo

Abra o projeto e rode (F5). Teclas 1 a 6 trocam a animação, espaço pausa, setas giram o personagem.

## Validação

O resultado completo está em [VALIDACAO_REFERENCIA.md](VALIDACAO_REFERENCIA.md).
Para repetir, na raiz do repositório, com Godot 4.4.1:

```
python3 validacao/ferramentas/validar_glb.py              # malha, pesos e animações do .glb
godot --path . --headless --import                        # importa o projeto
godot --path . -s validacao/validate_rig.gd               # rig no motor
godot --path . -s validacao/render_views.gd               # vistas da referência
godot --path . -s validacao/render_poses.gd               # poses das animações
godot --path . -s validacao/teste_articulacoes.gd         # teste de esforço das articulações
godot --path . -s validacao/render_silhueta.gd            # silhuetas em projeção ortográfica
python3 validacao/ferramentas/comparar_silhueta.py CAMINHO/folha_de_referencia.png
python3 validacao/ferramentas/comparar_referencia.py CAMINHO/folha_de_referencia.png
```

As texturas ajustadas são geradas por `python3 validacao/ferramentas/gerar_texturas.py`
(requer Pillow e NumPy). As alterações no `.glb` foram feitas, nesta ordem, por `corrigir_uv_glb.py`,
`remodelar_maos.py` e `remodelar_corpo.py` (todos em `validacao/ferramentas/`).
