# IFSP - Sistemas Distribuídos e Cloud Computing

Este repositório serve como material de apoio e ambiente de laboratório para a disciplina de **Sistemas Distribuídos (SISD)** do curso de **Ciência da Computação** do **Instituto Federal de Educação, Ciência e Tecnologia de São Paulo (IFSP) - Campus Salto**.

O foco principal é o estudo de **Infrastructure as Code (IaC)**, utilizando a linguagem **Python** e a biblioteca **Boto3** para interagir com a plataforma de cloud computing **Amazon Web Services (AWS)**.

---

## Estrutura do Projeto

O projeto está organizado em subdiretórios, onde cada um representa um conjunto de scripts de provisionamento de infraestrutura:

- `scripts/`: Contém os scripts Python para provisionamento de recursos AWS, como instâncias EC2, VPCs e Security Groups.
- `docs/`: Documentos de apoio, diagramas e materiais teóricos.

---

## 🛠️ Pré-requisitos

Para utilizar os scripts, você precisará ter:

1.  **Python 3.x** instalado.
2.  **AWS CLI** configurado com suas credenciais de acesso.
3.  Acesso a uma conta AWS com permissões adequadas para provisionar os recursos.

---

## ⚙️ Configuração do Ambiente

1.  **Clone o repositório:**
    ```sh
    git clone https://github.com/diegogrr/sisd-iac-aws-boto3.git
    cd sisd-iac-aws-boto3
    ```

2.  **Instale as dependências Python:**
    ```sh
    pip install -r requirements.txt
    ```

3.  **Configure as variáveis de ambiente:**
    - Crie um arquivo chamado `.env` na raiz do projeto, a partir do modelo `.env.example`.
    - Preencha as variáveis com os valores da sua conta AWS (IDs de sub-rede, chaves de segurança, etc.).

    ```ini
    # Conteúdo do arquivo .env (não versionado no Git)
    AMI_ID=ami-0b09ffb6d8b58ca91
    KEY_NAME=SEU_PAR_DE_CHAVES
    # ... adicione as outras variáveis conforme o .env.example
    ```

---

## 💡 Como Usar

Acesse a pasta `scripts/` e execute o script desejado. Por exemplo, para provisionar uma instância EC2:

```sh
python scripts/ec2_provisioner.py
```