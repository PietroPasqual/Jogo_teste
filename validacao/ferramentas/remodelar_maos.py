"""Reconstroi a malha das maos do Pescador como blocos facetados.

Uso (na raiz do repositorio):
    python3 validacao/ferramentas/remodelar_maos.py

As maos originais eram lisas, com dedos finos. Na folha de referencia elas sao
blocos facetados, como o resto do personagem. Este script troca a primitiva das
maos no .glb por uma malha nova, gerada a partir das posicoes dos ossos:

- palma e cinco dedos em secoes de retangulo chanfrado, com faces planas;
- cada falange presa ao seu osso, com mistura de pesos nas juntas;
- tres tons de pele por face (claro, medio, escuro), tirados das amostras de
  pele que ja existem no atlas Roupa, para marcar as facetas e separar os dedos.

O esqueleto, as animacoes e as outras primitivas nao mudam. O script pode ser
rodado de novo: ele sempre substitui a primitiva das maos inteira.
"""
import json
import struct
import sys

import numpy as np

GLB = "pescador_v29/pescador_v29.glb"
PRIMITIVA_MAOS = 3
ATLAS = (1536.0, 1792.0)
# Centros, em pixels, das amostras de pele do atlas Roupa.
TONS = {"claro": (1152.0, 1010.0), "medio": (1202.0, 1010.0), "escuro": (1180.0, 1010.0)}

# Meia largura e meia espessura (m) na base de cada dedo, e comprimento da ponta.
DEDOS = {
    "finger_index": (0.0089, 0.0104, 0.021),
    "finger_middle": (0.0090, 0.0108, 0.023),
    "finger_ring": (0.0088, 0.0103, 0.021),
    "finger_little": (0.0080, 0.0092, 0.018),
}
POLEGAR = (0.0118, 0.0110, 0.024)
CHANFRO = 0.3


def carregar(caminho):
    with open(caminho, "rb") as f:
        dados = f.read()
    n = struct.unpack_from("<I", dados, 12)[0]
    gltf = json.loads(dados[20:20 + n])
    inicio = 20 + n + 8
    tamanho = struct.unpack_from("<I", dados, 20 + n)[0]
    return gltf, dados[inicio:inicio + tamanho]


def salvar(caminho, gltf, binario, trocas):
    """Regrava o .glb, trocando o conteudo das bufferViews em `trocas`."""
    novo = bytearray()
    for i, bv in enumerate(gltf["bufferViews"]):
        bloco = trocas[i] if i in trocas else binario[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
        novo += b"\0" * (-len(novo) % 4)
        bv["byteOffset"] = len(novo)
        bv["byteLength"] = len(bloco)
        novo += bloco
    novo += b"\0" * (-len(novo) % 4)
    gltf["buffers"][0]["byteLength"] = len(novo)
    texto = json.dumps(gltf, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    texto += b" " * (-len(texto) % 4)
    total = 12 + 8 + len(texto) + 8 + len(novo)
    with open(caminho, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<I4s", len(texto), b"JSON"))
        f.write(texto)
        f.write(struct.pack("<I4s", len(novo), b"BIN\0"))
        f.write(novo)


def posicoes_dos_ossos(gltf):
    """Posicao global de cada osso no repouso (os nos so tem translacao)."""
    nos = gltf["nodes"]
    pai = {}
    for i, no in enumerate(nos):
        assert "rotation" not in no and "scale" not in no, "no com rotacao/escala: " + no.get("name", "?")
        for filho in no.get("children", []):
            pai[filho] = i
    posicoes = {}
    for j in gltf["skins"][0]["joints"]:
        p, i = np.zeros(3), j
        while i is not None:
            p += np.array(nos[i].get("translation", [0, 0, 0]), dtype=float)
            i = pai.get(i)
        posicoes[nos[j]["name"]] = p
    return posicoes


def unitario(v):
    return v / np.linalg.norm(v)


class Malha:
    """Acumula faces planas: cada face tem seus proprios vertices."""

    def __init__(self):
        self.pos, self.pesos, self.tons, self.faces = [], [], [], []

    def face(self, pontos, pesos, centro, tom=None):
        """Poligono convexo; a normal aponta para fora de `centro`."""
        pontos = [np.asarray(p, dtype=float) for p in pontos]
        normal = np.zeros(3)
        for i in range(1, len(pontos) - 1):
            normal += np.cross(pontos[i] - pontos[0], pontos[i + 1] - pontos[0])
        if np.linalg.norm(normal) < 1e-12:
            return
        if np.dot(normal, np.mean(pontos, axis=0) - centro) < 0:
            pontos, pesos = pontos[::-1], pesos[::-1]
            normal = -normal
        base = len(self.pos)
        self.pos += pontos
        self.pesos += pesos
        self.tons += [tom] * len(pontos)
        for i in range(1, len(pontos) - 1):
            self.faces.append((base, base + i, base + i + 1))


def anel(centro, eixo, lateral, meia_largura, meia_espessura):
    """Retangulo chanfrado (8 pontos) perpendicular a `eixo`."""
    u = unitario(lateral - np.dot(lateral, eixo) * eixo)
    n = unitario(np.cross(u, eixo))
    cw, ct = meia_largura * CHANFRO, meia_espessura * CHANFRO
    w, t = meia_largura, meia_espessura
    cantos = [(w, t - ct), (w - cw, t), (-(w - cw), t), (-w, t - ct), (-w, -(t - ct)), (-(w - cw), -t), (w - cw, -t), (w, -(t - ct))]
    return [centro + u * a + n * b for a, b in cantos]


def tubo(malha, aneis, tampa_inicio=True, tampa_fim=True):
    """Liga aneis consecutivos. Cada anel: (pontos, pesos)."""
    for (a, pa), (b, pb) in zip(aneis[:-1], aneis[1:]):
        centro = np.mean(a + b, axis=0)
        for i in range(8):
            j = (i + 1) % 8
            malha.face([a[i], a[j], b[j], b[i]], [pa, pa, pb, pb], centro)
    centro = np.mean([p for pontos, _ in aneis for p in pontos], axis=0)
    if tampa_inicio:
        malha.face(aneis[0][0], [aneis[0][1]] * 8, centro)
    if tampa_fim:
        malha.face(aneis[-1][0], [aneis[-1][1]] * 8, centro)


def construir_mao(ossos, lado):
    """Malha da mao direita (lado 'R') ou esquerda ('L') no espaco do modelo."""
    s = "." + lado
    espelho = np.array([1.0 if lado == "R" else -1.0, 1.0, 1.0])
    # Trabalha sempre como mao direita e espelha no fim.
    pos = {nome[:-2]: p * espelho for nome, p in ossos.items() if nome.endswith(s)}
    punho = pos["hand"]
    X, Y, Z = np.eye(3)
    malha = Malha()

    def so(osso):
        return {osso + s: 1.0}

    def meio(a, b):
        return {a + s: 0.5, b + s: 0.5}

    # Palma: do punho (dentro do punho da manga) ate a linha dos nos dos dedos.
    nos_dedos = [pos[d + "_01"] for d in DEDOS]
    centro_nos = np.mean(nos_dedos, axis=0)
    x_min = min(p[0] for p in nos_dedos) - 0.0085
    x_max = max(p[0] for p in nos_dedos) + 0.0092
    desce = unitario(centro_nos - punho)
    palma = [
        (anel(punho - desce * 0.016, desce, X, 0.0255, 0.0170), so("hand")),
        (anel(punho + desce * 0.006, desce, X, 0.0290, 0.0190), so("hand")),
        (anel(punho + desce * 0.030 + X * 0.001, desce, X, 0.0365, 0.0200), so("hand")),
        (anel(np.array([(x_min + x_max) / 2, centro_nos[1] + 0.004, centro_nos[2]]), desce, X, (x_max - x_min) / 2, 0.0170), so("hand")),
    ]
    tubo(malha, palma)

    def dedo(nome, meia_largura, meia_espessura, ponta, lateral, base_dentro):
        p1, p2, p3 = pos[nome + "_01"], pos[nome + "_02"], pos[nome + "_03"]
        d1, d2 = unitario(p2 - p1), unitario(p3 - p2)
        p4 = p3 + d2 * ponta
        d12, d23 = unitario(d1 + d2), d2
        w, t = meia_largura, meia_espessura
        o1, o2, o3 = nome + "_01", nome + "_02", nome + "_03"
        aneis = [
            (anel(p1 - d1 * base_dentro, d1, lateral, w, t), so("hand")),
            (anel(p1, d1, lateral, w * 1.03, t * 1.05), meio("hand", o1)),
            (anel(p1 + (p2 - p1) * 0.5, d1, lateral, w, t), so(o1)),
            (anel(p2, d12, lateral, w * 1.0, t * 1.07), meio(o1, o2)),
            (anel(p2 + (p3 - p2) * 0.5, d2, lateral, w * 0.95, t * 0.95), so(o2)),
            (anel(p3, d23, lateral, w * 0.94, t * 1.0), meio(o2, o3)),
            (anel(p3 + (p4 - p3) * 0.6, d2, lateral, w * 0.9, t * 0.88), so(o3)),
            (anel(p4, d2, lateral, w * 0.68, t * 0.6), so(o3)),
        ]
        tubo(malha, aneis)

    for nome, (w, t, ponta) in DEDOS.items():
        dedo(nome, w, t, ponta, X, 0.008)
    # O polegar sai pela lateral da palma; sua "largura" fica no eixo Z.
    dedo("thumb", POLEGAR[0], POLEGAR[1], POLEGAR[2], Z, 0.016)

    pontos = np.array(malha.pos) * espelho
    faces = np.array(malha.faces)
    if lado == "L":
        faces = faces[:, ::-1]
    return pontos, malha.pesos, faces


def tons_das_faces(pontos, faces, nomes_dos_pesos):
    """Tom de pele por face, pela direcao da normal no repouso e pela falange.

    As falanges alternam de tom no dorso, e as laterais entre os dedos ficam
    escuras: e isso que desenha os dedos e as juntas, como na referencia.
    """
    uv = np.zeros((len(pontos), 2))
    normais = np.zeros((len(pontos), 3))
    for face in faces:
        a, b, c = pontos[face]
        n = unitario(np.cross(b - a, c - a))
        nomes = [nome for v in face for nome in nomes_dos_pesos[v]]
        e_dedo = any("finger" in nome for nome in nomes)
        e_polegar = any("thumb" in nome for nome in nomes)
        falange_do_meio = any("_02" in nome for nome in nomes) and not any("_01" in nome for nome in nomes)
        lado_de_fora = n[0] * (1.0 if np.mean(pontos[face][:, 0]) < 0 else -1.0)
        if n[1] < -0.75:
            tom = "escuro"                      # pontas e faces de baixo
        elif e_dedo and abs(n[0]) > 0.6:
            tom = "escuro"                      # laterais: separam um dedo do outro
        elif n[2] > 0.45:
            tom = "medio" if (e_dedo and falange_do_meio) else "claro"   # dorso
        elif n[2] < -0.45:
            tom = "escuro" if (e_dedo and falange_do_meio) else "medio"  # palma
        elif e_polegar:
            tom = "claro" if n[1] > 0.2 else "medio"
        else:
            tom = "claro" if lado_de_fora > 0.5 else "medio"   # bordas da palma
        for v in face:
            normais[v] = n
            uv[v] = (TONS[tom][0] / ATLAS[0], TONS[tom][1] / ATLAS[1])
    return uv, normais


def main():
    gltf, binario = carregar(GLB)
    ossos = posicoes_dos_ossos(gltf)
    indice_do_osso = {gltf["nodes"][j]["name"]: i for i, j in enumerate(gltf["skins"][0]["joints"])}

    todas_pos, todos_pesos, todas_faces = [], [], []
    for lado in ("R", "L"):
        pontos, pesos, faces = construir_mao(ossos, lado)
        todas_faces.append(faces + sum(len(p) for p in todas_pos))
        todas_pos.append(pontos)
        todos_pesos += pesos
    pontos = np.concatenate(todas_pos)
    faces = np.concatenate(todas_faces)
    uv, normais = tons_das_faces(pontos, faces, todos_pesos)

    juntas = np.zeros((len(pontos), 4), dtype="<u2")
    pesos = np.zeros((len(pontos), 4), dtype="<f4")
    for v, mistura in enumerate(todos_pesos):
        for k, (nome, peso) in enumerate(mistura.items()):
            juntas[v, k] = indice_do_osso[nome]
            pesos[v, k] = peso

    prim = gltf["meshes"][0]["primitives"][PRIMITIVA_MAOS]
    blocos = {
        "POSITION": pontos.astype("<f4"),
        "NORMAL": normais.astype("<f4"),
        "TEXCOORD_0": uv.astype("<f4"),
        "JOINTS_0": juntas,
        "WEIGHTS_0": pesos,
    }
    trocas = {}
    for nome, bloco in blocos.items():
        acc = gltf["accessors"][prim["attributes"][nome]]
        acc["count"] = len(pontos)
        acc.pop("byteOffset", None)
        trocas[acc["bufferView"]] = bloco.tobytes()
        if nome == "POSITION":
            acc["min"] = [float(v) for v in bloco.min(0)]
            acc["max"] = [float(v) for v in bloco.max(0)]
    acc = gltf["accessors"][prim["indices"]]
    acc["count"] = int(faces.size)
    acc["componentType"] = 5123
    acc.pop("byteOffset", None)
    assert len(pontos) < 65535
    trocas[acc["bufferView"]] = faces.astype("<u2").tobytes()
    gltf["asset"].setdefault("extras", {})["maos"] = "blocos facetados (remodelar_maos.py)"
    salvar(GLB, gltf, binario, trocas)
    print(f"maos reconstruidas: {len(pontos)} vertices, {len(faces)} triangulos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
