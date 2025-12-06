"""
AL Drones - Population Analysis Tool
Analyzes population density in drone flight areas using IBGE data.
"""

import os
import argparse
import requests
import zipfile
import io
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
import pandas as pd


# Configuration
COLORS = {
    'Flight Geography': 'green',
    'Contingency Volume': 'orange',
    'Ground Risk Buffer': 'red',
    'Adjacent Area': 'blue',
}

ALBERS_BR = (
    "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)

# Cache for loaded grids
_GRID_CACHE = {}
_QUADRANT_INDEX = None


def extrair_layers_kml(kml_filename, layer_names):
    """Extract and union geometries from KML layers."""
    gdf = gpd.read_file(kml_filename, driver='KML')
    layers_poligonos = {}
    
    for name in layer_names:
        sel = gdf[gdf['Name'] == name]
        if sel.empty:
            print(f"⚠ Layer '{name}' not found in KML.")
            continue
        
        sel = sel[sel.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        if sel.empty:
            print(f"⚠ Layer '{name}' has no polygons.")
            continue
        
        layers_poligonos[name] = sel.geometry.union_all()
        print(f"✓ Layer '{name}' extracted.")
    
    return layers_poligonos


def carregar_indice_quadrantes():
    """
    Load the 500km aggregated grid to use as spatial index for quadrants.
    This grid shows which quadrants (grade_id) exist and their boundaries.
    """
    global _QUADRANT_INDEX
    
    if _QUADRANT_INDEX is not None:
        return _QUADRANT_INDEX
    
    url = "https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/grade_estatistica/censo_2022/grade_500km/BR500KM.zip"
    pasta = "dados_ibge/grade_500km"
    shp_path = os.path.join(pasta, "BR500KM.shp")
    
    if not os.path.exists(shp_path):
        os.makedirs(pasta, exist_ok=True)
        print("⬇ Downloading 500km grid index (one-time operation)...")
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                z.extractall(pasta)
        except Exception as e:
            print(f"✗ Error downloading 500km grid: {e}")
            return None
    
    # Load and convert to WGS84 for easy intersection with KML polygons
    _QUADRANT_INDEX = gpd.read_file(shp_path).to_crs(epsg=4326)
    print(f"✓ Quadrant index loaded: {len(_QUADRANT_INDEX)} cells")
    return _QUADRANT_INDEX


def identificar_grades_relevantes(area_geom):
    """
    Identify which IBGE grade_id quadrants intersect with the area of interest.
    Uses the 500km grid as spatial index.
    """
    quadrant_index = carregar_indice_quadrantes()
    
    if quadrant_index is None:
        print("✗ Error: Could not load quadrant index")
        return []
    
    # Find quadrants that intersect the area
    intersecting = quadrant_index[quadrant_index.intersects(area_geom)]
    
    if intersecting.empty:
        print("⚠ Warning: No quadrants found intersecting the polygon")
        print(f"  Polygon bounds: {area_geom.bounds}")
        return []
    
    # Extract unique QUADRANTE values (these correspond to grade_id numbers)
    grades_raw = sorted(intersecting['QUADRANTE'].unique().tolist())
    grades_relevantes = [int(g.replace("ID_", "")) for g in grades_raw]
    
    return grades_relevantes


def carregar_grid_ibge(grade_id, use_cache=True):
    """
    Download and load IBGE grid shapefile with caching.
    
    The IBGE Statistical Grid uses:
    - 1km x 1km cells in rural areas
    - 200m x 200m cells in urban areas
    - Albers Equal Area projection (SIRGAS2000)
    - Data from Census 2022
    """
    if use_cache and grade_id in _GRID_CACHE:
        return _GRID_CACHE[grade_id], grade_id
    
    url = f"https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/grade_estatistica/censo_2022/grade_estatistica/grade_id{grade_id}.zip"
    pasta = f"dados_ibge/grade_id{grade_id}"
    shp_path = os.path.join(pasta, f"grade_id{grade_id}.shp")
    
    if not os.path.exists(shp_path):
        os.makedirs(pasta, exist_ok=True)
        print(f"  ⬇ Downloading grade_id{grade_id}...")
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                z.extractall(pasta)
        except Exception as e:
            print(f"  ✗ Error downloading grade_id{grade_id}: {e}")
            return None, grade_id
    
    dados = gpd.read_file(shp_path)
    
    if use_cache:
        _GRID_CACHE[grade_id] = dados
    
    return dados, grade_id


def desenhar_contornos(ax, layers_poligonos, layer_order):
    """Draw layer boundaries."""
    for name in layer_order:
        if name in layers_poligonos:
            gpd.GeoSeries([layers_poligonos[name]]).boundary.plot(
                ax=ax, color=COLORS[name], linewidth=2
            )


def calcular_estatisticas(dados_intersec):
    """Calculate statistics from filtered grid."""
    if dados_intersec.empty:
        return 0, 0.0, 0.0
    
    total_pessoas = float(dados_intersec['TOTAL'].sum())
    area_total_km2 = float((dados_intersec.geometry.area.sum()) / 1e6)
    densidade_media = (total_pessoas / area_total_km2) if area_total_km2 > 0 else 0.0
    
    return total_pessoas, area_total_km2, densidade_media


def processar_todas_grades(area_geom, titulo, layers_poligonos, layers_para_mostrar, output_path=None, highlight_threshold=None, use_polygon_area=False):
    """
    Process all relevant IBGE grids and create a single combined map.
    Uses 500km grid as spatial index to identify relevant quadrants.
    
    Args:
        highlight_threshold: If set, cells with density > threshold will be highlighted in red
        use_polygon_area: If True, use actual polygon area instead of sum of cell areas
    """
    print(f"\n{'='*60}")
    print(f"Processing: {titulo}")
    print(f"{'='*60}")
    
    # Identify relevant grids using 500km index
    grades_relevantes = identificar_grades_relevantes(area_geom)
    
    if not grades_relevantes:
        print("⚠ No relevant grids found for this area.")
        return None
    
    print(f"✓ Identified {len(grades_relevantes)} relevant quadrants: {grades_relevantes}")
    
    # Collect data from all relevant grids
    todos_dados = []
    
    for grade_id in grades_relevantes:
        grid, _ = carregar_grid_ibge(grade_id)
        
        if grid is None:
            continue
        
        # Use spatial index for fast filtering
        try:
            possible_matches_idx = list(grid.sindex.intersection(area_geom.bounds))
            if not possible_matches_idx:
                continue
            
            possible_matches = grid.iloc[possible_matches_idx]
            dados_filtrados = possible_matches[possible_matches.intersects(area_geom)].copy()
            
            if not dados_filtrados.empty:
                print(f"  ✓ grade_id{grade_id}: {len(dados_filtrados)} cells found")
                todos_dados.append(dados_filtrados)
        except Exception as e:
            print(f"  ✗ grade_id{grade_id}: Error - {e}")
            continue
    
    if not todos_dados:
        print("⚠ No data found in any grid for this area.")
        return None
    
    # Combine all data
    dados_combinados = gpd.GeoDataFrame(pd.concat(todos_dados, ignore_index=True))
    print(f"✓ Total cells: {len(dados_combinados)}")
    
    # Calculate density in metric projection
    dados_area = dados_combinados.to_crs(ALBERS_BR)
    dados_area['area_km2'] = dados_area.geometry.area / 1e6
    dados_area['densidade_pop_km2'] = dados_area['TOTAL'] / dados_area['area_km2']
    dados_combinados['densidade_pop_km2'] = dados_area['densidade_pop_km2'].values
    
    # Plot
    fig, ax = plt.subplots(figsize=(24, 24))
    
    # Initialize variables for legend
    high_density = gpd.GeoDataFrame()
    normal_density = gpd.GeoDataFrame()
    
    # Plot cells with density highlighting if threshold is set
    if highlight_threshold is not None:
        # Separate high and normal density cells
        high_density = dados_combinados[dados_combinados['densidade_pop_km2'] > highlight_threshold]
        normal_density = dados_combinados[dados_combinados['densidade_pop_km2'] <= highlight_threshold]
        
        # Plot normal density cells in green
        if not normal_density.empty:
            normal_density.plot(
                ax=ax,
                color='green',
                alpha=0.5,
                edgecolor='darkgreen',
                linewidth=0.3,
                legend=False
            )
        
        # Plot high density cells with red highlight
        if not high_density.empty:
            high_density.plot(
                ax=ax,
                color='red',
                alpha=0.7,
                edgecolor='darkred',
                linewidth=0.5,
                legend=False
            )
    else:
        # Standard plot without highlighting - with colorbar legend
        im = dados_combinados.plot(
            column='densidade_pop_km2',
            ax=ax,
            cmap='YlOrBr',
            alpha=0.6,
            edgecolor='black',
            linewidth=0.2,
            legend=True,
            legend_kwds={'shrink': 0.3, 'label': 'Densidade (hab/km²)'}
        )
    
    # Draw layer boundaries with legend
    from matplotlib.patches import Patch
    legend_elements = []
    
    for name in layers_para_mostrar:
        if name in layers_poligonos:
            gpd.GeoSeries([layers_poligonos[name]]).boundary.plot(
                ax=ax, color=COLORS[name], linewidth=2.5
            )
            legend_elements.append(Patch(facecolor='none', edgecolor=COLORS[name], 
                                        linewidth=2, label=name))
    
    # Add high and low density cells to legend if threshold is set
    if highlight_threshold is not None:
        # Always add both legend items when threshold is set
        legend_elements.append(Patch(facecolor='green', edgecolor='darkgreen', 
                                    alpha=0.5, label=f'Densidade ≤ {highlight_threshold} hab/km²'))
        legend_elements.append(Patch(facecolor='red', edgecolor='darkred', 
                                    alpha=0.7, label=f'Densidade > {highlight_threshold} hab/km²'))
    
    # Add legend
    ax.legend(handles=legend_elements, loc='upper right', fontsize=12, 
             framealpha=0.9, edgecolor='black')
    
    ax.set_title(titulo, fontsize=18, fontweight='bold')
    ax.set_xlabel("Longitude [deg]", fontsize=14)
    ax.set_ylabel("Latitude [deg]", fontsize=14)
    
    try:
        cx.add_basemap(
            ax,
            crs=dados_combinados.crs.to_string(),
            source=cx.providers.OpenStreetMap.Mapnik,
            alpha=0.6,
            zoom=13
        )
    except Exception as e:
        print(f"⚠ Could not add basemap: {e}")
    
    # Statistics
    total_pessoas, area_total_km2, densidade_media = calcular_estatisticas(dados_area)
    
    # If use_polygon_area is True, recalculate density using actual polygon area
    if use_polygon_area:
        # Calculate actual polygon area in km²
        area_geom_projected = gpd.GeoSeries([area_geom], crs='EPSG:4326').to_crs(ALBERS_BR)
        area_real_km2 = area_geom_projected.area.iloc[0] / 1e6
        densidade_media = total_pessoas / area_real_km2 if area_real_km2 > 0 else 0.0
        
        info_texto = (
            f"Total population: {int(total_pessoas):,}\n"
            f"Polygon area: {area_real_km2:.2f} km²\n"
            f"Average density: {densidade_media:.2f} pop/km²"
        ).replace(",", ".")
    else:
        info_texto = (
            f"Total population: {int(total_pessoas):,}\n"
            f"Total cell area: {area_total_km2:.2f} km²\n"
            f"Average density: {densidade_media:.2f} pop/km²"
        ).replace(",", ".")
    
    ax.text(
        0.0, -0.10,
        info_texto,
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment='top',
        bbox=dict(facecolor='white', alpha=0.85)
    )
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Map saved: {output_path}")
    
    plt.close()
    
    return {
        'total_pessoas': total_pessoas,
        'area_total_km2': area_total_km2,
        'densidade_media': densidade_media
    }


def analyze_population(kml_file, output_dir='results'):
    """
    Main function to analyze population density from safety margins KML.
    
    Args:
        kml_file (str): Path to KML file with safety margins
        output_dir (str): Directory to save output maps
        
    Returns:
        dict: Statistics for each analyzed layer
    """
    os.makedirs(output_dir, exist_ok=True)
    
    layers_kml = ["Flight Geography", "Contingency Volume", "Ground Risk Buffer", "Adjacent Area"]
    
    print("="*60)
    print("AL DRONES - Population Analysis Tool")
    print("="*60)
    
    # Extract KML polygons
    layers_poligonos = extrair_layers_kml(kml_file, layers_kml)
    
    if not layers_poligonos:
        print("✗ No valid layers found in KML")
        return None
    
    results = {}
    
    # Plot 1 — Flight Geography
    stats = processar_todas_grades(
        area_geom=layers_poligonos['Flight Geography'],
        titulo="Population Density - Flight Geography",
        layers_poligonos=layers_poligonos,
        layers_para_mostrar=['Flight Geography'],
        output_path=os.path.join(output_dir, 'map_flight_geography.png'),
        highlight_threshold=5  # Highlight cells > 5 hab/km²
    )
    if stats:
        results['Flight Geography'] = stats
    
    # Plot 2 — Ground Risk Buffer
    stats = processar_todas_grades(
        area_geom=layers_poligonos['Ground Risk Buffer'],
        titulo="Population Density - Ground Risk Buffer",
        layers_poligonos=layers_poligonos,
        layers_para_mostrar=['Flight Geography', 'Contingency Volume', 'Ground Risk Buffer'],
        output_path=os.path.join(output_dir, 'map_ground_risk_buffer.png'),
        highlight_threshold=5  # Highlight cells > 5 hab/km²
    )
    if stats:
        results['Ground Risk Buffer'] = stats
    
    # Plot 3 — Adjacent Area ring
    # Note: Adjacent Area is built 5km from CV, but the analyzed ring excludes GRB
    if 'Adjacent Area' in layers_poligonos and 'Ground Risk Buffer' in layers_poligonos:
        area_anel = layers_poligonos['Adjacent Area'].difference(layers_poligonos['Ground Risk Buffer'])
        stats = processar_todas_grades(
            area_geom=area_anel,
            titulo="Population Density - Adjacent Area",
            layers_poligonos=layers_poligonos,
            layers_para_mostrar=['Flight Geography', 'Contingency Volume', 'Ground Risk Buffer', 'Adjacent Area'],
            output_path=os.path.join(output_dir, 'map_adjacent_area.png'),
            highlight_threshold=None,  # No highlighting for adjacent area
            use_polygon_area=True  # Use actual polygon area for density calculation
        )
        if stats:
            results['Adjacent Area'] = stats
    else:
        print("⚠ Cannot generate Adjacent Area plot: missing required layers.")
    
    print("\n" + "="*60)
    print("✓ Analysis complete!")
    print("="*60)
    
    return results


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Analyze population density in drone flight areas'
    )
    parser.add_argument(
        'kml_file',
        help='KML file with safety margins (output from generate_safety_margins.py)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='results',
        help='Output directory for maps (default: results/)'
    )
    
    args = parser.parse_args()
    
    analyze_population(args.kml_file, args.output_dir)


if __name__ == '__main__':
    main()