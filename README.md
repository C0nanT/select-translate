# select-translate

Selecione um texto em qualquer app (leitor de PDF, navegador, etc.) e veja a tradução para pt-BR num popup ao lado do mouse, sem precisar copiar e colar.

Feito para ler livros em inglês e só consultar a tradução quando travar numa frase.

## Requisitos

- Linux com sessão **X11** (não funciona no Wayland)
- Python 3 + GTK 3 (`python3-gi`), que já vêm no Ubuntu/GNOME
- Internet (usa o endpoint gratuito do Google Tradutor)

## Uso

```bash
make start    # liga preso ao terminal
```

Ctrl+C ou fechar o terminal desliga.

Ou direto: `python3 tradutor.py`.

- Selecione o texto -> aparece "Traduzindo…" e depois a tradução
- Clique em qualquer lugar -> o popup fecha
- Se a requisição falhar, o popup fica vermelho com o motivo

Enquanto estiver rodando, **qualquer** texto selecionado é enviado ao Google Tradutor.

## Configuração

Constantes no topo do `tradutor.py`:

| Constante | Padrão | O que faz |
|---|---|---|
| `DEBOUNCE_MS` | 500 | espera a seleção terminar antes de traduzir |
| `HIDE_AFTER_S` | 15 | o popup some sozinho depois desse tempo |
| `MAX_CHARS` | 3000 | ignora seleções maiores que isso |
| `POPUP_CHARS` | 80 | largura máxima do popup, em caracteres |
| `CLICK_HIDE_MS` | 0 | atraso para fechar depois de um clique |

## Android (tablet)

App em `android/` que adiciona **"Traduzir pt-BR"** ao menu da seleção de texto (Chrome, leitores de PDF que mostram itens de outros apps). Tocar no item abre um popup embaixo da tela; toque fora fecha.

Requer Android SDK em `~/Android/Sdk` (ou `ANDROID_HOME`) e Java 17+.

```bash
make android      # gera o APK debug e instala no tablet via USB (Depuração USB ligada)
make android-apk  # só gera o APK
```

O APK fica em `android/app/build/outputs/apk/debug/app-debug.apk`.
