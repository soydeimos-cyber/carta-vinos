import json
import re
import os

list_file = r"data\wine_list.json"
desc_file = r"data\wine_descriptions.json"
output_path = r"app.js"

def parse_wines_from_text(text, has_desc=False):
    lines = text.split('\n')
    extracted = []
    
    price_pattern = re.compile(r'([\d\,\.]+)\s*€')
    format_pattern = re.compile(r'(\d+(?:,\d+)?(?:ml|cl|L|l))', re.IGNORECASE)
    
    state = 0
    current_wine = {}
    current_tipo = "Blanco" # Default fallback
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        upper_line = re.sub(r'\s+', ' ', line.upper())
        if "VINOS BLANCOS" in upper_line:
            current_tipo = "Blanco"
        elif "VINOS ROSADOS" in upper_line:
            current_tipo = "Rosado"
        elif "VINOS TINTOS" in upper_line:
            current_tipo = "Tinto"
        elif "ESPUMOSOS" in upper_line:
            current_tipo = "Espumoso"
        elif "VINOS DE JEREZ" in upper_line or "VINOS DULCES" in upper_line or upper_line == "DULCES":
            current_tipo = "Dulce/Jerez"
            
        if line in ["Bahnschrift Light", "Bahnschrift SemiLight SemiConde", "Bahnschrift SemiCondensed", "Perpetua Titling MT"]:
            continue
            
        if state == 0:
            match = price_pattern.search(line)
            if match:
                price_str = match.group(1).replace(',', '.')
                name_part = line[:match.start()].strip()
                if not name_part: continue # Skip empty names (like trailing prices)
                
                fmt_match = format_pattern.search(name_part)
                formato = "75cl"
                if fmt_match:
                    fmt_raw = fmt_match.group(1).lower()
                    if "ml" in fmt_raw:
                        v = int(fmt_raw.replace('ml', ''))
                        formato = f"{v/10:g}cl"
                    else:
                        formato = fmt_raw
                    name_part = name_part.replace(fmt_match.group(0), "").strip()
                elif "MAGNUM" in name_part.upper():
                    formato = "150cl"
                    name_part = name_part.replace("MAGNUM", "").strip()
                elif "1,5L" in name_part.upper() or "1.5L" in name_part.upper() or "1500ML" in name_part.upper() or "1500ML" in name_part.upper():
                    formato = "150cl"
                    name_part = re.sub(r'1[,.]5L|1500[Mm][Ll]', '', name_part).strip()
                
                current_wine = {
                    "nombre": name_part,
                    "precio": float(price_str),
                    "formato": formato,
                    "tipo": current_tipo,
                    "descripcion": ""
                }
                state = 1
        elif state == 1:
            parts = [p.strip() for p in line.split('/')]
            current_wine["region"] = parts[0] if len(parts) > 0 else "Desconocida"
            current_wine["maker"] = parts[1] if len(parts) > 1 else "Desconocido"
            current_wine["uva"] = parts[2] if len(parts) > 2 else "Desconocida"
            current_wine["crianza"] = parts[3] if len(parts) > 3 else "No especificado"
            
            # Clean up region
            r = current_wine["region"]
            r = re.sub(r"^(?:A\.O\.C|A\.O\.P|D\.O\.C\.G|D\.O\.C\.a|D\.O\.C|D\.O\.P|D\.O\.|V\.T\.|I\.G\.P\.)\s*", "", r, flags=re.IGNORECASE).strip()
            r = re.sub(r"^(?:DOCa|DOP|DO|VT|D\.O\.Ca\.)\s*", "", r, flags=re.IGNORECASE).strip()
            current_wine["region"] = r
            
            if has_desc:
                state = 2
            else:
                extracted.append(current_wine)
                current_wine = {}
                state = 0
        elif state == 2:
            if price_pattern.search(line):
                if current_wine and current_wine.get("nombre"):
                    extracted.append(current_wine)
                current_wine = {}
                # Restart parsing this line
                match = price_pattern.search(line)
                price_str = match.group(1).replace(',', '.')
                name_part = line[:match.start()].strip()
                if not name_part:
                    state = 0
                    continue
                fmt_match = format_pattern.search(name_part)
                formato = "75cl"
                if fmt_match:
                    fmt_raw = fmt_match.group(1).lower()
                    if "ml" in fmt_raw:
                        v = int(fmt_raw.replace('ml', ''))
                        formato = f"{v/10:g}cl"
                    else:
                        formato = fmt_raw
                    name_part = name_part.replace(fmt_match.group(0), "").strip()
                elif "MAGNUM" in name_part.upper():
                    formato = "150cl"
                    name_part = name_part.replace("MAGNUM", "").strip()
                
                current_wine = {
                    "nombre": name_part,
                    "precio": float(price_str),
                    "formato": formato,
                    "tipo": current_tipo,
                    "descripcion": ""
                }
                state = 1
            else:
                current_wine["descripcion"] += line + "\n"
                
    if current_wine and current_wine.get("nombre") and state >= 1:
        extracted.append(current_wine)
        
    return extracted

def build_wines():
    try:
        with open(desc_file, 'r', encoding='utf-8') as f:
            desc_data = json.load(f)
            wines_with_desc = parse_wines_from_text(desc_data.get('content', ''), True)
    except Exception as e:
        print("Warning: could not read desc file:", e)
        wines_with_desc = []
        
    try:
        with open(list_file, 'r', encoding='utf-8') as f:
            list_data = json.load(f)
            all_wines = parse_wines_from_text(list_data.get('content', ''), False)
    except Exception as e:
        print("Error: could not read list file:", e)
        return []

    for w in all_wines:
        matched_desc = ""
        matched_crianza = w['crianza']
        for wd in wines_with_desc:
            name1 = w['nombre'].lower().replace(' ', '')
            name2 = wd['nombre'].lower().replace(' ', '')
            
            if len(name1)>5 and len(name2)>5 and (name1 in name2 or name2 in name1):
                matched_desc = wd['descripcion'].strip()
                if wd['crianza'] != "No especificado":
                    matched_crianza = wd['crianza']
                break
        
        w['descripcion'] = matched_desc
        w['crianza'] = matched_crianza
        
        # Calculate mesesBarrica for filters
        meses_match = re.search(r'(\d+)\s*meses', w['crianza'], re.IGNORECASE)
        w['mesesBarrica'] = int(meses_match.group(1)) if meses_match else 0
        
    return all_wines

def render_js(wines):
    js_code = f"""
// === BASE DE DATOS LOCAL ENRIQUECIDA GENERADA ===
const winesData = {json.dumps(wines, ensure_ascii=False, indent=2)};

// Extraer options únicos para selectores
const getUniqueOptions = (arr, key) => {{
    let values = arr.map(w => w[key]).filter(v => v && v.toLowerCase() !== "no especificado" && v !== "Desconocida");
    return [...new Set(values)].sort();
}};
const uvasUnicas = getUniqueOptions(winesData, 'uva');
const regionesUnicas = getUniqueOptions(winesData, 'region');
const formatosUnicos = getUniqueOptions(winesData, 'formato');

// === LÓGICA DE LA APLICACIÓN ===
document.addEventListener("DOMContentLoaded", () => {{
    const winesGrid = document.getElementById("winesGrid");
    const noResults = document.getElementById("noResults");
    const resultsCount = document.getElementById("resultsCount");
    
    // Filtros
    const typeFilters = document.querySelectorAll(".chip");
    const priceRange = document.getElementById("priceRange");
    const priceValue = document.getElementById("priceValue");
    const uvaSelect = document.getElementById("uvaFilter");
    const regionSelect = document.getElementById("regionFilter");
    const barricaSelect = document.getElementById("barricaFilter");
    const formatoSelect = document.getElementById("formatoFilter");
    const resetBtn = document.getElementById("resetFiltersBtn");
    const searchInput = document.getElementById("searchInput");

    // Llenar Selects
    uvasUnicas.forEach(uva => {{
        if(uvaSelect) {{
            const opt = document.createElement("option");
            opt.value = uva; opt.textContent = uva;
            uvaSelect.appendChild(opt);
        }}
    }});
    
    regionesUnicas.forEach(reg => {{
        if(regionSelect) {{
            const opt = document.createElement("option");
            opt.value = reg; opt.textContent = reg;
            regionSelect.appendChild(opt);
        }}
    }});

    formatosUnicos.forEach(fmt => {{
        if(formatoSelect) {{
            const opt = document.createElement("option");
            opt.value = fmt; opt.textContent = fmt;
            formatoSelect.appendChild(opt);
        }}
    }});

    let filters = {{
        tipo: "all",
        maxPrice: 200,
        uva: "all",
        region: "all",
        barrica: "all",
        formato: "all",
        search: "" 
    }};

    // Renderizar Vinos
    const renderWines = (winesToRender) => {{
        winesGrid.innerHTML = "";
        
        if (winesToRender.length === 0) {{
            winesGrid.classList.add("hidden");
            noResults.classList.remove("hidden");
            resultsCount.textContent = "0 vinos encontrados";
            return;
        }}

        winesGrid.classList.remove("hidden");
        noResults.classList.add("hidden");
        resultsCount.textContent = `Encontrados ${{winesToRender.length}} vinos para ti`;

        winesToRender.forEach((wine, index) => {{
            const card = document.createElement("div");
            card.className = "wine-card expanded";
            card.style.animationDelay = `${{(index % 10) * 0.05}}s`;
            
            let descHtml = '';
            if (wine.descripcion) {{
                descHtml = `
                <div class="wine-desc-toggle" onclick="this.nextElementSibling.classList.toggle('hidden'); this.textContent = this.textContent === 'Leer descripción 🔽' ? 'Ocultar descripción 🔼' : 'Leer descripción 🔽'">Leer descripción 🔽</div>
                <div class="wine-desc hidden" style="margin-top: 10px; font-size: 0.9em; color: #555; border-top: 1px solid #eee; padding-top: 10px;">
                    ${{wine.descripcion.replace(/\\n/g, '<br>')}}
                </div>
                `;
            }}

            card.innerHTML = `
                <div class="card-content">
                    <div class="wine-type">${{wine.tipo}}</div>
                    <div class="wine-name">${{wine.nombre}}</div>
                    <div class="wine-details">
                        <p><i class="icon">🍾</i> ${{wine.formato}}</p>
                        <p><i class="icon">🍇</i> ${{wine.uva}}</p>
                        <p><i class="icon">📍</i> ${{wine.region}}</p>
                        <p><i class="icon">🛢️</i> ${{wine.crianza}}</p>
                    </div>
                    ${{descHtml}}
                </div>
                <div class="wine-price" style="align-self: flex-start; margin-top: 10px;">${{wine.precio.toFixed(2)}}€</div>
            `;
            winesGrid.appendChild(card);
        }});
    }};

    // Función de filtrado
    const applyFilters = () => {{
        const filtered = winesData.filter(wine => {{
            const matchType = filters.tipo === "all" || wine.tipo.toLowerCase().includes(filters.tipo.toLowerCase());
            const matchPrice = wine.precio <= filters.maxPrice;
            const matchUva = filters.uva === "all" || wine.uva === filters.uva;
            const matchRegion = filters.region === "all" || wine.region === filters.region;
            const matchFormato = filters.formato === "all" || wine.formato === filters.formato;
            const matchName = filters.search === "" || wine.nombre.toLowerCase().includes(filters.search.toLowerCase());
            
            let matchBarrica = true;
            if(filters.barrica === "no_barrica") {{
                matchBarrica = wine.mesesBarrica === 0;
            }} else if(filters.barrica === "1_6") {{
                matchBarrica = wine.mesesBarrica >= 1 && wine.mesesBarrica <= 6;
            }} else if(filters.barrica === "7_12") {{
                matchBarrica = wine.mesesBarrica >= 7 && wine.mesesBarrica <= 12;
            }} else if(filters.barrica === "mas_12") {{
                matchBarrica = wine.mesesBarrica > 12 || wine.crianza.toLowerCase().includes("reserva") || wine.crianza.includes("años");
            }}

            return matchType && matchPrice && matchUva && matchRegion && matchBarrica && matchFormato && matchName;
        }});
        
        renderWines(filtered);
    }};

    // Controladores de Eventos
    typeFilters.forEach(btn => {{
        btn.addEventListener("click", (e) => {{
            typeFilters.forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            filters.tipo = e.target.dataset.filter;
            applyFilters();
        }});
    }});

    priceRange.addEventListener("input", (e) => {{
        filters.maxPrice = parseInt(e.target.value);
        priceValue.textContent = filters.maxPrice;
        applyFilters();
    }});

    if(uvaSelect) uvaSelect.addEventListener("change", (e) => {{ filters.uva = e.target.value; applyFilters(); }});
    if(regionSelect) regionSelect.addEventListener("change", (e) => {{ filters.region = e.target.value; applyFilters(); }});
    if(barricaSelect) barricaSelect.addEventListener("change", (e) => {{ filters.barrica = e.target.value; applyFilters(); }});
    if(formatoSelect) formatoSelect.addEventListener("change", (e) => {{ filters.formato = e.target.value; applyFilters(); }});
    if(searchInput) searchInput.addEventListener("input", (e) => {{ filters.search = e.target.value; applyFilters(); }});

    if(resetBtn) resetBtn.addEventListener("click", () => {{
        filters = {{ tipo: "all", maxPrice: 200, uva: "all", region: "all", barrica: "all", formato: "all", search: "" }};
        priceRange.value = 200;
        priceValue.textContent = "200";
        if(uvaSelect) uvaSelect.value = "all";
        if(regionSelect) regionSelect.value = "all";
        if(barricaSelect) barricaSelect.value = "all";
        if(formatoSelect) formatoSelect.value = "all";
        if(searchInput) searchInput.value = "";
        
        typeFilters.forEach(b => b.classList.remove("active"));
        document.querySelector('[data-filter="all"]').classList.add("active");
        applyFilters();
    }});

    // Inicializar
    renderWines(winesData);
}});
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_code)

if __name__ == "__main__":
    wines = build_wines()
    for i, w in enumerate(wines): w['id'] = i + 1
    render_js(wines)
    print(f"App guardada en {{output_path}} con {{len(wines)}} vinos.")
