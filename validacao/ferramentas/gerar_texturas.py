"""Gera as texturas auxiliares do Pescador de forma reproduzivel.

Uso: python3 validacao/ferramentas/gerar_texturas.py  (a partir da raiz do repositorio)

- pescador_v29_Roupa_ajustada.png: contraste e nitidez do camuflado, preservando
  os tons de pele originais (as maos usam um unico texel de pele deste atlas).
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


def roupa():
    original = Image.open(PASTA + "pescador_v29_Roupa.jpg").convert("RGB")
    ajustada = ImageEnhance.Contrast(original).enhance(1.12)
    # Sem aumento de saturacao: o vermelho medido ja fica no tom da referencia.
    ajustada = ajustada.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
    # Pele: mantem os pixels originais para nao alterar o tom das maos.
    o = np.asarray(original).astype(int)
    pele = (o[..., 0] > 110) & (o[..., 0] > o[..., 2] + 40) & (o[..., 1] > o[..., 2])
    mascara = Image.fromarray((pele * 255).astype("uint8")).filter(ImageFilter.MaxFilter(5))
    mascara = mascara.filter(ImageFilter.GaussianBlur(1.5))
    Image.composite(original, ajustada, mascara).save(PASTA + "pescador_v29_Roupa_ajustada.png")


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

    prim = gltf["meshes"][0]["primitives"][0]
    pos = acessor(prim["attributes"]["POSITION"]).astype(float)
    uv = acessor(prim["attributes"]["TEXCOORD_0"]).astype(float)
    juntas = acessor(prim["attributes"]["JOINTS_0"]).astype(int)
    pesos = acessor(prim["attributes"]["WEIGHTS_0"]).astype(float)
    indices = acessor(prim["indices"]).ravel().reshape(-1, 3)
    nomes = [gltf["nodes"][j]["name"] for j in gltf["skins"][0]["joints"]]
    dominante = np.array([nomes[juntas[i, pesos[i].argmax()]] for i in range(len(pos))])
    perna = np.array([d.startswith(("thigh", "shin")) for d in dominante])
    quadril = np.array([d == "root" for d in dominante]) & (pos[:, 1] < CINTURA_Y)
    calca_v = perna | quadril
    largura, altura = 768, 896
    mascara = Image.new("L", (largura, altura), 0)
    d = ImageDraw.Draw(mascara)
    for tri in indices[calca_v[indices].sum(1) >= 2]:
        a, b, c = uv[tri]
        # Pecas de cor solida usam um unico ponto do atlas: ficam fora da mascara.
        if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < 1e-7:
            continue
        d.polygon([(float(uv[v, 0]) * largura, float(uv[v, 1]) * altura) for v in tri], fill=255)
    mascara.filter(ImageFilter.GaussianBlur(0.6)).save(PASTA + "pants_mask.png")


CINTURA_Y = 0.96


if __name__ == "__main__":
    roupa()
    cabelo()
    calca()
    print("texturas geradas")
