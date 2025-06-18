from datetime import datetime
def generate_user_id(id):
    return f'PC{datetime.utcnow().year}U{str(id).zfill(3)}'
def generate_employee_id(id):
    return f'PC{datetime.utcnow().year}E{str(id).zfill(3)}'
def generate_employee_superviser_id(id):
    return f'PC{datetime.utcnow().year}S{str(id).zfill(3)}'
def generate_employee_admin_id(id):
    return f'PC{datetime.utcnow().year}A{str(id).zfill(3)}'


print(generate_employee_admin_id(1))
print(generate_employee_id(2))
print(generate_employee_superviser_id(3))
print(generate_user_id(4))