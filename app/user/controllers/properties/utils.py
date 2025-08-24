from datetime import datetime




def generate_property_id(id:int):
    return f'PC{datetime.utcnow().year}P{str(id).zfill(3)}'

def generate_document_id(id:int):
    return f'PC{datetime.utcnow().year}D{str(id).zfill(3)}'

