"""
API routes for retrieving table configuration from models.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.models import User, Organization, OrganizationMembership, Invite
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Whitelist of models that can be queried for table configuration
# This prevents arbitrary model access for security
ALLOWED_MODELS = {
    'User': User,
    'Organization': Organization,
    'OrganizationMembership': OrganizationMembership,
    'Invite': Invite,
}


@router.get("/table-config/{model_name}", response_model=Dict[str, Any])
def get_table_config(model_name: str):
    """
    Retrieve table configuration for a specific model.

    Args:
        model_name: Name of the model (User, Organization, OrganizationMembership, Invite)

    Returns:
        Dictionary containing table configuration including columns, default sort, etc.

    Raises:
        HTTPException: If model_name is not in the allowed list
    """
    logger.info("table_config_requested", model_name=model_name)

    if model_name not in ALLOWED_MODELS:
        logger.warning("table_config_invalid_model", model_name=model_name)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table configuration not available for model: {model_name}"
        )

    model_class = ALLOWED_MODELS[model_name]

    # Check if model has TableConfigMixin
    if not hasattr(model_class, 'get_table_config'):
        logger.error("table_config_missing_mixin", model_name=model_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model {model_name} does not implement table configuration"
        )

    config = model_class.get_table_config()
    logger.info("table_config_returned", model_name=model_name, column_count=len(config.get('columns', [])))

    return config
