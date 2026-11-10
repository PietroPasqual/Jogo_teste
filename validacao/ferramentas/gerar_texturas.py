"""Gera as texturas auxiliares do Pescador de forma reproduzivel.

Uso: python3 validacao/ferramentas/gerar_texturas.py  (a partir da raiz do repositorio)

- pescador_v29_Roupa_ajustada.png: atlas da roupa refeito a partir do original:
  sem o fundo e a pele que a roupa amostrava por engano, com as amostras de cor
  solida de uv_amostras.json, e com contraste e nitidez ajustados.
- pescador_v29_Rosto_ajustado.png: atlas da cabeca com a parte de tras do capuz
  repintada com camuflado.
- hair_curls_albedo.png: tufos recortados de cabelo, nos tons medidos na referencia.
- pants_mask.png: mascara da calca no espaco UV do atlas Roupa, calculada na pose
  de repouso pelos pesos dos ossos das pernas. Nao depende da animacao.
"""
import json
import struct
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

PASTA = "pescador_v29/"
AMOSTRAS = "validacao/ferramentas/uv_amostras.json"
# Caixas em pixels do atlas Roupa (x0, y0, x1, y1).
CAPUZ_ORIGEM = (720, 1248, 960, 1322)   # camuflado do capuz no close-up de costas
CAPUZ_ORIGEM_GRANDE = (700, 1238, 1000, 1330)
CAPUZ_DESTINO = (752, 198, 910, 254)    # area que o capuz amostra na vista de costas


def _abrir_glb():
    """Abre o .glb e devolve o JSON e uma funcao que le um acessor."""
    with open(PASTA + "pescador_v29.glb", "rb") as f:
        f.read(12)
        n, _ = struct.unpack("<II", f.read(8))
        gltf = json.loads(f.read(n))
        n, _ = struct.unpack("<II", f.read(8))
        binario = f.read(n)
    comp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    tipos = {5121: "u1", 5123: "u2", 5125: "u4", 5126: "f4"}

    def acessor(i):
        a = gltf["accessors"][i]
        bv = gltf["bufferViews"][a["bufferView"]]
        k = comp[a["type"]]
        dt = np.dtype(tipos[a["componentType"]])
        inicio = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        passo = bv.get("byteStride", k * dt.itemsize)
        bruto = np.frombuffer(binario, dtype=np.uint8, count=(a["count"] - 1) * passo + k * dt.itemsize, offset=inicio)
        linhas = np.lib.stride_tricks.as_strided(bruto, shape=(a["count"], k * dt.itemsize), strides=(passo, 1))
        return np.ascontiguousarray(linhas).view(dt).reshape(a["count"], k)

    return gltf, acessor


def _glb():
    """Le do .glb os dados do corpo: posicoes, UVs, triangulos e osso dominante."""
    gltf, acessor = _abrir_glb()
    prims = gltf["meshes"][0]["primitives"]
    corpo = prims[0]
    pos = acessor(corpo["attributes"]["POSITION"]).astype(float)
    uv = acessor(corpo["attributes"]["TEXCOORD_0"]).astype(float)
    juntas = acessor(corpo["attributes"]["JOINTS_0"]).astype(int)
    pesos = acessor(corpo["attributes"]["WEIGHTS_0"]).astype(float)
    nomes = [gltf["nodes"][j]["name"] for j in gltf["skins"][0]["joints"]]
    dominante = np.array([nomes[juntas[i, pesos[i].argmax()]] for i in range(len(pos))])
    # Corpo (0) e tecido do ombro (4) usam os mesmos vertices.
    indices = np.concatenate([acessor(prims[i]["indices"]).ravel().reshape(-1, 3) for i in (0, 4)]).astype(int)
    return pos, uv, indices, dominante


def _triangulos_com_area(uv, indices, largura, altura):
    px = uv[indices] * [largura, altura]
    area = np.abs((px[:, 1, 0] - px[:, 0, 0]) * (px[:, 2, 1] - px[:, 0, 1]) - (px[:, 1, 1] - px[:, 0, 1]) * (px[:, 2, 0] - px[:, 0, 0])) / 2
    return area >= 0.5


def _amostras():
    with open(AMOSTRAS, encoding="utf-8") as f:
        return json.load(f)


def _fundo(p):
    """Fundo cinza-azulado da folha de referencia."""
    azulado = (p[..., 2] - p[..., 0] >= 4) & (p[..., 1] >= p[..., 0] - 2)
    # Na borda da silhueta o fundo vem misturado com a roupa e fica cinza neutro.
    # A roupa nao tem cinza neutro nessa faixa de brilho: o camuflado e marrom,
    # o colete e mais escuro, e o ziper e as fivelas sao mais claros.
    soma = p[..., 0] + p[..., 1] + p[..., 2]
    neutro = (p.max(-1) - p.min(-1) <= 9) & (p[..., 2] >= p[..., 0] - 3) & (soma >= 115) & (soma <= 260)
    return azulado | neutro


def _pele(p):
    # Limiares apertados: o peixe do logo e bege claro e nao pode entrar aqui.
    return (p[..., 0] > 110) & (p[..., 0] > p[..., 2] + 70) & (p[..., 1] > p[..., 2] + 20)


def _preencher(imagem, ruim, passos=80):
    """Troca os pixels ruins pela media dos vizinhos bons, de fora para dentro."""
    img = imagem.astype(float)
    bom = ~ruim
    for _ in range(passos):
        if bom.all():
            break
        soma = np.zeros_like(img)
        conta = np.zeros(bom.shape)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b = np.roll(bom, (dy, dx), (0, 1))
            soma += np.roll(img, (dy, dx), (0, 1)) * b[..., None]
            conta += b
        novos = ~bom & (conta > 0)
        img[novos] = soma[novos] / conta[novos][:, None]
        bom = bom | novos
    return img


def _vertices_da_calca(pos, dominante):
    perna = np.array([d.startswith(("thigh", "shin")) for d in dominante])
    quadril = np.array([d == "root" for d in dominante]) & (pos[:, 1] < CINTURA_Y)
    return perna | quadril


def roupa():
    """Refaz o atlas da roupa a partir do original.

    1. Limpa o que a roupa amostrava por engano: fundo da folha e pele.
       (O mapa UV nao acompanha a silhueta da referencia, entao mangas, capuz
       e barras pegavam o fundo cinza e partes do corpo.)
    2. Pinta as amostras de cor solida dos triangulos corrigidos por
       corrigir_uv_glb.py.
    3. Aumenta contraste e nitidez, preservando os tons de pele das maos.
    """
    original = Image.open(PASTA + "pescador_v29_Roupa.jpg").convert("RGB")
    largura, altura = original.size
    o = np.asarray(original).astype(int)
    pos, uv, indices, dominante = _glb()
    mao = np.array([d.startswith(("hand", "finger", "thumb")) for d in dominante])
    com_area = _triangulos_com_area(uv, indices, largura, altura)
    e_mao = mao[indices].sum(1) >= 2

    cobertura = Image.new("L", (largura, altura), 0)
    d = ImageDraw.Draw(cobertura)
    for tri in indices[com_area & ~e_mao]:
        d.polygon([(float(uv[v, 0]) * largura, float(uv[v, 1]) * altura) for v in tri], fill=255)
    interior = np.asarray(cobertura.filter(ImageFilter.MinFilter(25))) > 0
    cobertura = np.asarray(cobertura.filter(ImageFilter.MaxFilter(5))) > 0
    # Pele com sombra (maos da folha) so e procurada perto da borda dos recortes
    # e fora deles: no interior ela se confunde com o bege do peixe do logo.
    pele_ampla = (o[..., 0] > 85) & (o[..., 0] > o[..., 2] + 30) & (o[..., 1] > o[..., 2] + 6) & (o[..., 0] - o[..., 1] < 85)
    estranho = _fundo(o) | _pele(o) | (pele_ampla & ~interior)
    ruim = cobertura & estranho
    # Faces laterais (tronco, quadril) ficam espremidas em uma coluna de poucos
    # pixels na borda do desenho, onde ha fundo, mao e sombra. Essa coluna e
    # refeita a partir da roupa vizinha.
    tri3 = pos[indices]
    area3 = np.linalg.norm(np.cross(tri3[:, 1] - tri3[:, 0], tri3[:, 2] - tri3[:, 0]), axis=1) / 2
    px = uv[indices] * [largura, altura]
    area2 = np.abs((px[:, 1, 0] - px[:, 0, 0]) * (px[:, 2, 1] - px[:, 0, 1]) - (px[:, 1, 1] - px[:, 0, 1]) * (px[:, 2, 0] - px[:, 0, 0])) / 2
    densidade = area2 / np.maximum(area3, 1e-12)
    esticado = com_area & ~e_mao & (densidade < 0.4 * np.median(densidade[com_area]))
    faixa = Image.new("L", (largura, altura), 0)
    d = ImageDraw.Draw(faixa)
    for tri in indices[esticado]:
        d.polygon([(float(uv[v, 0]) * largura, float(uv[v, 1]) * altura) for v in tri], fill=255, outline=255)
    ruim |= cobertura & (np.asarray(faixa.filter(ImageFilter.MaxFilter(5))) > 0)
    # Margem de 1 pixel: a borda do fundo vem misturada com a roupa.
    ruim = np.asarray(Image.fromarray((ruim * 255).astype("uint8")).filter(ImageFilter.MaxFilter(3))) > 0
    ruim &= cobertura
    limpo = _preencher(o, ruim | (~cobertura & estranho))
    limpo = np.where(cobertura[..., None], limpo, o).astype(int)

    # Capuz por tras: a area amostrada era a sombra sob o capuz, quase preta.
    # Recebe o camuflado do proprio capuz, copiado do close-up de costas do atlas.
    x0, y0, x1, y1 = CAPUZ_DESTINO
    tecido = original.crop(CAPUZ_ORIGEM).resize((x1 - x0, y1 - y0), Image.LANCZOS)
    peso = np.ones((y1 - y0, x1 - x0))
    borda = 8
    rampa = np.linspace(0.0, 1.0, borda)
    peso[-borda:, :] *= rampa[::-1][:, None]
    peso[:6, :] *= np.linspace(0.0, 1.0, 6)[:, None]
    peso[:, :borda] *= rampa[None, :]
    peso[:, -borda:] *= rampa[::-1][None, :]
    peso = peso[..., None]
    limpo[y0:y1, x0:x1] = (np.asarray(tecido).astype(float) * peso + limpo[y0:y1, x0:x1] * (1 - peso)).astype(int)

    # Amostras de cor solida.
    dados = _amostras()
    celula = dados["celula_px"]
    cor_padrao = np.median(limpo[cobertura], axis=0)
    calca_v = _vertices_da_calca(pos, dominante)
    cobertura_calca = Image.new("L", (largura, altura), 0)
    d = ImageDraw.Draw(cobertura_calca)
    for tri in indices[com_area & (calca_v[indices].sum(1) >= 2)]:
        d.polygon([(float(uv[v, 0]) * largura, float(uv[v, 1]) * altura) for v in tri], fill=255)
    cor_calca = np.median(limpo[np.asarray(cobertura_calca) > 0], axis=0)
    for amostra in dados["amostras"]:
        e_pele = mao[amostra["vertices"]].mean() > 0.5
        pontos = []
        for ax, ay, bx, by in amostra["linhas_originais_px"]:
            n = int(max(abs(bx - ax), abs(by - ay))) + 2
            xs = np.clip(np.linspace(ax, bx, n).round().astype(int), 0, largura - 1)
            ys = np.clip(np.linspace(ay, by, n).round().astype(int), 0, altura - 1)
            pontos.append(o[ys, xs])
        pontos = np.concatenate(pontos)
        if e_pele:
            validos = pontos[_pele(pontos)]
            cor = np.median(validos if len(validos) else pontos, axis=0)
        else:
            # Tolerancia maior aqui: a borda do fundo vem misturada e parece cinza.
            quase_fundo = pontos[:, 2] - pontos[:, 0] >= 0
            validos = pontos[~quase_fundo & ~_pele(pontos)]
            # Com poucos pixels de roupa na linha, a mediana nao e confiavel.
            e_calca = calca_v[amostra["vertices"]].mean() > 0.5
            reserva = cor_calca if e_calca else cor_padrao
            cor = np.median(validos, axis=0) if len(validos) >= 0.6 * len(pontos) else reserva
        cx, cy = amostra["centro_px"]
        x0, y0 = int(cx - celula / 2), int(cy - celula / 2)
        limpo[y0:y0 + celula, x0:x0 + celula] = cor

    base = Image.fromarray(limpo.astype("uint8"))
    ajustada = ImageEnhance.Contrast(base).enhance(1.12)
    # Sem aumento de saturacao: o vermelho medido ja fica no tom da referencia.
    ajustada = ajustada.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
    # Pele: mantem os pixels sem ajuste para nao alterar o tom das maos.
    pele = _pele(limpo)
    mascara = Image.fromarray((pele * 255).astype("uint8")).filter(ImageFilter.MaxFilter(5))
    mascara = mascara.filter(ImageFilter.GaussianBlur(1.5))
    Image.composite(base, ajustada, mascara).save(PASTA + "pescador_v29_Roupa_ajustada.png")


def rosto():
    """Refaz a parte de tras do capuz no atlas Rosto.

    Essa faixa do atlas era um borrao escuro com manchas esverdeadas. Recebe o
    camuflado do proprio capuz, copiado do close-up de costas do atlas Roupa.
    O resto do atlas (rosto, chapeu, oculos) fica identico.
    """
    atlas = Image.open(PASTA + "pescador_v29_Rosto.png").convert("RGB")
    largura, altura = atlas.size
    gltf, acessor = _abrir_glb()
    cabeca = gltf["meshes"][0]["primitives"][1]
    pos = acessor(cabeca["attributes"]["POSITION"]).astype(float)
    uv = acessor(cabeca["attributes"]["TEXCOORD_0"]).astype(float)
    indices = acessor(cabeca["indices"]).ravel().reshape(-1, 3).astype(int)
    centro = pos[indices].mean(1)
    capuz = (centro[:, 1] < 1.56) & (centro[:, 2] < -0.06)
    mascara = Image.new("L", (largura, altura), 0)
    d = ImageDraw.Draw(mascara)
    for tri in indices[capuz]:
        d.polygon([(float(uv[v, 0]) * largura, float(uv[v, 1]) * altura) for v in tri], fill=255)
    caixa = mascara.getbbox()
    mascara = mascara.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(2))
    tecido = Image.open(PASTA + "pescador_v29_Roupa.jpg").convert("RGB").crop(CAPUZ_ORIGEM_GRANDE)
    tecido = tecido.resize((caixa[2] - caixa[0], caixa[3] - caixa[1]), Image.LANCZOS)
    tecido = ImageEnhance.Contrast(tecido).enhance(1.12)
    tecido = tecido.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
    camada = atlas.copy()
    camada.paste(tecido, (caixa[0], caixa[1]))
    Image.composite(camada, atlas, mascara).save(PASTA + "pescador_v29_Rosto_ajustado.png")


def cabelo():
    random.seed(20260907)
    largura, altura = 512, 256
    tons = [(17, 12, 12), (21, 15, 15), (26, 18, 17), (33, 23, 21)]
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, largura, int(altura * 0.62)], fill=tons[1] + (255,))

    def tufo(cx, cy, r, cor):
        n = random.randint(5, 7)
        giro = random.uniform(0, math.tau)
        pontos = []
        for i in range(n * 2):
            a = giro + math.pi * i / n
            rr = r * (1.0 if i % 2 == 0 else random.uniform(0.45, 0.7))
            pontos.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        d.polygon(pontos, fill=cor + (255,))

    # Massa do cabelo: tufos em poucos tons, sem brilhos pontuais.
    for _ in range(1500):
        x = random.randint(-12, largura + 12)
        y = random.randint(0, int(altura * 0.78))
        tufo(x, y, random.uniform(7, 15), random.choice(tons[:3] + tons[:2]))
    # Borda inferior recortada: tufos mais esparsos em direcao a nuca.
    for _ in range(700):
        x = random.randint(-12, largura + 12)
        y = random.randint(int(altura * 0.6), altura)
        t = (y - altura * 0.6) / (altura * 0.4)
        if random.random() < 0.15 + 0.6 * t:
            continue
        tufo(x, y, random.uniform(9, 17), random.choice(tons))
    # Faz a textura repetir sem emenda na horizontal.
    faixa = 24
    esquerda = img.crop((0, 0, faixa, altura))
    img.paste(esquerda, (largura - faixa, 0), Image.linear_gradient("L").rotate(90).resize((faixa, altura)))
    img.save(PASTA + "hair_curls_albedo.png")


def calca():
    """Rasteriza no espaco UV os triangulos do corpo que pertencem a calca."""
    pos, uv, indices, dominante = _glb()
    calca_v = _vertices_da_calca(pos, dominante)
    largura, altura = 768, 896
    mascara = Image.new("L", (largura, altura), 0)
    d = ImageDraw.Draw(mascara)
    # Pecas de cor solida (um unico ponto do atlas) ficam fora desta etapa.
    com_area = _triangulos_com_area(uv, indices, largura, altura)
    for tri in indices[com_area & (calca_v[indices].sum(1) >= 2)]:
        d.polygon([(float(uv[v, 0]) * largura, float(uv[v, 1]) * altura) for v in tri], fill=255)
    mascara = mascara.filter(ImageFilter.GaussianBlur(0.6))
    # Amostras de cor solida que pertencem a calca (barras e cos).
    dados = _amostras()
    escala = largura / dados["atlas"][0]
    meia = dados["celula_px"] * escala / 2
    d = ImageDraw.Draw(mascara)
    for amostra in dados["amostras"]:
        if calca_v[amostra["vertices"]].mean() > 0.5:
            cx, cy = amostra["centro_px"][0] * escala, amostra["centro_px"][1] * escala
            d.rectangle([cx - meia, cy - meia, cx + meia - 1, cy + meia - 1], fill=255)
    mascara.save(PASTA + "pants_mask.png")


CINTURA_Y = 0.96


if __name__ == "__main__":
    roupa()
    rosto()
    cabelo()
    calca()
    print("texturas geradas")
