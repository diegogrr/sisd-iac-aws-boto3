"""
Automatiza a criação de uma nova instância EC2 utilizando a API do Boto3.

Comando equivalente do AWS CLI:
    aws ec2 run-instances --image-id ami-0b09ffb6d8b58ca91 --count 1 --instance-type t2.micro --key-name vockey
"""

import boto3

# Parâmetros de configuração
AMI_ID = 'ami-0b09ffb6d8b58ca91'  # Exemplo de ID da AMI
INSTANCE_TYPE = 't2.micro'
KEY_PAIR_NAME = 'vockey'


def create_ec2_instance():
    ec2 = boto3.resource('ec2')
    instance = ec2.create_instances(
        ImageId=AMI_ID,
        MinCount=1,
        MaxCount=1,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_PAIR_NAME
    )
    print(f"Instância EC2 criada: {instance[0].id}")

if __name__ == "__main__":
    create_ec2_instance()
