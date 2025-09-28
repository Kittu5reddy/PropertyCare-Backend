
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from datetime import datetime
import os

class SubscriptionInvoiceGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    def _add_pdf_metadata(self, canvas, doc, invoice_data):
        """Set PDF metadata like title, author, subject"""
        canvas.setTitle(f"Invoice {invoice_data.get('invoice_number', '')}")
        canvas.setAuthor("Vibhoos PropCare Pvt Ltd")
        canvas.setSubject("Subscription Invoice")
        canvas.setKeywords("Invoice, Subscription, PropCare, Payment")
    def setup_custom_styles(self):
        """Setup custom paragraph styles matching the invoice design - optimized for single page"""
        
        # Invoice title style - reduced size
        self.invoice_title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=3,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#2d6a4f'),
            fontName='Helvetica-Bold'
        )
        
        # Invoice number and date style - reduced size
        self.invoice_meta_style = ParagraphStyle(
            'InvoiceMeta',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=15,
            alignment=TA_RIGHT,
            textColor=colors.black
        )
        
        # Customer details style - reduced size and spacing
        self.customer_details_style = ParagraphStyle(
            'CustomerDetails',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=3,
            spaceBefore=1,
            alignment=TA_LEFT,
            leading=14
        )
        
        # Property details style - reduced size and spacing
        self.property_details_style = ParagraphStyle(
            'PropertyDetails',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=3,
            spaceBefore=10,
            alignment=TA_LEFT,
            leading=14
        )
        
        # Footer style - reduced size
        self.footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#555555'),
            spaceBefore=15
        )
        
        # Signature style - reduced size and spacing
        self.signature_style = ParagraphStyle(
            'Signature',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceBefore=20,
            spaceAfter=10
        )

    def generate_invoice(self, invoice_data, filename="subscription_invoice.pdf", logo_path=None, signature_path=None):
        """
        Generate a subscription invoice PDF
        
        Args:
            invoice_data (dict): Dictionary containing all invoice data
            filename (str): Output filename for the PDF
            logo_path (str): Path to logo image file (optional)
            signature_path (str): Path to signature image file (optional)
        """
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=20,
            bottomMargin=20
        )
        
        story = []
        
        # Header section with logo and invoice title
        story.extend(self._create_header_section(invoice_data, logo_path))
        
        # Customer details
        story.extend(self._create_customer_details(invoice_data.get('customer', {})))
        
        # Property details
        story.extend(self._create_property_details(invoice_data.get('property', {})))
        
        # Invoice table
        story.extend(self._create_invoice_table(invoice_data.get('items', []), invoice_data.get('total', 0)))
        
        # Signature section
        story.extend(self._create_signature_section(signature_path))
        
        # Footer
        story.extend(self._create_footer_section(invoice_data.get('contact_email', 'support@vibhoospropcare.com')))
        
        # Build PDF
        doc.build(story)
        print(f"Invoice generated successfully: {filename}")
    
    def _create_header_section(self, invoice_data, logo_path=None):
        """Create header section with logo and invoice title"""
        story = []
        
        # Create header table for logo and title side by side
        header_data = []
        
        # Logo cell
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=2.5*inch, height=2.2*inch)
                logo.hAlign = 'LEFT'
                logo_cell = logo
            except Exception as e:
                print(f"Could not load logo: {e}")
                logo_cell = Paragraph("<b>VIBHOOS<br/>PROPCARE</b><br/><i>PRIVATE LIMITED</i><br/><font size='8'>Safeguarding Your Properties, Always</font>", 
                                    self.customer_details_style)
        else:
            logo_cell = Paragraph("<b>VIBHOOS<br/>PROPCARE</b><br/><i>PRIVATE LIMITED</i><br/><font size='8'>Safeguarding Your Properties, Always</font>", 
                                self.customer_details_style)
        
        # Title and meta info cell with proper spacing
        title_content = f"""
        <b><font size='24' color='#2d6a4f'>Subscription Invoice</font></b><br/><br/>
        <font size='12'>Invoice #: {invoice_data.get('invoice_number', 'INV-2025-001')}</font><br/>
        <font size='12'>Date: {invoice_data.get('invoice_date', 'September 27, 2025')}</font>
        """
        title_cell = Paragraph(title_content, 
                              ParagraphStyle('TitleCell', parent=self.styles['Normal'], alignment=TA_RIGHT, spaceAfter=10))
        
        header_data.append([logo_cell, title_cell])
        
        header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 30))
        return story
    
    def _create_customer_details(self, customer):
        """Create customer details section"""
        story = []
        
        customer_items = [
            f"<b>Billed To:</b> {customer.get('name', 'N/A')}",
            f"<b>User ID:</b> {customer.get('user_id', 'N/A')}",
            f"<b>Email:</b> {customer.get('email', 'N/A')}",
            f"<b>Subscription Plan:</b> {customer.get('subscription_plan', 'N/A')}"
        ]
        
        for item in customer_items:
            story.append(Paragraph(item, self.customer_details_style))
        
        return story
    
    def _create_property_details(self, property_info):
        """Create property details section - compact spacing"""
        story = []
        
        property_items = [
            f"<b>Property Name:</b> {property_info.get('name', 'N/A')}",
            f"<b>Property ID:</b> {property_info.get('id', 'N/A')}"
        ]
        
        for item in property_items:
            story.append(Paragraph(item, self.property_details_style))
        
        story.append(Spacer(1, 10))  # Reduced spacing
        return story
    def _create_invoice_table(self, items, subtotal_amount):
        """Create the invoice items table with GST and total."""
        story = []

        # Calculate GST and total
        gst_rate = 0.18
        try:
            subtotal = float(subtotal_amount)
        except Exception:
            subtotal = 0.0
        gst_amount = round(subtotal * gst_rate, 2)
        grand_total = round(subtotal + gst_amount, 2)

        # Table headers
        headers = ['Description', 'Period', 'Amount']
        table_data = [headers]

        # Add items
        for item in items:
            row = [
                item.get('description', ''),
                item.get('period', ''),
                f"Rs: {item.get('amount', '0.00')}"
            ]
            table_data.append(row)

        # GST row
        gst_row = [ 'GST (18%)','', f"Rs: {gst_amount:.2f}"]
        table_data.append(gst_row)
        gst_row =  [ 'Total','', f"Rs: {grand_total:.2f}"]
        table_data.append(gst_row)

        # Total row
        # total_row = [ 'Total','', f"Rs: {grand_total:.2f}"]
        # table_data.append(total_row)

        # Create table with adjusted column widths
        table = Table(table_data, colWidths=[3.2*inch, 2.3*inch, 1.5*inch])

        # Style the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -2), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 8),
            # GST row styling
            ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
            # Total row styling
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            # ('ALIGN', (0, -1), (1, -1), 'RIGHT'),
        ]))

        story.append(table)
        story.append(Spacer(1, 15))
        return story

    def _create_signature_section(self, signature_path=None):
        """Create signature section - compact for single page"""
        story = []
        
        story.append(Paragraph("Authorized Signature", self.signature_style))
        story.append(Spacer(1, 5))  # Reduced spacing
        
        # Signature image (if provided) - smaller size
        if signature_path and os.path.exists(signature_path):
            try:
                signature = Image(signature_path, width=1.5*inch, height=0.7*inch)  # Smaller signature
                signature.hAlign = 'CENTER'
                story.append(signature)
                story.append(Spacer(1, 5))
            except Exception as e:
                print(f"Could not load signature: {e}")
                story.append(Spacer(1, 40))  # Reduced space for manual signature
        else:
            story.append(Spacer(1, 40))  # Reduced space for manual signature
        
        return story
    
    def _create_footer_section(self, contact_email):
        """Create footer section - compact for single page"""
        story = []
        
        story.append(Spacer(1, 10))  # Reduced spacing
        
        footer_items = [
            "Thank you for choosing Vibhoos PropCare",
            "This is a system-generated invoice.",
            f"For support, reach us at: <u><link href='mailto:{contact_email}'>{contact_email}</link></u>"
        ]
        
        for i, item in enumerate(footer_items):
            story.append(Paragraph(item, self.footer_style))
            if i < len(footer_items) - 1:  # Add small spacing between items except last
                story.append(Spacer(1, 3))
        
        return story


def create_sample_invoice(data: dict) -> None:
    """Create a sample invoice matching the HTML template exactly"""

    generator = SubscriptionInvoiceGenerator()
    
    # Sample data matching the HTML template
    
    # Generate the invoice
    generator.generate_invoice(
        sample_data,
        sample_data["name"],
        logo_path=sample_data['logo_path'],      # Optional: provide path to logo
        signature_path=sample_data['signature_path']    # Optional: provide path to signature
    )


def create_custom_invoice(invoice_data, output_filename="custom_invoice.pdf", logo_path=None, signature_path=None):
    """
    Create a custom invoice with your own data
    
    Args:
        invoice_data (dict): Your invoice data
        output_filename (str): Name for the output PDF file
        logo_path (str): Optional path to logo image
        signature_path (str): Optional path to signature image
    """
    generator = SubscriptionInvoiceGenerator()
    generator.generate_invoice(invoice_data, output_filename, logo_path, signature_path)


def create_bulk_invoices(invoices_list, logo_path=None, signature_path=None):
    """
    Create multiple invoices from a list of invoice data
    
    Args:
        invoices_list (list): List of invoice data dictionaries
        logo_path (str): Optional path to logo image
        signature_path (str): Optional path to signature image
    """
    generator = SubscriptionInvoiceGenerator()
    
    for i, invoice_data in enumerate(invoices_list):
        filename = f"invoice_{invoice_data.get('invoice_number', f'INV-{i+1:03d}')}.pdf"
        generator.generate_invoice(invoice_data, filename, logo_path, signature_path)
        print(f"Generated: {filename}")


if __name__ == "__main__":
    # Install required package first:
    # pip install reportlab
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(BASE_DIR, "image.png")
    signature_path = os.path.join(BASE_DIR, "sig.png")

    print("Subscription Invoice Generator - Based on HTML Template")
    print("=" * 55)
    sample_data = {
        "name":"one-month-payment-recpt.pdf",
        "logo_path":logo_path,
        "signature_path":signature_path,
        'invoice_number': 'INV-2025-001',
        'invoice_date': 'September 27, 2025',
        'customer': {
            'name': 'Palvai Kaushik Reddy',
            'user_id': 'U12345',
            'email': 'kaushikpalvai2004@gmail.com',
            'subscription_plan': 'Premium Monthly'
        },
        'property': {
            'name': 'Sunshine Residency',
            'id': 'PC2025P005'
        },
        'items': [
            {
                'description': 'PropCare Premium Subscription',
                'period': 'Sep 27, 2025 – Oct 26, 2025',
                'amount': '499.00'
            }
        ],
        'total': '499.00',
        'contact_email': 'support@vibhoospropcare.com'
    }
    # Generate sample invoice
    create_sample_invoice(sample_data)
    
    print("\nSample invoice generated: subscription_invoice.pdf")
    print("\nTo create custom invoices, use the create_custom_invoice() function")
    print("or instantiate SubscriptionInvoiceGenerator class directly.")
    
    # Example of custom usage:
    """
    # Single custom invoice
    custom_data = {
        'invoice_number': 'INV-2025-002',
        'invoice_date': 'October 1, 2025',
        'customer': {
            'name': 'John Doe',
            'user_id': 'U67890',
            'email': 'john.doe@example.com',
            'subscription_plan': 'Basic Monthly'
        },
        'property': {
            'name': 'Downtown Property',
            'id': 'PC2025P010'
        },
        'items': [
            {
                'description': 'PropCare Basic Subscription',
                'period': 'Oct 1, 2025 – Oct 31, 2025',
                'amount': '299.00'
            }
        ],
        'total': '299.00',
        'contact_email': 'support@vibhoospropcare.com'
    }
    
    create_custom_invoice(custom_data, "custom_invoice.pdf")
    
    # Bulk invoice generation
    invoices_list = [custom_data, ...]  # List of invoice data
    create_bulk_invoices(invoices_list)
    """