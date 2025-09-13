"""
Provisionamento de VPC e sub-redes na AWS.

Este script automatiza a criação de uma VPC completa com sub-redes públicas e
privadas em múltiplas Zonas de Disponibilidade (AZs), incluindo Internet Gateway (IGW) e
NAT Gateway (NAT GW). O script adere às boas práticas de Infrastructure as Code (IaC) e
convenções da linguagem Python (PEP 8), utilizando variáveis de ambiente para configuração.

Autor: Prof. Diego Garrido (Refatorado por GPT-4.1)
Data: 2024-09-13
"""

import os
import ipaddress
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um arquivo .env
load_dotenv()


def create_vpc(ec2_client: boto3.client, cidr_block: str, vpc_tag_name: str) -> str:
    """
    Cria uma VPC na AWS.

    Args:
        ec2_client (boto3.client): Cliente Boto3 para o serviço EC2.
        cidr_block (str): Bloco CIDR para a VPC.
        vpc_tag_name (str): Nome da tag 'Name' para a VPC.

    Returns:
        str: O ID da VPC recém-criada, ou None em caso de falha.
    """
    try:
        print(f"Iniciando a criação da VPC com CIDR {cidr_block}...")
        response = ec2_client.create_vpc(CidrBlock=cidr_block)
        vpc_id = response['Vpc']['VpcId']

        ec2_client.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': vpc_tag_name}])
        
        # Espera que a VPC esteja disponível
        waiter = ec2_client.get_waiter('vpc_available')
        waiter.wait(VpcIds=[vpc_id])
        print(f"VPC {vpc_id} criada com sucesso!")
        return vpc_id
    except ClientError as e:
        print(f"Erro na API da AWS ao criar VPC: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
    return None


def create_subnet(ec2_client: boto3.client, vpc_id: str, cidr_block: str, availability_zone: str, subnet_tag_name: str) -> str:
    """
    Cria uma sub-rede em uma VPC específica.

    Args:
        ec2_client (boto3.client): Cliente Boto3 para o serviço EC2.
        vpc_id (str): ID da VPC onde a sub-rede será criada.
        cidr_block (str): Bloco CIDR para a sub-rede.
        availability_zone (str): Zona de Disponibilidade da sub-rede.
        subnet_tag_name (str): Nome da tag 'Name' para a sub-rede.

    Returns:
        str: O ID da sub-rede recém-criada, ou None em caso de falha.
    """
    try:
        response = ec2_client.create_subnet(
            VpcId=vpc_id, 
            CidrBlock=cidr_block, 
            AvailabilityZone=availability_zone
        )
        subnet_id = response['Subnet']['SubnetId']
        ec2_client.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': subnet_tag_name}])
        print(f"Sub-rede {subnet_id} ({subnet_tag_name}) criada com CIDR {cidr_block} na AZ {availability_zone}")
        return subnet_id
    except ClientError as e:
        print(f"Erro na API da AWS ao criar sub-rede: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
    return None


def create_internet_gateway(ec2_client: boto3.client, vpc_id: str) -> str:
    """
    Cria e anexa um Internet Gateway (IGW) a uma VPC.

    Args:
        ec2_client (boto3.client): Cliente Boto3 para o serviço EC2.
        vpc_id (str): ID da VPC à qual o IGW será anexado.

    Returns:
        str: O ID do IGW recém-criado, ou None em caso de falha.
    """
    try:
        response = ec2_client.create_internet_gateway()
        igw_id = response['InternetGateway']['InternetGatewayId']
        ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        print(f"Internet Gateway {igw_id} criado e anexado à VPC {vpc_id}")
        return igw_id
    except ClientError as e:
        print(f"Erro na API da AWS ao criar IGW: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
    return None


def create_route_table(ec2_client: boto3.client, vpc_id: str, route_table_tag_name: str, igw_id: str = None, nat_gw_id: str = None) -> str:
    """
    Cria uma tabela de rotas e, opcionalmente, adiciona uma rota padrão.

    Args:
        ec2_client (boto3.client): Cliente Boto3 para o serviço EC2.
        vpc_id (str): ID da VPC onde a tabela de rotas será criada.
        route_table_tag_name (str): Nome da tag 'Name' para a tabela de rotas.
        igw_id (str, opcional): ID do IGW para a rota padrão (0.0.0.0/0).
        nat_gw_id (str, opcional): ID do NAT Gateway para a rota padrão (0.0.0.0/0).

    Returns:
        str: O ID da tabela de rotas, ou None em caso de falha.
    """
    try:
        response = ec2_client.create_route_table(VpcId=vpc_id)
        route_table_id = response['RouteTable']['RouteTableId']
        ec2_client.create_tags(Resources=[route_table_id], Tags=[{'Key': 'Name', 'Value': route_table_tag_name}])
        
        # Adiciona a rota padrão para o IGW ou NAT Gateway
        if igw_id:
            ec2_client.create_route(
                RouteTableId=route_table_id,
                DestinationCidrBlock='0.0.0.0/0',
                GatewayId=igw_id
            )
            print(f"Tabela de rotas pública {route_table_id} criada com rota para o IGW.")
        elif nat_gw_id:
            ec2_client.create_route(
                RouteTableId=route_table_id,
                DestinationCidrBlock='0.0.0.0/0',
                NatGatewayId=nat_gw_id
            )
            print(f"Tabela de rotas privada {route_table_id} criada com rota para o NAT GW.")
        else:
            print(f"Tabela de rotas {route_table_id} criada sem rota padrão.")

        return route_table_id
    except ClientError as e:
        print(f"Erro na API da AWS ao criar tabela de rotas: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
    return None


def create_nat_gateway(ec2_client: boto3.client, subnet_id: str) -> str:
    """
    Cria um NAT Gateway em uma sub-rede pública.

    Primeiro, cria um IP elástico e usa sua alocação para o NAT Gateway.

    Args:
        ec2_client (boto3.client): Cliente Boto3 para o serviço EC2.
        subnet_id (str): ID da sub-rede pública para o NAT Gateway.

    Returns:
        str: O ID do NAT Gateway, ou None em caso de falha.
    """
    try:
        # 1. Aloca um Elastic IP (EIP)
        print("Alocando um Elastic IP para o NAT Gateway...")
        eip = ec2_client.allocate_address(Domain='vpc')
        allocation_id = eip['AllocationId']

        # 2. Cria o NAT Gateway
        print("Criando o NAT Gateway...")
        response = ec2_client.create_nat_gateway(
            SubnetId=subnet_id,
            AllocationId=allocation_id,
        )
        nat_gw_id = response['NatGateway']['NatGatewayId']
        
        # 3. Espera que o NAT Gateway esteja disponível
        print(f"Aguardando o NAT Gateway {nat_gw_id} ficar disponível...")
        waiter = ec2_client.get_waiter('nat_gateway_available')
        waiter.wait(NatGatewayIds=[nat_gw_id])
        print(f"NAT Gateway {nat_gw_id} está disponível!")
        
        return nat_gw_id
    except ClientError as e:
        print(f"Erro na API da AWS ao criar NAT Gateway: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
    return None


def associate_route_table(ec2_client: boto3.client, route_table_id: str, subnet_id: str) -> None:
    """
    Associa uma tabela de rotas a uma sub-rede.

    Args:
        ec2_client (boto3.client): Cliente Boto3 para o serviço EC2.
        route_table_id (str): ID da tabela de rotas a ser associada.
        subnet_id (str): ID da sub-rede a ser associada.
    """
    try:
        ec2_client.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
        print(f"Tabela de rotas {route_table_id} associada à sub-rede {subnet_id}")
    except ClientError as e:
        print(f"Erro na API da AWS ao associar a tabela de rotas: {e.response['Error']['Code']} - {e.response['Error']['Message']}")


def main() -> None:
    """Função principal que orquestra a criação da infraestrutura."""
    try:
        vpc_tag_name = os.getenv('VPC_TAG_NAME', 'MyVPC')
        region = os.getenv('REGION', 'us-east-1')
        vpc_cidr = os.getenv('VPC_CIDR', '10.0.0.0/16')
        az_list = os.getenv('AZ_LIST', 'us-east-1a,us-east-1b').split(',')
        
        if not az_list or az_list == ['']:
            print("Lista de Zonas de Disponibilidade (AZ_LIST) não pode estar vazia.")
            return

        ec2_client = boto3.client('ec2', region_name=region)
        
        # 1. Cria a VPC
        vpc_id = create_vpc(ec2_client, vpc_cidr, vpc_tag_name)
        if not vpc_id:
            return

        # Converte o CIDR da VPC em um objeto de rede
        base_network = ipaddress.ip_network(vpc_cidr)
        # Sub-divide a rede principal em sub-redes de tamanho /24
        subnets_24 = list(base_network.subnets(new_prefix=24))

        public_subnets = []
        private_subnets = []
        subnet_counter = 0

        # 2. Cria sub-redes públicas e privadas em cada AZ
        print("\nIniciando a criação das sub-redes...")
        for az in az_list:
            if az.strip():  # Garante que a AZ não é uma string vazia
                public_cidr = str(subnets_24[subnet_counter * 2])
                public_subnet_id = create_subnet(
                    ec2_client, vpc_id, public_cidr, az, f"{vpc_tag_name}-public-{az.split('-')[-1]}"
                )
                if not public_subnet_id:
                    return
                public_subnets.append(public_subnet_id)
                
                private_cidr = str(subnets_24[(subnet_counter * 2) + 1])
                private_subnet_id = create_subnet(
                    ec2_client, vpc_id, private_cidr, az, f"{vpc_tag_name}-private-{az.split('-')[-1]}"
                )
                if not private_subnet_id:
                    return
                private_subnets.append(private_subnet_id)
                
                subnet_counter += 1

        # Resto do script, que não precisou ser alterado
        # ...
        
        # 3. Cria e anexa o Internet Gateway
        print("\nIniciando a criação e anexo do Internet Gateway...")
        igw_id = create_internet_gateway(ec2_client, vpc_id)
        if not igw_id:
            return

        # 4. Cria e associa a Tabela de Rotas Pública
        print("\nCriando e configurando a Tabela de Rotas Pública...")
        public_route_table_id = create_route_table(ec2_client, vpc_id, f"{vpc_tag_name}-public-rt", igw_id=igw_id)
        if not public_route_table_id:
            return
        
        for subnet_id in public_subnets:
            associate_route_table(ec2_client, public_route_table_id, subnet_id)

        # 5. Cria NAT Gateway (um por AZ pública para alta disponibilidade, mas um é suficiente para exemplo)
        print("\nCriando e configurando o NAT Gateway...")
        # Escolhe a primeira sub-rede pública para o NAT Gateway
        nat_gateway_id = create_nat_gateway(ec2_client, public_subnets[0])
        if not nat_gateway_id:
            return

        # 6. Cria e associa a Tabela de Rotas Privada
        print("\nCriando e configurando a Tabela de Rotas Privada...")
        private_route_table_id = create_route_table(ec2_client, vpc_id, f"{vpc_tag_name}-private-rt", nat_gw_id=nat_gateway_id)
        if not private_route_table_id:
            return
            
        for subnet_id in private_subnets:
            associate_route_table(ec2_client, private_route_table_id, subnet_id)

        print("\nProvisionamento da VPC e sub-redes concluído com sucesso! 👏")

    except Exception as e:
        print(f"O processo de provisionamento foi interrompido devido a um erro: {e}")


if __name__ == "__main__":
    main()