"""
Encerramento de Instâncias EC2 na AWS com Boto3.

Este script automatiza o encerramento de instâncias EC2,
aderindo às boas práticas de Infrastructure as Code (IaC) e
convenções da linguagem Python (PEP 8).

Autor: Prof. Diego Garrido (Refatorado por GPT-4.1)
Data: 2024-09-13
"""
import boto3
from botocore.exceptions import ClientError


def listar_instancias_ec2() -> list:
    """
    Lista todas as instâncias EC2 na conta AWS.

    Retorna:
        list: Uma lista de dicionários, onde cada dicionário contém o ID,
              estado e nome (tag 'Name') de uma instância.
              Exemplo: [{'id': 'i-12345', 'state': 'running', 'name': 'WebServer'}]
    
    Raises:
        ClientError: Se ocorrer um erro durante a chamada à API da AWS.
    """
    try:
        ec2_client = boto3.client('ec2')
        response = ec2_client.describe_instances()

        instancias = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_id = instance.get('InstanceId')
                state = instance.get('State', {}).get('Name')
                name = 'N/A'
                
                # Busca a tag 'Name'
                for tag in instance.get('Tags', []):
                    if tag.get('Key') == 'Name':
                        name = tag.get('Value')
                        break
                
                instancias.append({'id': instance_id, 'state': state, 'name': name})
        
        return instancias

    except ClientError as e:
        print(f"Erro na API da AWS ao listar instâncias: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        raise
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao listar instâncias: {e}")
        raise


def encerrar_instancia_ec2(instance_id: str) -> None:
    """
    Encerra (termina) uma instância EC2 na AWS.

    Args:
        instance_id (str): O ID da instância EC2 a ser encerrada.

    Raises:
        ClientError: Se ocorrer um erro durante a chamada à API da AWS.
    """
    try:
        ec2_client = boto3.client('ec2')
        print(f"Iniciando o encerramento da instância EC2: {instance_id}")
        ec2_client.terminate_instances(InstanceIds=[instance_id])
        print(f"Instância EC2 {instance_id} encerrada com sucesso!")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidInstanceID.NotFound':
            print(f"Erro: A instância com o ID '{instance_id}' não foi encontrada.")
        else:
            print(f"Erro na API da AWS: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        raise
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao encerrar a instância {instance_id}: {e}")
        raise


def main() -> None:
    """Função principal para executar o fluxo de encerramento de instâncias."""
    try:
        print("Listando instâncias EC2 disponíveis...")
        instancias = listar_instancias_ec2()
        
        if not instancias:
            print("Não há instâncias EC2 disponíveis para listar.")
            return

        print("\nInstâncias EC2 disponíveis:")
        # Ordena as instâncias pelo estado e depois pelo nome, para melhor visualização
        instancias_ordenadas = sorted(instancias, key=lambda x: (x['state'], x['name']))

        for idx, instancia in enumerate(instancias_ordenadas):
            print(f"{idx + 1}. ID: {instancia['id']}, Estado: {instancia['state']}, Nome: {instancia['name']}")
        
        try:
            escolha = int(input("\nDigite o número da instância que deseja encerrar: ")) - 1
            if 0 <= escolha < len(instancias_ordenadas):
                instance_id = instancias_ordenadas[escolha]['id']
                encerrar_instancia_ec2(instance_id)
            else:
                print("Escolha inválida. O processo foi abortado.")
        except ValueError:
            print("Entrada inválida. Por favor, digite um número inteiro. O processo foi abortado.")

    except Exception:
        print("O processo foi interrompido devido a um erro.")


if __name__ == '__main__':
    main()