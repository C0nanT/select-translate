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

App em `android/` que adiciona **"Traduzir pt-BR"** ao menu da seleção de texto. Tocar no item abre um popup embaixo da tela, por cima do app.

**Requisitos**

- Android 6+
- Depuração USB ligada (só para `make android`)
- Android SDK em `~/Android/Sdk` (ou `ANDROID_HOME`) e Java 17+

```bash
make android      # gera o APK debug e instala no tablet via USB
make android-apk  # só gera o APK
```

O APK fica em `android/app/build/outputs/apk/debug/app-debug.apk`. Para instalar à mão, copie o arquivo para o tablet, abra-o no gerenciador de arquivos e permita instalar de fonte desconhecida.

**Uso**

- Selecione o texto -> toque em "Traduzir pt-BR" no menu -> aparece "Traduzindo…" e depois a tradução
- Some sozinho em 15 s; a barra embaixo mostra o tempo restante
- Segurar o dedo sobre o popup pausa o tempo
- Toque fora -> o popup fecha
- Falha na requisição -> popup vermelho com o motivo
- Texto acima de 3000 caracteres -> aviso "Texto grande demais (N caracteres)"

**Leitores de PDF (risco em aberto, ainda não testado no tablet):** alguns leitores podem ter menu de seleção próprio e esconder itens de outros apps, e aí "Traduzir pt-BR" não aparece. Teste primeiro no Chrome; depois, leitores candidatos: Xodo, ReadEra, Librera.

**Configuração**

Constantes em `android/app/src/main/java/com/conan/tradutor/Config.kt`:

| Constante | Padrão | O que faz |
|---|---|---|
| `HIDE_AFTER_S` | 15 | o popup some sozinho depois desse tempo |
| `MAX_CHARS` | 3000 | ignora seleções maiores que isso |
| `POPUP_CHARS` | 80 | largura máxima do popup, em caracteres |

Depois de mudar, rode `make android`.

**Privacidade:** o texto só é enviado ao Google Tradutor quando você toca em "Traduzir pt-BR", não a cada seleção.
