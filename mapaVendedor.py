import pandas as pd
import folium
from folium import DivIcon

# 1) Ler e preparar o DataFrame
df = pd.read_csv('dbmapaVENDEDORES.csv', encoding="ISO-8859-1", sep=";")

# Converter colunas de coordenadas para valores numéricos
df['LATITUDE CASA']  = pd.to_numeric(df['LATITUDE CASA'], errors='coerce')
df['LONGITUDE CASA'] = pd.to_numeric(df['LONGITUDE CASA'], errors='coerce')
df['LATITUDE']       = pd.to_numeric(df['LATITUDE'], errors='coerce')
df['LONGITUDE']      = pd.to_numeric(df['LONGITUDE'], errors='coerce')

# Filtrar linhas que possuem VENDEDOR e SUPERVISOR
df = df.dropna(subset=['VENDEDOR', 'SUPERVISOR'])

# 2) Preparar cores para cada VENDEDOR (garantindo cores suficientes)
cores = ['blue', 'red', 'green', 'purple', 'orange', 'darkred'
         ,'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 
         'lightblue', 'gray', 'black', 'yellow']
vendedores = df['VENDEDOR'].unique()
cores_VENDEDOR = {vendedor: cores[i % len(cores)] for i, vendedor in enumerate(vendedores)}

# 3) Criar o mapa base (centralizado em uma localização de referência)
mapa = folium.Map(location=[-3.7424091, -38.4867581], zoom_start=13)

# Adicionar CSS para a animação do ícone piscante
css = """
<style>
@keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0; }
    100% { opacity: 1; }
}
.blinking-home {
    animation: blink 1s infinite;
    font-size: 24px;
}
</style>
"""
mapa.get_root().html.add_child(folium.Element(css))

# Dicionários para armazenar os overlays
seller_layers = {}       # Overlay individual para cada vendedor
supervisor_layers = {}   # Overlay agrupado por supervisor

# 4) Construir overlays para cada VENDEDOR e agrupar por SUPERVISOR
for vendedor in vendedores:
    # Selecionar registros válidos para este vendedor
    df_vendedor = df[
        (df['VENDEDOR'] == vendedor) &
        (df['LATITUDE CASA'].notna()) &
        (df['LONGITUDE CASA'].notna()) &
        (df['LATITUDE'].notna()) &
        (df['LONGITUDE'].notna())
    ]
    
    if df_vendedor.empty:
        continue  # Pula se não houver dados válidos
    
    # Considera que todas as linhas deste vendedor possuem o mesmo supervisor
    supervisor = df_vendedor.iloc[0]['SUPERVISOR']
    cor = cores_VENDEDOR[vendedor]
    
    # --- Overlay do VENDEDOR ---
    fg_vendedor = folium.FeatureGroup(name=f"VENDEDOR: {vendedor}", show=False)
    
    # Converter explicitamente as coordenadas para float
    casa_lat = float(df_vendedor.iloc[0]['LATITUDE CASA'])
    casa_lon = float(df_vendedor.iloc[0]['LONGITUDE CASA'])
    casa_coords = [casa_lat, casa_lon]
    
    # Ícone da casa com efeito piscante usando o ícone "home" do Font Awesome
    folium.Marker(
        location=casa_coords,
        popup=f"Casa do VENDEDOR {vendedor}",
        icon=DivIcon(
            icon_size=(30, 30),
            icon_anchor=(15, 15),
            html=f'<div class="blinking-home" style="color:{cor};"><i class="fa fa-home"></i></div>'
        )
    ).add_to(fg_vendedor)
    
    # Inicializa a rota com a casa do vendedor
    rota = [casa_coords]
    
    # Adicionar marcadores para os clientes e acumular as coordenadas na rota
    for idx, row in df_vendedor.iterrows():
        cliente_coords = [float(row['LATITUDE']), float(row['LONGITUDE'])]
        folium.Marker(
            location=cliente_coords,
            popup=row['CLIENTE'],
            icon=folium.Icon(color=cor)
        ).add_to(fg_vendedor)
        rota.append(cliente_coords)
    
    # Print para depuração: mostra o vendedor e a lista de pontos da rota
    print(vendedor, rota)
    
    # Desenhar a rota se houver pelo menos dois pontos
    if len(rota) > 1:
        folium.PolyLine(rota, color=cor, weight=5).add_to(fg_vendedor)
    
    seller_layers[vendedor] = fg_vendedor
    mapa.add_child(fg_vendedor)
    
    # --- Overlay do SUPERVISOR ---
    if supervisor not in supervisor_layers:
        fg_supervisor = folium.FeatureGroup(name=f"SUPERVISOR: {supervisor}", show=False)
        supervisor_layers[supervisor] = fg_supervisor
        mapa.add_child(fg_supervisor)
    else:
        fg_supervisor = supervisor_layers[supervisor]
    
    # Adicionar os mesmos elementos deste vendedor ao overlay do supervisor
    folium.Marker(
        location=casa_coords,
        popup=f"Casa do VENDEDOR {vendedor}",
        icon=DivIcon(
            icon_size=(30, 30),
            icon_anchor=(15, 15),
            html=f'<div class="blinking-home" style="color:{cor};"><i class="fa fa-home"></i></div>'
        )
    ).add_to(fg_supervisor)
    
    for idx, row in df_vendedor.iterrows():
        cliente_coords = [float(row['LATITUDE']), float(row['LONGITUDE'])]
        folium.Marker(
            location=cliente_coords,
            popup=row['CLIENTE'],
            icon=folium.Icon(color=cor)
        ).add_to(fg_supervisor)
    
    if len(rota) > 1:
        folium.PolyLine(rota, color=cor, weight=2.5).add_to(fg_supervisor)

# 5) Adicionar o controle de camadas para selecionar VENDEDOR ou SUPERVISOR
folium.LayerControl(collapsed=False).add_to(mapa)

# 6) Salvar o mapa em HTML
mapa.save("mapa_VENDEDORES_SUPERVISORES.html")
print("Mapa salvo!")
