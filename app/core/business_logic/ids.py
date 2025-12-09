from datetime import datetime
# ===========================
# ID Generators
# ===========================

def generate_user_id(id: int) -> str:
    return f'VPCUSR{str(id).zfill(4)}'

def generate_employee_id(id: int) -> str:
    return f'VPC{datetime.utcnow().year}E{str(id).zfill(3)}'

def generate_employee_supervisor_id(id: int) -> str:
    return f'VPC{datetime.utcnow().year}S{str(id).zfill(3)}'

def generate_subscription_id(id: int) -> str:
    return f'VPC{datetime.utcnow().year}SUB{str(id).zfill(3)}'

def generate_service_id(id: int) -> str:
    return f'VPC{datetime.utcnow().year}SRV{str(id).zfill(3)}'

def generate_transaction_id(id: int) -> str:
    return f'VPC{datetime.utcnow().year}T{str(id).zfill(3)}'

def generate_property_id(id: int) -> str:
    return f'VPCPT{str(id).zfill(4)}'

def generate_admin_id(id: int) -> str:
    return f'VPCADMIN{str(id).zfill(2)}'

def generate_plan_id(id: int) -> str:
    return f'VPC{datetime.utcnow().year}PLN{str(id).zfill(3)}'

def generate_invoice_id(id: int) -> str:
    return f'VPC{datetime.utcnow().year}INV{str(id).zfill(3)}'

def generate_support_ticket_id(id: int) -> str:
    return f'VPC{datetime.utcnow().year}SUP{str(id).zfill(3)}'

