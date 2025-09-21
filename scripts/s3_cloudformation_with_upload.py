import boto3
import logging
import os
import mimetypes # Para detectar tipos de conteúdo dos arquivos
from botocore.exceptions import ClientError

# --- Configuração Inicial ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
cf_client = boto3.client('cloudformation', region_name='us-east-1')

# --- Configuração de Caminhos ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STACK_NAME = 'meu-site-estatico-boto3'
TEMPLATE_V1_PATH = os.path.join(PROJECT_ROOT, 'configs', 's3-bucket-v1.yaml')
TEMPLATE_V2_PATH = os.path.join(PROJECT_ROOT, 'configs', 's3-bucket-v2.yaml')
ASSETS_S3_DIR = os.path.join(PROJECT_ROOT, 'assets', 's3') # Local dos arquivos para upload

# --- UPLOAD DE ARQUIVOS PARA O S3 ---
def upload_assets_to_s3(bucket_name, local_directory):
    """
    Varre um diretório local e faz o upload de todos os arquivos para um bucket S3,
    mantendo a estrutura de subdiretórios e definindo o Content-Type.
    """
    logging.info(f"Iniciando upload de arquivos de '{local_directory}' para o bucket '{bucket_name}'...")
    s3_client = boto3.client('s3')

    try:
        # os.walk percorre recursivamente a árvore de diretórios
        for root, _, files in os.walk(local_directory):
            for filename in files:
                # Monta o caminho completo do arquivo local
                local_path = os.path.join(root, filename)
                
                # Gera o caminho relativo para ser usado como chave do objeto no S3
                relative_path = os.path.relpath(local_path, local_directory)
                s3_key = relative_path.replace(os.sep, "/") # Garante barras normais no S3

                # Adivinha o tipo de conteúdo (MIME type) do arquivo
                content_type, _ = mimetypes.guess_type(local_path)
                if content_type is None:
                    content_type = 'application/octet-stream' # Padrão genérico

                logging.info(f"  -> Uploading {local_path} para s3://{bucket_name}/{s3_key}")
                
                # Faz o upload do arquivo com os metadados corretos
                s3_client.upload_file(
                    local_path,
                    bucket_name,
                    s3_key,
                    ExtraArgs={'ContentType': content_type}
                )
        logging.info("Upload de todos os arquivos concluído com sucesso!")
    except Exception as e:
        logging.error(f"Ocorreu um erro durante o upload dos arquivos: {e}")
        raise

# ... (o resto das funções stack_exists, deploy_stack, get_stack_outputs permanecem iguais) ...
def stack_exists(stack_name):
    try:
        cf_client.describe_stacks(StackName=stack_name)
        return True
    except ClientError as e:
        if "does not exist" in e.response['Error']['Message']:
            return False
        else:
            raise

def deploy_stack(stack_name, template_path):
    logging.info(f"Lendo o arquivo de template: {template_path}")
    with open(template_path, 'r') as f:
        template_body = f.read()

    if stack_exists(stack_name):
        logging.info(f"Stack '{stack_name}' já existe. Iniciando atualização...")
        try:
            cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_IAM']
            )
            waiter = cf_client.get_waiter('stack_update_complete')
            waiter.wait(StackName=stack_name)
            logging.info("Atualização da stack concluída com sucesso!")
        except ClientError as e:
            if "No updates are to be performed" in e.response['Error']['Message']:
                logging.info("Nenhuma atualização necessária. A stack já está no estado desejado.")
            else:
                raise
    else:
        logging.info(f"Stack '{stack_name}' não encontrada. Iniciando criação...")
        cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Capabilities=['CAPABILITY_IAM']
        )
        waiter = cf_client.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)
        logging.info("Criação da stack concluída com sucesso!")

def get_stack_outputs(stack_name):
    if not stack_exists(stack_name):
        logging.warning(f"Stack '{stack_name}' não existe. Não é possível obter outputs.")
        return None

    response = cf_client.describe_stacks(StackName=stack_name)
    outputs = response["Stacks"][0].get("Outputs", [])
    if not outputs:
        logging.info("A stack não possui outputs.")
        return None

    logging.info("--- Outputs da Stack ---")
    output_dict = {}
    for output in outputs:
        logging.info(f"  {output['OutputKey']}: {output['OutputValue']}")
        output_dict[output['OutputKey']] = output['OutputValue']
    logging.info("------------------------")
    return output_dict

def delete_stack(stack_name):
    outputs = get_stack_outputs(stack_name)
    bucket_name = outputs.get('NomeDoBucketCriado') if outputs else None

    if bucket_name:
        try:
            logging.info(f"Esvaziando o bucket S3: {bucket_name}")
            s3 = boto3.resource('s3')
            bucket = s3.Bucket(bucket_name)
            bucket.objects.all().delete()
            logging.info("Bucket esvaziado com sucesso.")
        except Exception as e:
            logging.error(f"Não foi possível esvaziar o bucket antes da exclusão: {e}")

    logging.info(f"Iniciando exclusão da stack '{stack_name}'...")
    cf_client.delete_stack(StackName=stack_name)
    waiter = cf_client.get_waiter('stack_delete_complete')
    waiter.wait(StackName=stack_name)
    logging.info("Stack excluída com sucesso.")


# --- Fluxo de Execução Principal ---
if __name__ == '__main__':
    try:
        # ETAPA 1
        logging.info("--- INICIANDO ETAPA 1: DEPLOY DA V1 (BUCKET PRIVADO) ---")
        deploy_stack(STACK_NAME, TEMPLATE_V1_PATH)
        get_stack_outputs(STACK_NAME)
        input("\n>>> Pressione Enter para continuar para a ETAPA 2 (Update)...")

        # ETAPA 2
        logging.info("\n--- INICIANDO ETAPA 2: DEPLOY DA V2 (SITE ESTÁTICO) ---")
        deploy_stack(STACK_NAME, TEMPLATE_V2_PATH)
        outputs = get_stack_outputs(STACK_NAME)
        
        # --- CHAMADA DA NOVA FUNÇÃO DE UPLOAD ---
        bucket_name = outputs.get('NomeDoBucketCriado')
        if bucket_name:
            upload_assets_to_s3(bucket_name, ASSETS_S3_DIR)
            logging.info("Site implantado! Teste a URL do output 'URLdoSite'.")
        else:
            logging.error("Não foi possível encontrar o nome do bucket nos outputs da stack.")
        
        input("\n>>> Pressione Enter para continuar para a ETAPA 3 (Exclusão)...")

        # ETAPA 3
        logging.info("\n--- INICIANDO ETAPA 3: EXCLUSÃO DA STACK ---")
        delete_stack(STACK_NAME)

    except ClientError as e:
        logging.error(f"Um erro do Boto3 ocorreu: {e.response['Error']['Message']}")
    except FileNotFoundError as e:
        logging.error(f"Erro: Arquivo de template não encontrado. Verifique o caminho. {e}")
    except Exception as e:
        logging.error(f"Um erro inesperado ocorreu: {e}")