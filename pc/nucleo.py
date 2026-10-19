"""Nucleo: regras puras, sem GTK e sem rede."""
import re

MAX_CHARS = 3000


# Copia da juntarLinhas de android/.../Tradutor.kt: manter as duas iguais,
# conferidas pelos casos compartilhados em casos/juntar_linhas.json.
# Texto copiado de PDF traz \n em cada fim de linha (e hifen em palavra cortada);
# junta as linhas, linha em branco continua separando paragrafos.
def juntar_linhas(texto):
    def hifen(m):  # dis-|tributed some o hifen; Monolith-|To fica
        return "" if m.group(1).islower() else "-"

    pars = re.split(r"\n[ \t]*\n\s*", texto.replace("\r\n", "\n"))
    out = []
    for par in pars:
        par = re.sub(r"-[ \t]*\n[ \t]*(?=(.?))", hifen, par)
        par = re.sub(r"[ \t]*\n[ \t]*", " ", par)
        par = re.sub(r"[ \t]{2,}", " ", par)
        out.append(par.strip())
    return "\n\n".join(out)
