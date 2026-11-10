"""Corrige o UV dos triangulos do corpo que amostravam uma unica linha do atlas.

Uso (na raiz do repositorio):
    python3 validacao/ferramentas/corrigir_uv_glb.py

Problema: 554 triangulos da roupa (topos de ombro, barras, laterais de bolso,
solas) tinham os tres vertices sobre uma mesma linha do atlas Roupa. Cada um
aparecia como um borrao riscado. Aqui cada grupo desses triangulos passa a
apontar para uma amostra de cor solida propria, em uma area livre do atlas.

So os valores de TEXCOORD_0 desses vertices mudam no .glb. Posicoes, normais,
pesos, ossos, animacoes e o tamanho do arquivo ficam identicos.

A lista das amostras (com as linhas originais, usadas para escolher a cor) e
gravada em uv_amostras.json. O script e idempotente: se o .glb ja estiver
corrigido, nao faz nada.
"""
import json
import struct
import sys

import numpy as np

GLB = "pescador_v29/pescador_v29.glb"
AMOSTRAS = "validacao/ferramentas/uv_amostras.json"
LARGURA, ALTURA = 1536, 1792  # tamanho do atlas Roupa
# Grade de amostras em uma area do atlas que nenhum triangulo usa.
ORIGEM_X, ORIGEM_Y, CELULA, COLUNAS = 1040, 1100, 16, 24
PRIMITIVAS_ROUPA = (0, 4)  # corpo e tecido do ombro: compartilham os vertices


def main():
    with open(GLB, "rb") as f:
        dados = bytearray(f.read())
    n_json = struct.unpack_from("<I", dados, 12)[0]
    gltf = json.loads(dados[20:20 + n_json])
    inicio_bin = 20 + n_json + 8
    prims = gltf["meshes"][0]["primitives"]
    assert prims[0]["attributes"]["TEXCOORD_0"] == prims[4]["attributes"]["TEXCOORD_0"]

    def faixa(i):
        a = gltf["accessors"][i]
        bv = gltf["bufferViews"][a["bufferView"]]
        assert "byteStride" not in bv
        return inicio_bin + bv.get("byteOffset", 0) + a.get("byteOffset", 0), a

    def ler(i, dtype, comp):
        pos, a = faixa(i)
        return np.frombuffer(dados, dtype=dtype, count=a["count"] * comp, offset=pos).reshape(a["count"], comp)

    acc_uv = prims[0]["attributes"]["TEXCOORD_0"]
    uv = ler(acc_uv, "<f4", 2).astype(np.float64)
    tipos_indice = {5123: "<u2", 5125: "<u4"}
    linhas = []
    for pi in PRIMITIVAS_ROUPA:
        a = gltf["accessors"][prims[pi]["indices"]]
        idx = ler(prims[pi]["indices"], tipos_indice[a["componentType"]], 1).reshape(-1, 3).astype(int)
        px = uv[idx] * [LARGURA, ALTURA]
        area = np.abs((px[:, 1, 0] - px[:, 0, 0]) * (px[:, 2, 1] - px[:, 0, 1]) - (px[:, 1, 1] - px[:, 0, 1]) * (px[:, 2, 0] - px[:, 0, 0])) / 2
        extensao = (px.max(1) - px.min(1)).max(1)
        for tri in idx[(area < 0.5) & (extensao >= 0.5)]:
            linhas.append([int(v) for v in tri])
    if not linhas:
        print("nenhum triangulo em linha: o .glb ja esta corrigido")
        return 0

    # Triangulos que compartilham vertices precisam da mesma amostra.
    pai = {}

    def raiz(v):
        while pai.setdefault(v, v) != v:
            pai[v] = pai[pai[v]]
            v = pai[v]
        return v

    for tri in linhas:
        for v in tri[1:]:
            pai[raiz(v)] = raiz(tri[0])
    grupos = {}
    for tri in linhas:
        grupos.setdefault(raiz(tri[0]), []).append(tri)

    amostras = []
    novo_uv = uv.copy()
    for celula, (_, tris) in enumerate(sorted(grupos.items())):
        cx = ORIGEM_X + (celula % COLUNAS) * CELULA + CELULA / 2
        cy = ORIGEM_Y + (celula // COLUNAS) * CELULA + CELULA / 2
        vertices = sorted({v for tri in tris for v in tri})
        segmentos = []
        for tri in tris:
            p = uv[tri] * [LARGURA, ALTURA]
            a, b = p[p[:, 0].argmin() if np.ptp(p[:, 0]) >= np.ptp(p[:, 1]) else p[:, 1].argmin()], p[p[:, 0].argmax() if np.ptp(p[:, 0]) >= np.ptp(p[:, 1]) else p[:, 1].argmax()]
            segmentos.append([round(float(a[0]), 2), round(float(a[1]), 2), round(float(b[0]), 2), round(float(b[1]), 2)])
        amostras.append({"celula": celula, "centro_px": [cx, cy], "vertices": vertices, "linhas_originais_px": segmentos})
        novo_uv[vertices] = [cx / LARGURA, cy / ALTURA]

    pos, a = faixa(acc_uv)
    antes = len(dados)
    dados[pos:pos + a["count"] * 8] = novo_uv.astype("<f4").tobytes()
    assert len(dados) == antes
    with open(GLB, "wb") as f:
        f.write(dados)
    with open(AMOSTRAS, "w", encoding="utf-8") as f:
        json.dump({"atlas": [LARGURA, ALTURA], "celula_px": CELULA, "amostras": amostras}, f)
    print(f"{len(linhas)} triangulos em {len(amostras)} amostras; {sum(len(s['vertices']) for s in amostras)} vertices com UV novo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
