# Bosque Vivo — primeiro protótipo

Um jogo 3D em primeira pessoa sobre cuidar de uma pequena família de espíritos do bosque. Inspirado no tema geral de cuidado e crescimento de uma comunidade, com personagens, cenário e regras próprios. Esta é uma base jogável feita só com formas geradas pelo Unity; nenhum pacote ou asset externo é necessário.

## Abrir

1. Instale **Unity 6.3 LTS** no Unity Hub. O projeto foi preparado para um projeto **3D (Built-In Render Pipeline)**.
2. Extraia o ZIP e use **Add project from disk** no Unity Hub, escolhendo a pasta `prototipo-bosque-vivo`.
3. Se o editor pedir uma versão de Unity diferente, abra com sua versão instalada da linha 6.3.
4. Em **Edit → Project Settings → Player → Other Settings → Active Input Handling**, selecione **Input Manager (Old)** ou **Both**. Reinicie o editor se solicitado.
5. Espere a compilação terminar. No menu superior, clique em **Bosque Vivo → Criar cena do protótipo**. Abra `Assets/Scenes/BosqueVivo.unity` e pressione **Play**.

O menu de criação de cena gera o nível inicial no editor e o mundo, os recursos e os personagens ao entrar no modo Play. Se o projeto abrir sem uma cena, basta usar o menu citado acima.

## Controles

| Tecla | Ação |
| --- | --- |
| WASD | Caminhar |
| Mouse | Olhar |
| E | Coletar madeira ou frutas ao mirar em um recurso próximo |
| F | Alimentar os moradores que estão com fome |
| B | Construir um lugar para dormir (3 madeiras) |
| N | Encerrar o dia |
| Esc | Soltar ou capturar o cursor |

No começo há 3 moradores, 2 camas, 5 frutas e 3 madeiras. À noite, a fome aumenta, a falta de camas reduz o ânimo, e um novo morador chega se o ânimo estiver alto. Você vence ao chegar ao dia 7 com a comunidade ativa; perde se o ânimo chegar a zero. Os recursos voltam a crescer a cada manhã.

## Estrutura

- `Assets/Scripts/PrototypeWorld.cs`: ciclo de dias, recursos, moradores, regras e interface temporária.
- `Assets/Scripts/FirstPersonWalker.cs`: câmera e movimento em primeira pessoa.
- `Assets/Scripts/ResourcePickup.cs`: recursos interativos.
- `Assets/Editor/CreatePrototypeScene.cs`: comando que cria e salva a cena de entrada.
- `DESIGN.md`: visão do jogo e etapas após o protótipo.

## Estado

O código foi revisado estaticamente, mas **não foi executado no Unity neste ambiente**. Este protótipo serve para validar o ciclo principal; as formas e a interface são provisórias. Uma próxima etapa é testar no editor, corrigir eventuais diferenças da sua versão e substituir as formas por uma direção visual definida com você.

