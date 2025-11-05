from datetime import datetime
import uuid

def generate_subscription_id(category: str, sub_type: str) -> str:
    """Generate a unique subscription ID like SUB-PRM-PM-20251105-ABC123"""
    prefix = "SUB"
    category_code = ''.join(word[0].upper() for word in category.split()[:2])  # e.g. Property Management → PM
    sub_code = sub_type[:3].upper()  # e.g. Premium → PRE
    timestamp = datetime.now().strftime("%Y%m%d")
    random_code = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{sub_code}-{category_code}-{timestamp}-{random_code}"
