

from erpnext.stock.doctype.stock_ledger_entry.stock_ledger_entry import StockLedgerEntry


class SerialNoStockLedgerEntry(StockLedgerEntry):
    def on_submit(self):
        self.check_stock_frozen_date()
        self.calculate_batch_qty()

        if not self.get("via_landed_cost_voucher"):
            if self.company == "Husaingadh Enterprise LLP":
                from erpnext.stock.doctype.serial_no.serial_no import process_serial_no

                process_serial_no(self)
            else:
                from warranty_management.warranty_management.doctype.distributor_serial_no.distributor_serial_no import process_serial_no
                # from erpnext.stock.doctype.serial_no.serial_no import process_serial_no

                process_serial_no(self)