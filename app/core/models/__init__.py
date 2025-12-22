from app.core.services.db import Base, metadata

# Import all models here so Alembic / Base.metadata.create_all sees them
from .consultation import Consultation, ConsultationHistory
from .newsletter import NewsLetter
from .property_details import PropertyDetails, PropertyHistory
from .property_documents import PropertyDocuments
from .subscriptions_plans import SubscriptionPlans, SubscriptionPlansHistory
from .subscriptions import Subscriptions, SubscriptionHistory
from .subscriptions_transactions import SubscriptionsTransactions
from .additional_services import AdditionalServices,AdditionalServicesHistory
from .associates import Associates

__all__ = [
    "Base",
    "metadata",
    "Associates",
    "Consultation",
    "ConsultationHistory",
    "Discounts",
    "NewsLetter",
    "PropertyDetails",
    "PropertyHistory",
    "PropertyDocuments",
    "Subscriptions",
    "SubscriptionHistory",
    "SubscriptionPlans",
    "SubscriptionPlansHistory",
    "TransactionSubOffline",
    "AdditionalServices",
    'AdditionalServicesHistory',
    'SubscriptionsTransactions'
]
