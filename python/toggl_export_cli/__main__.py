"""Main module for the Toggl Export CLI tool."""

import argparse
import logging
import sys
import os
from datetime import datetime, date # Added date
from typing import NoReturn, Optional
import calendar # Added for month range calculation
try:
    from zoneinfo import ZoneInfo # Use zoneinfo (Python 3.9+)
except ImportError:
    # Fallback or error handling if zoneinfo is not available
    # For simplicity, let's assume it is for now.
    # from pytz import timezone as ZoneInfo # Example using pytz
    logging.warning("zoneinfo module not found, timezone features might be limited.")
    ZoneInfo = None # Or handle appropriately

# Configure logging specifically for this tool
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("toggl_export_cli")

# --- Dependencies from the sync package ---
# This assumes the 'toggl_github_sync' package is importable
# (e.g., installed via pip -e . or PYTHONPATH is set correctly)
try:
    from toggl_github_sync.config import load_config
    # Assuming parse_date is needed here as well, or reimplement/copy it
    from toggl_github_sync.__main__ import parse_date # Reuse existing parser
    from .exporter import fetch_and_export_toggl_csv
except ImportError as e:
    logger.error(
        "Could not import dependencies from 'toggl_github_sync'. "
        "Ensure it's installed or PYTHONPATH is configured correctly. Error: %s", e
    )
    sys.exit(1)


def csv_to_pdf(csv_file_path: str, pdf_file_path: Optional[str] = None) -> str:
    """
    Convert CSV file to a formatted PDF with wrapped description text.
    
    Args:
        csv_file_path: Path to the CSV file to convert
        pdf_file_path: Optional path for the PDF output file. If None, uses the same name as CSV but with .pdf extension.
    
    Returns:
        Path to the created PDF file
    """
    try:
        import pandas as pd
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
    except ImportError as e:
        logger.error(f"Required libraries for PDF conversion not installed: {e}")
        logger.error("Please install pandas and reportlab: pip install pandas reportlab")
        sys.exit(1)
    
    # Determine PDF filename if not provided
    if pdf_file_path is None:
        base_name = os.path.splitext(csv_file_path)[0]
        pdf_file_path = f"{base_name}.pdf"
    
    logger.info(f"Converting CSV to PDF: {pdf_file_path}")
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        
        # Initialize PDF document with letter size
        page_width, page_height = letter
        doc = SimpleDocTemplate(pdf_file_path, pagesize=letter)
        elements = []
        
        # Set up styles
        styles = getSampleStyleSheet()
        style_normal = styles['Normal']
        
        # Calculate available width for the table (with page margins)
        margin = 0.5 * inch  # 0.5 inch margin on each side
        available_width = page_width - (2 * margin)
        
        # Process data and determine column widths
        data = [df.columns.tolist()]  # Header row
        
        # Convert all data to strings and add rows
        for _, row in df.iterrows():
            table_row = []
            for value in row:
                cell = str(value) if pd.notna(value) else ""
                table_row.append(cell)
            data.append(table_row)
        
        # Determine minimum widths for each column except the last
        import string
        from reportlab.pdfbase.pdfmetrics import stringWidth
        
        # Function to get minimum column width based on content
        def get_min_width(col_data):
            max_width = 0
            for item in col_data:
                # Calculate width of string in points
                width = stringWidth(str(item), 'Helvetica', 10) + 10  # Add padding
                max_width = max(max_width, width)
            return max_width
        
        # Get all data by column
        columns_data = list(zip(*data))
        
        # Calculate minimum widths for all columns except the last
        col_widths = []
        total_used_width = 0
        
        for i, col_data in enumerate(columns_data[:-1]):  # Skip the last column
            min_width = get_min_width(col_data)
            min_width = min(min_width, available_width * 0.15)  # Cap at 15% of available width
            col_widths.append(min_width)
            total_used_width += min_width
        
        # Last column gets remaining space
        last_col_width = available_width - total_used_width
        col_widths.append(last_col_width)
        
        # Convert data: only wrap text in the last column
        wrapped_data = []
        col_count = len(columns_data)
        last_col_index = col_count - 1
        
        for row in data:
            wrapped_row = []
            for i, cell in enumerate(row):
                if i == last_col_index:
                    # Only wrap text in the last column
                    wrapped_cell = Paragraph(str(cell), style_normal) if isinstance(cell, str) else cell
                    wrapped_row.append(wrapped_cell)
                else:
                    # Keep all other columns as simple text (no wrapping)
                    wrapped_row.append(cell)
            wrapped_data.append(wrapped_row)
        
        # Create table with the calculated column widths
        table = Table(wrapped_data, colWidths=col_widths, repeatRows=1)
        
        # Style the table
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            
            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Border styling
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Alternate row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(table)
        
        # Build the PDF
        doc.build(elements)
        logger.info(f"PDF export completed: {pdf_file_path}")
        return pdf_file_path
        
    except Exception as e:
        logger.error(f"Error converting CSV to PDF: {e}", exc_info=True)
        sys.exit(1)


def main() -> NoReturn:
    """Run the export CLI application."""
    parser = argparse.ArgumentParser(description="Export Toggl time entries to a CSV file.")
    parser.add_argument(
        "--output-file",
        type=str,
        required=False, # Make optional
        default=None,   # Default to None to check if provided
        help="Path to the output CSV file. Defaults to YYYYMMDD-YYYYMMDD.csv or YYYYMM.csv based on date range.",
    )

    # Group for mutually exclusive date arguments
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        "--start-date",
        type=str,
        help="Start date for export in YYYY-MM-DD format.",
    )
    date_group.add_argument(
        "--end-date", # Note: Making this exclusive with start_date means you can't specify just an end date. Consider if separate start/end or a range is better. For now, keeping it simple.
        type=str,
        help="End date for export in YYYY-MM-DD format.",
    )
    date_group.add_argument(
        "--month",
        type=str,
        help="Specify the entire month for export in YYYY-MM format. Overrides --start-date and --end-date.",
    )
    
    # Add PDF conversion option
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Convert the generated CSV to a multi-page, letter-sized PDF with wrapped description text.",
    )

    args = parser.parse_args()

    # Load configuration (needed for API key and timezone defaults)
    try:
         config = load_config()
    except Exception as e:
         logger.error("Failed to load configuration: %s", e, exc_info=True)
         sys.exit(1)

    # Determine date range (datetime objects)
    start_date_obj: Optional[datetime] = None
    end_date_obj: Optional[datetime] = None
    output_filename_base: str = "" # For generating default filename

    # Get timezone-aware 'today' if needed for defaults
    today_date: Optional[date] = None
    try:
        # Assuming config has a 'timezone' key like 'America/New_York'
        tz_str = config.timezone or 'UTC' # Default to UTC if not found
        if ZoneInfo:
            tz = ZoneInfo(tz_str)
            today_date = datetime.now(tz).date()
        else:
            # Handle case where ZoneInfo is not available (e.g., use naive datetime)
            today_date = datetime.utcnow().date()
            logger.warning("Defaulting date range to UTC 'today' due to missing timezone info.")
    except Exception as e:
        logger.warning(f"Could not determine timezone-aware 'today': {e}. Using naive UTC.", exc_info=True)
        today_date = datetime.utcnow().date()


    if args.month:
        try:
            year, month = map(int, args.month.split('-'))
            # Keep time info as start/end of day might matter for Toggl API
            first_day_dt = datetime(year, month, 1)
            _, last_day_num = calendar.monthrange(year, month)
            # Set end_date to end of the day
            last_day_dt = datetime(year, month, last_day_num, 23, 59, 59)
            start_date_obj = first_day_dt
            end_date_obj = last_day_dt
            date_range_str = f"the month of {args.month}"
            output_filename_base = args.month.replace('-', '') # YYYYMM
        except ValueError:
            logger.error("Invalid format for --month. Please use YYYY-MM.")
            sys.exit(1)
    elif args.start_date or args.end_date:
         start_date_obj = parse_date(args.start_date) if args.start_date else None
         end_date_obj = parse_date(args.end_date) if args.end_date else None

         # Use today for filename generation if one endpoint is missing
         temp_start_for_filename = start_date_obj.date() if start_date_obj else today_date
         temp_end_for_filename = end_date_obj.date() if end_date_obj else today_date

         output_filename_base = f"{temp_start_for_filename.strftime('%Y%m%d')}-{temp_end_for_filename.strftime('%Y%m%d')}"

         # Adjust logging string based on provided dates
         start_str = args.start_date if args.start_date else 'beginning'
         end_str = args.end_date if args.end_date else 'end'
         if start_date_obj and end_date_obj:
             date_range_str = f"{args.start_date} to {args.end_date}"
         elif start_date_obj:
             date_range_str = f"from {args.start_date} onwards"
         elif end_date_obj:
             date_range_str = f"up to {args.end_date}"
    else:
        # Default case: No dates specified, use today
        # Note: The fetch_and_export function might have its own default logic.
        # We are setting start/end date objects here primarily for filename generation.
        # Passing None to the function might still be correct if it handles defaults internally.
        start_date_obj = datetime(today_date.year, today_date.month, today_date.day) if today_date else None
        # Set end_date to end of the day
        end_date_obj = datetime(today_date.year, today_date.month, today_date.day, 23, 59, 59) if today_date else None
        date_range_str = f"today ({today_date.strftime('%Y-%m-%d')})" if today_date else "today (UTC)"
        output_filename_base = f"{today_date.strftime('%Y%m%d')}-{today_date.strftime('%Y%m%d')}" if today_date else "export"


    # Determine final output file path
    output_file = args.output_file
    if output_file is None:
        output_file = f"{output_filename_base}.csv"

    logger.info(f"Starting CSV export to {output_file}")
    if start_date_obj or end_date_obj: # Log if any date filter is applied
         logger.info(f"Exporting date range: {date_range_str}")

    # Call the export function with the determined path and original date objects (can be None)
    try:
        # Pass original start/end dates (could be None if not specified by user)
        # The function should handle None values according to its logic (e.g., default to today)
        fetch_and_export_toggl_csv(config, output_file, start_date=start_date_obj, end_date=end_date_obj)
        logger.info(f"CSV export completed: {output_file}")
        
        # Convert to PDF if requested
        if args.pdf:
            csv_to_pdf(output_file)
            
    except Exception as e:
        logger.error("An error occurred during the export process: %s", e, exc_info=True)


if __name__ == "__main__":
    main() 