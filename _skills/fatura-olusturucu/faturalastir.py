import argparse
import sys
import os
import random
import shutil
from datetime import datetime, timedelta
from fpdf import FPDF
from fpdf.enums import XPos, YPos

class InvoicePDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Roboto", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "Thank you for your business.", align="C")

def generate_invoice(brand_name, company_name, company_email, company_address, amount, currency, output_dir, description_override=None):
    # Set dates
    today = datetime.now()
    issue_date = today.strftime('%d/%m/%Y')
    due_date = (today + timedelta(days=15)).strftime('%d/%m/%Y')
    
    # Invoice number
    invoice_number = f"INV-{today.strftime('%Y%m%d')}-{random.randint(100, 999)}"
    
    # File name (INVOICE_[Brand]_[DD-MM-YYYY].pdf)
    safe_brand = "".join([c if c.isalnum() else "_" for c in brand_name])
    filename = f"INVOICE_{safe_brand}_{today.strftime('%d-%m-%Y')}.pdf"
    
    # Ensure output dir exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, filename)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        pdf = InvoicePDF()
        pdf.add_font("Roboto", "", os.path.join(script_dir, "Roboto-Regular.ttf"))
        pdf.add_font("Roboto", "B", os.path.join(script_dir, "Roboto-Bold.ttf"))
        pdf.add_font("Roboto", "I", os.path.join(script_dir, "Roboto-Regular.ttf")) # Fallback
        
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Header
        pdf.set_font("Roboto", "B", 24)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(100, 10, "INVOICE", new_x=XPos.RIGHT, new_y=YPos.TOP)
        
        pdf.set_font("Roboto", "", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(40, 5, "Invoice No:", new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
        pdf.set_text_color(30, 30, 30)
        pdf.cell(50, 5, invoice_number, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
        
        # Spacer
        pdf.cell(100, 5, "", new_x=XPos.RIGHT, new_y=YPos.TOP)
        
        pdf.set_text_color(80, 80, 80)
        pdf.cell(40, 5, "Date of Issue:", new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
        pdf.set_text_color(30, 30, 30)
        pdf.cell(50, 5, issue_date, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
        
        # Spacer
        pdf.cell(100, 5, "", new_x=XPos.RIGHT, new_y=YPos.TOP)
        
        pdf.set_text_color(80, 80, 80)
        pdf.cell(40, 5, "Due Date:", new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
        pdf.set_text_color(30, 30, 30)
        pdf.cell(50, 5, due_date, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
        
        pdf.ln(10)
        
        # From section
        pdf.set_font("Roboto", "B", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(100, 5, "Dolunay Özeren", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Roboto", "", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(100, 5, "Mithatpaşa Cad. No: 103/3", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(100, 5, "Onur Mahallesi, Balçova, 35330 İzmir", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(100, 5, "ozerendolunay@gmail.com", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(100, 5, "+90 533 366 62 13", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.ln(15)
        
        # To section
        pdf.set_fill_color(248, 249, 250)
        pdf.rect(10, pdf.get_y(), 190, 35, 'F')
        
        pdf.set_y(pdf.get_y() + 5)
        pdf.set_x(15)
        pdf.set_font("Roboto", "B", 9)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(100, 5, "BILLED TO", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_x(15)
        pdf.set_font("Roboto", "B", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(100, 6, company_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        if company_email:
            pdf.set_x(15)
            pdf.set_font("Roboto", "", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(100, 5, company_email, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
        if company_address:
            pdf.set_x(15)
            clean_address = company_address.replace("\\n", " ").replace("\n", " ")
            pdf.multi_cell(150, 5, clean_address)
            
        pdf.set_y(pdf.get_y() + 15)
        
        # Table Header
        pdf.set_fill_color(248, 249, 250)
        pdf.set_font("Roboto", "B", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(100, 10, "  DESCRIPTION", border="B", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(30, 10, "UNIT COST", border="B", align="R", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(20, 10, "QTY", border="B", align="C", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(40, 10, "AMOUNT", border="B", align="R", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
        
        # Table Row
        pdf.set_font("Roboto", "", 10)
        pdf.set_text_color(30, 30, 30)
        description = description_override if description_override else f"{brand_name} collaboration with @dolunay_ozeren"
        pdf.cell(100, 10, f"  {description}", border="B", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(30, 10, f"{currency} {amount}", border="B", align="R", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(20, 10, "1", border="B", align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(40, 10, f"{currency} {amount}", border="B", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(15)
        
        # Totals
        pdf.set_x(120)
        pdf.set_font("Roboto", "", 10)
        pdf.cell(30, 6, "Subtotal", align="L", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(40, 6, f"{currency} {amount}", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_x(120)
        pdf.cell(30, 6, "Tax Rate", align="L", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(40, 6, "0%", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_x(120)
        pdf.cell(30, 6, "Tax", align="L", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(40, 6, f"{currency} 0", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Line for total
        pdf.set_x(120)
        pdf.cell(70, 2, "", border="T", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_x(120)
        pdf.set_font("Roboto", "B", 12)
        pdf.cell(30, 8, "Total Due", align="L", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(40, 8, f"{currency} {amount}", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.output(output_path)
        
        # Try to auto-copy to Downloads for quick access
        downloads_dir = os.path.expanduser("~/Downloads")
        downloads_path = os.path.join(downloads_dir, filename)
        try:
            shutil.copy2(output_path, downloads_path)
            print(f"COPY: Also saved to {downloads_path}")
        except (PermissionError, OSError):
            # Sandbox may block ~/Downloads access, that's OK
            pass
        
        print(f"SUCCESS: Invoice generated at {output_path}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FAILED to generate invoice PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an invoice PDF.")
    parser.add_argument("--brand", required=True, help="Brand name for the description")
    parser.add_argument("--company", required=True, help="Company legal name")
    parser.add_argument("--email", default="", help="Company email")
    parser.add_argument("--address", default="", help="Company address")
    parser.add_argument("--amount", required=True, help="Amount (e.g. 600)")
    parser.add_argument("--currency", default="$", help="Currency symbol (e.g. $ or TL)")
    parser.add_argument("--description", default="", help="Custom description for the invoice line item")
    parser.add_argument("--output", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "uretilen-faturalar"), help="Output directory")
    
    args = parser.parse_args()
    
    generate_invoice(
        args.brand,
        args.company,
        args.email,
        args.address,
        args.amount,
        args.currency,
        os.path.abspath(args.output),
        args.description or None
    )
