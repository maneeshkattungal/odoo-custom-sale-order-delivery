from odoo import _, api, Command, fields, models
from odoo.tools.float_utils import float_compare
from collections import defaultdict


class StockMove(models.Model):
    _inherit = "stock.move"

    def _assign_picking(self):
        Picking = self.env['stock.picking']
        grouped_moves = defaultdict(lambda: self.env['stock.move'])

        for move in self:
            if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) <= 0:
                continue
            # Group moves by product_id for identical products
            grouped_moves[move.product_id] |= move

        for product, moves in grouped_moves.items():
            if len(moves) > 1:
                # If there are identical products, create a single delivery for them
                picking_type_id = self[0].warehouse_id.out_type_id.id  # Get the picking type from the warehouse

                picking_vals = {
                    'partner_id': self[0].partner_id.id,
                    'picking_type_id': picking_type_id,
                    'location_id': self[0].warehouse_id.lot_stock_id.id,
                    'origin': self[0].name,
                }

                picking = Picking.create(picking_vals)

                for move in moves:
                    move.write({'picking_id': picking.id})
                picking.action_confirm()
                picking.action_assign()
            else:
                # For other products, create separate deliveries
                for move in moves:
                    picking_type_id = move.warehouse_id.out_type_id.id

                    picking_vals = {
                        'partner_id': move.partner_id.id,
                        'picking_type_id': picking_type_id,
                        'location_id': move.warehouse_id.lot_stock_id.id,
                        'origin': move.origin,
                    }

                    picking = Picking.create(picking_vals)

                    move.write({'picking_id': picking.id})
                    picking.action_confirm()
                    picking.action_assign()

        return True
