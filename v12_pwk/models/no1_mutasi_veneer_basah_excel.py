# -*- coding: utf-8 -*-

import datetime
from datetime import datetime
import pytz
from odoo import models


class MutasiVeneerBasahReportXls(models.AbstractModel):
    _name = 'report.v12_pwk.mutasi_veneer_basah_report_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):        
        alamat = ' Jl. Raya Krangan - Pringsurat, Karanglo, Kupen, Kec. Pringsurat, Kabupaten Temanggung, Jawa Tengah 56272'

        sheet = workbook.add_worksheet('Sheet 1')
        format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True})
        format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
        formatHeaderCompany = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
        formatHeader = workbook.add_format({'font_size': 10, 'valign':'vcenter', 'align': 'left', 'bold': False, 'text_wrap': True})
        formatHeaderCenter = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True, 'text_wrap': True})
        formatHeaderRight = workbook.add_format({'font_size': 10, 'valign':'vcenter', 'align': 'left', 'num_format': '#,##0'})
        formatHeaderTable = workbook.add_format({'font_size': 10, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True})
        formatHeaderTableRight = workbook.add_format({'font_size': 10, 'valign':'vcenter', 'align': 'right', 'bold': True, 'bg_color':'#3eaec2', 'text_wrap': True, 'num_format': '#,##0'})
        formatHeaderDetailCenter = workbook.add_format({'font_size': 10, 'valign':'vcenter', 'align': 'centre', 'text_wrap': True})
        formatHeaderDetailCenterNumber = workbook.add_format({'font_size': 10, 'valign':'vcenter', 'align': 'centre', 'text_wrap': True, 'num_format': '#,##0'})
        formatHeaderDetailCenterNumberFour = workbook.add_format({'font_size': 10, 'valign':'vcenter', 'align': 'centre', 'text_wrap': True, 'num_format': '#,##4'})
        formatHeaderDetailLeft = workbook.add_format({'font_size': 10, 'valign':'vcenter', 'align': 'left'})
        formatHeaderDetailRight = workbook.add_format({'font_size': 10, 'valign':'vcenter', 'align': 'right', 'num_format': '#,##0'})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
        font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center'})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        
        formatHeaderTable.set_border(1)
        formatHeaderTableRight.set_border(1)
        formatHeaderDetailCenter.set_border(1)
        formatHeaderDetailCenterNumber.set_border(1)
        formatHeaderDetailCenterNumberFour.set_border(1)
        formatHeaderDetailRight.set_border(1)
        formatHeaderDetailLeft.set_border(1)

        formatHeaderTable.set_text_wrap()
        formatHeaderTableRight.set_text_wrap()
        formatHeaderDetailCenter.set_text_wrap()
        formatHeaderDetailRight.set_text_wrap()
        formatHeaderDetailLeft.set_text_wrap()
        
        # Set Column Width
        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 35)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 25)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)
        sheet.set_column(12, 12, 15)
        sheet.set_column(13, 13, 15)
        sheet.set_column(14, 14, 15)
        sheet.set_column(15, 15, 15)
        sheet.set_column(16, 16, 15)
        sheet.set_column(17, 17, 15)        

        sheet.set_row(8, 25)
        sheet.set_row(9, 30)

        # Header        
        sheet.merge_range(2, 0, 2, 16, 'LAPORAN MUTASI VENEER BASAH - STACKING', formatHeaderCenter)
        sheet.merge_range(3, 0, 3, 16, lines.date, formatHeaderCenter)

        # Table Header
        sheet.merge_range(8, 0, 9, 0, 'NO', formatHeaderTable)
        sheet.merge_range(8, 1, 9, 1, 'NAMA', formatHeaderTable)
        sheet.merge_range(8, 2, 9, 2, 'NO. TDP', formatHeaderTable)
        sheet.merge_range(8, 3, 9, 3, 'ALAMAT', formatHeaderTable)
        sheet.merge_range(8, 4, 8, 6, 'Dokumen Pelengkap Ekspor', formatHeaderTable)
        sheet.merge_range(8, 7, 8, 10, 'Data Barang Ekspor Sesuai PEB', formatHeaderTable)
        sheet.merge_range(8, 11, 9, 11, 'BUYER', formatHeaderTable)
        sheet.merge_range(8, 12, 9, 12, 'LC / TT', formatHeaderTable)
        sheet.merge_range(8, 13, 9, 13, 'CNF / FOB', formatHeaderTable)
        sheet.merge_range(8, 14, 9, 14, 'Kurs BI', formatHeaderTable)
        sheet.merge_range(8, 15, 9, 15, 'Kurs MK', formatHeaderTable)
        sheet.merge_range(8, 16, 9, 16, 'TOTAL ( Kurs MK x Volume )', formatHeaderTable)

        sheet.write(9, 4, 'No. & Tgl. Dokumen V-Legal', formatHeaderTable)
        sheet.write(9, 5, 'No. & Tgl. PEB', formatHeaderTable)
        sheet.write(9, 6, 'Lokasi Stuffing', formatHeaderTable)
        sheet.write(9, 7, 'Volume ( M3 )', formatHeaderTable)
        sheet.write(9, 8, 'Netto ( Kg )', formatHeaderTable)
        sheet.write(9, 9, 'Jumlah ( Unit )', formatHeaderTable)
        sheet.write(9, 10, 'Nilai ( USD )', formatHeaderTable)                