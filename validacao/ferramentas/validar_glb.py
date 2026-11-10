"""Validacao estatica da malha do Pescador, direto no arquivo GLB.

Uso (na raiz do repositorio):
    python3 validacao/ferramentas/validar_glb.py

Confere geometria, pesos de skin, UVs, matrizes de ligacao, animacoes e
texturas embutidas. Grava validacao/validation_report_glb.json e termina com
codigo 1 se algum erro for encontrado.
"""
import io
import json
import struct
import sys

import numpy as np
from PIL import Image

GLB = "pescador_v29/pescador_v29.glb"
RELATORIO = "validacao/validation_report_glb.json"
OSSOS_ESPERADOS = 68
ANIMACOES_ESPERADAS = ["Idle", "Grip_Rod", "Rig_Mobility", "Shoulder_Abduction", "Shoulder_Stress"]
COMPONENTES = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
TIPOS = {5120: "i1", 5121: "u1", 5122: "i2", 5123: "u2", 5125: "u4", 5126: "f4"}


def carregar(caminho):
    with open(caminho, "rb") as f:
        magia, versao, tamanho = struct.unpack("<4sII", f.read(12))
        assert magia == b"glTF" and versao == 2, "cabecalho GLB invalido"
        n, tipo = struct.unpack("<II", f.read(8))
        gltf = json.loads(f.read(n))
        n, tipo = struct.unpack("<II", f.read(8))
        binario = f.read(n)
    return gltf, binario, tamanho


def main():
    gltf, binario, tamanho = carregar(GLB)
    erros, avisos, dados = [], [], {"arquivo": GLB, "bytes": tamanho}

    def erro(cond, msg):
        if not cond:
            erros.append(msg)

    def aviso(cond, msg):
        if not cond:
            avisos.append(msg)

    def acessor(i):
        a = gltf["accessors"][i]
        bv = gltf["bufferViews"][a["bufferView"]]
        n = COMPONENTES[a["type"]]
        dt = np.dtype(TIPOS[a["componentType"]])
        inicio = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        passo = bv.get("byteStride", n * dt.itemsize)
        fim = inicio + (a["count"] - 1) * passo + n * dt.itemsize
        erro(fim <= bv.get("byteOffset", 0) + bv["byteLength"] and fim <= len(binario), f"acessor {i} passa do fim do buffer")
        bruto = np.frombuffer(binario, dtype=np.uint8, count=(a["count"] - 1) * passo + n * dt.itemsize, offset=inicio)
        linhas = np.lib.stride_tricks.as_strided(bruto, shape=(a["count"], n * dt.itemsize), strides=(passo, 1))
        return np.ascontiguousarray(linhas).view(dt).reshape(a["count"], n)

    skin = gltf["skins"][0]
    ossos = len(skin["joints"])
    erro(ossos == OSSOS_ESPERADOS, f"esperados {OSSOS_ESPERADOS} ossos, encontrados {ossos}")
    ibm = acessor(skin["inverseBindMatrices"]).astype(float)
    erro(len(ibm) == ossos, "numero de matrizes de ligacao diferente do numero de ossos")
    erro(np.isfinite(ibm).all(), "matriz de ligacao com valor invalido")
    dados["ossos"] = ossos

    primitivas = []
    for pi, p in enumerate(gltf["meshes"][0]["primitives"]):
        nome = gltf["materials"][p["material"]]["name"]
        pos = acessor(p["attributes"]["POSITION"]).astype(float)
        idx = acessor(p["indices"]).ravel().astype(np.int64)
        info = {"primitiva": pi, "material": nome, "vertices": len(pos), "triangulos": len(idx) // 3}
        erro(np.isfinite(pos).all(), f"prim {pi}: posicao com NaN/inf")
        erro(len(idx) % 3 == 0, f"prim {pi}: indices nao formam triangulos")
        erro(idx.max() < len(pos) and idx.min() >= 0, f"prim {pi}: indice fora da faixa de vertices")
        tri = pos[idx].reshape(-1, 3, 3)
        area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) * 0.5
        info["triangulos_degenerados"] = int((area < 1e-12).sum())
        aviso(info["triangulos_degenerados"] == 0, f"prim {pi} ({nome}): {info['triangulos_degenerados']} triangulos com area zero")
        info["caixa_min"] = pos.min(0).round(4).tolist()
        info["caixa_max"] = pos.max(0).round(4).tolist()
        if "NORMAL" in p["attributes"]:
            normal = acessor(p["attributes"]["NORMAL"]).astype(float)
            comprimento = np.linalg.norm(normal, axis=1)
            erro(np.isfinite(normal).all(), f"prim {pi}: normal com NaN/inf")
            info["normais_fora_de_unidade"] = int((np.abs(comprimento - 1.0) > 0.01).sum())
            aviso(info["normais_fora_de_unidade"] == 0, f"prim {pi} ({nome}): {info['normais_fora_de_unidade']} normais nao unitarias")
        if "TEXCOORD_0" in p["attributes"]:
            uv = acessor(p["attributes"]["TEXCOORD_0"]).astype(float)
            erro(np.isfinite(uv).all(), f"prim {pi}: UV com NaN/inf")
            info["uv_fora_de_0_1"] = int(((uv < -1e-4) | (uv > 1 + 1e-4)).any(axis=1).sum())
            aviso(info["uv_fora_de_0_1"] == 0, f"prim {pi} ({nome}): {info['uv_fora_de_0_1']} UVs fora de 0..1")
        if "JOINTS_0" in p["attributes"]:
            juntas = acessor(p["attributes"]["JOINTS_0"]).astype(int)
            pesos = acessor(p["attributes"]["WEIGHTS_0"]).astype(float)
            if gltf["accessors"][p["attributes"]["WEIGHTS_0"]]["componentType"] == 5121:
                pesos = pesos / 255.0
            elif gltf["accessors"][p["attributes"]["WEIGHTS_0"]]["componentType"] == 5123:
                pesos = pesos / 65535.0
            erro(juntas.max() < ossos, f"prim {pi}: peso aponta para osso inexistente")
            erro((pesos >= -1e-6).all(), f"prim {pi}: peso negativo")
            soma = pesos.sum(1)
            info["pesos_nao_normalizados"] = int((np.abs(soma - 1.0) > 0.01).sum())
            erro(info["pesos_nao_normalizados"] == 0, f"prim {pi} ({nome}): {info['pesos_nao_normalizados']} vertices com pesos que nao somam 1")
            info["vertices_sem_peso"] = int((soma < 1e-6).sum())
            erro(info["vertices_sem_peso"] == 0, f"prim {pi} ({nome}): {info['vertices_sem_peso']} vertices sem nenhum peso")
        else:
            erro(False, f"prim {pi} ({nome}): sem dados de skin")
        primitivas.append(info)
    dados["primitivas"] = primitivas

    todas = np.concatenate([acessor(p["attributes"]["POSITION"]).astype(float) for p in gltf["meshes"][0]["primitives"]])
    dados["altura_m"] = round(float(todas[:, 1].max() - todas[:, 1].min()), 4)
    dados["assimetria_x_m"] = round(float(abs(todas[:, 0].max() + todas[:, 0].min())), 4)
    erro(1.6 < dados["altura_m"] < 2.1, f"altura {dados['altura_m']} m fora do esperado para o personagem")
    erro(abs(todas[:, 1].min()) < 0.01, "os pes nao estao no chao (y=0)")

    nomes = [a["name"] for a in gltf["animations"]]
    for esperado in ANIMACOES_ESPERADAS:
        erro(esperado in nomes, f"animacao ausente: {esperado}")
    animacoes = []
    for a in gltf["animations"]:
        duracao, finito = 0.0, True
        for canal in a["channels"]:
            erro(canal["target"]["node"] < len(gltf["nodes"]), f"animacao {a['name']}: canal aponta para no inexistente")
            amostrador = a["samplers"][canal["sampler"]]
            tempos = acessor(amostrador["input"]).astype(float)
            valores = acessor(amostrador["output"]).astype(float)
            finito = finito and np.isfinite(tempos).all() and np.isfinite(valores).all()
            erro((np.diff(tempos.ravel()) > 0).all(), f"animacao {a['name']}: tempos fora de ordem")
            if canal["target"]["path"] == "rotation":
                erro((np.abs(np.linalg.norm(valores, axis=1) - 1.0) < 0.01).all(), f"animacao {a['name']}: rotacao nao unitaria")
            duracao = max(duracao, float(tempos.max()))
        erro(finito, f"animacao {a['name']}: valor invalido")
        animacoes.append({"nome": a["name"], "canais": len(a["channels"]), "duracao_s": round(duracao, 3)})
    dados["animacoes"] = animacoes

    texturas = []
    for im in gltf.get("images", []):
        bv = gltf["bufferViews"][im["bufferView"]]
        bruto = binario[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
        try:
            imagem = Image.open(io.BytesIO(bruto))
            imagem.load()
            texturas.append({"nome": im.get("name"), "tamanho": list(imagem.size)})
        except Exception as e:  # noqa: BLE001
            erro(False, f"textura {im.get('name')} nao abre: {e}")
    dados["texturas"] = texturas

    dados["erros"], dados["avisos"], dados["passou"] = erros, avisos, not erros
    with open(RELATORIO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    for p in primitivas:
        print(p)
    print("altura:", dados["altura_m"], "m | animacoes:", [a["nome"] for a in animacoes], "| texturas:", texturas)
    for a in avisos:
        print("AVISO:", a)
    for e in erros:
        print("ERRO:", e)
    print("GLB_VALIDATION_PASS" if not erros else "GLB_VALIDATION_FAIL")
    return 0 if not erros else 1


if __name__ == "__main__":
    sys.exit(main())
