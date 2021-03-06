from odoo import api,fields,models,_
import time
from odoo.exceptions import UserError, RedirectWarning, ValidationError, except_orm, Warning
from datetime import datetime, date
from datetime import datetime, timedelta
from dateutil.relativedelta import *
from odoo.tools.safe_eval import safe_eval
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_round
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils
import math
import re    
from num2words import num2words


class PwkPurchaseRequestDateLine(models.Model):
    _name = "pwk.purchase.request.date.line"

    reference = fields.Many2one('pwk.purchase.request.date', string='Reference')        
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(compute="_get_sale_fields", string='Thick', store=True)
    width = fields.Float(compute="_get_sale_fields", string='Width', store=True)
    length = fields.Float(compute="_get_sale_fields", string='Length', store=True)
    grade_id = fields.Many2one(compute="_get_sale_fields", comodel_name='pwk.grade', string='Grade', store=True)
    quantity = fields.Float(string='PCS')
    volume = fields.Float(compute="_get_volume", string='M3')

    @api.depends('quantity')
    def _get_volume(self):
        for res in self:
            res.volume = res.quantity * res.thick * res.width * res.length / 1000000000    

    @api.depends('product_id')
    def _get_sale_fields(self):
        for res in self:
            if res.product_id:
                res.thick = res.product_id.tebal
                res.width = res.product_id.lebar
                res.length = res.product_id.panjang
                res.grade_id = res.product_id.grade.id    

class PwkPurchaseRequestDate(models.Model):
    _name = "pwk.purchase.request.date"

    reference = fields.Many2one('pwk.purchase.request', string='Reference')            
    date_start = fields.Date('Start Period')
    date_end = fields.Date('End Period')    
    line_ids = fields.One2many('pwk.purchase.request.date.line', 'reference', string='Lines')

class PwkPurchaseRequestVolume(models.Model):
    _name = "pwk.purchase.request.volume"
    _order = "jenis_kayu asc, thick asc,width asc,length asc"

    reference = fields.Many2one('pwk.purchase.request', string='Reference')    
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(compute="_get_sale_fields", string='Thick', store=True)
    width = fields.Float(compute="_get_sale_fields", string='Width', store=True)
    length = fields.Float(compute="_get_sale_fields", string='Length', store=True)
    jenis_kayu = fields.Char(compute="_get_sale_fields", string='Jenis Kayu', store=True)
    grade_id = fields.Many2one(compute="_get_sale_fields", comodel_name='pwk.grade', string='Grade', store=True)
    date_start = fields.Date('Start Period')
    date_end = fields.Date('End Period')

    volume_ordered = fields.Float(string='Volume PR', digits=dp.get_precision('FourDecimal'))

    quantity = fields.Float(compute="_get_quantity", string='Requested PCS', digits=dp.get_precision('ZeroDecimal'))
    volume = fields.Float(string='Requested M3', digits=dp.get_precision('FourDecimal'))
    
    quantity_pr = fields.Float(compute="_get_quantity", string='Assigned PCS', digits=dp.get_precision('ZeroDecimal'))
    volume_pr = fields.Float(compute="_get_volume", string='Assigned M3', digits=dp.get_precision('FourDecimal'))
    
    quantity_remaining = fields.Float(compute="_get_quantity", string='Remaining PCS', digits=dp.get_precision('ZeroDecimal'))
    volume_remaining = fields.Float(compute="_get_volume", string='Remaining M3', digits=dp.get_precision('FourDecimal'))
    
    product_uom_id = fields.Many2one("uom.uom", string='UoM')
    truck = fields.Char(string='Truck')    

    @api.multi
    def _get_quantity(self):
        for res in self:            
            res.quantity = res.volume / res.thick / res.width / res.length * 1000000000    
            res.quantity_pr = res.volume_pr / res.thick / res.width / res.length * 1000000000    
            res.quantity_remaining = res.volume_remaining / res.thick / res.width / res.length * 1000000000    

    @api.multi
    def _get_volume(self):
        for res in self:
            volume_remaining = 0
            volume_pr = 0

            if res.reference.date_ids and res.reference.date_ids.line_ids:
                for line in res.reference.date_ids.line_ids:
                    if line.product_id == res.product_id:
                        volume_pr += line.quantity

            res.volume_pr = volume_pr
            res.volume_remaining = res.volume - volume_pr        

    @api.depends('product_id')
    def _get_sale_fields(self):
        for res in self:
            if res.product_id:
                res.thick = res.product_id.tebal
                res.width = res.product_id.lebar
                res.length = res.product_id.panjang
                res.grade_id = res.product_id.grade.id
                res.jenis_kayu = res.product_id.jenis_kayu.name

class PwkPurchaseRequestLine(models.Model):
    _name = "pwk.purchase.request.line"
    _order = "jenis_kayu asc, thick asc,width asc,length asc"

    reference = fields.Many2one('pwk.purchase.request', string='Reference')    
    is_selected = fields.Boolean('.')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(compute="_get_sale_fields", string='Thick', store=True)
    width = fields.Float(compute="_get_sale_fields", string='Width', store=True)
    length = fields.Float(compute="_get_sale_fields", string='Length', store=True)
    jenis_kayu = fields.Char(compute="_get_sale_fields", string='Jenis Kayu', store=True)
    grade_id = fields.Many2one(compute="_get_sale_fields", comodel_name='pwk.grade', string='Grade', store=True)
    date_start = fields.Date('Start Period')
    date_end = fields.Date('End Period')

    quantity_ordered = fields.Float(string='PCS', digits=dp.get_precision('ZeroDecimal'))
    volume_ordered = fields.Float(string='M3', digits=dp.get_precision('FourDecimal'))

    quantity = fields.Float(string='Requested PCS', digits=dp.get_precision('ZeroDecimal'))
    volume = fields.Float(compute="_get_volume", string='Requested M3', digits=dp.get_precision('FourDecimal'))
    
    quantity_pr = fields.Float(compute="_get_quantity", string='Assigned PCS', digits=dp.get_precision('ZeroDecimal'))
    volume_pr = fields.Float(compute="_get_volume", string='Assigned M3', digits=dp.get_precision('FourDecimal'))
    
    quantity_remaining = fields.Float(compute="_get_quantity", string='Remaining PCS', digits=dp.get_precision('ZeroDecimal'))
    volume_remaining = fields.Float(compute="_get_volume", string='Remaining M3', digits=dp.get_precision('FourDecimal'))
    
    product_uom_id = fields.Many2one("uom.uom", string='UoM')
    truck = fields.Char(string='Truck')    

    @api.multi
    def _get_quantity(self):
        for res in self:
            quantity_remaining = 0
            quantity_pr = 0

            if res.reference.date_ids and res.reference.date_ids.line_ids:
                for line in res.reference.date_ids.line_ids:
                    if line.product_id == res.product_id:
                        quantity_pr += line.quantity

            res.quantity_pr = quantity_pr
            res.quantity_remaining = res.quantity - quantity_pr

    @api.depends('quantity')
    def _get_volume(self):
        for res in self:
            res.volume = res.quantity * res.thick * res.width * res.length / 1000000000    
            res.volume_pr = res.quantity_pr * res.thick * res.width * res.length / 1000000000    
            res.volume_remaining = res.quantity_remaining * res.thick * res.width * res.length / 1000000000    

    @api.depends('product_id')
    def _get_sale_fields(self):
        for res in self:
            if res.product_id:
                res.thick = res.product_id.tebal
                res.width = res.product_id.lebar
                res.length = res.product_id.panjang
                res.grade_id = res.product_id.grade.id
                res.jenis_kayu = res.product_id.jenis_kayu.name

class PwkPurchaseRequest(models.Model):    
    _name = "pwk.purchase.request"

    pr_type = fields.Selection([('Bahan Baku','Bahan Baku'),('Bahan Penolong','Bahan Penolong')], string='Jenis PR')
    formula_type = fields.Selection([('PCS','PCS'),('M3','M3')], string='Satuan')
    date_id = fields.Many2one('pwk.purchase.request.date', string="Weekly PR")
    name = fields.Char('Nomor PR')
    date_start = fields.Date('Period')
    date_end = fields.Date('Period')
    qty_assign = fields.Integer('Quantity')
    date = fields.Date('Tanggal PR')    
    product_type = fields.Selection([
        ('Produksi','Produksi'),
        ('Mekanik','Mekanik'),
        ('Elektrik','Elektrik')]
        , string="Tipe", default="Produksi")
    state = fields.Selection([
        ('Draft','Draft'),
        ('Department Approved','Department Approved'),
        ('Purchasing Approved','Purchasing Approved'),
        ('Cancelled','Cancelled')]
        , string="Status", default="Draft")
    line_ids = fields.One2many('pwk.purchase.request.line', 'reference', string='Lines')
    volume_ids = fields.One2many('pwk.purchase.request.volume', 'reference', string='Lines')
    date_ids = fields.One2many('pwk.purchase.request.date', 'reference', string='Dates')

    @api.multi
    def button_assign(self):
        for res in self:
            if res.date_start and res.date_end:
                if res.formula_type == "PCS":
                    if res.line_ids:
                        for line in res.line_ids:                        
                            if line.quantity_ordered > 0:
                                if (line.quantity <= line.quantity_remaining):
                                    current_date_id = self.env['pwk.purchase.request.date'].search([
                                        ('reference', '=', res.id),
                                        ('date_start', '=', res.date_start),
                                        ('date_end', '=', res.date_end)
                                    ])

                                    if not current_date_id:
                                        current_date_id = self.env['pwk.purchase.request.date'].create({
                                            'reference': res.id,
                                            'date_start': res.date_start,
                                            'date_end': res.date_end,
                                        })

                                    self.env['pwk.purchase.request.date.line'].create({
                                        'reference': current_date_id.id,
                                        'product_id': line.product_id.id,
                                        'quantity': line.quantity_ordered
                                    })

                                    line.write({                                
                                        'is_selected': False,
                                        'quantity_ordered': 0
                                    })

                                else:
                                    raise UserError(_('Quantity PR melebihi Quantity yang di Request'))

                elif res.formula_type == "M3":
                    if res.volume_ids:
                        for line in res.volume_ids:                        
                            if line.volume_ordered > 0:
                                if (line.volume <= line.volume_remaining):
                                    current_date_id = self.env['pwk.purchase.request.date'].search([
                                        ('reference', '=', res.id),
                                        ('date_start', '=', res.date_start),
                                        ('date_end', '=', res.date_end)
                                    ])

                                    if not current_date_id:
                                        current_date_id = self.env['pwk.purchase.request.date'].create({
                                            'reference': res.id,
                                            'date_start': res.date_start,
                                            'date_end': res.date_end,
                                        })

                                    self.env['pwk.purchase.request.date.line'].create({
                                        'reference': current_date_id.id,
                                        'product_id': line.product_id.id,
                                        'quantity': line.volume_ordered
                                    })

                                    line.write({                                
                                        'is_selected': False,
                                        'volume_ordered': 0
                                    })

                                else:
                                    raise UserError(_('Quantity PR melebihi Quantity yang di Request'))
                
            else:
                raise UserError(_('Periode PR belum diisi'))          

            res.write({
                'date_start': False,
                'date_end': False,
            })


    @api.multi
    def button_draft(self):
        for res in self:
            res.state = "Draft"    

    @api.multi
    def button_approve1(self):
        for res in self:
            res.state = "Department Approved"

    @api.multi
    def button_approve2(self):
        for res in self:
            res.state = "Purchasing Approved"

    def get_sequence(self, name=False, obj=False, product=None, context=None):
        sequence_id = self.env['ir.sequence'].search([
            ('name', '=', name),
            ('code', '=', obj),
            ('suffix', '=', '.PR.' + product + '%(month)s-%(year)s')
        ])
        if not sequence_id :
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': name,
                'code': obj,
                'implementation': 'no_gap',
                'suffix': '.PR.' + product + '%(month)s-%(year)s',
                'padding': 3
            })
        return sequence_id.next_by_id()

    @api.model
    def create(self, vals):
        product_type = ""

        if vals.get('product_type') == "Produksi":
            product_type = "PD."
        elif vals.get('product_type') == "Mekanik":
            product_type = "MK."
        elif vals.get('product_type') == "Elektrik":
            product_type = "EL."

        vals['name'] = self.get_sequence('Purchase Request', 'pwk.purchase.request', '%s' % product_type)
        # vals['name'] = self.get_sequence('Rencana Produksi Bulanan', 'pwk.rpb', '%s' % year_month)
        return super(PwkPurchaseRequest, self).create(vals)    

class PwkRpbContainerLine(models.Model):    
    _name = "pwk.rpb.container.line"

    reference = fields.Many2one('pwk.rpb.container', string='Reference')
    sale_id = fields.Many2one('sale.order', 'No. Order')
    sale_line_id = fields.Many2one('sale.order.line', 'No. Order Line')
    partner_id = fields.Many2one(compute="_get_sale_fields", comodel_name='res.partner', string='Buyer')
    product_id = fields.Many2one(compute="_get_sale_fields", comodel_name='product.product', string='Product')
    thick = fields.Float(compute="_get_sale_fields", string='Thick')
    width = fields.Float(compute="_get_sale_fields", string='Width')
    length = fields.Float(compute="_get_sale_fields", string='Length')
    glue_id = fields.Many2one(compute="_get_sale_fields", comodel_name='pwk.glue', string='Glue')
    grade_id = fields.Many2one(compute="_get_sale_fields", comodel_name='pwk.grade', string='Grade')        
    total_volume = fields.Float(compute="_get_sale_fields", string='Total Volume', digits=dp.get_precision('FourDecimal'))
    job_order_status = fields.Char(compute="_get_sale_fields", string='Job Order Status')
    total_qty = fields.Float(string='Ordered Qty', digits=dp.get_precision('TwoDecimal'))
    remaining_qty = fields.Float(string='Qty Remaining', digits=dp.get_precision('TwoDecimal'))
    remaining_volume = fields.Float(compute="_get_container_vol", string='Vol Remaining')
    container_qty = fields.Float('Cont Pcs', digits=dp.get_precision('TwoDecimal'))
    container_vol = fields.Float(compute="_get_container_vol", string='Cont Vol')

    @api.depends('container_qty', 'remaining_qty')
    def _get_container_vol(self):
        for res in self:
            if res.container_qty:
                res.container_vol = res.container_qty * res.thick * res.width * res.length / 1000000000

            if res.container_qty:
                res.remaining_volume = res.remaining_qty * res.thick * res.width * res.length / 1000000000

    @api.depends('sale_line_id')
    def _get_sale_fields(self):
        for res in self:
            if res.sale_line_id:
                res.partner_id = res.sale_line_id.order_id.partner_id.id
                res.product_id = res.sale_line_id.product_id.id
                res.thick = res.sale_line_id.thick
                res.width = res.sale_line_id.width
                res.length = res.sale_line_id.length
                res.glue_id = res.sale_line_id.product_id.glue.id
                res.grade_id = res.sale_line_id.product_id.grade.id
                res.total_qty = res.sale_line_id.product_uom_qty
                res.total_volume = res.sale_line_id.volume
                res.job_order_status = res.sale_line_id.order_id.job_order_status

class PwkRpbContainer(models.Model):    
    _name = "pwk.rpb.container"

    reference = fields.Many2one('pwk.rpb', string='Reference')
    name = fields.Char('Container No.')
    no_container = fields.Char('Container No.')
    jumlah_container = fields.Integer('Jumlah Container')
    line_ids = fields.One2many('pwk.rpb.container.line', 'reference', string='Lines', ondelete="cascade")
    total_product = fields.Float(compute="_get_qty", string='Jumlah Product', digits=dp.get_precision('TwoDecimal'))
    total_product_qty = fields.Float(compute="_get_qty", string='Jumlah Qty Product', digits=dp.get_precision('TwoDecimal'))

    @api.depends('line_ids')
    def _get_qty(self):
        for res in self:
            total_qty = 0
            total_product = 0
            total_product_qty = 0

            if res.line_ids:
                for line in res.line_ids:
                    total_product += 1
                    total_product_qty + line.container_qty

            res.total_product = total_product
            res.total_product_qty = total_product_qty

class PwkRpbLineDetail1(models.Model):    
    _name = "pwk.rpb.line.detail1"

    reference = fields.Many2one('pwk.rpb.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    ply = fields.Float(string='Ply')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpbLineDetail2(models.Model):    
    _name = "pwk.rpb.line.detail2"

    reference = fields.Many2one('pwk.rpb.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    ply = fields.Float(string='Ply')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpbLineDetail3(models.Model):    
    _name = "pwk.rpb.line.detail3"

    reference = fields.Many2one('pwk.rpb.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    ply = fields.Float(string='Ply')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpbLineDetail4(models.Model):    
    _name = "pwk.rpb.line.detail4"

    reference = fields.Many2one('pwk.rpb.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    ply = fields.Float(string='Ply')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpbLineDetail5(models.Model):    
    _name = "pwk.rpb.line.detail5"

    reference = fields.Many2one('pwk.rpb.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    ply = fields.Float(string='Ply')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpbLine(models.Model):    
    _name = "pwk.rpb.line"
    _order = 'container_id,width asc,length asc,thick asc'

    reference = fields.Many2one('pwk.rpb', string='Reference')
    container_id = fields.Many2one('pwk.rpb.container', string='Container')
    jumlah_container = fields.Integer('Jml Container')
    sale_id = fields.Many2one('sale.order', 'No. Order')
    sale_line_id = fields.Many2one('sale.order.line', 'No. Order Line')
    partner_id = fields.Many2one(compute="_get_sale_fields", comodel_name='res.partner', string='Buyer')
    product_id = fields.Many2one(compute="_get_sale_fields", comodel_name='product.product', string='Product')
    po_number = fields.Char(compute="_get_sale_fields", string='PO No.')
    marking = fields.Char(compute="_get_sale_fields", string='Marking')
    thick = fields.Float(compute="_get_sale_fields", string='Thick', store=True)
    width = fields.Float(compute="_get_sale_fields", string='Width', store=True)
    length = fields.Float(compute="_get_sale_fields", string='Length', store=True)
    glue_id = fields.Many2one(compute="_get_sale_fields", comodel_name='pwk.glue', string='Glue')
    grade_id = fields.Many2one(compute="_get_sale_fields", comodel_name='pwk.grade', string='Grade')        
    total_volume = fields.Float(compute="_get_sale_fields", string='Total Volume', digits=dp.get_precision('FourDecimal'))
    job_order_status = fields.Char(compute="_get_sale_fields", string='Job Order Status')

    total_qty = fields.Float(string='Order PCS', digits=dp.get_precision('TwoDecimal'))
    spare_qty = fields.Float('Qty Spare (%)', digits=dp.get_precision('ZeroDecimal'))  
    total_qty_spare = fields.Float(compute="_get_total_qty_spare", string='Qty Spare')
    total_vol = fields.Float(compute="_get_volume", string='Order M3', digits=dp.get_precision('FourDecimal'))

    container_qty = fields.Float('Cont Pcs', digits=dp.get_precision('TwoDecimal'), store=True)
    container_vol = fields.Float(compute="_get_volume", string='Cont M3', digits=dp.get_precision('FourDecimal'), store=True)
    
    subtotal_qty = fields.Float(compute="_get_subtotal_qty", string='Total RPB PCS', digits=dp.get_precision('TwoDecimal'), store=True)
    subtotal_vol = fields.Float(compute="_get_volume", string='Total RPB M3', digits=dp.get_precision('FourDecimal'), store=True)
    
    outstanding_rpb_pcs = fields.Float(compute="_get_outstanding_rpb", string='Sisa RPB PCS', digits=dp.get_precision('TwoDecimal'), store=True)
    outstanding_rpb_vol = fields.Float(compute="_get_volume", string='Sisa RPB M3', digits=dp.get_precision('FourDecimal'), store=True)
    
    outstanding_order_pcs = fields.Float(string='Sisa Order PCS', digits=dp.get_precision('TwoDecimal'), store=True)
    outstanding_order_vol = fields.Float(compute="_get_volume", string='Sisa Order M3', digits=dp.get_precision('FourDecimal'), store=True)

    detail_ids_1 = fields.One2many('pwk.rpb.line.detail1', 'reference', string='Lines', ondelete="cascade")
    detail_ids_2 = fields.One2many('pwk.rpb.line.detail2', 'reference', string='Lines', ondelete="cascade")
    detail_ids_3 = fields.One2many('pwk.rpb.line.detail3', 'reference', string='Lines', ondelete="cascade")
    detail_ids_4 = fields.One2many('pwk.rpb.line.detail4', 'reference', string='Lines', ondelete="cascade")
    detail_ids_5 = fields.One2many('pwk.rpb.line.detail5', 'reference', string='Lines', ondelete="cascade")

    bom_id = fields.Many2one('mrp.bom', string='BoM')
    is_detail1 = fields.Boolean('Detail 1')
    is_detail2 = fields.Boolean('Detail 2')
    is_detail3 = fields.Boolean('Detail 3')
    is_detail4 = fields.Boolean('Detail 3')
    is_detail5 = fields.Boolean('Detail 3')
    is_selected_detail1 = fields.Boolean('Bill of Material 1')
    is_selected_detail2 = fields.Boolean('Bill of Material 2')
    is_selected_detail3 = fields.Boolean('Bill of Material 3')
    is_selected_detail4 = fields.Boolean('Bill of Material 4')
    is_selected_detail5 = fields.Boolean('Bill of Material 5')

    bom_status = fields.Char(compute="_get_bom_status", string='BoM Status', store=True)

    @api.depends('is_selected_detail1','is_selected_detail2','is_selected_detail3','is_selected_detail4','is_selected_detail5')
    def _get_bom_status(self):
        for res in self:
            if res.is_selected_detail1 or res.is_selected_detail2 or res.is_selected_detail3 or res.is_selected_detail4 or res.is_selected_detail5:
                res.bom_status = "Ready"
            else:
                res.bom_status = "Not Ready"

    @api.depends('container_qty', 'spare_qty')
    def _get_total_qty_spare(self):
        for res in self:
            if res.spare_qty == 0:
                res.total_qty_spare = res.container_qty
            else:
                res.total_qty_spare = res.container_qty + round((res.container_qty * res.spare_qty / 100))

    @api.depends('container_qty', 'jumlah_container')
    def _get_subtotal_qty(self):
        for res in self:
            res.subtotal_qty = res.container_qty * res.jumlah_container

    @api.depends('subtotal_qty')
    def _get_outstanding_rpb(self):
        for res in self:
            outstanding_rpb_pcs = res.subtotal_qty

            rpm_line_ids = self.env['pwk.rpm.line'].search([
                ('reference.rpb_id', '=', res.reference.id)
            ])
            
            if rpm_line_ids:
                for line in rpm_line_ids:
                    if line.sale_line_id == res.sale_line_id:
                        outstanding_rpb_pcs -= line.total_qty

            res.outstanding_rpb_pcs = outstanding_rpb_pcs

    @api.depends('container_qty', 'subtotal_qty', 'outstanding_rpb_pcs', 'outstanding_order_pcs', 'total_qty')
    def _get_volume(self):
        for res in self:
            res.container_vol = res.container_qty * res.thick * res.width * res.length / 1000000000
            res.subtotal_vol = res.subtotal_qty * res.thick * res.width * res.length / 1000000000
            res.outstanding_rpb_vol = res.outstanding_rpb_pcs * res.thick * res.width * res.length / 1000000000
            res.outstanding_order_vol = res.outstanding_order_pcs * res.thick * res.width * res.length / 1000000000
            res.total_vol = res.total_qty * res.thick * res.width * res.length / 1000000000

    @api.depends('sale_line_id')
    def _get_sale_fields(self):
        for res in self:
            if res.sale_line_id:
                res.partner_id = res.sale_line_id.order_id.partner_id.id
                res.product_id = res.sale_line_id.product_id.id
                res.thick = res.sale_line_id.thick
                res.width = res.sale_line_id.width
                res.length = res.sale_line_id.length
                res.glue_id = res.sale_line_id.product_id.glue.id
                res.grade_id = res.sale_line_id.product_id.grade.id
                res.total_qty = res.sale_line_id.product_uom_qty
                res.total_volume = res.sale_line_id.volume
                res.job_order_status = res.sale_line_id.order_id.job_order_status
                res.po_number = res.sale_line_id.order_id.po_number
                res.marking = res.sale_line_id.marking

    @api.multi
    def button_reload_bom(self):
        for line in self:
            if line.detail_ids_1:
                for detail in line.detail_ids_1:
                    detail.unlink()

            if line.detail_ids_2:
                for detail in line.detail_ids_2:
                    detail.unlink()

            if line.detail_ids_3:
                for detail in line.detail_ids_3:
                    detail.unlink()

            if line.detail_ids_4:
                for detail in line.detail_ids_4:
                    detail.unlink()

            if line.detail_ids_5:
                for detail in line.detail_ids_5:
                    detail.unlink()

            bom_ids = self.env['mrp.bom'].search([
                ('product_tmpl_id.name', '=', line.product_id.name)
            ])
            
            if bom_ids:
                if len(bom_ids) >= 1:
                    line.write({'is_detail1': True})
                    for bom_line in bom_ids[0].bom_line_ids:                        
                        self.env['pwk.rpb.line.detail1'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'ply': bom_line.product_qty,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })

                if len(bom_ids) >= 2:
                    line.write({'is_detail2': True})
                    for bom_line in bom_ids[1].bom_line_ids:
                        self.env['pwk.rpb.line.detail2'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'ply': bom_line.product_qty,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })
                    
                if len(bom_ids) >= 3:
                    line.write({'is_detail3': True})                    
                    for bom_line in bom_ids[2].bom_line_ids:
                        self.env['pwk.rpb.line.detail3'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'ply': bom_line.product_qty,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })

                if len(bom_ids) >= 4:
                    line.write({'is_detail4': True})                    
                    for bom_line in bom_ids[3].bom_line_ids:
                        self.env['pwk.rpb.line.detail4'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'ply': bom_line.product_qty,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })

                if len(bom_ids) >= 5:
                    line.write({'is_detail5': True})                    
                    for bom_line in bom_ids[4].bom_line_ids:
                        self.env['pwk.rpb.line.detail5'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'ply': bom_line.product_qty,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })

                if len(bom_ids) == 1:
                    line.write({'is_selected_detail1': True})

class PwkRpb(models.Model):    
    _name = "pwk.rpb"

    name = fields.Char('Nomor RPB')

    month = fields.Selection([
        ('Januari','Januari'),
        ('Februari','Februari'),
        ('March','March'),
        ('April','April'),
        ('Mei','Mei'),
        ('Juni','Juni'),
        ('Juli','Juli'),
        ('Agustus','Agustus'),
        ('September','September'),
        ('Oktober','Oktober'),
        ('November','November'),
        ('Desember','Desember')
    ], string="Bulan")

    date_start = fields.Date('Periode')
    date_end = fields.Date('Periode')
    state = fields.Selection([('Draft','Draft'),('Purchase Request','Purchase Request')], string="Status", default="Draft")
    line_ids = fields.One2many('pwk.rpb.line', 'reference', string='Lines', ondelete="cascade")
    container_ids = fields.One2many('pwk.rpb.container', 'reference', string='Container', ondelete="cascade")
    rpm_ids = fields.One2many('pwk.rpm', 'rpb_id', string='RPM', ondelete="cascade")
    target = fields.Float('Target ( M3 )', digits=dp.get_precision('FourDecimal'))    
    actual = fields.Float(compute="_get_actual", string='Aktual ( M3 )', digits=dp.get_precision('FourDecimal'))
    is_pr = fields.Boolean('Purchase Request')
    pr_veneer_id = fields.Many2one('pwk.purchase.request', string='PR Veneer Core')
    pr_barecore_id = fields.Many2one('pwk.purchase.request', string='PR Barecore')
    pr_faceback_id = fields.Many2one('pwk.purchase.request', string='PR Veneer FB')
    pr_mdf_id = fields.Many2one('pwk.purchase.request', string='PR MDF')
    rpb_line_count = fields.Integer(string='# of Lines', compute='_get_count')

    @api.multi
    def action_view_lines(self):
        # action = self.env.ref('v12_pwk.pwk_rpb_line_tree').read()[0]
        action = self.env.ref('v12_pwk.action_pwk_rpb_line').read()[0]
        ids = []
        for res in self:
            if res.line_ids:
                for line in res.line_ids:
                    ids.append(line.id)

        print("IDS ", ids)
        action['domain'] = [('id', 'in', ids)]
        return action

    @api.multi
    def _get_count(self):
        for res in self:
            if res.line_ids:
                res.rpb_line_count = len(res.line_ids)

    @api.multi
    def button_reload_all_bom(self):
        for res in self:
            if res.line_ids:
                for line in res.line_ids:
                    line.button_reload_bom()

            # if res.volume_ids:                
            #     for vol in res.volume_ids:
            #         vol.button_reload_bom()

    @api.multi
    def action_cancel(self):
        for res in self:
            res.pr_veneer_id.button_draft()
            res.pr_barecore_id.button_draft()
            res.pr_faceback_id.button_draft()
            res.pr_mdf_id.button_draft()

            res.pr_veneer_id.unlink()
            res.pr_barecore_id.unlink()
            res.pr_faceback_id.unlink()
            res.pr_mdf_id.unlink()

            res.write({
                'is_pr': False,
                'state': 'Draft',
            })

    @api.multi
    def action_create_pr(self):
        for res in self:
            product_list = []

            if res.line_ids:

                # PR Veneer
                product_list = []
                request_veneer = self.env['pwk.purchase.request'].create({
                    'date': fields.Date.today(),
                    'pr_type': 'Bahan Baku',
                    'formula_type': 'M3',
                })

                for line in res.line_ids:
                    if line.is_detail1 and line.is_selected_detail1:
                        bom_ids = line.detail_ids_1
                    elif line.is_detail2 and line.is_selected_detail2:
                        bom_ids = line.detail_ids_2
                    elif line.is_detail3 and line.is_selected_detail3:
                        bom_ids = line.detail_ids_3
                    elif line.is_detail4 and line.is_selected_detail4:
                        bom_ids = line.detail_ids_4
                    elif line.is_detail5 and line.is_selected_detail5:
                        bom_ids = line.detail_ids_5

                    for bom in bom_ids:
                        if not bom.product_id.goods_type and bom.product_id.jenis_kayu.name != "MDF":
                            if bom.quantity > bom.available_qty:
                                if bom.product_id.id not in product_list:
                                    product_list.append(bom.product_id.id)
                                
                                    self.env['pwk.purchase.request.volume'].create({
                                        'reference': request_veneer.id,
                                        'product_id': bom.product_id.id,
                                        'product_uom_id': bom.product_id.uom_po_id.id,
                                        'volume': 1.1 * ((bom.quantity - bom.available_qty) * line.thick * line.width * line.length / 1000000000)
                                    })

                                else:                                
                                    current_line_ids = self.env['pwk.purchase.request.volume'].search([
                                        ('reference', '=', request_veneer.id),
                                        ('product_id', '=', bom.product_id.id),
                                    ])

                                    if current_line_ids:
                                        current_line_ids[0].write({
                                            'quantity': current_line_ids[0].quantity + (1.1 * ((bom.quantity - bom.available_qty)))
                                        })

                # PR Barecore
                product_list = []
                request_barecore = self.env['pwk.purchase.request'].create({
                    'date': fields.Date.today(),
                    'pr_type': 'Bahan Baku',
                    'formula_type': 'PCS',
                })

                for line in res.line_ids:                    
                    if line.is_detail1 and line.is_selected_detail1:
                        bom_ids = line.detail_ids_1
                    elif line.is_detail2 and line.is_selected_detail2:
                        bom_ids = line.detail_ids_2
                    elif line.is_detail3 and line.is_selected_detail3:
                        bom_ids = line.detail_ids_3
                    elif line.is_detail4 and line.is_selected_detail4:
                        bom_ids = line.detail_ids_4
                    elif line.is_detail5 and line.is_selected_detail5:
                        bom_ids = line.detail_ids_5

                    for bom in bom_ids:
                        if bom.product_id.goods_type == "Barecore":
                            if bom.quantity > bom.available_qty:
                                if bom.product_id.id not in product_list:
                                    product_list.append(bom.product_id.id)

                                    self.env['pwk.purchase.request.line'].create({
                                        'reference': request_barecore.id,
                                        'product_id': bom.product_id.id,
                                        'product_uom_id': bom.product_id.uom_po_id.id,
                                        'quantity': 1.05 * (bom.quantity - bom.available_qty)
                                    })                            
                                else:
                                    current_line_ids = self.env['pwk.purchase.request.line'].search([
                                        ('reference', '=', request_barecore.id),
                                        ('product_id', '=', bom.product_id.id),
                                    ])

                                    if current_line_ids:
                                        current_line_ids[0].write({
                                            'quantity': current_line_ids[0].quantity + (1.05 * ((bom.quantity - bom.available_qty)))
                                        })


                # PR Faceback
                product_list = []
                request_faceback = self.env['pwk.purchase.request'].create({
                    'date': fields.Date.today(),
                    'pr_type': 'Bahan Baku',
                    'formula_type': 'M3',
                })

                for line in res.line_ids:                    
                    if line.is_detail1 and line.is_selected_detail1:
                        bom_ids = line.detail_ids_1
                    elif line.is_detail2 and line.is_selected_detail2:
                        bom_ids = line.detail_ids_2
                    elif line.is_detail3 and line.is_selected_detail3:
                        bom_ids = line.detail_ids_3
                    elif line.is_detail4 and line.is_selected_detail4:
                        bom_ids = line.detail_ids_4
                    elif line.is_detail5 and line.is_selected_detail5:
                        bom_ids = line.detail_ids_5

                    for bom in bom_ids:
                        if bom.product_id.goods_type == "Faceback":
                            if bom.quantity > bom.available_qty:
                                if bom.product_id.id not in product_list:
                                    product_list.append(bom.product_id.id)
                                
                                    self.env['pwk.purchase.request.volume'].create({
                                        'reference': request_faceback.id,
                                        'product_id': bom.product_id.id,
                                        'product_uom_id': bom.product_id.uom_po_id.id,
                                        'volume': 1.05 * ((bom.quantity - bom.available_qty) * line.thick * line.width * line.length / 1000000000)
                                    })

                                else:                                
                                    current_line_ids = self.env['pwk.purchase.request.volume'].search([
                                        ('reference', '=', request_faceback.id),
                                        ('product_id', '=', bom.product_id.id),
                                    ])

                                    if current_line_ids:
                                        current_line_ids[0].write({
                                            'quantity': current_line_ids[0].quantity + (1.05 * ((bom.quantity - bom.available_qty)))
                                        })

                # PR MDF
                product_list = []
                request_mdf = self.env['pwk.purchase.request'].create({
                    'date': fields.Date.today(),
                    'pr_type': 'Bahan Baku',
                    'formula_type': 'PCS',
                })

                for line in res.line_ids:                    
                    if line.is_detail1 and line.is_selected_detail1:
                        bom_ids = line.detail_ids_1
                    elif line.is_detail2 and line.is_selected_detail2:
                        bom_ids = line.detail_ids_2
                    elif line.is_detail3 and line.is_selected_detail3:
                        bom_ids = line.detail_ids_3
                    elif line.is_detail4 and line.is_selected_detail4:
                        bom_ids = line.detail_ids_4
                    elif line.is_detail5 and line.is_selected_detail5:
                        bom_ids = line.detail_ids_5

                    for bom in bom_ids:
                        if bom.product_id.jenis_kayu.name == "MDF":
                            print ("Masuk MDF")
                            if bom.quantity > bom.available_qty:
                                if bom.product_id.id not in product_list:
                                    product_list.append(bom.product_id.id)

                                    self.env['pwk.purchase.request.line'].create({
                                        'reference': request_mdf.id,
                                        'product_id': bom.product_id.id,
                                        'product_uom_id': bom.product_id.uom_po_id.id,
                                        'quantity': 1.05 * (bom.quantity - bom.available_qty)
                                    })                            
                                else:
                                    current_line_ids = self.env['pwk.purchase.request.line'].search([
                                        ('reference', '=', request_mdf.id),
                                        ('product_id', '=', bom.product_id.id),
                                    ])

                                    if current_line_ids:
                                        current_line_ids[0].write({
                                            'quantity': current_line_ids[0].quantity + (1.05 * ((bom.quantity - bom.available_qty)))
                                        })


                res.write({
                    'pr_veneer_id': request_veneer.id,                    
                    'pr_barecore_id': request_barecore.id,
                    'pr_faceback_id': request_faceback.id,
                    'pr_mdf_id': request_mdf.id,
                    'is_pr': True,
                    'state': 'Purchase Request'
                })

        return True

    @api.depends('line_ids.total_volume')
    def _get_actual(self):
        for res in self:
            actual = 0
            if res.line_ids:
                for line in res.line_ids:
                    actual += line.subtotal_vol
            res.actual = actual

    @api.multi
    def button_progress(self):
        for res in self:
            res.state = "Progress"

    @api.multi
    def button_done(self):
        for res in self:
            res.state = "Done"

    def get_sequence(self, name=False, obj=False, year_month=False, context=None):
        sequence_id = self.env['ir.sequence'].search([
            ('name', '=', name),
            ('code', '=', obj),
            ('suffix', '=', '.' + year_month + '.RPB.PWK')
        ])
        if not sequence_id :
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': name,
                'code': obj,
                'implementation': 'no_gap',
                'suffix': '.' + year_month + '.RPB.PWK',
                'padding': 3
            })
        return sequence_id.next_by_id()

    @api.model
    def create(self, vals):
        month_name = ''
        # month = vals['date_start'].month
        # year = vals['date_start'].year        

        # if month == 1:
        #     month_name = 'Jan'
        # elif month == 2:
        #     month_name = 'Feb'
        # elif month == 3:
        #     month_name = 'Mar'
        # elif month == 4:
        #     month_name = 'Apr'
        # elif month == 5:
        #     month_name = 'Mei'
        # elif month == 6:
        #     month_name = 'Jun'
        # elif month == 7:
        #     month_name = 'Jul'
        # elif month == 8:
        #     month_name = 'Agt'
        # elif month == 9:
        #     month_name = 'Sep'
        # elif month == 10:
        #     month_name = 'Okt'
        # elif month == 11:
        #     month_name = 'Nov'
        # elif month == 12:
        #     month_name = 'Des'

        year_month = str('Jan') + '-' + str('2021')
        
        vals['name'] = self.get_sequence('Rencana Produksi Bulanan', 'pwk.rpb', '%s' % year_month)
        return super(PwkRpb, self).create(vals)

class PwkRpmLineDetail1(models.Model):    
    _name = "pwk.rpm.line.detail1"

    reference = fields.Many2one('pwk.rpm.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpmLineDetail2(models.Model):    
    _name = "pwk.rpm.line.detail2"

    reference = fields.Many2one('pwk.rpm.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpmLineDetail3(models.Model):    
    _name = "pwk.rpm.line.detail3"

    reference = fields.Many2one('pwk.rpm.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpmLineDetail4(models.Model):    
    _name = "pwk.rpm.line.detail4"

    reference = fields.Many2one('pwk.rpm.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpmLineDetail5(models.Model):    
    _name = "pwk.rpm.line.detail5"

    reference = fields.Many2one('pwk.rpm.line', string='Reference')
    product_id = fields.Many2one('product.product', string='Product')
    thick = fields.Float(string='Thick')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    quantity = fields.Float(string='Quantity')
    available_qty = fields.Float(compute="_get_available_qty", string="Qty Available")
    
    @api.depends('product_id')
    def _get_available_qty(self):
        for res in self:
            if res.product_id:
                res.available_qty = res.product_id.qty_available

class PwkRpmLine(models.Model):    
    _name = "pwk.rpm.line"

    reference = fields.Many2one('pwk.rpm', string='Reference')
    sale_id = fields.Many2one('sale.order', 'No. Order')
    sale_line_id = fields.Many2one('sale.order.line', 'No. Order Line')
    partner_id = fields.Many2one(compute="_get_sale_fields", comodel_name='res.partner', string='Buyer')
    product_id = fields.Many2one(compute="_get_sale_fields", comodel_name='product.product', string='Product')
    thick = fields.Float(compute="_get_sale_fields", string='Thick')
    width = fields.Float(compute="_get_sale_fields", string='Width')
    length = fields.Float(compute="_get_sale_fields", string='Length')
    glue_id = fields.Many2one(compute="_get_sale_fields", comodel_name='pwk.glue', string='Glue')
    grade_id = fields.Many2one(compute="_get_sale_fields", comodel_name='pwk.grade', string='Grade')        
    spare_qty = fields.Float('Qty Spare (%)', digits=dp.get_precision('ZeroDecimal'))  
    
    remaining_qty = fields.Float(string='Qty Remaining')
    remaining_volume = fields.Float(compute="_get_volume", string='Vol Remaining', digits=dp.get_precision('FourDecimal'))

    total_qty = fields.Float(string='Qty RPM')
    total_qty_spare = fields.Float(compute="_get_total_qty_spare", string='Qty RPM (Spare)')
    total_volume = fields.Float(compute="_get_volume", string='Vol RPM', digits=dp.get_precision('FourDecimal'))

    detail_ids_1 = fields.One2many('pwk.rpm.line.detail1', 'reference', string='Lines', ondelete="cascade")
    detail_ids_2 = fields.One2many('pwk.rpm.line.detail2', 'reference', string='Lines', ondelete="cascade")
    detail_ids_3 = fields.One2many('pwk.rpm.line.detail3', 'reference', string='Lines', ondelete="cascade")
    detail_ids_4 = fields.One2many('pwk.rpm.line.detail4', 'reference', string='Lines', ondelete="cascade")
    detail_ids_5 = fields.One2many('pwk.rpm.line.detail5', 'reference', string='Lines', ondelete="cascade")

    bom_id = fields.Many2one('mrp.bom', string='BoM')
    is_detail1 = fields.Boolean('Detail 1')
    is_detail2 = fields.Boolean('Detail 2')
    is_detail3 = fields.Boolean('Detail 3')
    is_detail4 = fields.Boolean('Detail 3')
    is_detail5 = fields.Boolean('Detail 3')
    is_selected_detail1 = fields.Boolean('Bill of Material 1')
    is_selected_detail2 = fields.Boolean('Bill of Material 2')
    is_selected_detail3 = fields.Boolean('Bill of Material 3')
    is_selected_detail4 = fields.Boolean('Bill of Material 4')
    is_selected_detail5 = fields.Boolean('Bill of Material 5')    

    @api.depends('total_qty', 'spare_qty')
    def _get_total_qty_spare(self):
        for res in self:
            res.total_qty_spare = res.total_qty + round((res.total_qty * res.spare_qty / 100))

    @api.depends('total_qty', 'remaining_qty')
    def _get_volume(self):
        for res in self:
            res.total_volume = res.total_qty * res.thick * res.width * res.length / 1000000000
            res.remaining_volume = res.remaining_qty * res.thick * res.width * res.length / 1000000000

    @api.depends('sale_line_id')
    def _get_sale_fields(self):
        for res in self:
            if res.sale_line_id:
                res.partner_id = res.sale_line_id.order_id.partner_id.id
                res.product_id = res.sale_line_id.product_id.id
                res.thick = res.sale_line_id.thick
                res.width = res.sale_line_id.width
                res.length = res.sale_line_id.length
                res.glue_id = res.sale_line_id.product_id.glue.id
                res.grade_id = res.sale_line_id.product_id.grade.id

    @api.multi
    def button_reload_bom(self):
        for line in self:
            if line.detail_ids_1:
                for detail in line.detail_ids_1:
                    detail.unlink()

            if line.detail_ids_2:
                for detail in line.detail_ids_2:
                    detail.unlink()

            if line.detail_ids_3:
                for detail in line.detail_ids_3:
                    detail.unlink()

            if line.detail_ids_4:
                for detail in line.detail_ids_4:
                    detail.unlink()

            if line.detail_ids_5:
                for detail in line.detail_ids_5:
                    detail.unlink()

            bom_ids = self.env['mrp.bom'].search([
                ('product_tmpl_id.name', '=', line.product_id.name)
            ])

            if bom_ids:
                if len(bom_ids) >= 1:
                    line.write({'is_detail1': True})
                    for bom_line in bom_ids[0].bom_line_ids:                        
                        self.env['pwk.rpm.line.detail1'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })

                if len(bom_ids) >= 2:
                    line.write({'is_detail2': True})
                    for bom_line in bom_ids[1].bom_line_ids:
                        self.env['pwk.rpm.line.detail2'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })
                    
                if len(bom_ids) >= 3:
                    line.write({'is_detail3': True})                    
                    for bom_line in bom_ids[2].bom_line_ids:
                        self.env['pwk.rpm.line.detail3'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })

                if len(bom_ids) >= 4:
                    line.write({'is_detail4': True})                    
                    for bom_line in bom_ids[3].bom_line_ids:
                        self.env['pwk.rpm.line.detail4'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })

                if len(bom_ids) >= 5:
                    line.write({'is_detail5': True})                    
                    for bom_line in bom_ids[4].bom_line_ids:
                        self.env['pwk.rpm.line.detail5'].create({
                            'reference': line.id,
                            'product_id': bom_line.product_id.id,
                            'thick': bom_line.product_id.tebal,
                            'width': bom_line.product_id.lebar,
                            'length': bom_line.product_id.panjang,
                            'quantity': bom_line.product_qty * line.total_qty_spare
                        })

class PwkRpm(models.Model):    
    _name = "pwk.rpm"

    month = fields.Selection([
        ('Januari','Januari'),
        ('Februari','Februari'),
        ('March','March'),
        ('April','April'),
        ('Mei','Mei'),
        ('Juni','Juni'),
        ('Juli','Juli'),
        ('Agustus','Agustus'),
        ('September','September'),
        ('Oktober','Oktober'),
        ('November','November'),
        ('Desember','Desember')
    ], string="Bulan")

    name = fields.Char('Nomor RPM')
    date_start = fields.Date('Periode')
    date_end = fields.Date('Periode')    
    rpb_id = fields.Many2one('pwk.rpb', string='RPB')    
    is_pr = fields.Boolean('Purchase Request')
    pr_id = fields.Many2one('pwk.purchase.request', string='Purchase Request')
    state = fields.Selection([('Draft','Draft'),('Purchase Request','Purchase Request')], string="Status", default="Draft")
    line_ids = fields.One2many('pwk.rpm.line', 'reference', string='Lines', ondelete="cascade")

    @api.multi
    def action_create_pr(self):
        for res in self:
            product_list = []

            if res.line_ids:
                request_id = self.env['pwk.purchase.request'].create({
                    'date': fields.Date.today(),
                })

                for line in res.line_ids:                    
                    if line.is_detail1 and line.is_selected_detail1:
                        bom_ids = line.detail_ids_1
                    elif line.is_detail2 and line.is_selected_detail2:
                        bom_ids = line.detail_ids_2
                    elif line.is_detail3 and line.is_selected_detail3:
                        bom_ids = line.detail_ids_3
                    elif line.is_detail4 and line.is_selected_detail4:
                        bom_ids = line.detail_ids_4
                    elif line.is_detail5 and line.is_selected_detail5:
                        bom_ids = line.detail_ids_5

                    for bom in bom_ids:
                        if bom.quantity > bom.available_qty:
                            if bom.product_id.id not in product_list:
                                product_list.append(bom.product_id.id)

                                self.env['pwk.purchase.request.line'].create({
                                    'reference': request_id.id,
                                    'product_id': bom.product_id.id,                    
                                    'quantity': bom.quantity - bom.available_qty,
                                })

                            else:
                                current_line_ids = self.env['pwk.purchase.request.line'].search([
                                    ('reference', '=', request_id.id),
                                    ('product_id', '=', bom.product_id.id),
                                ])

                                if current_line_ids:
                                    current_line_ids[0].write({
                                        'quantity': current_line_ids[0].quantity + (bom.quantity - bom.available_qty)
                                    })

            return res.write({
                'pr_id': request_id.id,
                'is_pr': True,
                'state': 'Purchase Request'
            })


    @api.multi
    def button_reload(self):              
        for res in self:
            if res.rpb_id:
                if res.line_ids:
                    for current_line in res.line_ids:
                        current_line.unlink()

                for line in res.rpb_id.line_ids:                
                    rpm_line_id = self.env['pwk.rpm.line'].create({
                        'reference': res.id,
                        'sale_line_id': line.sale_line_id.id,
                        'sale_id': line.sale_line_id.order_id.id,
                        'remaining_qty': line.outstanding_rpb_pcs
                    })

                    if line.is_selected_detail1:
                        bom_ids = line.detail_ids_1
                    elif line.is_selected_detail2:
                        bom_ids = line.detail_ids_2
                    elif line.is_selected_detail3:
                        bom_ids = line.detail_ids_3
                    elif line.is_selected_detail4:
                        bom_ids = line.detail_ids_4
                    elif line.is_selected_detail5:
                        bom_ids = line.detail_ids_5

                    for bom in bom_ids:
                        self.env['pwk.rpm.line.detail1'].create({
                            'reference': rpm_line_id.id,
                            'product_id': bom.product_id.id,
                            'thick': bom.thick,
                            'width': bom.width,
                            'length': bom.length,
                            'quantity': bom.quantity
                        })

                    rpm_line_id.write({
                        'is_selected_detail1': True,
                        'is_detail1': True
                    })

            return True    

    @api.multi
    def button_cancel(self):
        for res in self:
            res.write({
                'state': "Draft",                
                'is_pr': False
            })

            if res.pr_id:
                res.pr_id.unlink() 

    @api.multi
    def button_done(self):
        for res in self:
            res.state = "Done"

    def get_sequence(self, name=False, obj=False, year_month=False, context=None):
        sequence_id = self.env['ir.sequence'].search([
            ('name', '=', name),
            ('code', '=', obj),
            ('suffix', '=', '.' + year_month + '.RPM.PWK')
        ])
        if not sequence_id :
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': name,
                'code': obj,
                'implementation': 'no_gap',
                'suffix': '.' + year_month + '.RPM.PWK',
                'padding': 3
            })
        return sequence_id.next_by_id()

    @api.model
    def create(self, vals):
        month_name = ''
        # month = vals['date_start'].month
        # year = vals['date_start'].year

        # day_of_month = vals['date_start'].day
        # week_number = (day_of_month - 1) // 7 + 1

        # if month == 1:
        #     month_name = 'Jan'
        # elif month == 2:
        #     month_name = 'Feb'
        # elif month == 3:
        #     month_name = 'Mar'
        # elif month == 4:
        #     month_name = 'Apr'
        # elif month == 5:
        #     month_name = 'Mei'
        # elif month == 6:
        #     month_name = 'Jun'
        # elif month == 7:
        #     month_name = 'Jul'
        # elif month == 8:
        #     month_name = 'Agt'
        # elif month == 9:
        #     month_name = 'Sep'
        # elif month == 10:
        #     month_name = 'Okt'
        # elif month == 11:
        #     month_name = 'Nov'
        # elif month == 12:
        #     month_name = 'Des'

        year_month = 'Week-' + str('1') + '.' + str('Jan') + '-' + str('2021')

        vals['name'] = self.get_sequence('Rencana Produksi Mingguan', 'pwk.rpm', '%s' % year_month)
        return super(PwkRpm, self).create(vals)

class ResCompany(models.Model):    
    _inherit = "res.company"

    nomor_tdp = fields.Char('Nomor TDP')

class PwkNotaPerusahaanLine(models.Model):    
    _name = "pwk.nota.perusahaan.line"

    reference = fields.Many2one('pwk.nota.perusahaan', 'Reference')
    picking_id = fields.Many2one('stock.picking', 'Surat Jalan')
    product_id = fields.Many2one('product.product', 'Product')
    jenis_kayu_id = fields.Many2one('pwk.jenis.kayu', related='product_id.jenis_kayu', string='Jenis Kayu')
    quantity = fields.Float('Quantity', digits=dp.get_precision('TwoDecimal'))
    volume_stepel_meter = fields.Float('Volume SM', digits=dp.get_precision('FourDecimal'))    
    volume_kubik = fields.Float('Volume Kubik', digits=dp.get_precision('FourDecimal'))
    keterangan = fields.Text('Keterangan')
    picking_id = fields.Many2one('stock.picking', 'Surat Jalan')
    move_id = fields.Many2one('stock.move', 'Stock Move')

class PwkNotaPerusahaan(models.Model):    
    _name = "pwk.nota.perusahaan"

    name = fields.Char('No. Nota Perusahaan')
    keterangan = fields.Text('Keterangan')
    provinsi = fields.Char('Provinsi',)
    kota = fields.Char('Kab. / Kota')    
    period_start = fields.Date('Dari Tanggal')
    period_end = fields.Date('Sampai Tanggal')
    masa_berlaku = fields.Integer('Masa Berlaku')
    pengirim_nama = fields.Char('Nama Pengirim')
    pengirim_alamat = fields.Char('Alamat Pengirim')
    pengirim_telepon = fields.Char('Telepon Pengirim')
    partner_id = fields.Many2one('res.partner', 'Nama Penerima', domain="[('customer','=',True)]")
    alamat_muat = fields.Char('Alamat Lokasi Muat')
    jenis_alat_angkut = fields.Char('Jenis Alat Angkut')
    alamat_bongkar = fields.Char('Alamat Lokasi Bongkar')
    tanggal_penerbit = fields.Date('Tanggal Penerbit')
    nama_penerima = fields.Char('Nama Penerima')
    tanggal_penerimaan = fields.Date('Tanggal Penerimaan')
    office_selection = fields.Selection([('Temanggung','Temanggung'),('Jakarta','Jakarta')], string="Lokasi", default="Temanggung", track_visibility="always")
    certificate_id = fields.Many2one('pwk.certificate', 'Certificate')
    is_logo = fields.Boolean('Show Legal Logo', default=True)    
    total_qty = fields.Float(compute="_get_total", string="Total Qty")
    total_volume_stepel_meter = fields.Float(compute="_get_total", string="Total Volume SM")
    total_volume_kubik = fields.Float(compute="_get_total", string="Total Volume M3")
    line_ids = fields.One2many('pwk.nota.perusahaan.line', 'reference', string="Lines", ondelete="cascade")
    dengan_huruf = fields.Char('Dengan Huruf')

    @api.depends('line_ids.quantity','line_ids.volume_stepel_meter', 'line_ids.volume_kubik')
    def _get_total(self):
        for res in self:
            total_qty = 0
            total_volume_stepel_meter = 0
            total_volume_kubik = 0

            if res.line_ids:
                for line in res.line_ids:
                    total_qty += line.quantity
                    total_volume_stepel_meter += line.volume_stepel_meter
                    total_volume_kubik = line.volume_kubik

            res.total_qty = total_qty
            res.total_volume_stepel_meter = total_volume_stepel_meter
            res.total_volume_kubik = total_volume_kubik

    def get_sequence(self, name=False, obj=False, context=None):
        sequence_id = self.env['ir.sequence'].search([
            ('name', '=', name),
            ('code', '=', obj),
            ('prefix', '=', 'PWKWI.'),
            ('suffix', '=', '.NP.%(month)s.%(year)s')
        ])
        if not sequence_id :
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': name,
                'code': obj,
                'implementation': 'no_gap',
                'prefix': 'PWKWI.',
                'suffix': '.NP.%(month)s.%(year)s',
                'padding': 3
            })
        return sequence_id.next_by_id()

    @api.model
    def create(self, vals):
        vals['name'] = self.get_sequence('Nota Perusahaan', 'pwk.nota.perusahaan')
        return super(PwkNotaPerusahaan, self).create(vals)

    @api.multi
    def print_nota_perusahaan(self):                
        return self.env.ref('v12_pwk.nota_perusahaan').report_action(self)

    @api.multi
    def print_daftar_kayu_olahan(self):                
        return self.env.ref('v12_pwk.daftar_kayu_olahan').report_action(self)

class PwkPaymentNoteLine(models.Model):    
    _name = "pwk.payment.note.line"

    reference = fields.Many2one('pwk.payment.note', string="Reference")
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order No.")
    tanggal_pembelian = fields.Date('Tanggal Pembelian', default=fields.Date.today())
    volume = fields.Float('Volume', digits=dp.get_precision('FourDecimal'))
    amount = fields.Float('Tagihan', digits=dp.get_precision('TwoDecimal'))

class PwkPaymentNote(models.Model):    
    _name = "pwk.payment.note"

    name = fields.Char('Payment Note No.')
    journal_id = fields.Many2one('account.journal', string='Bank / Cash', domain="[('type','in',('cash','bank'))]")
    account_id = fields.Many2one('account.account', string='Akun Biaya')
    date = fields.Date('Tanggal', default=fields.Date.today())
    date_from = fields.Date('Start Period')
    date_to = fields.Date('End Period')
    partner_id = fields.Many2one('res.partner', 'Pembayaran Kepada', domain="[('supplier','=',True)]")
    pembayaran_untuk = fields.Char('Pembayaran Untuk')
    line_ids = fields.One2many('pwk.payment.note.line', 'reference', string="Lines", ondelete="cascade")
    note = fields.Text('Notes')
    rekening = fields.Text('Rekening Supplier')
    tanggal_bayar = fields.Date('Tanggal Bayar', default=fields.Date.today())
    office_selection = fields.Selection([('Temanggung','Temanggung'),('Jakarta','Jakarta')], string="Lokasi", default="Temanggung", track_visibility="always")
    certificate_id = fields.Many2one('pwk.certificate', 'Certificate')
    is_logo = fields.Boolean('Show Legal Logo', default=True)    
    pph_rate = fields.Float("Persentase Pph")
    amount_untaxed = fields.Float(compute="_get_amount", string="Subtotal", digits=dp.get_precision('TwoDecimal'))
    amount_tax = fields.Float(compute="_get_amount", string="Nilai Pph", digits=dp.get_precision('TwoDecimal'))
    amount_total = fields.Float(compute="_get_amount", string="Total Tagihan", digits=dp.get_precision('TwoDecimal'))
    state = fields.Selection([('Draft','Draft'),('Paid','Paid'),('Cancelled','Cancelled')], string="Status", default="Draft")
    move_id = fields.Many2one('account.move', 'Journal Entries')

    @api.multi
    def button_reload(self):
        for res in self:
            if res.line_ids:
                for line in res.line_ids:
                    line.unlink()

            if res.date_from and res.date_to:
                purchase_ids = self.env['purchase.order'].search([
                    ('partner_id','=',res.partner_id.id),
                    ('purchase_type','=','Rotary'),
                    ('date_order','>=',res.date_from),
                    ('date_order','<=',res.date_to),
                    ('state','>=','purchase'),
                    ])

                if purchase_ids:
                    for purchase in purchase_ids:
                        self.env['pwk.payment.note.line'].create({
                            'reference': res.id,
                            'purchase_id': purchase.id,
                            'tanggal_pembelian': purchase.date_order,
                            'volume': purchase.total_volume,
                            'amount': purchase.amount_untaxed,
                            })

    @api.depends('line_ids.amount','pph_rate')
    def _get_amount(self):
        for res in self:
            amount_untaxed = 0
            if res.line_ids:
                for line in res.line_ids:
                    amount_untaxed += line.amount

            amount_tax = amount_untaxed * res.pph_rate / 100
            amount_total = amount_untaxed + amount_tax

            res.amount_untaxed = amount_untaxed
            res.amount_tax = amount_tax
            res.amount_total = amount_total

    def get_sequence(self, name=False, obj=False, context=None):
        sequence_id = self.env['ir.sequence'].search([
            ('name', '=', name),
            ('code', '=', obj),
            ('suffix', '=', '/PAYMENT - LOG/PW/%(year)s')
        ])
        if not sequence_id :
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': name,
                'code': obj,
                'implementation': 'no_gap',
                'suffix': '/PAYMENT - LOG/PW/%(year)s',
                'padding': 3
            })
        return sequence_id.next_by_id()

    @api.model
    def create(self, vals):
        vals['name'] = self.get_sequence('Payment Note', 'pwk.payment.note')
        return super(PwkPaymentNote, self).create(vals)

    @api.multi
    def print_payment_note(self):                
        return self.env.ref('v12_pwk.payment_note').report_action(self)

    @api.multi
    def button_cancel(self):                
        for res in self:
            if res.move_id:
                res.move_id.button_cancel()
                res.move_id.unlink()

            if res.line_ids:
                for line in res.line_ids:
                    line.purchase_id.write({'is_paid':False})

            res.write({'state':'Cancelled'})

    @api.multi
    def button_draft(self):                
        for res in self:
            res.write({'state':'Draft'})

    @api.multi
    def button_paid(self):                
        for res in self:
            if res.line_ids:                
                moveline_ids = []
                debit_line = (0, 0, {
                    'name': res.name,
                    'account_id': res.account_id.id,
                    'journal_id': res.journal_id.id,
                    'date': res.tanggal_bayar,
                    'debit': res.amount_total,
                    'credit': 0,
                })
                moveline_ids.append(debit_line)

                credit_line = (0, 0, {
                    'name': res.name,
                    'account_id': res.journal_id.default_debit_account_id.id,
                    'journal_id': res.journal_id.id,
                    'date': res.tanggal_bayar,
                    'credit': res.amount_total,
                    'debit': 0,
                })
                moveline_ids.append(credit_line)

                # Create Journal                
                move_id = self.env['account.move'].create({
                    'narration': res.name,
                    'ref': res.name,
                    'journal_id': res.journal_id.id,
                    'date': res.tanggal_bayar,
                    'line_ids': moveline_ids
                    })

                move_id.action_post()

                for line in res.line_ids:
                    line.purchase_id.write({'is_paid':True})

                res.write({
                    'move_id': move_id.id,
                    'state': 'Paid'
                    })                

class AccountAccount(models.Model):    
    _inherit = "account.account"

    liquidity_type = fields.Selection([('Cash','Cash'),('Bank','Bank')], string="Liquidity Type")
    short_name = fields.Char('Short Name')

class ResPartner(models.Model):    
    _inherit = "res.partner"

    contact_person = fields.Char('Contact Person')
    code = fields.Char('Code')
    komisi = fields.Float('Komisi')
    fax = fields.Char('Fax')
    bank_account_id = fields.Many2one('res.partner.bank','Bank Account')

class PwkCratesConversion(models.Model):
    _name = "pwk.crates.conversion"

    name = fields.Char("Crates Conversion")
    conversion = fields.Float('Conversion')

class PwkShipVia(models.Model):
    _name = "pwk.ship.via"

    name = fields.Char("Ship Via")

class PwkPort(models.Model):
    _name = "pwk.port"

    name = fields.Char("Port")

class PwkDestination(models.Model):
    _name = "pwk.destination"

    name = fields.Char("Destination")    

class PwkJenisKayu(models.Model):
    _name = "pwk.jenis.kayu"

    name = fields.Char("Jenis Kayu")

class PwkJenisCore(models.Model):
    _name = "pwk.jenis.core"

    name = fields.Char("Jenis Core")

class PwkGrade(models.Model):
    _name = "pwk.grade"

    name = fields.Char("Grade")

class PwkGlue(models.Model):
    _name = "pwk.glue"

    name = fields.Char("Glue")

class AccountInvoiceRefund(models.TransientModel):    
    _inherit = "account.invoice.refund"

    @api.multi
    def compute_refund(self, mode='refund'):
        inv_obj = self.env['account.invoice']
        inv_tax_obj = self.env['account.invoice.tax']
        inv_line_obj = self.env['account.invoice.line']
        context = dict(self._context or {})
        xml_id = False

        for form in self:
            created_inv = []
            date = False
            description = False
            for inv in inv_obj.browse(context.get('active_ids')):
                refund = form._get_refund(inv, mode)
                created_inv.append(refund.id)
                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_ids
                    to_reconcile_ids = {}
                    to_reconcile_lines = self.env['account.move.line']
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_lines += line
                            to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                        if line.reconciled:
                            line.remove_move_reconcile()
                    refund.action_invoice_open()
                    for tmpline in refund.move_id.line_ids:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_lines += tmpline
                    to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                    if mode == 'modify':
                        invoice = inv.read(inv_obj._get_refund_modify_read_fields())
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(invoice['invoice_line_ids'])
                        invoice_lines = inv_obj.with_context(mode='modify')._refund_cleanup_lines(invoice_lines)
                        tax_lines = inv_tax_obj.browse(invoice['tax_line_ids'])
                        tax_lines = inv_obj._refund_cleanup_lines(tax_lines)
                        invoice.update({
                            'type': inv.type,
                            'date_invoice': form.date_invoice,
                            'state': 'draft',
                            'number': False,
                            'invoice_line_ids': invoice_lines,
                            'tax_line_ids': tax_lines,
                            'date': date,
                            'formula_type': inv.formula_type,
                            'invoice_type': inv.invoice_type,
                            'origin': inv.origin,
                            'original_invoice_id': inv.id,
                            'fiscal_position_id': inv.fiscal_position_id.id,
                            'partner_bank_id': inv.partner_bank_id.id,
                        })
                        for field in inv_obj._get_refund_common_fields():
                            if inv_obj._fields[field].type == 'many2one':
                                invoice[field] = invoice[field] and invoice[field][0]
                            else:
                                invoice[field] = invoice[field] or False
                        inv_refund = inv_obj.create(invoice)
                        body = _('Correction of <a href=# data-oe-model=account.invoice data-oe-id=%d>%s</a><br>Reason: %s') % (inv.id, inv.number, description)
                        inv_refund.message_post(body=body)
                        if inv_refund.payment_term_id.id:
                            inv_refund._onchange_payment_term_date_invoice()
                        created_inv.append(inv_refund.id)
                xml_id = inv.type == 'out_invoice' and 'action_invoice_out_refund' or \
                         inv.type == 'out_refund' and 'action_invoice_tree1' or \
                         inv.type == 'in_invoice' and 'action_invoice_in_refund' or \
                         inv.type == 'in_refund' and 'action_invoice_tree2'
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            if mode == 'modify':
                # When refund method is `modify` then it will directly open the new draft bill/invoice in form view
                if inv_refund.type == 'in_invoice':
                    view_ref = self.env.ref('account.invoice_supplier_form')
                else:
                    view_ref = self.env.ref('account.invoice_form')
                form_view = [(view_ref.id, 'form')]
                if 'views' in result:
                    result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
                else:
                    result['views'] = form_view
                result['res_id'] = inv_refund.id
            else:
                invoice_domain = safe_eval(result['domain'])
                invoice_domain.append(('id', 'in', created_inv))
                result['domain'] = invoice_domain
            return result
        return True    

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    sequence_export_id = fields.Many2one('ir.sequence', string='Export Seq', copy=False)    
    sequence_waste_rotary_id = fields.Many2one('ir.sequence', string='Waste Rotary Seq', copy=False)
    sequence_waste_pabrik_ppn_id = fields.Many2one('ir.sequence', string='Waste Pabrik PPN Seq', copy=False)
    sequence_waste_pabrik_non_ppn_id = fields.Many2one('ir.sequence', string='Waste Pabrik Non-PPN Seq', copy=False)    
    refund_sequence_export_id = fields.Many2one('ir.sequence', string='Refund Export Sequence', copy=False)
    refund_sequence_waste_id = fields.Many2one('ir.sequence', string='Refund Waste Sequence', copy=False)

class AccountMove(models.Model):
    _inherit = ["account.move", "mail.thread", "mail.activity.mixin"]
    _name = "account.move"

    name = fields.Char(string='Number', required=True, copy=False, default='/', track_visibility="always")
    ref = fields.Char(string='Reference', copy=False, track_visibility="always")
    date = fields.Date(required=True, states={'posted': [('readonly', True)]}, index=True, default=fields.Date.context_today, track_visibility="always")    
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], string='Status',
      required=True, readonly=True, copy=False, default='draft',
      help='All manually created new journal entries are usually in the status \'Unposted\', '
           'but you can set the option to skip that status on the related journal. '
           'In that case, they will behave as journal entries automatically created by the '
           'system on document validation (invoices, bank statements...) and will be created '
           'in \'Posted\' status.', track_visibility="always")
    line_ids = fields.One2many('account.move.line', 'move_id', string='Journal Items',
        states={'posted': [('readonly', True)]}, copy=True, track_visibility="always")    
    narration = fields.Text(string='Internal Note', track_visibility="always")
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', store=True, readonly=True, track_visibility="always")    
    # Dummy Account field to search on account.move by account_id
    dummy_account_id = fields.Many2one('account.account', related='line_ids.account_id', string='Account', store=False, readonly=True, track_visibility="always")
    tax_cash_basis_rec_id = fields.Many2one(
        'account.partial.reconcile',
        string='Tax Cash Basis Entry of',
        help="Technical field used to keep track of the tax cash basis reconciliation. "
        "This is needed when cancelling the source: it will post the inverse journal entry to cancel that part too.", track_visibility="always")
    auto_reverse = fields.Boolean(string='Reverse Automatically', default=False, help='If this checkbox is ticked, this entry will be automatically reversed at the reversal date you defined.', track_visibility="always")
    reverse_date = fields.Date(string='Reversal Date', help='Date of the reverse accounting entry.', track_visibility="always")
    reverse_entry_id = fields.Many2one('account.move', String="Reverse entry", store=True, readonly=True, copy=False, track_visibility="always")
    tax_type_domain = fields.Char(store=False, help='Technical field used to have a dynamic taxes domain on the form view.', track_visibility="always")

    method_type = fields.Char(compute="_get_amount_bank", string="Cash/Bank", track_visibility="always")
    bank_account_id = fields.Many2one('res.partner.bank','Bank Account', track_visibility="always")
    from_bank = fields.Many2one('res.partner.bank','From Bank', track_visibility="always")
    transaction_type = fields.Selection([('SO','SO'),('SO Retur','SO Retur'),('PO','PO'),('PO Retur','PO Retur')],string="Transaction", track_visibility="always")
    description_bank = fields.Char("Description", track_visibility="always")
    account_bank = fields.Many2one(compute="_get_amount_bank", comodel_name="account.account", string="Bank Account", track_visibility="always")
    source_destination = fields.Many2one("res.partner", string="Partner", domain="['|',('customer','=',True),('supplier','=',True)]", track_visibility="always")
    type_bank = fields.Char(compute="_get_amount_bank", string="Type Bank", track_visibility="always")
    amount_bank = fields.Float(compute="_get_amount_bank", string="Amount Bank", track_visibility="always")
    amount_bank_terbilang = fields.Char(compute="_get_amount_bank_terbilang", string="Amount Bank Terbilang", track_visibility="always")
    office_selection = fields.Selection([('Temanggung','Temanggung'),('Jakarta','Jakarta')], string="Lokasi", default="Temanggung", track_visibility="always")

    @api.depends('line_ids.debit','line_ids.account_id','line_ids.credit')
    def _get_amount_bank(self):
        for res in self:
            amount_bank_debit = 0
            amount_bank_credit = 0
            amount_bank = 0
            type_bank = ""
            method_type = ""
            account_bank = False
            if res.line_ids:
                for line in res.line_ids:
                    if line.account_id.user_type_id.name == "Bank and Cash":
                        amount_bank_debit += line.debit
                        amount_bank_credit += line.credit
                        account_bank = line.account_id.id

                        if line.account_id.liquidity_type == "Cash":
                            method_type = "Cash"
                        elif line.account_id.liquidity_type == "Bank":
                            method_type = "Transfer"

                if amount_bank_debit > amount_bank_credit:
                    type_bank = "Receipt"
                    amount_bank = amount_bank_debit - amount_bank_credit
                elif amount_bank_debit < amount_bank_credit:
                    type_bank = "Payment"
                    amount_bank = amount_bank_credit - amount_bank_debit

            res.amount_bank = amount_bank
            res.account_bank = account_bank
            res.type_bank = type_bank
            res.method_type = method_type

    def terbilang_english(self, satuan):        
        huruf = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve","Thirteen","Fourteen","Fivteen","Sixteen","Seventeen","Eighteen","Nineteen","Twenty"]
        hasil = ""; 
        if satuan < 21: 
            hasil = hasil + huruf[int(satuan)];         
        elif satuan < 100:
            hasil = hasil + self.terbilang_english(satuan / 10) + "ty " + self.terbilang_english(satuan % 10);      
        elif satuan < 1000: 
            hasil = hasil + self.terbilang_english(satuan / 100) +" Hundred " + self.terbilang_english(satuan % 100); 
        elif satuan < 2000: 
            hasil = hasil + self.terbilang_english(satuan / 1000) + "Thousand " + self.terbilang_english(satuan - 1000); 
        elif satuan < 1000000: 
            hasil = hasil + self.terbilang_english(satuan % 100000) + self.terbilang_english(satuan / 1000) + " Thousand " + self.terbilang_english(satuan % 1000); 
        elif satuan < 1000000000:
            hasil = hasil + self.terbilang_english(satuan % 100000000) + self.terbilang_english(satuan / 1000000) + " Million " + self.terbilang_english(satuan % 1000000);
        elif satuan < 1000000000000:
            hasil = hasil + self.terbilang_english(satuan / 1000000000) + " Billion " + self.terbilang_english(satuan % 1000000000)
        elif satuan >= 1000000000000:
            hasil = "Angka terlalu besar, harus kurang dari 1 Trilyun!"; 
        return hasil;       

    def terbilang(self, satuan):
        huruf = ["","Satu","Dua","Tiga","Empat","Lima","Enam","Tujuh","Delapan","Sembilan","Sepuluh","Sebelas"]
        # huruf = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve"]
        hasil = ""; 
        if satuan < 12: 
            hasil = hasil + huruf[int(satuan)]; 
        elif satuan < 20: 
            hasil = hasil + self.terbilang(satuan-10)+" Belas"; 
        elif satuan < 100:
            hasil = hasil + self.terbilang(satuan/10)+" Puluh "+self.terbilang(satuan%10); 
        elif satuan < 200: 
            hasil=hasil+"Seratus "+self.terbilang(satuan-100); 
        elif satuan < 1000: 
            hasil=hasil+self.terbilang(satuan/100)+" Ratus "+self.terbilang(satuan%100); 
        elif satuan < 2000: 
            hasil=hasil+"Seribu "+self.terbilang(satuan-1000); 
        elif satuan < 1000000: 
            hasil=hasil+self.terbilang(satuan/1000)+" Ribu "+self.terbilang(satuan%1000); 
        elif satuan < 1000000000:
            hasil=hasil+self.terbilang(satuan/1000000)+" Juta "+self.terbilang(satuan%1000000);
        elif satuan < 1000000000000:
            hasil=hasil+self.terbilang(satuan/1000000000)+" Milyar "+self.terbilang(satuan%1000000000)
        elif satuan >= 1000000000000:
            hasil="Angka terlalu besar, harus kurang dari 1 Trilyun!"; 
        return hasil;

    @api.depends('amount_bank')
    def _get_amount_bank_terbilang(self):
        for res in self:
            amount = res.terbilang(res.amount_bank)
            res.amount_bank_terbilang = amount + " Rupiah"

    @api.multi
    def post(self, invoice=False):
        self._post_validate()
        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        self.mapped('line_ids').create_analytic_lines()
        for move in self:
            if move.name == '/':
                new_name = False
                sequence = False
                journal = move.journal_id

                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        if invoice:
                            if invoice.invoice_type == "Lokal":
                                if not journal.sequence_id:
                                    raise UserError(_('Please define a sequence for the Invoice Lokal'))
                                sequence = journal.sequence_id
                            elif invoice.invoice_type == "Export":
                                if not journal.sequence_export_id:
                                    raise UserError(_('Please define a sequence for the Invoice Expor'))
                                sequence = journal.sequence_export_id
                            elif invoice.invoice_type == "Waste Rotary":
                                if not journal.sequence_waste_rotary_id:
                                    raise UserError(_('Please define a sequence for the Invoice Waste Rotary'))
                                sequence = journal.sequence_waste_rotary_id
                            elif invoice.invoice_type == "Waste Pabrik PPN":
                                if not journal.sequence_waste_pabrik_ppn_id:
                                    raise UserError(_('Please define a sequence for the Invoice Waste Pabrik PPN'))
                                sequence = journal.sequence_waste_pabrik_ppn_id
                            elif invoice.invoice_type == "Waste Pabrik Non-PPN":
                                if not journal.sequence_waste_pabrik_non_ppn_id:
                                    raise UserError(_('Please define a sequence for the Invoice Waste Pabrik Non PPN'))
                                sequence = journal.sequence_waste_pabrik_non_ppn_id
                            else:
                                sequence = journal.sequence_id
                        else:
                            sequence = journal.sequence_id

                        # sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            if not journal.refund_sequence_id:
                                raise UserError(_('Please define a sequence for the credit notes'))
                            sequence = journal.refund_sequence_id

                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))

                if new_name:
                    move.name = new_name

            if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
                # For opening moves, we set the reconciliation date threshold
                # to the move's date if it wasn't already set (we don't want
                # to have to reconcile all the older payments -made before
                # installing Accounting- with bank statements)
                move.company_id.account_bank_reconciliation_start = move.date

        return self.write({'state': 'posted'})    

class PwkCertificate(models.Model):
    _name = 'pwk.certificate'

    name = fields.Char('Certificate Name')    
    detail = fields.Text('Detail Certificate')    
    detail2 = fields.Text('Detail Certificate 2')    
    detail3 = fields.Text('Detail Certificate 3')    
    detail4 = fields.Text('Detail Certificate 4')    

class PwkConsignee(models.Model):
    _name = 'pwk.consignee'

    name = fields.Text('Consignee')

class PwkMethodPayment(models.Model):
    _name = 'pwk.method.payment'

    name = fields.Text('Method of Payment')

class PwkNotifyParty(models.Model):
    _name = 'pwk.notify.party'

    name = fields.Text('Notify Party')
    address1 = fields.Char('Address 1')
    address2 = fields.Char('Address 2')
    address3 = fields.Char('Address 3')
    phone = fields.Char('Phone')
    fax = fields.Char('Fax')

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'    

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.date','invoice_id.formula_type','sheets')
    def _compute_price(self):        
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        price_subtotal_signed = 0
        if self.invoice_line_tax_ids:
            if self.invoice_id.formula_type == "Volume":                
                taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
            elif self.invoice_id.formula_type == "PCS":
                taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.sheets, product=self.product_id, partner=self.invoice_id.partner_id)
            else:
                taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)

        if self.invoice_id.formula_type == "Volume":
            self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        elif self.invoice_id.formula_type == "PCS":
            self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.sheets * price
        else:
            self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price

        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(price_subtotal_signed, self.invoice_id.company_id.currency_id, self.company_id or self.env.user.company_id, date or fields.Date.today())
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
    
    commercial_name3 = fields.Char('Commercial Name 3')
    commercial_option = fields.Selection([('Default','Default'),('Commercial 1','Commercial 1'),('Commercial 2','Commercial 2')])
    parent_type = fields.Char(compute="_get_parent_type", string='Parent Type')
    crate_to_sheet = fields.Integer('Crate to Sheet')
    crates_conversion_id = fields.Many2one('pwk.crates.conversion', 'Crate to Sheet')
    marking = fields.Char('Marking')
    thick = fields.Float('T', digits=dp.get_precision('OneDecimal'))
    width = fields.Float('W', digits=dp.get_precision('TwoDecimal'))
    length = fields.Float('L', digits=dp.get_precision('TwoDecimal'))
    crates = fields.Integer('Crates')
    remarks = fields.Text('Remarks')
    sheets = fields.Integer('Sheets')
    container_no = fields.Char('Container No')    
    seal_no = fields.Char('Seal No')
    shipping_marks = fields.Char('Shipping Marks')
    quantity = fields.Float(string='Qty', digits=dp.get_precision('FourDecimal'),
        required=True, default=1)
    price_subtotal = fields.Monetary(string='Amount (without Taxes)',
        store=True, readonly=True, compute='_compute_price', help="Total amount without taxes")

    @api.onchange('crates','crates_conversion_id')
    def _onchange_crates(self):
        if self.crates and self.crates_conversion_id:
            self.sheets = self.crates * self.crates_conversion_id.conversion

    @api.depends('invoice_id.type')
    def _get_parent_type(self):
        for res in self:
            parent_type = ''
            if res.invoice_id:
                parent_type = res.invoice_id.type
            res.parent_type = parent_type

    @api.onchange('product_id','commercial_option')
    def _onchange_product_id(self):
        domain = {}
        if not self.invoice_id:
            return

        part = self.invoice_id.partner_id
        fpos = self.invoice_id.fiscal_position_id
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        type = self.invoice_id.type

        if not part:
            warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a partner.'),
                }
            return {'warning': warning}

        if not self.product_id:
            if type not in ('in_invoice', 'in_refund'):
                self.price_unit = 0.0
            domain['uom_id'] = []
            if fpos:
                self.account_id = fpos.map_account(self.account_id)
        else:
            self_lang = self
            if part.lang:
                self_lang = self.with_context(lang=part.lang)

            product = self_lang.product_id
            account = self.get_invoice_line_account(type, product, fpos, company)
            if account:
                self.account_id = account.id
            self._set_taxes()

            product_name = self_lang._get_invoice_line_name_from_product()
            if product_name != None:
                self.name = product_name

            # Get Commercial Name
            if self.commercial_option == "Commercial 1":
                self.name = self.product_id.commercial_name1
            elif self.commercial_option == "Commercial 2":
                self.name = self.product_id.commercial_name2
            elif self.commercial_option == "Commercial 3":
                self.name = self.product_id.commercial_name3

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:

                if self.uom_id and self.uom_id.id != product.uom_id.id:
                    self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
        return {'domain': domain}

    @api.onchange('width','length','thick','crates','sheets')
    def _onchange_volume(self):              
        self.quantity = ((self.width * self.length * self.thick) * self.sheets) / 1000000000        

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def print_invoice_export(self):                
        return self.env.ref('v12_pwk.invoice_export').report_action(self)

    @api.multi
    def print_invoice_local(self):                
        return self.env.ref('v12_pwk.invoice_local').report_action(self)

    @api.multi
    def print_invoice_waste(self):                
        return self.env.ref('v12_pwk.invoice_waste').report_action(self)

    @api.multi
    def print_packing_list_export(self):                
        return self.env.ref('v12_pwk.packing_list_export').report_action(self)

    @api.multi
    def print_packing_list_local(self):                
        return self.env.ref('v12_pwk.packing_list_local').report_action(self)

    @api.multi
    def print_packing_list_waste(self):                
        return self.env.ref('v12_pwk.packing_list_waste').report_action(self)

    @api.multi
    def print_credit_note(self):                
        return self.env.ref('v12_pwk.credit_note_en').report_action(self)

    @api.multi
    def print_debit_note(self):                
        return self.env.ref('v12_pwk.debit_note_en').report_action(self)

    @api.multi
    def print_credit_note_en(self):                
        return self.env.ref('v12_pwk.credit_note').report_action(self)

    @api.multi
    def print_debit_note_en(self):                
        return self.env.ref('v12_pwk.debit_note').report_action(self)

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'formula_type', 'global_discount')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax - self.global_discount
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id
            amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())
            amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    global_discount = fields.Monetary('Discount')
    manual_number = fields.Char('Manual No.')
    manual_packing_list = fields.Char('Manual PL No.')

    is_saldo_awal = fields.Boolean('Saldo Awal')
    original_number = fields.Char('Original No.')
    number_packing_list = fields.Char(compute="_get_packing_list_no", string="Packing List No.")
    dpp_amount = fields.Float(compute="_get_dpp_amount", string="DPP Amount")
    attn = fields.Char("Attn")
    objek_penghasilan = fields.Char("Objek Pajak")
    bukti_potong = fields.Char("No. Bukti Potong")

    sheet_name = fields.Char('Satuan')
    
    document_id = fields.Binary(attachment=True)
    document_id_name = fields.Char("Document Name")
    note_delivery = fields.Text("Notes")
    
    is_sign = fields.Boolean('Show Sign', default=True)
    sign_type = fields.Selection([('Buyer','Buyer'),('Bank','Bank')], string='Sign Location', default='Buyer')
    is_logo = fields.Boolean('Show Legal Logo', default=True)
    is_debit_note = fields.Boolean('Debit Notes', default=False)
    is_credit_note = fields.Boolean('Credit Notes', default=False)

    office_selection = fields.Selection([('Temanggung','Temanggung'),('Jakarta','Jakarta')], string="Lokasi", default="Temanggung")
    sign = fields.Char('TTD Atas Nama', default="Milena Utomo")

    is_seal_container = fields.Boolean('Show Seal and Container', default=True)
    is_marking = fields.Boolean('Show Marking', default=True)
    pre_carriage = fields.Char('Pre Carriage By')

    description1 = fields.Text('Description 1')
    description2 = fields.Text('Description 2')
    description3 = fields.Text('Description 3')

    amount_total_terbilang = fields.Char(compute="_get_terbilang", string='Amount Total Terbilang')
    amount_total_terbilang_en = fields.Char(compute="_get_terbilang_english", string='Amount Total Terbilang English')
    shipping_marks = fields.Char('Shipping Marks')
    komisi = fields.Float(compute="_get_komisi", string='Komisi')
    tipe_komisi = fields.Selection([('PCS','PCS'),('M3','M3')], string='PCS / M3')
    total_komisi = fields.Float(compute="_get_total_komisi", string='Total Komisi')
    amount_untaxed = fields.Monetary(string='Untaxed Amount',
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    amount_untaxed_signed = fields.Monetary(string='Untaxed Amount in Company Currency', currency_field='company_currency_id',
        store=True, readonly=True, compute='_compute_amount')
    amount_untaxed_invoice_signed = fields.Monetary(string='Untaxed Amount in Invoice Currency', currency_field='currency_id',
        readonly=True, compute='_compute_sign_taxes')
    amount_tax = fields.Monetary(string='Tax',
        store=True, readonly=True, compute='_compute_amount')
    amount_tax_signed = fields.Monetary(string='Tax in Invoice Currency', currency_field='currency_id',
        readonly=True, compute='_compute_sign_taxes')
    amount_total = fields.Monetary(string='Total',
        store=True, readonly=True, compute='_compute_amount')
    amount_total_signed = fields.Monetary(string='Total in Invoice Currency', currency_field='currency_id',
        store=True, readonly=True, compute='_compute_amount',
        help="Total amount in the currency of the invoice, negative for credit notes.")
    amount_total_company_signed = fields.Monetary(string='Total in Company Currency', currency_field='company_currency_id',
        store=True, readonly=True, compute='_compute_amount',
        help="Total amount in the currency of the company, negative for credit notes.")
    
    vendor_invoice_no = fields.Char('Vendor Invoice No.')
    vendor_invoice_date = fields.Date('Vendor Invoice Date')
    total_crates = fields.Float(compute="_get_total", string="Total Crates")
    total_sheets = fields.Float(compute="_get_total", string="Total Sheets")
    total_volume = fields.Float(compute="_get_total", string="Total Volume", digits=dp.get_precision('FourDecimal'))
    gross_weight = fields.Float('Gross Weight')
    net_weight = fields.Float('Nett Weight')
    is_cancel = fields.Boolean('Cancelled')
    packing_list_no = fields.Char('PL Produksi No.')
    sale_order_no = fields.Char('Sales Order No.')
    contract_no = fields.Char('Contract No.')
    invoice_type = fields.Selection([('Lokal','Lokal'),('Export','Export'),('Waste Rotary','Waste Rotary'),('Waste Pabrik PPN','Waste Pabrik PPN'),('Waste Pabrik Non-PPN','Waste Pabrik Non-PPN')], string="Tipe Invoice", default="Lokal")
    do_date = fields.Date('Tgl Surat Jalan')
    do_number = fields.Char('No. Surat Jalan')
    ship_via = fields.Many2one('pwk.ship.via','Delivered By')
    po_number = fields.Char('Nomor PO')
    formula_type = fields.Selection([('Volume','Volume'),('PCS','PCS')], string="Price Formula")    
    original_invoice_id = fields.Many2one('account.invoice', 'Original Invoice')

    commercial_option = fields.Selection([('Default','Default'),('Commercial 1','Commercial 1'),('Commercial 2','Commercial 2')])
    method_payment_id = fields.Many2one('pwk.method.payment', 'Method of Payment')
    certificate_id = fields.Many2one('pwk.certificate', 'Certificate')
    consignee_id = fields.Many2one('pwk.consignee', 'Consignee')
    notify_party_id = fields.Many2one('pwk.notify.party', 'Notify Party')
    vessel_name = fields.Char('Vessel Name')
    container_no = fields.Char('Container No')
    container_number = fields.Char('Total Container')
    seal_no = fields.Char('Seal No')
    departure_date = fields.Date('Departure Date')
    port_loading = fields.Many2one('pwk.port','Port Of Loading')
    port_discharge = fields.Many2one('pwk.port','Port Of Discharge')
    country_origin = fields.Many2one('res.country','Country Of Origin')
    destination = fields.Many2one('pwk.destination','Destination')
    country_final_destination = fields.Many2one('res.country','Country Final Dest')
    second_partner_id = fields.Many2one('res.partner','2nd Vendor', domain=[('supplier','=',True)])

    @api.depends('invoice_line_ids.price_unit','invoice_line_ids.quantity','invoice_line_ids.invoice_line_tax_ids')
    def _get_dpp_amount(self):
        for res in self:
            dpp_amount = 0
            if res.invoice_line_ids:
                for line in res.invoice_line_ids:
                    if line.invoice_line_tax_ids:
                        dpp_amount += line.price_subtotal

            res.dpp_amount = dpp_amount

    def _get_packing_list_no(self):
        for res in self:
            number_packing_list = ''
            if res.number:
                number_packing_list = res.number.replace('INV', 'PL')
            res.number_packing_list = number_packing_list


    def terbilang(self, satuan):
        huruf = ["","Satu","Dua","Tiga","Empat","Lima","Enam","Tujuh","Delapan","Sembilan","Sepuluh","Sebelas"]
        # huruf = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve"]
        hasil = ""; 
        if satuan < 12: 
            hasil = hasil + huruf[int(satuan)]; 
        elif satuan < 20: 
            hasil = hasil + self.terbilang(satuan-10)+" Belas"; 
        elif satuan < 100:
            hasil = hasil + self.terbilang(satuan/10)+" Puluh "+self.terbilang(satuan%10); 
        elif satuan < 200: 
            hasil=hasil+"Seratus "+self.terbilang(satuan-100); 
        elif satuan < 1000: 
            hasil=hasil+self.terbilang(satuan/100)+" Ratus "+self.terbilang(satuan%100); 
        elif satuan < 2000: 
            hasil=hasil+"Seribu "+self.terbilang(satuan-1000); 
        elif satuan < 1000000: 
            hasil=hasil+self.terbilang(satuan/1000)+" Ribu "+self.terbilang(satuan%1000); 
        elif satuan < 1000000000:
            hasil=hasil+self.terbilang(satuan/1000000)+" Juta "+self.terbilang(satuan%1000000);
        elif satuan < 1000000000000:
            hasil=hasil+self.terbilang(satuan/1000000000)+" Milyar "+self.terbilang(satuan%1000000000)
        elif satuan >= 1000000000000:
            hasil="Angka terlalu besar, harus kurang dari 1 Trilyun!"; 
        return hasil;

    @api.depends('amount_total')
    def _get_terbilang(self):
        for res in self:
            amount = res.terbilang(res.amount_total)
            res.amount_total_terbilang = amount + " Rupiah"

    def terbilang_english(self, satuan):        
        huruf = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve","Thirteen","Fourteen","Fivteen","Sixteen","Seventeen","Eighteen","Nineteen","Twenty"]
        hasil = ""; 
        if satuan < 21: 
            hasil = hasil + huruf[int(satuan)];            
        elif satuan < 100:
            hasil = hasil + self.terbilang_english(satuan / 10) + "ty " + self.terbilang_english(satuan % 10);
        elif satuan < 1000: 
            hasil = hasil + self.terbilang_english(satuan / 100) +" Hundred " + self.terbilang_english(satuan % 100); 
        elif satuan < 2000: 
            hasil = hasil + self.terbilang_english(satuan / 1000) + "Thousand " + self.terbilang_english(satuan - 1000); 
        elif satuan < 1000000: 
            hasil = hasil + self.terbilang_english(satuan % 100000) + self.terbilang_english(satuan / 1000) + " Thousand " + self.terbilang_english(satuan % 1000); 
        elif satuan < 1000000000:
            hasil = hasil + self.terbilang_english(satuan % 100000000) + self.terbilang_english(satuan / 1000000) + " Million " + self.terbilang_english(satuan % 1000000);
        elif satuan < 1000000000000:
            hasil = hasil + self.terbilang_english(satuan / 1000000000) + " Billion " + self.terbilang_english(satuan % 1000000000)
        elif satuan >= 1000000000000:
            hasil = "Angka terlalu besar, harus kurang dari 1 Trilyun!"; 

        return hasil;       

    @api.depends('amount_total')
    def _get_terbilang_english(self):
        for res in self:
            amount = num2words(res.amount_total)
            # amount = res.terbilang_english(int(res.amount_total))
            res.amount_total_terbilang_en = amount + " Rupiah"

    @api.depends('invoice_line_ids.crates','invoice_line_ids.sheets','invoice_line_ids.quantity')
    def _get_total(self):
        for res in self:
            total_crates = 0
            total_sheets = 0
            total_volume = 0
            if res.invoice_line_ids:                
                for invoice_line in res.invoice_line_ids:
                    total_crates += invoice_line.crates
                    total_sheets += invoice_line.sheets
                    total_volume += invoice_line.quantity
            res.total_crates = total_crates
            res.total_sheets = total_sheets
            res.total_volume = total_volume

    @api.depends('partner_id')
    def _get_komisi(self):
        for res in self:
            komisi = 0
            if res.partner_id:                
                komisi = res.partner_id.komisi
            res.komisi = komisi

    @api.depends('komisi','formula_type','invoice_line_ids.sheets','invoice_line_ids.quantity')
    def _get_total_komisi(self):
        for res in self:
            total_komisi = 0
            if res.invoice_line_ids:
                for line in res.invoice_line_ids:
                    if res.formula_type == "PCS":
                        total_komisi += line.sheets
                    elif res.formula_type == "Volume":
                        total_komisi += line.quantity
            res.total_komisi = total_komisi * res.komisi


    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            if not line.account_id or line.display_type:
                continue
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            if self.formula_type == "Volume":
                taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            elif self.formula_type == "PCS":
                taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.sheets, line.product_id, self.partner_id)['taxes']
            else:
                taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']

            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped

    state = fields.Selection([
            ('draft','Draft'),
            ('proforma', 'Pro-forma'),
            ('open', 'Open'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'In Payment' status is used when payments have been registered for the entirety of the invoice in a journal configured to post entries at bank reconciliation only, and some of them haven't been reconciled with a bank statement line yet.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self._get_aml_for_amount_residual():
            residual_company_signed += line.amount_residual
            if line.currency_id == self.currency_id:
                residual += line.amount_residual_currency if line.currency_id else line.amount_residual
            else:
                if line.currency_id:
                    residual += line.currency_id._convert(line.amount_residual_currency, self.currency_id, line.company_id, line.date or fields.Date.today())
                else:
                    residual += line.company_id.currency_id._convert(line.amount_residual, self.currency_id, line.company_id, line.date or fields.Date.today())
        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual)
        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False

    @api.model
    def komisi_src_move_line_get(self):
        res = []        
        komisi_ids = self.env['account.account'].search([('code','=','6100.20')])        
        move_line_dict = {            
            'type': 'dest',
            'name': "Biaya Komisi",
            'price_unit': self.total_komisi,
            'quantity': 1,
            'price': self.total_komisi,
            'account_id': komisi_ids[0].id,
            'invoice_id': self.id,
        }
        res.append(move_line_dict)
        return res

    @api.model
    def komisi_dest_move_line_get(self):
        res = []        
        hutang_ids = self.env['account.account'].search([('code','=','2500.10')])        
        move_line_dict = {            
            'type': 'dest',
            'name': "Hutang Komisi",
            'price_unit': self.total_komisi,
            'quantity': 1,
            'price': self.total_komisi,
            'account_id': hutang_ids[0].id,
            'invoice_id': self.id,
        }
        res.append(move_line_dict)
        return res

    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            move_line_dict = {}
            if not line.account_id:
                continue

            if self.formula_type == "PCS" and line.sheets == 0:
                continue
            if self.formula_type == "Volume" and line.quantity==0:
                continue

            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))
            analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

            if self.formula_type == "PCS":
                move_line_dict = {
                    'invl_id': line.id,
                    'type': 'src',
                    'name': line.name,
                    'price_unit': line.price_unit,
                    'quantity': line.sheets,
                    'price': line.price_subtotal,
                    'account_id': line.account_id.id,
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'account_analytic_id': line.account_analytic_id.id,
                    'analytic_tag_ids': analytic_tag_ids,
                    'tax_ids': tax_ids,
                    'invoice_id': self.id,
                }

            elif self.formula_type == "Volume":
                move_line_dict = {
                    'invl_id': line.id,
                    'type': 'src',
                    'name': line.name,
                    'price_unit': line.price_unit,
                    'quantity': line.quantity,
                    'price': line.price_subtotal,
                    'account_id': line.account_id.id,
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'account_analytic_id': line.account_analytic_id.id,
                    'analytic_tag_ids': analytic_tag_ids,
                    'tax_ids': tax_ids,
                    'invoice_id': self.id,
                }

            else:                
                move_line_dict = {
                    'invl_id': line.id,
                    'type': 'src',
                    'name': line.name,
                    'price_unit': line.price_unit,
                    'quantity': line.quantity,
                    'price': line.price_subtotal,
                    'account_id': line.account_id.id,
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'account_analytic_id': line.account_analytic_id.id,
                    'analytic_tag_ids': analytic_tag_ids,
                    'tax_ids': tax_ids,
                    'invoice_id': self.id,
                }

            res.append(move_line_dict)

        return res

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids.filtered(lambda line: line.account_id):
                raise UserError(_('Please add at least one invoice line.'))
            if inv.move_id:
                continue


            if not inv.date_invoice:
                inv.write({'date_invoice': fields.Date.context_today(self)})
            if not inv.date_due:
                inv.write({'date_due': inv.date_invoice})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.compute_invoice_totals(company_currency, iml)

            name = inv.name or ''
            if inv.payment_term_id:
                totlines = inv.payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
                res_amount_currency = total_currency
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency._convert(t[1], inv.currency_id, inv.company_id, inv._get_currency_rate_date() or fields.Date.today())
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': inv.journal_id.id,
                'date': date,
                'narration': inv.comment,
            }
            move = account_move.create(move_vals)
            # Pass invoice in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post(invoice = inv)
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.write(vals)

            # Asset            
            context = dict(self.env.context)            
            context.pop('default_type', None)
            inv.invoice_line_ids.with_context(context).asset_create()

        return True

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: not inv.partner_id):
            raise UserError(_("The field Vendor is required, please complete it to validate the Vendor Bill."))
        # if to_open_invoices.filtered(lambda inv: inv.state != 'proforma'):
        #     raise UserError(_("Invoice must be in Proforma state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        if to_open_invoices.filtered(lambda inv: not inv.account_id):
            raise UserError(_('No account was found to create the invoice, be sure you have installed a chart of account.'))

        if to_open_invoices.filtered(lambda inv: inv.state != 'proforma'):
            to_open_invoices.action_date_assign()
            to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()

    @api.multi
    def invoice_validate(self):
        for invoice in self:
            if invoice.partner_id not in invoice.message_partner_ids:
                invoice.message_subscribe([invoice.partner_id.id])

            # Auto-compute reference, if not already existing and if configured on company
            # if not invoice.reference and invoice.type == 'out_invoice':
            #     invoice.reference = invoice._get_computed_reference()

            # DO NOT FORWARD-PORT.
            # The reference is copied after the move creation because we need the move to get the invoice number but
            # we need the invoice number to get the reference.
            # invoice.move_id.ref = invoice.reference
        self._check_duplicate_supplier_reference()

        return self.write({'state': 'open'})
        
    @api.multi
    def action_invoice_proforma(self):
        if self.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Invoice must be a draft in order to set it to Pro-forma."))
        self.action_date_assign()
        self.action_move_create()
        return self.write({'state': 'proforma'})

    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            #unreconcile all journal items of the invoice, since the cancellation will unlink them anyway
            inv.move_id.line_ids.filtered(lambda x: x.account_id.reconcile).remove_move_reconcile()

        # First, set the invoices as cancelled and detach the move ids
        self.write({'state': 'cancel', 'move_id': False, 'is_cancel':True, 'is_efaktur_exported':False})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            moves.unlink()
        return True

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # jenis_kayu = fields.Related('pwk.jenis.kayu', 'Jenis Kayu')
    service_to_purchase = fields.Boolean('Service to Purchase')

    # jenis_kayu_id = fields.Many2one(
    #     comodel_name='pwk.jenis.kayu',
    #     related='product_variant_id.jenis_kayu',
    #     string='Jenis Kayu (FB)',
    #     store=True, readonly=True)
    # jenis_core_id = fields.Many2one(
    #     comodel_name='pwk.jenis.core',
    #     related='product_variant_id.jenis_core',
    #     string='Jenis Core',
    #     store=True, readonly=True)
    # tebal_id = fields.Float(        
    #     related='product_variant_id.tebal',
    #     string='Tebal',
    #     store=True, readonly=True)
    # lebar_id = fields.Float(        
    #     related='product_variant_id.lebar',
    #     string='Lebar',
    #     store=True, readonly=True)
    # panjang_id = fields.Float(        
    #     related='product_variant_id.panjang',
    #     string='Panjang',
    #     store=True, readonly=True)
    # grade_id = fields.Many2one(
    #     comodel_name='pwk.grade',
    #     related='product_variant_id.grade',
    #     string='Grade',
    #     store=True, readonly=True)
    # marking_grade_id = fields.Many2one(
    #     comodel_name='pwk.grade',
    #     related='product_variant_id.marking_grade',
    #     string='Marking Grade',
    #     store=True, readonly=True)
    # glue_id = fields.Many2one(
    #     comodel_name='pwk.glue',
    #     related='product_variant_id.glue',
    #     string='Glue',
    #     store=True, readonly=True)
    # glue_certificate_id = fields.Char(        
    #     related='product_variant_id.glue_certificate',
    #     string='Glue Certificate',
    #     store=True, readonly=True)
    # tebal = fields.Float('Tebal')
    # lebar = fields.Float('Lebar')
    # panjang = fields.Float('Panjang')
    # grade = fields.Many2one('pwk.grade', 'Grade')
    # marking_grade = fields.Many2one('pwk.grade', 'Marking Grade')
    # glue = fields.Many2one('pwk.glue', 'Glue')
    # glue_certificate = fields.Char('Glue Certificate')

class ProductProduct(models.Model):
    _inherit = 'product.product'    

    service_to_purchase = fields.Boolean('Service to Purchase')
    jenis_kayu = fields.Many2one('pwk.jenis.kayu', 'Jenis Kayu (FB)')
    jenis_core = fields.Many2one('pwk.jenis.core', 'Jenis Core')
    goods_type = fields.Selection([
        ('Plywood','Plywood'),
        ('Blockboard','Blockboard'),
        ('Barecore','Barecore'),
        ('Faceback','Faceback'),
        ('MDF','MDF')]
        , string="Goods Type")
    tebal = fields.Float('Tebal')
    lebar = fields.Float('Lebar')
    panjang = fields.Float('Panjang')
    grade = fields.Many2one('pwk.grade', 'Grade')
    marking_grade = fields.Many2one('pwk.grade', 'Marking Grade')
    glue = fields.Many2one('pwk.glue', 'Glue')
    glue_certificate = fields.Char('Glue Certificate')
    commercial_name1 = fields.Char('Commercial Name 1')
    commercial_name2 = fields.Char('Commercial Name 2')
    commercial_name3 = fields.Char('Commercial Name 3')    

    @api.model
    def create(self, vals):
    	# product_name = self.env['product.template'].browse(vals['product_tmpl_id']).name
    	product = self.env['product.product'].search([('name', '=', vals['name'])])    	

    	if product:
    		raise ValueError(_('Exists ! Already a Product exists in this name'))

    	return super(ProductProduct, self).create(vals)   

    # @api.multi
    # def name_get(self):
    #     # TDE: this could be cleaned a bit I think

    #     def _name_get(d):
    #         name = d.get('name', '')
    #         jenis_kayu = d.get('jenis_kayu', '')
    #         tebal = d.get('tebal', '')
    #         lebar = d.get('lebar', '')
    #         panjang = d.get('panjang', '')
    #         grade = d.get('grade', '')
    #         glue = d.get('glue', '')
    #         # code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
    #         # if code:
    #         #     name = '[%s] %s' % (code,name)
    #         if tebal and lebar and panjang and grade and glue:
    #             name = '%s %s %sx%sx%s Grade %s Glue %s' % (name, (jenis_kayu or ''), int(tebal), int(lebar), int(panjang), grade, glue)
    #         elif tebal and lebar and panjang and grade:
    #             name = '%s %s %sx%sx%s Grade %s' % (name, (jenis_kayu or ''), int(tebal), int(lebar), int(panjang), grade)            
    #         elif tebal and lebar and panjang:
    #             name = '%s %s %sx%sx%s' % (name, (jenis_kayu or ''), int(tebal), int(lebar), int(panjang))
    #         return (d['id'], name)

    #     partner_id = self._context.get('partner_id')
    #     if partner_id:
    #         partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
    #     else:
    #         partner_ids = []

    #     # all user don't have access to seller and partner
    #     # check access and use superuser
    #     self.check_access_rights("read")
    #     self.check_access_rule("read")

    #     result = []

    #     # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
    #     # Use `load=False` to not call `name_get` for the `product_tmpl_id`
    #     self.sudo().read(['name', 'default_code', 'product_tmpl_id', 'attribute_value_ids', 'attribute_line_ids'], load=False)

    #     product_template_ids = self.sudo().mapped('product_tmpl_id').ids

    #     if partner_ids:
    #         supplier_info = self.env['product.supplierinfo'].sudo().search([
    #             ('product_tmpl_id', 'in', product_template_ids),
    #             ('name', 'in', partner_ids),
    #         ])
    #         # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
    #         # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
    #         supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
    #         supplier_info_by_template = {}
    #         for r in supplier_info:
    #             supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
    #     for product in self.sudo():
    #         # display only the attributes with multiple possible values on the template
    #         variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id')
    #         variant = product.attribute_value_ids._variant_name(variable_attributes)

    #         name = variant and "%s (%s)" % (product.name, variant) or product.name
    #         sellers = []
    #         if partner_ids:
    #             product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
    #             sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
    #             if not sellers:
    #                 sellers = [x for x in product_supplier_info if not x.product_id]
    #         if sellers:
    #             for s in sellers:
    #                 seller_variant = s.product_name and (
    #                     variant and "%s (%s)" % (s.product_name, variant) or s.product_name
    #                     ) or False
    #                 mydict = {
    #                           'id': product.id,
    #                           'name': seller_variant or name,
    #                           'default_code': s.product_code or product.default_code,
    #                           }
    #                 temp = _name_get(mydict)
    #                 if temp not in result:
    #                     result.append(temp)
    #         else:
    #             mydict = {
    #                       'id': product.id,
    #                       'name': name,
    #                       'default_code': product.default_code,
    #                       'jenis_kayu': product.jenis_kayu.name,
    #                       'tebal': product.tebal,
    #                       'lebar': product.lebar,
    #                       'panjang': product.panjang,
    #                       'grade': product.grade.name,
    #                       'glue': product.glue.name,
    #                       }
    #             result.append(_name_get(mydict))
    #     return result    
