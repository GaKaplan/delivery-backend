import pdfplumber
import re

def parse_pdf(file_path):
    """
    Parses a PDF file and extracts a list of dicts with 'name' and 'address'.
    Supports:
    1. Specific format: "Code 0 Address" (e.g., "7145 0 AV GAONA 2759")
    2. Fallback: "Name - Address" or comma separated.
    """
    extracted_data = [] # List of {"name": str, "address": str}
    
    # Regex for "Code 0 Address"
    # Captures: (Code) (0) (Address up to end of line or before other columns)
    # The image shows "Client or Address" column. Often PDF text extraction might merge columns or keep them spaced.
    # We'll try to match a number, space, 0, space, and then the text.
    # Given the visual: "7145   0 AV GAONA 2759"
    regex_code_0_addr = re.compile(r'^\d+\s+0\s+(.+)')

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Method 1: Regex for "Code 0 Address"
                match = regex_code_0_addr.search(line)
                if match:
                    # The group(1) includes address + trailing columns.
                    # Example: "AV GAONA 2759 14 10:00 A 23:00"
                    # We need to aggressively strip the trailing columns.
                    # Strategy: Split by double spaces (often used in PDFs to separate columns)
                    full_addr_part = match.group(1).strip()
                    
                    # Split by 2 or more spaces
                    parts = re.split(r'\s{2,}', full_addr_part)
                    address_candidate = parts[0]
                    
                    # Further cleanup: If the address ends with a single number that looks like "Bultos" (e.g. " 14"), 
                    # or time (e.g. "10:00"), strictly speaking we hope double space caught it.
                    # But if single spaced: "AV GAONA 2759 14" -> Geocoder might fail.
                    # Let's assume the address is Street + Number.
                    # Note: We can try a regex to cut off if we see a standalone small number at the end? 
                    # Or just rely on the fact that Nominatim is smart?
                    # The logs show "AV GAONA 2759 14 10:00 A 23:00" failed.
                    # Nominatim probably tried to find "AV GAONA 2759 14 10:00 A 23:00" and failed.
                    
                    # Let's try to remove things that look like times or stand-alone payload numbers
                    # Remove " \d{1,3} \d{1,2}:\d{2}" etc.
                    # Simple heuristic: Split by "   " (3 spaces) first? 
                    # The sample shows wide gaps. The logs showed "AV GAONA 2759 14 ...".
                    # If I look at the log: "Could not geocode: AV GAONA 2759 14 10:00 A 23:00"
                    # It seems `parts[0]` logic FAILED because `pdfplumber` might have merged them with single spaces?
                    # If so, we are in trouble unless we know the column structure.
                    # However, "AV GAONA 2759" is Street + Number.
                    # Try to regex match the address part specifically?
                    
                    # HEURISTIC: Address usually ends with a number. The next column is "Cant. Bultos" (Number).
                    # So we have Address Number + Box Number. "2759 14".
                    # This is ambiguous. "2759" vs "2759 14".
                    # However, usually addresses don't have just a 2-digit number after the house number.
                    # Let's try to append ", Argentina" (or just pass it) but we MUST clean the tail.
                    
                    # Aggressive cleanup:
                    # 1. Remove obvious time patterns like "10:00 A 23:00" or "9 a 14"
                    cleaned = re.sub(r'\d{1,2}:\d{2}.*', '', address_candidate)
                    cleaned = re.sub(r'\s\d{1,2}\s+[aA]\s+\d{1,2}.*', '', cleaned)
                    
                    # 2. If we have "Street Number OtherNumber", identifying "OtherNumber" is hard without column positions.
                    # But if we rely on `re.split(r'\s{2,}', ...)`, we assume 2 spaces. 
                    # If the user pdf DOES NOT have 2 spaces, we might need to assume the address is the first X words? No.
                    
                    # Let's blindly try to use the `parts[0]` strategy again, but maybe the regex needs to be better 
                    # at capturing the 0 separator? `^\d+\s+0\s+(.+)`
                    # The issue is `pdfplumber` might produce "AV GAONA 2759 14" with ONE space if columns overlap.
                    # BUT `pdfplumber` usually does `layout=True` by default or we can try `x_tolerance`.
                    
                    # Let's assume for now that simply appending default country helps Nominatim disambiguate, 
                    # OR we try to strip the last token if it's a small number?
                    
                    # Better yet: Let's remove any trailing text that matches the "Bultos" / "Horario" pattern 
                    # if we can guess it.
                    # For now, just taking `parts[0]` splits by 2+ spaces. 
                    # If the log showed "AV GAONA 2759 14...", it means there was NOT 2 spaces between 2759 and 14.
                    # That implies the PDF columns are tight.
                    
                    # Let's try to pass `layout=True` to `extract_text`? 
                    # Default is `x_tolerance=3`.
                    
                    # Let's just strip known bad patterns from the end.
                    # "14 10:00 A 23:00" -> Remove time. Remove small integers at the end?
                    
                    # New Regex for cleaning:
                    # Remove " \d{1,3} \d{1,2}:\d{2}.*" (Bultos + Time)
                    # Remove " \d{1,3} \d{1,2} [aA] \d{1,2}.*" (Bultos + Time range)
                    
                    address_clean = address_candidate
                    # Remove time range "10:00 A 23:00"
                    address_clean = re.sub(r'\s+\d{1,2}:\d{2}.*$', '', address_clean)
                    # Remove simplified time range "9 a 14" or "9 A 14"
                    address_clean = re.sub(r'\s+\d{1,2}\s+[aA]\s+\d{1,2}.*$', '', address_clean)
                    
                    # Remove dangling small number at the end (Bultos) if previous token is also a number (Address Number)
                    # Pattern: "Text Number Number" -> "Text Number"
                    # e.g. "GAONA 2759 14" -> "GAONA 2759"
                    # But be careful of "Av 9 de Julio". "9" is number, "Julio" is text.
                    # Regex: `(\D+\d+)\s+\d+$`
                    match_bultos = re.search(r'^(.+\d+)\s+\d+$', address_clean)
                    if match_bultos:
                        address_clean = match_bultos.group(1)
                    
                    extracted_data.append({"name": f"Cliente {len(extracted_data)+1}", "address": address_clean})
                    continue

                # Method 2: Fallback (existing logic)
                if ' - ' in line:
                    parts = line.split(' - ')
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        address = " ".join(parts[1:]).strip()
                        extracted_data.append({"name": name, "address": address})
                elif ',' in line:
                     parts = line.split(',')
                     if len(parts) >= 2:
                        name = parts[0].strip()
                        address = " ".join(parts[1:]).strip()
                        extracted_data.append({"name": name, "address": address})
                else:
                    # Fallback
                    # Skip headers
                    if "Cód.Cli" in line or "Importe" in line or "Page" in line:
                        continue
                        
                    if len(line) > 10:
                         extracted_data.append({"name": "Posible Dirección", "address": line})
                    
    return extracted_data
