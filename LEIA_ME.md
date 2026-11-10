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
| `Idle_Referencia` | Repouso com as mãos semifechadas, como na folha de referência. Criada pela cena ao carregar. |
| `Idle` | Repouso original, com as mãos abertas. |
| `Grip_Rod` | Fecha as mãos para segurar a vara. |
| `Rig_Mobility`, `Shoulder_Abduction`, `Shoulder_Stress` | Testes de movimento do rig. |

## O que a cena ajusta

No `pescador_v29.glb`, só o UV de alguns triângulos da roupa foi corrigido. A malha, o rig e as
animações são os originais da V29. Os demais ajustes são aplicados por `pescador_scene.gd`
quando a cena carrega:

- **Cabelo cacheado** (`hair_curls.gd`): touca de cabelo presa ao osso da cabeça.
- **Ombros** (`shoulder_corrective.gd`): corretivo automático, sem a ombreira saliente.
- **Roupa** (`pescador_v29_Roupa_ajustada.png`): atlas refeito, sem riscos nem fundo, com mais contraste.
- **Capuz por trás** (`pescador_v29_Rosto_ajustado.png`): camuflado no lugar do borrão escuro.
- **Calça cargo escura** (`pants_darken.gdshader` + `pants_mask.png`).
- **Lentes escuras** dos óculos.
- **Mãos semifechadas** na animação `Idle_Referencia`.

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
python3 validacao/ferramentas/comparar_referencia.py CAMINHO/folha_de_referencia.png
```

As texturas ajustadas são geradas por `python3 validacao/ferramentas/gerar_texturas.py`
(requer Pillow e NumPy). A correção de UV do `.glb` é feita uma vez por
`python3 validacao/ferramentas/corrigir_uv_glb.py`.
