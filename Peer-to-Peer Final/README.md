# Alunos: Amilka Lilian

# &nbsp;	Ruan da Cunha Isabel	

# 

# \# Simulação de Rede P2P (BitTorrent)

# 

# Este projeto implementa uma simulação de uma rede Peer-to-Peer (P2P) baseada em alguns princípios do BitTorrent, utilizando Sockets em Python.

# 

# \## Como Funciona

# 

# A arquitetura consiste em dois componentes principais:

# 

# 1\.  \*\*Tracker (`server.py`)\*\*: Um servidor centralizado que opera via \*\*UDP\*\*. Ele não armazena os arquivos, apenas mantém um registro de quais peers estão na rede e quais "pedaços" de arquivos cada um possui.

# 2\.  \*\*Peer (`peer.py`)\*\*: O cliente da rede. Cada peer pode tanto baixar pedaços de arquivos de outros peers quanto servir seus próprios pedaços. A comunicação entre peers para a transferência de dados ocorre via \*\*TCP\*\*.

# 

# O fluxo de trabalho é o seguinte:

# \* Um peer entra na rede e, a cada 3 segundos, informa ao Tracker (via UDP) a lista de pedaços de arquivos que possui.

# \* Quando um peer deseja baixar algo, ele solicita ao Tracker a lista de todos os outros peers e seus respectivos pedaços.

# \* Com base nessa lista, o peer determina qual pedaço, que ele ainda não tem, é o mais raro na rede (ou seja, está disponível no menor número de peers).

# \* Ele então escolhe \*\*aleatoriamente\*\* um dos peers que possui esse pedaço raro.

# \* Uma conexão \*\*TCP\*\* direta é estabelecida com o peer escolhido para baixar aquele pedaço específico.

# \* O processo se repete até que o peer complete o download de todos os pedaços de um arquivo.

# 

# \## Instruções para Compilação e Execução

# 

# O programa não requer compilação. Siga os passos abaixo para executar.

# 

# \### Passo 1: Preparar os Arquivos

# 

# Crie alguns arquivos de texto (ex: `a.txt`, `b.txt`) no mesmo diretório onde você salvou `peer.py`. Coloque conteúdos diferentes neles. Pelo menos um peer precisa iniciar com um arquivo para que a rede tenha algo para compartilhar.

# 

# \### Passo 2: Iniciar o Servidor (Tracker)

# 

# 1\.  Abra um terminal.

# 2\.  Navegue até o diretório onde você salvou os arquivos.

# 3\.  Execute o comando:

# &nbsp;   ```sh

# &nbsp;   python server.py

# &nbsp;   ```

# 4\.  O programa solicitará o \*\*IP\*\* e a \*\*Porta\*\* para o servidor. Use o IP da máquina onde o servidor está rodando (ex: `192.168.0.10`) e uma porta livre (ex: `9090`).

# 

# &nbsp;   ```

# &nbsp;   Digite o IP do Servidor (Tracker): 192.168.0.10

# &nbsp;   Digite a Porta do Servidor (ex: 9090): 9090

# &nbsp;   ```

# &nbsp;   O servidor estará ativo e aguardando conexões.

# 

# \### Passo 3: Iniciar um ou mais Peers

# 

# Para simular a rede, você precisará de pelo menos dois peers. Abra um novo terminal para cada peer que desejar iniciar.

# 

# 1\.  Abra um novo terminal.

# 2\.  Navegue até o mesmo diretório.

# 3\.  Execute o comando:

# &nbsp;   ```sh

# &nbsp;   python peer.py

# &nbsp;   ```

# 4\.  O programa solicitará:

# &nbsp;   \* O \*\*IP e Porta do Tracker\*\* (os mesmos que você definiu no Passo 2).

# &nbsp;   \* O \*\*seu próprio IP\*\*. Este é o IP que outros peers usarão para se conectar a você via TCP. Deve ser o IP da máquina do peer.

# 

# &nbsp;   \*\*Exemplo (Peer 1, que tem o arquivo `a.txt`):\*\*

# &nbsp;   ```

# &nbsp;   Digite o IP do Servidor (Tracker): 192.168.0.10

# &nbsp;   Digite a Porta do Tracker: 9090

# &nbsp;   Digite o SEU PRÓPRIO IP para outros peers se conectarem: 192.168.0.11

# &nbsp;   ```

# 

# &nbsp;   \*\*Exemplo (Peer 2, sem arquivos iniciais):\*\*

# &nbsp;   ```

# &nbsp;   Digite o IP do Servidor (Tracker): 192.168.0.10

# &nbsp;   Digite a Porta do Tracker: 9090

# &nbsp;   Digite o SEU PRÓPRIO IP para outros peers se conectarem: 192.168.0.12

# &nbsp;   ```

# 

# \### Passo 4: Usar o Peer

# 

# Após iniciar, o peer mostrará um prompt `>`. Você pode usar os seguintes comandos:

# 

# \* `!baixar`: Inicia o processo de busca e download do pedaço mais raro disponível na rede.

# \* `!meus\_pedacos`: Mostra uma lista detalhada dos arquivos e pedaços que você possui no momento.

# \* `!sair`: Envia uma mensagem de desconexão para o Tracker e encerra o cliente.

