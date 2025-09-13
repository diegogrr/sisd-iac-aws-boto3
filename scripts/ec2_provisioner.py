"""
Provisionamento de Instância EC2 na AWS com Boto3.

Este script automatiza a criação de uma instância EC2,
aderindo às boas práticas de Infrastructure as Code (IaC) e
convenções da linguagem Python (PEP 8).

Autor: Prof. Diego Garrido
Data: 2024-09-13
"""
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um arquivo .env
load_dotenv()

# --- Configurações da Instância EC2 ---
# Variáveis de ambiente são utilizadas para desacoplar configurações sensíveis
# ou que mudam entre ambientes (dev, prod) do código-fonte.
# A função os.getenv() lê a variável de ambiente, e o segundo argumento
# é um valor padrão caso a variável não seja encontrada.

# Exemplo de AMI do Amazon Linux 2023 kernel-6.1
AMI_ID = os.getenv('AMI_ID', 'ami-0b09ffb6d8b58ca91')
INSTANCE_TYPE = os.getenv('INSTANCE_TYPE', 't3.micro')
KEY_NAME = os.getenv('KEY_NAME')
SECURITY_GROUP_IDS = os.getenv('SECURITY_GROUP_IDS').split(',') if os.getenv('SECURITY_GROUP_IDS') else []
SUBNET_ID = os.getenv('SUBNET_ID')
TAG_NAME = os.getenv('TAG_NAME', 'MyEC2-Boto3')


def provisionar_instancia_ec2(
    ami_id: str,
    instance_type: str,
    key_name: str,
    security_group_ids: list,
    subnet_id: str,
    tag_name: str
) -> str:
    """
    Cria e provisiona uma nova instância EC2 na AWS.

    Args:
        ami_id (str): ID da Amazon Machine Image (AMI) a ser usada.
        instance_type (str): Tipo de instância EC2 (ex: t3.micro).
        key_name (str): Nome do par de chaves SSH para acesso.
        security_group_ids (list): Lista de IDs de Security Groups.
        subnet_id (str): ID da Subnet na VPC para a instância.
        tag_name (str): Valor da tag 'Name' para a instância.

    Returns:
        str: O ID da instância EC2 recém-criada.

    Raises:
        ClientError: Se ocorrer um erro durante a chamada à API da AWS.
        Exception: Para outros erros inesperados.
    """
    try:
        ec2 = boto3.resource('ec2')
        print('Iniciando o provisionamento de uma nova instância EC2...')
        
        instance = ec2.create_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroupIds=security_group_ids,
            SubnetId=subnet_id,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': tag_name}]
            }]
        )
        
        instance_id = instance[0].id
        print(f'Instância EC2 provisionada com sucesso! Name: {tag_name}')
        return instance_id

    except ClientError as e:
        print(f'Erro na API da AWS: {e.response["Error"]["Code"]} - {e.response["Error"]["Message"]}')
        raise
    except Exception as e:
        print(f'Ocorreu um erro inesperado: {e}')
        raise


def main() -> None:
    """Função principal para executar o fluxo de provisionamento."""
    print('Iniciando o processo de criação de instância EC2...')
    try:
        # Chama a função de provisionamento com os parâmetros definidos
        instance_id = provisionar_instancia_ec2(
            ami_id=AMI_ID,
            instance_type=INSTANCE_TYPE,
            key_name=KEY_NAME,
            security_group_ids=SECURITY_GROUP_IDS,
            subnet_id=SUBNET_ID,
            tag_name=TAG_NAME
        )
        print(f'Processo concluído. Instância criada com ID: {instance_id}')
    except Exception:
        print('O processo de criação foi interrompido devido a um erro.')


if __name__ == "__main__":
    main()