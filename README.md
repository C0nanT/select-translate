# select-translate

Selecione um texto em qualquer app (leitor de PDF, navegador, etc.) e veja a tradução para pt-BR num popup fixo embaixo da tela, sem precisar copiar e colar.

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

Ou direto: `python3 pc/tradutor.py`.

Testes: `make test` (PC + Android). Para o `git push` rodar os testes antes de enviar, ative o hook uma vez em cada clone com `make hooks`. Sem Java ou Android SDK o push é bloqueado; `git push --no-verify` pula.

- Selecione o texto -> aparece "Traduzindo…" e depois a tradução
- Clique em qualquer lugar -> o popup fecha
- Segure e arraste o popup para mudar de lugar; os próximos abrem ali (fica salvo em `~/.config/select-translate.json`; apague o arquivo para voltar ao padrão)
- Se a requisição falhar, o popup fica vermelho com o motivo

Enquanto estiver rodando, **qualquer** texto selecionado é enviado ao Google Tradutor.

## Configuração

Constantes no topo de `pc/popup.py` (`HIDE_AFTER_S`, `POPUP_CHARS`, `CLICK_HIDE_MS`, `MARGIN`), `pc/nucleo.py` (`MAX_CHARS`) e `pc/selecao.py`:

| Constante | Padrão | O que faz |
|---|---|---|
| `DEBOUNCE_MS` | 500 | espera a seleção terminar antes de traduzir |
| `HIDE_AFTER_S` | 15 | o popup some sozinho depois desse tempo |
| `MAX_CHARS` | 3000 | ignora seleções maiores que isso |
| `POPUP_CHARS` | 80 | largura máxima do popup, em caracteres |
| `CLICK_HIDE_MS` | 0 | atraso para fechar depois de um clique |
| `MARGIN` | 8 | distância do popup até a borda da tela |

## Android (tablet)

App em `android/` com duas formas de traduzir; as duas abrem o mesmo popup embaixo da tela, por cima do app:

- **Bolha flutuante** (funciona em qualquer leitor, inclusive o visualizador de PDF do Files by Google): copie o texto e toque na bolha **文**.
- **Item "Traduzir pt-BR"** no menu da seleção, nos apps que mostram itens de outros apps nesse menu.

Testado num Lenovo TB336FU com Android 16, lendo PDF no Files by Google.

**Requisitos**

- Android 6+
- Depuração USB ligada (só para `make android`)
- Android SDK em `~/Android/Sdk` (ou `ANDROID_HOME`) e Java 17+

```bash
make android      # gera o APK debug e instala no tablet via USB
make android-apk  # só gera o APK
```

O APK fica em `android/app/build/outputs/apk/debug/app-debug.apk`. Para instalar à mão, copie o arquivo para o tablet, abra-o no gerenciador de arquivos e permita instalar de fonte desconhecida.

**Bolha**

- Ligar: toque no ícone **Tradutor** na lista de apps. Na primeira vez ele abre a tela de "Sobrepor a outros apps": ative para o Tradutor e toque no ícone de novo
- No Android 13+, ao ligar a bolha o app pede permissão de notificação (para mostrar "Toque para desligar"); negar não impede a bolha
- Desligar: segure o dedo parado sobre a bolha até vibrar, ou toque na notificação "Bolha do Tradutor ligada"
- Toque curto traduz; arraste a bolha para mudar de lugar (passou do limiar de toque do sistema, não traduz nem desliga)
- A bolha lembra onde foi deixada: ao ligar de novo volta para o último lugar, ajustada à tela (também depois de girar ou trocar de aparelho)
- Ao reiniciar o tablet, a bolha não volta sozinha: toque no ícone de novo
- O Android avisa "Tradutor colou da área de transferência" a cada tradução; é esperado

**Uso**

- Copie o texto e toque na bolha (ou selecione e toque em "Traduzir pt-BR" no menu) -> aparece "Traduzindo…" e depois a tradução
- Some sozinho em 15 s; a barra embaixo mostra o tempo restante
- Segurar o dedo sobre o popup pausa o tempo
- Segure parado até vibrar e arraste para mudar o popup de lugar; os próximos abrem ali (arrastar sem segurar rola o texto)
- Toque fora -> o popup fecha
- Falha na requisição -> popup vermelho com o motivo
- Texto acima de 3000 caracteres -> aviso "Texto grande demais (N caracteres)"

**Leitores de PDF:** o visualizador de PDF do Files by Google tem menu de seleção próprio (só "Copiar" e "Selecionar tudo"), então "Traduzir pt-BR" não aparece nele: use a bolha. No navegador o item também não apareceu no primeiro teste; ainda não investigado.

**Configuração**

Constantes em `android/app/src/main/java/com/conan/tradutor/Config.kt`:

| Constante | Padrão | O que faz |
|---|---|---|
| `HIDE_AFTER_S` | 15 | o popup some sozinho depois desse tempo |
| `MAX_CHARS` | 3000 | seleções maiores que isso (contadas por code point: emoji conta 1) mostram o aviso "Texto grande demais" |
| `MAX_URL` | 8000 | teto da URL já codificada (acentos e emoji incham); acima disso mostra o mesmo aviso. Valor conservador, ainda não medido no aparelho |
| `POPUP_CHARS` | 80 | largura máxima do popup, em caracteres |

Avisos do popup vermelho ao tocar na bolha: "Nada copiado" (área de transferência vazia, com imagem/arquivo ou com leitura bloqueada) e "Nada para traduzir" (texto sem nenhuma letra, como "42"; nenhuma requisição é feita). Pelo menu "Traduzir pt-BR", esses casos fecham sem mostrar nada.

Depois de mudar, rode `make android`.

**Privacidade:** o texto só é enviado ao Google Tradutor quando você toca na bolha ou em "Traduzir pt-BR", não a cada seleção ou cópia.
