# Copyright <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WizardModel(models.TransientModel):
    _name = "connector_magento.add_backend.wizard"
    _description = "Wizard model"

    def get_default_object(self, model):
        domain = []
        active_ids = self.env.context.get("active_ids", False)
        active_model = self.env.context.get("active_model", False)

        if not active_ids:
            return []
        domain.append(("id", "in", active_ids))
        export = self.env[active_model]
        if active_model == model:
            return export.search(domain)

    def get_default_model(self):
        model = self.env.context.get("active_model", False)
        if model:
            return self.env["ir.model"].search([("model", "=", model)], limit=1).id
        return False

    def get_default_backend(self):
        return self.env["magento.backend"].search([], limit=1)

    def _get_ids_and_model(self):
        active_model = self.env.context.get("active_model", False)
        binding_field = "magento_bind_ids"
        if active_model == "product.template":
            binding_field = "magento_variant_bind_ids"

        if hasattr(self.env[active_model], binding_field):
            bindings = self.env[active_model].browse(
                self.env.context.get("active_ids", [])
            )
            if active_model == "product.template":
                # Necesito que me devuelva en el caso de product_template los productos variantes
                # que estan asociados a la plantilla
                bindings = bindings.mapped("product_variant_ids")
            return bindings, getattr(bindings, binding_field)._name
        else:
            raise ValueError("Model not supported")

    def check_backend_binding(self, to_export_ids=None, dest_model=None):
        if not dest_model or not to_export_ids:
            (to_export_ids, dest_model) = self._get_ids_and_model()
        for model in to_export_ids:
            bind_count = self.env[dest_model].search_count(
                [("odoo_id", "=", model.id), ("backend_id", "=", self.backend_id.id)]
            )
            if not bind_count:
                vals = {
                    "odoo_id": model.id,
                    "backend_id": self.backend_id.id,
                    "product_type": self.product_type,
                }
                if self.product_type == "grouped":
                    vals["product_links"] = [(6, 0, self.product_links.ids)]
                binding = self.env[dest_model].create(vals)
                if self.action == "import":
                    if getattr(binding, "sync_from_magento", False):
                        binding.sync_from_magento()
                elif self.action == "export":
                    if getattr(binding, "sync_to_magento", False):
                        binding.sync_to_magento()

    # Fields
    product_type = fields.Selection(
        [
            ("simple", "Simple Product"),
            # ('configurable', 'Configurable Product'),
            ("grouped", "Grouped Product"),
            # ('bundle', 'Bundle Product'),
            # ('virtual', 'Virtual Product'),
            # ('downloadable', 'Downloadable Product'),
        ],
        default="simple",
        required=True,
    )
    product_links = fields.Many2many(
        "magento.product.product",
        "magento_product_product_grouped_rel",
        string="Linked Products",
    )
    backend_id = fields.Many2one(
        comodel_name="magento.backend", required=True, default=get_default_backend
    )
    model_id = fields.Many2one("ir.model", default=get_default_model)
    action = fields.Selection(
        [
            ("only_create", "Only create binding"),
            ("import", "Import"),
            ("export", "Export"),
        ],
        default="export",
        required=True,
    )

    def action_accept(self):
        self.ensure_one()
        self.check_backend_binding()
