# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from pytz import timezone

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.components.mapper import mapping

DATES_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
UTC = timezone("UTC")


class MagentoImportMapper(AbstractComponent):
    _name = "magento.import.mapper"
    _inherit = ["base.magento.connector", "base.import.mapper"]
    _usage = "import.mapper"

    @mapping
    def data(self, record):
        return {"data": record}


class MagentoExportMapper(AbstractComponent):
    _name = "magento.export.mapper"
    _inherit = ["base.magento.connector", "base.export.mapper"]
    _usage = "export.mapper"


def normalize_datetime(field):
    """Change a invalid date which comes from Magento, if
    no real date is set to null for correct import to
    OpenERP"""

    def modifier(self, record, to_attr):
        value = record[field]
        if value and value != "0000-00-00 00:00:00":
            dt = None
            try:
                dt = datetime.fromisoformat(value).astimezone(UTC)
            except ValueError:
                for fmt in DATES_FORMATS:
                    try:
                        dt = datetime.strptime(value, fmt)
                    except ValueError:
                        pass
                    else:
                        break
            if dt:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None
    return modifier
