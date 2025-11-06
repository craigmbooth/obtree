"""
Model mixins for shared functionality across models.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime


class TableConfigMixin:
    """
    Mixin to provide table configuration for models.

    Models should define a __table_config__ class attribute with column definitions.

    Example:
        __table_config__ = {
            'columns': [
                {
                    'field': 'id',
                    'label': 'ID',
                    'visible': True,
                    'sortable': True,
                    'width': 80,
                    'formatter': 'plaintext'
                },
                {
                    'field': 'email',
                    'label': 'Email',
                    'visible': True,
                    'sortable': True,
                    'formatter': 'plaintext'
                }
            ],
            'default_sort': {'field': 'created_at', 'dir': 'desc'}
        }
    """

    __table_config__: Dict[str, Any] = {
        'columns': [],
        'default_sort': None
    }

    @classmethod
    def get_table_config(cls) -> Dict[str, Any]:
        """
        Returns the table configuration for this model.

        Returns:
            Dictionary containing column definitions and table settings.
        """
        config = cls.__table_config__.copy()

        # Add model name for reference
        config['model_name'] = cls.__name__

        # Ensure columns exist
        if 'columns' not in config:
            config['columns'] = []

        # Filter to only visible columns
        config['visible_columns'] = [
            col for col in config['columns'] if col.get('visible', True)
        ]

        return config

    def to_table_dict(self) -> Dict[str, Any]:
        """
        Converts model instance to a dictionary suitable for table display.
        Only includes fields marked as visible in __table_config__.

        Returns:
            Dictionary with visible field values.
        """
        config = self.get_table_config()
        result = {}

        for column in config.get('columns', []):
            if not column.get('visible', True):
                continue

            field = column['field']
            value = getattr(self, field, None)

            # Handle special formatting
            if isinstance(value, datetime):
                result[field] = value.isoformat()
            elif value is None:
                result[field] = None
            else:
                result[field] = value

        return result

    @classmethod
    def get_visible_fields(cls) -> List[str]:
        """
        Returns a list of field names that should be visible in tables.

        Returns:
            List of field names marked as visible.
        """
        config = cls.get_table_config()
        return [col['field'] for col in config.get('columns', []) if col.get('visible', True)]


# Common formatter types for reference:
# - 'plaintext': Simple text display
# - 'datetime': Format datetime objects
# - 'date': Format date objects
# - 'boolean': Display boolean as Yes/No or icons
# - 'badge': Display as colored badge (for status, role, etc.)
# - 'email': Display email with mailto link
# - 'money': Format as currency
# - 'link': Display as hyperlink
