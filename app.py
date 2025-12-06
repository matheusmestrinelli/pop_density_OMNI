"""
AL Drones - Population Analysis Web Application
Streamlit interface for drone safety analysis tools.
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
    page_title="AL Drones - Population Analysis",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with AL Drones branding
st.markdown("""
<style>
    /* AL Drones Color Palette */
    :root {
        --aldrones-green: #00ff00;
        --aldrones-dark: #1a1a1a;
        --aldrones-blue: #0066cc;
        --aldrones-gray: #333333;
    }
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1a1a1a 0%, #2a2a3e 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border-left: 5px solid #00ff00;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .main-header h1 {
        color: #ffffff;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: #00ff00;
        font-size: 1.2rem;
        margin: 0;
    }
    
    /* Card styling */
    .info-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 255, 0, 0.2);
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .info-card h3 {
        color: #00ff00;
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
</style>
""", unsafe_allow_html=True)


def create_header():
    """Create application header."""
    st.markdown("""
    <div class="main-header">
        <h1>🚁 AL Drones - Population Analysis Tool</h1>
        <p>Líder em Certificação de Drones | Análise de Densidade Populacional</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application."""
    # Header
    create_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Sistema de Análise")
        st.markdown("""
        Este sistema realiza:
        
        1. 📍 **Geração de Margens de Segurança**
           - Flight Geography
           - Contingency Volume
           - Ground Risk Buffer
           - Adjacent Area
        
        2. 📊 **Análise Populacional**
           - Dados IBGE Censo 2022
           - Mapas de densidade
           - Estatísticas detalhadas
        """)
        
        st.markdown("---")
        st.markdown("### 📞 Contato")
        st.markdown("""
        **AL Drones**  
        Líder em Certificação de Drones
        
        🌐 [aldrones.com.br](https://aldrones.com.br)  
        📧 contato@aldrones.com.br  
        📱 [@aldrones_aviation](https://instagram.com/aldrones_aviation)
        """)
    
    # Main content
    st.markdown("""
    <div class="info-card">
        <h3>ℹ️ Como usar</h3>
        <p>Faça upload de um arquivo KML contendo a geometria do voo (ponto ou polígono). 
        O sistema irá automaticamente:</p>
        <ul>
            <li>Gerar as 4 camadas de segurança</li>
            <li>Analisar a densidade populacional com dados do IBGE</li>
            <li>Gerar mapas e estatísticas detalhadas</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    st.markdown("### 📤 Upload do KML")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo KML de entrada",
        type=['kml'],
        key='kml_input'
    )
    
    if uploaded_file:
        # Create two columns for parameters
        st.markdown("### ⚙️ Configuração dos Parâmetros")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Parâmetros de Voo")
            fg_size = st.number_input(
                "Flight Geography Buffer (m)",
                min_value=0.0,
                value=0.0,
                step=10.0,
                help="Deixe em 0 se o KML já contém um polígono"
            )
            
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
            
            # Create metrics with color coding
            cols = st.columns(len(results))
            for idx, (layer_name, stats) in enumerate(results.items()):
                with cols[idx]:
                    densidade = stats['densidade_media']
                    
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
                            <p style="color: #fff; font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{int(stats['total_pessoas']):,}</p>
                            <p style="color: #ff0000; font-size: 1.1rem; margin: 0;">⚠️ {densidade:.1f} hab/km²</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.metric(
                            label=layer_name,
                            value=f"{int(stats['total_pessoas']):,}",
                            delta=f"{densidade:.1f} hab/km²"
                        )
            
            # Detailed statistics table
            with st.expander("📋 Estatísticas Detalhadas"):
                import pandas as pd
                stats_df = pd.DataFrame(results).T
                stats_df.columns = ['População Total', 'Área (km²)', 'Densidade (hab/km²)']
                stats_df['População Total'] = stats_df['População Total'].astype(int)
                stats_df['Área (km²)'] = stats_df['Área (km²)'].round(2)
                stats_df['Densidade (hab/km²)'] = stats_df['Densidade (hab/km²)'].round(2)
                st.dataframe(stats_df, use_container_width=True)
            
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
        <p>Desenvolvido com 💚 pela AL Drones | 
        <a href="https://aldrones.com.br" target="_blank">aldrones.com.br</a></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()