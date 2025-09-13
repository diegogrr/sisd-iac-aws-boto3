# Provisionamento de Infraestrutura de Rede na AWS com Python e Boto3

Este documento detalha o script `vpc_complete_provisioner.py`, que automatiza a criação de uma infraestrutura de rede robusta e escalável na Amazon Web Services (AWS). O script é uma ferramenta didática para o estudo de **Infrastructure as Code (IaC)**, demonstrando como orquestrar a criação de múltiplos recursos na nuvem de forma programática.

---

## 💡 Sobre o Script

O `vpc_complete_provisioner.py` é um projeto de IaC que cria uma **VPC (Virtual Private Cloud)** completa, seguindo as melhores práticas de arquitetura de nuvem. As principais funcionalidades são:

- **Criação da VPC:** Provisiona uma VPC com um bloco CIDR IPv4 definido, que serve como base para toda a infraestrutura.
- **Sub-redes Dinâmicas:** Gera automaticamente sub-redes públicas e privadas em diferentes **Zonas de Disponibilidade (AZs)**. A alocação dos blocos CIDR das sub-redes é totalmente dinâmica, adaptando-se a qualquer CIDR /16 de VPC fornecido.
- **Conectividade:** Configura um **Internet Gateway (IGW)** para permitir a comunicação da sub-rede pública com a internet.
- **NAT Gateway (NAT GW):** Cria um NAT Gateway em uma das sub-redes públicas, habilitando o tráfego de saída das sub-redes privadas para a internet de forma segura.
- **Roteamento:** Configura e associa tabelas de rotas para direcionar o tráfego corretamente, isolando as sub-redes privadas.
- **Uso de Tags:** Aplica automaticamente tags de nome (`Name`) a todos os recursos criados, seguindo uma convenção para facilitar a identificação e a organização.

---

## ⚙️ Dependências

Para executar este script, você precisará ter as seguintes bibliotecas Python instaladas em seu ambiente virtual:

- `boto3`: A biblioteca oficial da AWS para Python, usada para interagir com os serviços da nuvem.
- `python-dotenv`: Para carregar as variáveis de configuração de um arquivo `.env`, garantindo que informações sensíveis não fiquem expostas no código.
- `ipaddress`: Módulo padrão do Python, utilizado para manipular endereços IP e redes de forma programática, garantindo a geração dinâmica de CIDRs.

Você pode instalar todas as dependências de uma vez usando o arquivo `requirements.txt`:

```sh
pip install -r requirements.txt
```
## 📋 Configuração

O script utiliza variáveis de ambiente para a configuração. Antes de executá-lo, siga estes passos para configurar seu ambiente:

1. **Crie um arquivo** `.env` na raiz do seu projeto, a partir do modelo `.env.example`.

2. **Preencha as variáveis** com os valores da sua conta AWS:

```
# Exemplo de conteúdo do arquivo .env
# Este arquivo não deve ser enviado ao Git!

# Nome da VPC (usado para gerar tags)
VPC_TAG_NAME=ProjetoSISD-VPC

# Região da AWS onde os recursos serão criados
REGION=us-east-1

# Bloco CIDR da VPC. O script adapta os CIDRs das sub-redes a este valor.
VPC_CIDR=10.0.0.0/16

# Zonas de Disponibilidade onde as sub-redes serão criadas, separadas por vírgula.
AZ_LIST=us-east-1a,us-east-1b
```

## 🚀 Execução

Após configurar seu ambiente virtual e o arquivo `.env`, execute o script a partir do terminal na raiz do projeto:

```sh
python scripts/vpc_complete_provisioner.py
```

O script exibirá o progresso da criação dos recursos, desde a VPC até as tabelas de rotas. Ao final, uma mensagem de sucesso confirmará a conclusão do provisionamento.