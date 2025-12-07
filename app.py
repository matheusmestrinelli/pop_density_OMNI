"""
AL Drones - Flight Area Analysis Tool
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
import geopandas as gpd

# Import from src folder
from src import generate_safety_margins as gsm
from src import population_analysis as pa


# Page configuration
st.set_page_config(
    page_title="AL Drones - Flight Area Analysis Tool",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS with AL Drones branding
st.markdown("""
<style>
    /* Hide Streamlit header elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
      
    /* Hide sidebar toggle button */
    [data-testid="collapsedControl"] {display: none;}
    
    /* AL Drones Color Palette */
    :root {
        --aldrones-green: #054750;
        --aldrones-dark: #1a1a1a;
        --aldrones-yellow: #E0AB25;
        --aldrones-gray: #333333;
    }
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #054750 0%, #0D0B54 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0rem;
        border-left: 5px solid #E0AB25;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .main-header h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0rem;
    }
    
    .main-header p {
        color: #054750;
        font-size: 1rem;
        margin: 0;
    }
    
    /* Card styling */
    .info-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 1rem;
        border-radius: 0px;
        border: 0px solid rgba(0, 255, 0, 0.2);
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .info-card h3 {
        color: #E0AB25;
        margin-top: 0;
    }
    
    .info-card p {
        color: #e0e0e0;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00cc00 0%, #00ff00 100%);
        color: #000000;
        font-weight: 600;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 5px;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background: linear-gradient(90deg, #00ff00 0%, #66ff66 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 255, 0, 0.4);
    }
    
    /* File uploader */
    .uploadedFile {
        background: rgba(0, 255, 0, 0.1);
        border: 2px dashed #00ff00;
        border-radius: 5px;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a1a 0%, #2a2a3e 100%);
    }
    
    /* Success messages */
    .stSuccess {
        background: rgba(0, 255, 0, 0.1);
        border-left: 4px solid #00ff00;
        color: #00ff00;
    }
    
    /* Info messages */
    .stInfo {
        background: rgba(0, 102, 204, 0.1);
        border-left: 4px solid #0066cc;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #00cc00 0%, #00ff00 100%);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(0, 255, 0, 0.05);
        border-radius: 5px;
        color: #00ff00;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #00ff00;
        font-size: 2rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: #e0e0e0;
    }
    
    /* Tables */
    .dataframe {
        background: rgba(255, 255, 255, 0.05);
        color: #e0e0e0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #888888;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 3rem;
    }
    
    .footer a {
        color: #00ff00;
        text-decoration: none;
    }
    
    .footer a:hover {
        color: #66ff66;
    }
    
    /* Steps indicator */
    .step-indicator {
        background: rgba(0, 255, 0, 0.1);
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border-left: 3px solid #00ff00;
        margin: 1rem 0;
        font-weight: 600;
        color: #00ff00;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
</style>
""", unsafe_allow_html=True)


def create_header():
    """Create application header with logos."""
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: center; align-items: center; gap: 3rem; margin-bottom: 2rem;">
            <img src="https://aldrones.com.br/wp-content/uploads/2021/01/Logo-branca-2.png" 
                 alt="AL Drones Logo" 
                 style="height: 70px; object-fit: contain;">
            <div style="width: 2px; height: 100px; background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.4), transparent);"></div>
            <img src="https://www.omnibrasil.com.br/assets/home/img/logo-branco-omni.png" 
                 alt="Omni Logo" 
                 style="height: 70px; object-fit: contain;">
        </div>
        <h1 style="text-align: center;">Análise da Área de Voo para o SwissDrones SDO 50 V3</h1>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application."""
    # Header
    create_header()
    
    # Main content
    st.markdown("""
    <div class="info-card">
        <h3>ℹ️ Como usar</h3>
        <p>Faça upload de um arquivo KML contendo a geometria do voo (linha ou polígono). 
        A ferramenta irá automaticamente:</p>
        <ul>
            <li>Gerar polígonos com as margens de segurança aplicáveis</li>
            <li>Analisar a densidade populacional na área de interesse utilizando os dados do IBGE 2022</li>
            <li>Gerar mapas e estatísticas detalhadas</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    st.markdown("### 📤 Upload do KML")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo KML de entrada",
        type=['kml'],
        key='kml_input',
        on_change=lambda: st.session_state.pop('analysis_results', None)  # Clear results on new upload
    )
    
    if uploaded_file:
        # Read geometry to check type
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            gdf_check = gpd.read_file(tmp_path, driver='KML')
            geom_types = gdf_check.geometry.type.unique()
            has_polygon = any(g in ['Polygon', 'MultiPolygon'] for g in geom_types)
            has_point_or_line = any(g in ['Point', 'LineString', 'MultiPoint', 'MultiLineString'] for g in geom_types)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
        except Exception as e:
            st.error(f"Erro ao ler KML: {str(e)}")
            has_polygon = False
            has_point_or_line = True
        
        # Create two columns for parameters
        st.markdown("### ⚙️ Configuração dos Parâmetros")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Parâmetros de Voo")
            
            # Only show FG buffer if geometry is point or line
            if has_point_or_line and not has_polygon:
                fg_size = st.number_input(
                    "Flight Geography Buffer (m)",
                    min_value=0.0,
                    value=50.0,
                    step=10.0,
                    help="Buffer para criar a área de voo a partir do ponto/linha"
                )
            else:
                fg_size = 0.0
                st.info("📍 Geometria detectada: Polígono (Flight Geography já definido)")
            
            height = st.number_input(
                "Altura de Voo (m)",
                min_value=0.0,
                value=100.0,
                step=10.0,
                help="Altura de voo em metros"
            )
        
        with col2:
            st.markdown("#### Parâmetros de Buffer")
            cv_size = st.number_input(
                "Contingency Volume (m)",
                min_value=0.0,
                value=50.0,
                step=10.0,
                help="Tamanho do volume de contingência"
            )
            
            corner_style = st.selectbox(
                "Estilo de Cantos",
                options=['square', 'rounded'],
                index=0,
                help="Estilo dos cantos dos buffers"
            )
        
        # Calculate GRB preview
        grb_preview = gsm.calculate_grb_size(height)
        st.info(f"📊 Ground Risk Buffer calculado: {grb_preview:.2f} m")
        
        # Process button
        if st.button("🚀 Iniciar Análise Completa", type="primary"):
            # Clear previous results
            if 'analysis_results' in st.session_state:
                del st.session_state['analysis_results']
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # ETAPA 1: Gerar Margens de Segurança
                status_text.markdown('<div class="step-indicator">📍 Etapa 1/2: Gerando margens de segurança...</div>', unsafe_allow_html=True)
                progress_bar.progress(10)
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp_input:
                    tmp_input.write(uploaded_file.getvalue())
                    tmp_input_path = tmp_input.name
                
                # Generate output path
                output_dir = tempfile.mkdtemp()
                safety_kml_path = os.path.join(output_dir, 'safety_margins.kml')
                
                # Generate safety margins
                result_path = gsm.generate_safety_margins(
                    input_kml_path=tmp_input_path,
                    output_kml_path=safety_kml_path,
                    fg_size=fg_size,
                    height=height,
                    cv_size=cv_size,
                    corner_style=corner_style
                )
                
                progress_bar.progress(30)
                st.success("✅ Margens de segurança geradas com sucesso!")
                
                # Read KML data for download
                with open(result_path, 'rb') as f:
                    kml_data = f.read()
                
                # ETAPA 2: Análise Populacional
                status_text.markdown('<div class="step-indicator">📊 Etapa 2/2: Analisando densidade populacional...</div>', unsafe_allow_html=True)
                progress_bar.progress(40)
                
                st.info("⏳ Baixando dados do IBGE e processando... Isso pode levar alguns minutos.")
                
                # Run population analysis
                analysis_output_dir = os.path.join(output_dir, 'analysis_results')
                os.makedirs(analysis_output_dir, exist_ok=True)
                
                results = pa.analyze_population(result_path, analysis_output_dir)
                
                progress_bar.progress(100)
                status_text.empty()
                
                if results:
                    # Store results in session state to persist across reruns
                    st.session_state['analysis_results'] = {
                        'stats': results,
                        'output_dir': analysis_output_dir,
                        'kml_data': kml_data
                    }
                else:
                    st.warning("⚠️ Nenhum resultado foi gerado. Verifique o arquivo KML.")
                
                # Cleanup temp input file
                if os.path.exists(tmp_input_path):
                    os.unlink(tmp_input_path)
            
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Erro durante o processamento: {str(e)}")
                import traceback
                with st.expander("Ver detalhes do erro"):
                    st.code(traceback.format_exc())
        
        # Display results if they exist in session state
        if 'analysis_results' in st.session_state:
            results = st.session_state['analysis_results']['stats']
            analysis_output_dir = st.session_state['analysis_results']['output_dir']
            kml_data = st.session_state['analysis_results']['kml_data']
            
            st.success("✅ Análise concluída com sucesso!")
            
            # Download KML button (always available)
            st.download_button(
                label="📥 Download KML com Margens de Segurança",
                data=kml_data,
                file_name='safety_margins.kml',
                mime='application/vnd.google-earth.kml+xml',
                key='download_kml_final',
                use_container_width=False
            )
            
            # Display results
            st.markdown("---")
            st.markdown("## 📈 Resultados da Análise")
            
            # Create metrics with color coding - DENSITY FIRST
            cols = st.columns(len(results))
            for idx, (layer_name, stats) in enumerate(results.items()):
                with cols[idx]:
                    # Use maximum density for FG and GRB, average for Adjacent Area
                    if layer_name in ['Flight Geography', 'Ground Risk Buffer']:
                        densidade = stats['densidade_maxima']
                        density_label = "Máx"
                    else:
                        densidade = stats['densidade_media']
                        density_label = "Média"
                    
                    # Define threshold based on layer
                    if layer_name == 'Adjacent Area':
                        threshold = 50
                    else:  # Flight Geography or Ground Risk Buffer
                        threshold = 5
                    
                    # Color code the density
                    if densidade > threshold:
                        st.markdown(f"""
                        <div style="background: rgba(255, 0, 0, 0.1); padding: 1rem; border-radius: 5px; border-left: 4px solid #ff0000;">
                            <p style="color: #888; font-size: 0.9rem; margin: 0;">{layer_name}</p>
                            <p style="color: #ff0000; font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0;">
                                ⚠️ {densidade:.1f} <span style="color: #ff6666; font-size: 1.2rem; font-weight: 600;">hab/km²</span>
                            </p>
                            <p style="color: #aaa; font-size: 0.8rem; margin: 0;">Densidade {density_label}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: rgba(0, 255, 0, 0.05); padding: 1rem; border-radius: 5px; border-left: 4px solid #00ff00;">
                            <p style="color: #888; font-size: 0.9rem; margin: 0;">{layer_name}</p>
                            <p style="color: #00ff00; font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0;">
                                ✓ {densidade:.1f} <span style="color: #66ff66; font-size: 1.2rem; font-weight: 600;">hab/km²</span>
                            </p>
                            <p style="color: #aaa; font-size: 0.8rem; margin: 0;">Densidade {density_label}</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Detailed statistics table
            with st.expander("📋 Estatísticas Detalhadas"):
                import pandas as pd
                stats_data = []
                for layer, stat in results.items():
                    stats_data.append({
                        'Camada': layer,
                        'População Total': int(stat['total_pessoas']),
                        'Área (km²)': round(stat['area_km2'], 2),
                        'Densidade Média (hab/km²)': round(stat['densidade_media'], 2),
                        'Densidade Máxima (hab/km²)': round(stat['densidade_maxima'], 2)
                    })
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
            
            # Display maps
            st.markdown("---")
            st.markdown("## 🗺️ Mapas de Densidade Populacional")
            
            maps = [
                ('map_flight_geography.png', 'Flight Geography'),
                ('map_ground_risk_buffer.png', 'Ground Risk Buffer'),
                ('map_adjacent_area.png', 'Adjacent Area')
            ]
            
            for map_file, map_title in maps:
                map_path = os.path.join(analysis_output_dir, map_file)
                if os.path.exists(map_path):
                    st.markdown(f"### {map_title}")
                    st.image(map_path, use_container_width=True)
            
            # Download results
            st.markdown("---")
            st.markdown("## 📥 Download dos Resultados")
            
            col1, col2, col3 = st.columns(3)
            
            for idx, (map_file, map_title) in enumerate(maps):
                map_path = os.path.join(analysis_output_dir, map_file)
                if os.path.exists(map_path):
                    with [col1, col2, col3][idx]:
                        with open(map_path, 'rb') as f:
                            file_data = f.read()
                            st.download_button(
                                label=f"📥 {map_title}",
                                data=file_data,
                                file_name=map_file,
                                mime='image/png',
                                use_container_width=True,
                                key=f"download_map_{idx}"
                            )
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© 2025 AL Drones - Todos os direitos reservados</p>
        <p>Desenvolvido pela AL Drones | 
        <a href="https://aldrones.com.br" target="_blank">aldrones.com.br</a></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
