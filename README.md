# Bosque Vivo — protótipo v0.2

Um jogo 3D em primeira pessoa sobre cuidar de uma pequena família de espíritos do bosque. Inspirado no tema geral de cuidado e crescimento de uma comunidade, com personagens, cenário e regras próprios. Esta é uma base jogável feita só com formas geradas pelo Unity; nenhum pacote ou asset externo é necessário.

## Abrir

1. Use **Unity 6.3 LTS (6000.3.25f1)** no Unity Hub. O projeto usa o **Built-In Render Pipeline**.
2. Se baixou o ZIP do GitHub, extraia e selecione a pasta **`Jogo_teste-main`** em **Add project from disk**. A pasta correta contém `Assets`, `Packages` e `ProjectSettings`.
3. Se o Hub mostrar um aviso de versão ausente para um ZIP antigo, escolha a instalação **6000.3.25f1** ou baixe o ZIP atualizado do repositório.
4. Em **Edit → Project Settings → Player → Other Settings → Active Input Handling**, selecione **Input Manager (Old)** ou **Both**. Reinicie o editor se solicitado.
5. Espere a compilação terminar. No menu superior, clique em **Bosque Vivo → Criar cena do protótipo**. Abra `Assets/Scenes/BosqueVivo.unity` e pressione **Play**.

O menu de criação de cena gera o nível inicial no editor e o mundo, os recursos e os personagens ao entrar no modo Play. Se o projeto abrir sem uma cena, basta usar o menu citado acima.

## Controles

| Tecla | Ação |
| --- | --- |
| WASD | Caminhar |
| Shift | Correr |
| Mouse | Olhar |
| E | Coletar madeira ou frutas ao mirar em um recurso próximo |
| F | Alimentar os moradores que estão com fome |
| B | Construir um lugar para dormir (3 madeiras) |
| G | Construir uma horta (4 madeiras; produz 3 frutas por manhã; limite de 3) |
| N | Encerrar o dia |
| Esc | Soltar ou capturar o cursor |
| R | Recomeçar depois da vitória ou derrota |

No começo há 3 moradores, 2 camas, 5 frutas e 3 madeiras. Cada morador começa com fome leve. À noite, a fome aumenta; quem já estiver com fome alta sofrerá, e a falta de camas reduz o ânimo. A previsão na interface mostra exatamente a perda de ânimo da próxima noite. Um novo morador chega se o ânimo estiver em pelo menos 50. Você vence ao chegar ao dia 7 com a comunidade ativa; perde se o ânimo chegar a zero. Os recursos voltam a crescer a cada manhã.

O progresso é salvo localmente ao coletar, alimentar, construir, atravessar a noite, suspender ou fechar o jogo. Isso inclui quais recursos já foram coletados no dia. Ao reabrir, a partida é retomada; após terminar, use **R** ou o botão **Recomeçar** para apagar a partida salva e tentar de novo. Durante a partida, não há botão de apagar o progresso por acidente.

## Estrutura

- `Assets/Scripts/PrototypeWorld.cs`: ciclo de dias, recursos, moradores, regras e interface temporária.
- `Assets/Scripts/FirstPersonWalker.cs`: câmera e movimento em primeira pessoa.
- `Assets/Scripts/ResourcePickup.cs`: recursos interativos.
- `Assets/Scripts/ResidentVisual.cs`: movimento leve dos moradores.
- `Assets/Editor/CreatePrototypeScene.cs`: comando que cria e salva a cena de entrada.
- `DESIGN.md`: visão do jogo e etapas após o protótipo.

## Estado

O código foi revisado estaticamente, mas **não foi executado no Unity neste ambiente**. Este protótipo serve para validar o ciclo principal; as formas e a interface são provisórias. Uma próxima etapa é testar no editor, corrigir eventuais diferenças da sua versão e substituir as formas por uma direção visual definida com você.
