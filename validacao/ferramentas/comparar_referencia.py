"""Monta comparacoes lado a lado (referencia | render) e mede cores.

Uso (na raiz do repositorio, depois de rodar validacao/render_views.gd):
    python3 validacao/ferramentas/comparar_referencia.py CAMINHO/folha_de_referencia.png

A folha de referencia e a imagem de 1254x1254 com as quatro vistas de corpo
inteiro e os close-ups. As imagens saem em validacao/imagens/comparacao/ e as
cores medidas em validacao/color_report.json.
"""
import json
import sys

import numpy as np
from PIL import Image

RENDERS = "validacao/imagens/renders/"
SAIDA = "validacao/imagens/comparacao/"
RELATORIO = "validacao/color_report.json"
TOLERANCIA = 22  # diferenca maxima por canal (0-255) para considerar a cor igual


def ajustar(im, altura):
    return im.resize((int(im.width * altura / im.height), altura), Image.LANCZOS)


def lado_a_lado(a, b, nome, altura=900):
    a, b = ajustar(a, altura), ajustar(b, altura)
    tela = Image.new("RGB", (a.width + b.width + 10, altura), (255, 0, 255))
    tela.paste(a, (0, 0))
    tela.paste(b, (a.width + 10, 0))
    tela.save(SAIDA + nome)


def mediana(imagem, caixa, filtro=None):
    x0, y0, x1, y1 = caixa
    pixels = np.asarray(imagem).astype(int)[y0:y1, x0:x1].reshape(-1, 3)
    if filtro is not None:
        pixels = pixels[filtro(pixels)]
    return [int(v) for v in np.median(pixels, axis=0)] if len(pixels) else None


def pele(p):
    return (p[:, 0] > 110) & (p[:, 0] > p[:, 2] + 40)


def escuro(p):
    return p.sum(1) < 200


def vermelho(p):
    return (p[:, 0] > 120) & (p[:, 1] < 70) & (p[:, 2] < 80)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    ref = Image.open(sys.argv[1]).convert("RGB")
    if ref.size != (1254, 1254):
        print("aviso: a folha de referencia esperada tem 1254x1254; os recortes podem ficar deslocados")

    def render(nome):
        return Image.open(RENDERS + nome).convert("RGB")

    corpo = (400, 60, 720, 820)
    cabeca = (180, 0, 960, 700)
    lado_a_lado(ref.crop((60, 25, 345, 775)), render("render_front.png").crop(corpo), "frente.png")
    lado_a_lado(ref.crop((560, 25, 800, 775)), render("render_back.png").crop(corpo), "costas.png")
    lado_a_lado(ref.crop((375, 25, 540, 775)), render("render_side.png").crop(corpo), "lado.png")
    lado_a_lado(ref.crop((1012, 22, 1242, 365)), render("render_head_front.png").crop(cabeca), "cabeca_frente.png", 700)
    lado_a_lado(ref.crop((690, 790, 1000, 1150)), render("render_head_back.png").crop(cabeca), "cabeca_costas.png", 700)
    lado_a_lado(ref.crop((1015, 385, 1240, 665)), render("render_head_three_quarter.png").crop(cabeca), "cabeca_3_4.png", 700)

    frente, cab_frente, cab_costas = render("render_front.png"), render("render_head_front.png"), render("render_head_back.png")
    medidas = {
        "rosto": (mediana(ref, (1060, 200, 1200, 330), pele), mediana(cab_frente, (420, 250, 720, 420), pele)),
        "maos": (mediana(ref, (60, 400, 345, 480), pele), mediana(frente, (430, 430, 700, 500), pele)),
        "cabelo": (mediana(ref, (740, 870, 960, 1010), escuro), mediana(cab_costas, (450, 150, 680, 300), escuro)),
        "lentes": (mediana(ref, (1065, 175, 1195, 205), escuro), mediana(cab_frente, (470, 185, 690, 240), escuro)),
        # Uma coxa so, para nao pegar o fundo entre as pernas.
        "calca": (mediana(ref, (165, 470, 210, 550)), mediana(frente, (505, 500, 540, 590))),
        "vermelho_do_casaco": (mediana(ref, (60, 150, 345, 420), vermelho), mediana(frente, (430, 200, 700, 430), vermelho)),
    }
    relatorio, tudo_ok = {}, True
    for nome, (r, m) in medidas.items():
        diferenca = max(abs(a - b) for a, b in zip(r, m)) if r and m else None
        ok = diferenca is not None and diferenca <= TOLERANCIA
        tudo_ok = tudo_ok and ok
        relatorio[nome] = {"referencia_rgb": r, "render_rgb": m, "diferenca_maxima": diferenca, "dentro_da_tolerancia": ok}
        print(f"{nome:20s} referencia={r} render={m} diferenca={diferenca} {'OK' if ok else 'DIFERENTE'}")
    relatorio["tolerancia_por_canal"] = TOLERANCIA
    relatorio["todas_dentro_da_tolerancia"] = tudo_ok
    with open(RELATORIO, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    print("COLOR_CHECK_PASS" if tudo_ok else "COLOR_CHECK_DIFF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
