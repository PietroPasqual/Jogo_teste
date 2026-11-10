"""Ajusta a forma do corpo do Pescador para aproximar a silhueta da referencia.

Uso (na raiz do repositorio):
    python3 validacao/ferramentas/remodelar_corpo.py

Move vertices da primitiva do corpo no .glb, sem mudar pesos, UVs nem ossos:

- Mangas: mais cheias do cotovelo ao punho. Na folha de referencia nao ha vao
  entre o braco e o tronco; no modelo original havia.
- Tenis: mais largos, altos e compridos, como as botas da folha.
- Aba do chapeu: reta, firme e quase circular (era ondulada e caida de um lado).
- Capuz: um pouco mais alto atras e dos lados, junto da nuca.

O ombro nao e tocado, porque o corretivo de ombro (shoulder_corrective.gd) foi
calculado para a forma original dessa regiao.

O script grava em asset.extras o que aplicou e nao repete uma etapa ja
aplicada (cada ajuste e relativo a forma atual do arquivo).
"""
import sys

import numpy as np

from remodelar_maos import GLB, carregar, posicoes_dos_ossos, salvar

PRIMITIVA_CORPO = 0
PRIMITIVA_CABECA = 1
MANGA_GANHO = 0.15          # aumento do raio da manga
MANGA_INICIO, MANGA_CHEIA = 0.18, 0.45   # fracao do braco (0 = ombro, 1 = punho)
TENIS_LARGURA, TENIS_ALTURA, TENIS_COMPRIMENTO = 0.12, 0.12, 0.07
ABA_INICIO = 0.105          # raio (m) onde a aba comeca, na base da copa
ABA_RAIO, ABA_AVANCO = 0.180, 0.012   # raio da borda e quanto ela avanca na frente
ABA_ALTURA = 1.732          # altura (m) da borda nas laterais e atras
ABA_FRENTE = 0.032          # quanto a borda sobe na frente, para mostrar a franja
CAPUZ_ATRAS, CAPUZ_FRENTE = 0.06, 0.02


def suave(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ajustar_corpo(gltf, binario, ossos, nomes, trocas):
    prim = gltf["meshes"][0]["primitives"][PRIMITIVA_CORPO]
    acc_pos, pos = ler(gltf, binario, prim, "POSITION", "<f4", 3)
    _, juntas = ler(gltf, binario, prim, "JOINTS_0", "<u2", 4)
    _, pesos = ler(gltf, binario, prim, "WEIGHTS_0", "<f4", 4)
    pos = pos.astype(np.float64).copy()

    def peso_de(*ossos_alvo):
        indices = [nomes.index(o) for o in ossos_alvo]
        return (pesos * np.isin(juntas, indices)).sum(1)

    movidos = 0
    for lado in ("R", "L"):
        s = "." + lado
        # Mangas: afasta os vertices do eixo do braco.
        ombro, cotovelo, punho = ossos["upper_arm" + s], ossos["forearm" + s], ossos["hand" + s]
        w = peso_de("upper_arm" + s, "upper_arm_twist" + s, "forearm" + s, "forearm_twist" + s, "hand" + s)
        alvo = np.where(w > 0.01)[0]
        no_braco = ((pos[alvo] - ombro) @ (cotovelo - ombro)) / ((cotovelo - ombro) @ (cotovelo - ombro)) < 1.0
        # Cada vertice e tratado pelo trecho (braco ou antebraco) em que cai.
        for a, b, t0, t1, neste in ((ombro, cotovelo, 0.0, 0.5, no_braco), (cotovelo, punho, 0.5, 1.0, ~no_braco)):
            eixo = b - a
            v = alvo[neste]
            uc = np.clip(((pos[v] - a) @ eixo) / (eixo @ eixo), 0.0, 1.0)
            no_eixo = a + uc[:, None] * eixo
            t = t0 + uc * (t1 - t0)
            fator = 1.0 + MANGA_GANHO * w[v] * suave(MANGA_INICIO, MANGA_CHEIA, t)
            pos[v] = no_eixo + (pos[v] - no_eixo) * fator[:, None]
            movidos += int((fator > 1.0005).sum())

        # Tenis: mais largos, altos e compridos.
        w = peso_de("foot" + s, "toes" + s)
        v = np.where(w > 0.01)[0]
        centro_x = ossos["foot" + s][0]
        calcanhar_z = pos[v][w[v] > 0.9][:, 2].min()
        pos[v, 0] = centro_x + (pos[v, 0] - centro_x) * (1.0 + TENIS_LARGURA * w[v])
        pos[v, 1] = pos[v, 1] * (1.0 + TENIS_ALTURA * w[v] * suave(0.20, 0.10, pos[v, 1]))
        pos[v, 2] = calcanhar_z + (pos[v, 2] - calcanhar_z) * (1.0 + TENIS_COMPRIMENTO * w[v])
        movidos += len(v)

    gravar(acc_pos, pos, trocas)
    return f"mangas +{int(MANGA_GANHO * 100)}%, tenis mais encorpados ({movidos} vertices)"


def pecas(pos, indices):
    """Separa a primitiva em pecas ligadas (vertices na mesma posicao contam como um)."""
    _, inv = np.unique(np.round(pos, 4), axis=0, return_inverse=True)
    inv = inv.ravel()
    pai = np.arange(inv.max() + 1)

    def raiz(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for tri in inv[indices]:
        a = raiz(tri[0])
        pai[raiz(tri[1])] = a
        pai[raiz(tri[2])] = a
    return np.array([raiz(x) for x in inv])


def ajustar_cabeca(gltf, binario, ossos, nomes, trocas):
    prim = gltf["meshes"][0]["primitives"][PRIMITIVA_CABECA]
    acc_pos, pos = ler(gltf, binario, prim, "POSITION", "<f4", 3)
    acc_idx = gltf["accessors"][prim["indices"]]
    bv = gltf["bufferViews"][acc_idx["bufferView"]]
    tipo = {5123: "<u2", 5125: "<u4"}[acc_idx["componentType"]]
    indices = np.frombuffer(binario, dtype=tipo, count=acc_idx["count"], offset=bv.get("byteOffset", 0)).reshape(-1, 3).astype(int)
    pos = pos.astype(np.float64).copy()
    peca = pecas(pos, indices)
    usado = np.zeros(len(pos), bool)
    usado[indices.ravel()] = True

    # Chapeu: a peca que contem o ponto mais alto. A aba original era ondulada e
    # caia mais de um lado; na referencia ela e reta, firme e quase circular.
    topo = np.where(usado)[0][pos[usado, 1].argmax()]
    chapeu = np.where((peca == peca[topo]) & usado)[0]
    h = pos[chapeu]
    copa = h[h[:, 1] > h[:, 1].max() - 0.05]
    cx, cz = copa[:, 0].mean(), copa[:, 2].mean()
    r = np.hypot(h[:, 0] - cx, h[:, 2] - cz)
    angulo = np.arctan2(h[:, 0] - cx, h[:, 2] - cz)
    setores = 24
    setor = ((angulo + np.pi) / (2 * np.pi) * setores).astype(int) % setores
    raio_borda, altura_borda = np.zeros(setores), np.zeros(setores)
    for k in range(setores):
        m = setor == k
        raio_borda[k] = r[m].max()
        altura_borda[k] = h[m][r[m] > raio_borda[k] - 0.02][:, 1].mean()

    def no_angulo(valores):
        # Interpola entre os centros dos setores, para nao criar degraus.
        f = (angulo + np.pi) / (2 * np.pi) * setores - 0.5
        k0 = np.floor(f).astype(int)
        t = f - k0
        return valores[k0 % setores] * (1 - t) + valores[(k0 + 1) % setores] * t

    raio_antigo, altura_antiga = no_angulo(raio_borda), no_angulo(altura_borda)
    ao_longo = np.clip((r - ABA_INICIO) / (raio_antigo - ABA_INICIO), 0.0, 1.0)
    # Borda nova: circulo um pouco deslocado para a frente.
    frente = np.cos(angulo)
    raio_novo = ABA_RAIO + ABA_AVANCO * frente
    novo_r = np.where(r > ABA_INICIO, ABA_INICIO + (r - ABA_INICIO) * (raio_novo - ABA_INICIO) / (raio_antigo - ABA_INICIO), r)
    escala = np.where(r > 1e-6, novo_r / np.maximum(r, 1e-6), 1.0)
    pos[chapeu, 0] = cx + (h[:, 0] - cx) * escala
    pos[chapeu, 2] = cz + (h[:, 2] - cz) * escala
    altura_nova = ABA_ALTURA + ABA_FRENTE * (0.5 + 0.5 * frente) ** 2
    pos[chapeu, 1] = h[:, 1] + ao_longo * (altura_nova - altura_antiga)

    # Capuz: a peca que contem o ponto mais baixo. Sobe um pouco atras e dos
    # lados, onde a referencia mostra um capuz volumoso encostado na nuca.
    base = np.where(usado)[0][pos[usado, 1].argmin()]
    capuz = np.where((peca == peca[base]) & usado)[0]
    c = pos[capuz]
    y0 = c[:, 1].min()
    para_tras = np.clip(0.5 - 0.5 * np.cos(np.arctan2(c[:, 0], c[:, 2] + 0.04)), 0.0, 1.0)
    ganho = CAPUZ_FRENTE + (CAPUZ_ATRAS - CAPUZ_FRENTE) * para_tras
    pos[capuz, 1] = y0 + (c[:, 1] - y0) * (1.0 + ganho)

    gravar(acc_pos, pos, trocas)
    return f"aba do chapeu reta (raio {ABA_RAIO} m), capuz +{int(CAPUZ_ATRAS * 100)}% atras"


def ler(gltf, binario, prim, nome, dtype, comp):
    acc = gltf["accessors"][prim["attributes"][nome]]
    bv = gltf["bufferViews"][acc["bufferView"]]
    assert "byteStride" not in bv and acc.get("byteOffset", 0) == 0
    dados = np.frombuffer(binario, dtype=dtype, count=acc["count"] * comp, offset=bv.get("byteOffset", 0))
    return acc, dados.reshape(acc["count"], comp)


def gravar(acc_pos, pos, trocas):
    novo = pos.astype("<f4")
    acc_pos["min"] = [float(x) for x in novo.min(0)]
    acc_pos["max"] = [float(x) for x in novo.max(0)]
    trocas[acc_pos["bufferView"]] = novo.tobytes()


def main():
    gltf, binario = carregar(GLB)
    extras = gltf["asset"].setdefault("extras", {})
    ossos = posicoes_dos_ossos(gltf)
    nomes = [gltf["nodes"][j]["name"] for j in gltf["skins"][0]["joints"]]
    trocas = {}
    for chave, etapa in (("corpo", ajustar_corpo), ("cabeca", ajustar_cabeca)):
        if chave in extras:
            print(f"{chave}: ja ajustado ({extras[chave]})")
            continue
        extras[chave] = etapa(gltf, binario, ossos, nomes, trocas) + " (remodelar_corpo.py)"
        print(f"{chave}: {extras[chave]}")
    if trocas:
        salvar(GLB, gltf, binario, trocas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
