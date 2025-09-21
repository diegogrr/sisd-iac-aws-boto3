import boto3
import logging
import os
from botocore.exceptions import ClientError

# --- Configuração Inicial ---
# Configura o logging para exibir mensagens informativas no terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define o cliente do CloudFormation que usaremos para interagir com a AWS
# É importante especificar a região para garantir consistência
cf_client = boto3.client('cloudformation', region_name='us-east-1')

# --- Configuração de Caminhos ---
# Descobre o caminho absoluto do diretório onde este script (s3_cloudformation.py) está localizado.
# __file__ é uma variável especial do Python que contém o caminho para o arquivo atual.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Como o script está em 'projeto/scripts', subimos um nível para encontrar a raiz do projeto.
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Agora, construímos os caminhos para os templates a partir da raiz do projeto.
# Isso garante que sempre funcionará, não importa de onde você execute o script.
STACK_NAME = 'meu-site-estatico-boto3'
TEMPLATE_V1_PATH = os.path.join(PROJECT_ROOT, 'configs', 's3-bucket-v1.yaml')
TEMPLATE_V2_PATH = os.path.join(PROJECT_ROOT, 'configs', 's3-bucket-v2.yaml')


def stack_exists(stack_name):
    """Verifica se uma stack do CloudFormation já existe."""
    try:
        cf_client.describe_stacks(StackName=stack_name)
        return True
    except ClientError as e:
        # A exceção 'ValidationError' com a mensagem "does not exist" é a forma
        # que a API nos diz que a stack não foi encontrada.
        if "does not exist" in e.response['Error']['Message']:
            return False
        else:
            raise

def deploy_stack(stack_name, template_path):
    """
    Cria uma nova stack ou atualiza uma existente.
    Diferente do 'aws cloudformation deploy', o Boto3 exige que a gente
    verifique se a stack existe para saber se devemos criar ou atualizar.
    """
    logging.info(f"Lendo o arquivo de template: {template_path}")
    with open(template_path, 'r') as f:
        template_body = f.read()

    if stack_exists(stack_name):
        logging.info(f"Stack '{stack_name}' já existe. Iniciando atualização...")
        try:
            # Tenta atualizar a stack
            cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_IAM'] # Boa prática incluir, caso o template crie roles
            )
            # 'waiter' é um recurso do Boto3 que pausa o script até a operação terminar
            waiter = cf_client.get_waiter('stack_update_complete')
            waiter.wait(StackName=stack_name)
            logging.info("Atualização da stack concluída com sucesso!")
        except ClientError as e:
            # Se não houver mudanças, a API retorna um erro específico que podemos ignorar
            if "No updates are to be performed" in e.response['Error']['Message']:
                logging.info("Nenhuma atualização necessária. A stack já está no estado desejado.")
            else:
                raise
    else:
        logging.info(f"Stack '{stack_name}' não encontrada. Iniciando criação...")
        # Cria a stack, pois ela não existe
        cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Capabilities=['CAPABILITY_IAM']
        )
        # Pausa o script até a criação da stack terminar
        waiter = cf_client.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)
        logging.info("Criação da stack concluída com sucesso!")

def get_stack_outputs(stack_name):
    """Busca e exibe os Outputs de uma stack."""
    if not stack_exists(stack_name):
        logging.warning(f"Stack '{stack_name}' não existe. Não é possível obter outputs.")
        return

    response = cf_client.describe_stacks(StackName=stack_name)
    outputs = response["Stacks"][0].get("Outputs", [])
    if not outputs:
        logging.info("A stack não possui outputs.")
        return

    logging.info("--- Outputs da Stack ---")
    for output in outputs:
        logging.info(f"  {output['OutputKey']}: {output['OutputValue']}")
    logging.info("------------------------")

def delete_stack(stack_name):
    """Exclui uma stack do CloudFormation."""
    # Antes de excluir, é preciso esvaziar o bucket S3
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        outputs = response["Stacks"][0].get("Outputs", [])
        bucket_name = None
        for out in outputs:
            if out['OutputKey'] == 'NomeDoBucketCriado':
                bucket_name = out['OutputValue']
                break
        
        if bucket_name:
            logging.info(f"Esvaziando o bucket S3: {bucket_name}")
            s3 = boto3.resource('s3')
            bucket = s3.Bucket(bucket_name)
            bucket.objects.all().delete()
            logging.info("Bucket esvaziado com sucesso.")

    except Exception as e:
        logging.error(f"Não foi possível esvaziar o bucket antes da exclusão: {e}")
        # Mesmo com erro, tentamos prosseguir com a exclusão da stack

    logging.info(f"Iniciando exclusão da stack '{stack_name}'...")
    cf_client.delete_stack(StackName=stack_name)
    waiter = cf_client.get_waiter('stack_delete_complete')
    waiter.wait(StackName=stack_name)
    logging.info("Stack excluída com sucesso.")


# --- Fluxo de Execução Principal ---
if __name__ == '__main__':
    try:
        # ETAPA 1: Criar a stack com a Versão 1
        logging.info("--- INICIANDO ETAPA 1: DEPLOY DA V1 (BUCKET PRIVADO) ---")
        deploy_stack(STACK_NAME, TEMPLATE_V1_PATH)
        get_stack_outputs(STACK_NAME)
        input("\n>>> Pressione Enter para continuar para a ETAPA 2 (Update)...")

        # ETAPA 2: Atualizar a stack com a Versão 2
        logging.info("\n--- INICIANDO ETAPA 2: DEPLOY DA V2 (SITE ESTÁTICO) ---")
        deploy_stack(STACK_NAME, TEMPLATE_V2_PATH)
        get_stack_outputs(STACK_NAME)
        logging.info("Agora você pode fazer o upload do 'index.html' e testar a URL do site.")
        input("\n>>> Pressione Enter para continuar para a ETAPA 3 (Exclusão)...")

        # ETAPA 3: Excluir a stack
        logging.info("\n--- INICIANDO ETAPA 3: EXCLUSÃO DA STACK ---")
        delete_stack(STACK_NAME)

    except ClientError as e:
        logging.error(f"Um erro do Boto3 ocorreu: {e.response['Error']['Message']}")
    except FileNotFoundError as e:
        logging.error(f"Erro: Arquivo de template não encontrado. Verifique o caminho. {e}")
    except Exception as e:
        logging.error(f"Um erro inesperado ocorreu: {e}")