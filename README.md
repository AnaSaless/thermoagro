# ThermoAgro

Painel web para monitorar sensores e acionar atuadores de um silo agrícola em tempo real, usando MQTT. Os valores chegam do dispositivo, aparecem na tela na mesma hora e ficam gravados no banco para consulta do histórico.

## O que o sistema faz

- **Monitoramento ao vivo** de temperatura (°C), umidade (%) e nível do silo, com atualização instantânea na tela via Socket.IO
- **Alerta por cor** em cada sensor (verde, amarelo ou vermelho) conforme faixas configuradas:

  | Sensor | Verde | Amarelo | Vermelho |
  |---|---|---|---|
  | Temperatura | de 20 °C a 25 °C | acima de 25 °C até 28 °C | abaixo de 20 °C ou acima de 28 °C |
  | Umidade | abaixo de 15% | de 15% a 20% | 20% ou mais |
  | Nível do silo | de 51 a 400 | não se aplica | até 50 ou acima de 400 |

- **Histórico** de leituras de cada sensor, gravado no banco
- **Atuador "Porta do Silo"** (servo motor): abre e fecha pela interface, com registro de cada acionamento
- **Administração** (só para administradores): cadastro, edição e exclusão de sensores, atuadores e usuários
- **Login** com sessão e controle de acesso às telas de administração

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Backend | Python, Flask, Flask-SQLAlchemy, Flask-Migrate |
| Tempo real | Flask-SocketIO, Flask-MQTT (paho-mqtt) |
| Banco de dados | SQLite |
| Frontend | Templates Jinja, Bootstrap 5, Bootstrap Icons, JavaScript |

## Como funciona a comunicação

O sistema usa o broker MQTT público `broker.emqx.io` (porta 1883). O dispositivo e o painel conversam por dois tópicos:

| Tópico | Direção | Mensagem |
|---|---|---|
| `sensor` | dispositivo para o painel | `{"id": 1, "value": 23.5}` (id 1 é temperatura, 2 é umidade e 3 é nível do silo) |
| `servo` | painel para o dispositivo | `{"servo": 180}` abre a porta e `{"servo": 90}` fecha |

Para testar sem o dispositivo, basta publicar uma leitura no tópico `sensor`, por exemplo com o Mosquitto:

```bash
mosquitto_pub -h broker.emqx.io -t sensor -m '{"id":1,"value":23.5}'
```

## Como rodar localmente

Pré-requisitos: Python 3.10 ou superior e acesso à internet (o app conecta no broker ao iniciar).

```bash
python -m venv .venv
source .venv/bin/activate      # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

O painel abre em `http://localhost:8081`. O banco SQLite é criado sozinho na primeira execução, junto com três usuários de exemplo:

| Usuário | Senha | Função |
|---|---|---|
| admin | admin | administrador |
| operador | operador | operador |
| estatistico | estatistico | estatístico |

## Estrutura

```
.
├── run.py                  ponto de entrada (servidor na porta 8081)
├── config.py
├── requirements.txt
└── app/
    ├── __init__.py         criação do app e configuração do MQTT
    ├── bootstrap.py        cria perfis, usuários e sensores padrão
    ├── mqtt_handlers.py    recebe as leituras e envia à tela em tempo real
    ├── controllers/        autenticação, sensores, atuadores e usuários
    ├── models/             usuário, sensor, leitura, atuador e histórico
    ├── routes/             páginas principais e erros
    ├── views/templates/    telas HTML
    └── static/             CSS, JavaScript e imagens
```

## Melhorias previstas

- Usar um broker MQTT próprio, com autenticação, no lugar do broker público
- Ler a chave secreta do Flask de uma variável de ambiente (hoje está fixa no código)
- Trocar as senhas dos usuários de exemplo no primeiro acesso
