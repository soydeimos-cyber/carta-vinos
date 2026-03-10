import re
import json

input_path = r"C:\Users\pcsag\.gemini\antigravity\brain\24d1781b-c8ba-4392-97cc-10e5801871af\.system_generated\steps\135\output.txt"
output_path = r"C:\Users\pcsag\.gemini\antigravity\scratch\wine_app\app.js"

wines = []
with open(input_path, 'r', encoding='utf-8') as f:
    text = f.read()
    # La respuesta es un JSON con "status" y "answer". El "answer" tiene la lista.
    try:
        data = json.loads(text)
        lines = data.get("answer", "").split("\n")
    except:
        lines = text.split("\n")

for line in lines:
    if not line.strip(): continue
    # Ej: "Fino Arroyuelo 370ml, Dulce/Jerez, 15.00€ [1]"
    match = re.search(r'^(.*?)[\,\;]\s*(Blanco|Tinto|Rosado|Espumoso|Dulce\/Jerez|Jerez|Dulce)[\,\;]\s*([\d\,\.]+)\s*€', line, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        wtype = match.group(2).strip()
        price_str = match.group(3).replace(',', '.')
        try:
            price = float(price_str)
            wines.append({
                "id": len(wines) + 1,
                "nombre": name,
                "tipo": wtype,
                "precio": price
            })
        except:
            pass

js_code = f"""
// === BASE DE DATOS LOCAL GENERADA DE LA CARTA ACTUAL ===
const winesData = {json.dumps(wines, ensure_ascii=False, indent=2)};

// === LÓGICA DE LA APLICACIÓN ===
document.addEventListener("DOMContentLoaded", () => {{
    const winesGrid = document.getElementById("winesGrid");
    const noResults = document.getElementById("noResults");
    const resultsCount = document.getElementById("resultsCount");
    const typeFilters = document.querySelectorAll(".chip");
    const priceRange = document.getElementById("priceRange");
    const priceValue = document.getElementById("priceValue");
    const resetBtn = document.getElementById("resetFiltersBtn");

    let currentFilter = "all";
    let currentMaxPrice = 200;

    // Renderizar Vinos
    const renderWines = (wines) => {{
        winesGrid.innerHTML = "";
        
        if (wines.length === 0) {{
            winesGrid.classList.add("hidden");
            noResults.classList.remove("hidden");
            resultsCount.textContent = "0 vinos encontrados";
            return;
        }}

        winesGrid.classList.remove("hidden");
        noResults.classList.add("hidden");
        resultsCount.textContent = `Encontrados ${{wines.length}} vinos para ti`;

        wines.forEach((wine, index) => {{
            const card = document.createElement("div");
            card.className = "wine-card";
            card.style.animationDelay = `${{(index % 10) * 0.05}}s`;
            
            card.innerHTML = `
                <div>
                    <div class="wine-type">${{wine.tipo}}</div>
                    <div class="wine-name">${{wine.nombre}}</div>
                </div>
                <div class="wine-price">${{wine.precio.toFixed(2)}}</div>
            `;
            winesGrid.appendChild(card);
        }});
    }};

    // Función de filtrado
    const applyFilters = () => {{
        const filtered = winesData.filter(wine => {{
            const matchType = currentFilter === "all" || wine.tipo.toLowerCase().includes(currentFilter.toLowerCase());
            const matchPrice = wine.precio <= currentMaxPrice;
            return matchType && matchPrice;
        }});
        
        renderWines(filtered);
    }};

    // Controladores de Eventos
    typeFilters.forEach(btn => {{
        btn.addEventListener("click", (e) => {{
            typeFilters.forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            currentFilter = e.target.dataset.filter;
            applyFilters();
        }});
    }});

    priceRange.addEventListener("input", (e) => {{
        currentMaxPrice = parseInt(e.target.value);
        priceValue.textContent = currentMaxPrice;
        applyFilters();
    }});

    resetBtn.addEventListener("click", () => {{
        currentFilter = "all";
        currentMaxPrice = 200;
        priceRange.value = 200;
        priceValue.textContent = "200";
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
print(f"App guardada en {{output_path}} con {{len(wines)}} vinos.")
