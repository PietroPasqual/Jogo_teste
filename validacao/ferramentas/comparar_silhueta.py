"""Compara a silhueta do modelo com a da folha de referencia.

Uso (na raiz do repositorio, depois de rodar validacao/render_silhueta.gd):
    python3 validacao/ferramentas/comparar_silhueta.py CAMINHO/folha_de_referencia.png

Para cada vista (frente, lado, costas) alinha as duas silhuetas pela altura,
grava uma sobreposicao em validacao/imagens/silhueta/ (modelo ao fundo,
contorno da referencia em amarelo) e mede a largura em varias alturas.
"""
import json
import sys

import numpy as np
from PIL import Image, ImageFilter

PASTA = "validacao/imagens/silhueta/"
RELATORIO = "validacao/silhouette_report.json"
# Colunas de cada vista na folha de referencia (1254x1254), linhas 15 a 790.
VISTAS = {"frente": (55, 350), "lado": (372, 545), "costas": (555, 805)}
LINHAS = (15, 790)
ALTURA = 900
# Fracoes da altura (0 = topo do chapeu, 1 = sola) onde a largura e medida.
NIVEIS = {"copa_do_chapeu": 0.04, "aba_do_chapeu": 0.085, "rosto": 0.12, "ombros": 0.24, "peito": 0.32,
          "cintura": 0.47, "maos": 0.555, "coxas": 0.62, "joelhos": 0.74, "canelas": 0.86, "pes": 0.975}


def mascara_referencia(ref, colunas):
    recorte = np.asarray(ref.crop((colunas[0], LINHAS[0], colunas[1], LINHAS[1]))).astype(int)
    r, g, b = recorte[..., 0], recorte[..., 1], recorte[..., 2]
    soma = r + g + b
    # Fundo da folha: cinza levemente azulado, de brilho medio.
    cor_de_fundo = (b >= r - 2) & (r - g >= 0) & (r - g <= 6) & (soma >= 85) & (soma <= 215)
    # So conta como fundo o que esta ligado a borda do recorte (o ziper e as
    # fivelas tambem sao cinza, mas ficam dentro do personagem).
    semente = np.zeros(cor_de_fundo.shape, bool)
    semente[0, :] = semente[:, 0] = semente[:, -1] = True
    fundo = _ligado(cor_de_fundo, semente)
    m = Image.fromarray((~fundo * 255).astype("uint8")).filter(ImageFilter.MedianFilter(5))
    m = np.asarray(m) > 0
    # Fica so com o personagem (a folha tem um icone de peixe no canto).
    semente = np.zeros(m.shape, bool)
    semente[m.shape[0] // 3, m.shape[1] // 2] = True
    return _ligado(m, semente)


def _ligado(permitido, semente):
    """Pixels de `permitido` ligados a `semente` (preenchimento por vizinhanca)."""
    atual = semente & permitido
    while True:
        cresce = atual.copy()
        cresce[1:, :] |= atual[:-1, :]
        cresce[:-1, :] |= atual[1:, :]
        cresce[:, 1:] |= atual[:, :-1]
        cresce[:, :-1] |= atual[:, 1:]
        cresce &= permitido
        if (cresce == atual).all():
            return atual
        atual = cresce


def mascara_modelo(caminho):
    im = np.asarray(Image.open(caminho).convert("RGB")).astype(int)
    return ~((im[..., 1] > 200) & (im[..., 0] < 80) & (im[..., 2] < 80))


def recortar(m):
    ys, xs = np.where(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def normalizar(m):
    m = recortar(m)
    largura = max(1, round(m.shape[1] * ALTURA / m.shape[0]))
    return np.asarray(Image.fromarray((m * 255).astype("uint8")).resize((largura, ALTURA), Image.NEAREST)) > 0


def larguras(m):
    saida = {}
    for nome, f in NIVEIS.items():
        y = int(f * (ALTURA - 1))
        faixa = m[max(0, y - 3):y + 4].any(0)
        xs = np.where(faixa)[0]
        saida[nome] = round(float(xs.max() - xs.min() + 1) / ALTURA, 4) if len(xs) else 0.0
    return saida


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    ref = Image.open(sys.argv[1]).convert("RGB")
    relatorio = {}
    for vista, colunas in VISTAS.items():
        r = normalizar(mascara_referencia(ref, colunas))
        m = normalizar(mascara_modelo(PASTA + vista + ".png"))
        lr, lm = larguras(r), larguras(m)
        relatorio[vista] = {n: {"referencia": lr[n], "modelo": lm[n], "razao": round(lm[n] / lr[n], 3) if lr[n] else None} for n in NIVEIS}
        largura = max(r.shape[1], m.shape[1]) + 20
        tela = np.zeros((ALTURA, largura, 3), dtype="uint8") + 40

        def colar(mask, cor, alpha):
            x0 = (largura - mask.shape[1]) // 2
            area = tela[:, x0:x0 + mask.shape[1]]
            area[mask] = (area[mask] * (1 - alpha) + np.array(cor) * alpha).astype("uint8")

        colar(m, (90, 160, 255), 1.0)
        borda = r & ~(np.asarray(Image.fromarray((r * 255).astype("uint8")).filter(ImageFilter.MinFilter(5))) > 0)
        colar(r, (255, 220, 0), 0.25)
        colar(borda, (255, 230, 0), 1.0)
        Image.fromarray(tela).save(PASTA + "sobreposicao_" + vista + ".png")
        print(vista)
        for n in NIVEIS:
            d = relatorio[vista][n]
            print(f"  {n:16s} referencia={d['referencia']:.3f} modelo={d['modelo']:.3f} razao={d['razao']}")
    with open(RELATORIO, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
