import json
import re
import os

list_file = r"data\wine_list.json"
desc_file = r"data\wine_descriptions.json"

wines = []

def parse_wines_from_text(text, has_desc=False):
    lines = text.split('\n')
    current_wine = {}
    extracted = []
    
    # We are looking for lines with prices, e.g., "15.00€"
    price_pattern = re.compile(r'([\d\,\.]+)\s*€')
    format_pattern = re.compile(r'(\d+(?:,\d+)?(?:ml|cl|L|l))', re.IGNORECASE)
    
    # State machine
    # 0 = looking for name/price
    # 1 = looking for region/grape/crianza
    # 2 = looking for description (only if has_desc)
    
    state = 0
    
    for line in lines:
        line = line.strip()
        if not line or line in ["Bahnschrift Light", "Bahnschrift SemiLight SemiConde", "Bahnschrift SemiCondensed", "Perpetua Titling MT"]:
            continue
            
        if state == 0:
            match = price_pattern.search(line)
            if match:
                price_str = match.group(1).replace(',', '.')
                name_part = line[:match.start()].strip()
                
                # Check for format in name
                fmt_match = format_pattern.search(name_part)
                formato = "75cl" # default
                if fmt_match:
                    formato = fmt_match.group(1).lower()
                    name_part = name_part.replace(fmt_match.group(0), "").strip()
                elif "MAGNUM" in name_part.upper():
                    formato = "150cl"
                    name_part = name_part.replace("MAGNUM", "").strip()
                elif "1,5L" in name_part.upper() or "1.5L" in name_part.upper() or "1500ML" in name_part.upper():
                    formato = "150cl"
                
                current_wine = {
                    "nombre": name_part,
                    "precio": float(price_str),
                    "formato": formato.replace("ml", "cl") if "ml" in formato else formato, # standardize later
                    "descripcion": ""
                }
                state = 1
        elif state == 1:
            # Region / Maker / Grape / Crianza
            parts = [p.strip() for p in line.split('/')]
            current_wine["region"] = parts[0] if len(parts) > 0 else "Desconocida"
            current_wine["maker"] = parts[1] if len(parts) > 1 else "Desconocido"
            current_wine["uva"] = parts[2] if len(parts) > 2 else "Desconocida"
            current_wine["crianza"] = parts[3] if len(parts) > 3 else "No especificado"
            
            if has_desc:
                state = 2
            else:
                extracted.append(current_wine)
                current_wine = {}
                state = 0
        elif state == 2:
            # If line has a price, it's the next wine
            if price_pattern.search(line):
                extracted.append(current_wine)
                current_wine = {}
                # re-process this line as state 0
                match = price_pattern.search(line)
                price_str = match.group(1).replace(',', '.')
                name_part = line[:match.start()].strip()
                fmt_match = format_pattern.search(name_part)
                formato = "75cl"
                if fmt_match:
                    formato = fmt_match.group(1).lower()
                    name_part = name_part.replace(fmt_match.group(0), "").strip()
                elif "MAGNUM" in name_part.upper():
                    formato = "150cl"
                    name_part = name_part.replace("MAGNUM", "").strip()
                elif "1500ML" in name_part.upper():
                    formato = "150cl"
                    name_part = name_part.replace("1500ML", "").strip()
                elif "1500Ml" in name_part:
                    formato = "150cl"
                    name_part = name_part.replace("1500Ml", "").strip()
                elif "1500cl" in name_part:
                    formato = "150cl"
                
                current_wine = {
                    "nombre": name_part,
                    "precio": float(price_str),
                    "formato": formato.replace("ml", "cl") if "ml" in formato else formato,
                    "descripcion": ""
                }
                state = 1
            else:
                # Accumulate description
                current_wine["descripcion"] += line + "\n"
                
    if current_wine and state >= 1:
        extracted.append(current_wine)
        
    return extracted

def main():
    try:
        with open(desc_file, 'r', encoding='utf-8') as f:
            desc_data = json.load(f)
            wines_with_desc = parse_wines_from_text(desc_data.get('content', ''), True)
    except:
        wines_with_desc = []
        
    try:
        with open(list_file, 'r', encoding='utf-8') as f:
            list_data = json.load(f)
            all_wines = parse_wines_from_text(list_data.get('content', ''), False)
    except:
        all_wines = []

    # Merge descriptions into the main list
    # Use name matching (ignoring case)
    
    for w in all_wines:
        # Standardize format strings
        f_str = w['formato']
        if f_str.endswith('ml'):
            try:
                v = int(f_str.replace('ml', ''))
                w['formato'] = f"{v/10:g}cl"
            except:
                pass
                
        # Find matching description
        matched_desc = ""
        matched_crianza = w['crianza']
        for wd in wines_with_desc:
            name1 = w['nombre'].lower().replace(' ', '')
            name2 = wd['nombre'].lower().replace(' ', '')
            
            # Simple soft match
            if name1 in name2 or name2 in name1:
                matched_desc = wd['descripcion'].strip()
                if wd['crianza'] != "No especificado":
                    matched_crianza = wd['crianza']
                break
        
        w['descripcion'] = matched_desc
        w['crianza'] = matched_crianza

    # Assign Tipo (Blanco, Tinto, etc) by guessing from Regions or categories if needed, 
    # but the text has headers like "VINOS BLANCOS", "VINOS TINTOS".
    # Wait, the parser doesn't track headers. Let's fix that.

    print(json.dumps(all_wines[:3], indent=2, ensure_ascii=False))
    print(f"Total wines parsed: {len(all_wines)}")

if __name__ == "__main__":
    main()
