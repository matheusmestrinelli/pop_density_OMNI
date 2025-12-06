"""
AL Drones - Population Analysis Web Application
Streamlit interface for drone safety analysis tools.
"""

import streamlit as st
import os
import tempfile
import base64
from pathlib import Path
import geopandas as gpd
from src.generate_safety_margins import generate_safety_margins
from src.population_analysis import analyze_population


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
</style>
""", unsafe_allow_html=True)


def load_logo():
    """Load AL Drones logo."""
    # You would replace this with the actual logo path
    logo_path = "assets/logo.svg"
    if os.path.exists(logo_path):
        with open(logo_path, "r") as f:
            return f.read()
    return None


def create_header():
    """Create application header."""
    st.markdown("""
    <div class="main-header">
        <h1>🚁 AL Drones - Population Analysis Tool</h1>
        <p>Líder em Certificação de Drones | Análise de Densidade Populacional</p>
    </div>
    """, unsafe_allow_html=True)


def step1_safety_margins():
    """Step 1: Generate Safety Margins."""
    st.markdown("### 📍 Etapa 1: Gerar Margens de Segurança")
    
    st.markdown("""
    <div class="info-card">
        <h3>ℹ️ Sobre esta etapa</h3>
        <p>Faça upload de um arquivo KML contendo a geometria do voo (ponto ou polígono). 
        O sistema irá gerar automaticamente 4 camadas de segurança:</p>
        <ul>
            <li><strong style="color: #00ff00;">Flight Geography</strong> - Área de voo</li>
            <li><strong style="color: #ffcc00;">Contingency Volume</strong> - Volume de contingência</li>
            <li><strong style="color: #ff0000;">Ground Risk Buffer</strong> - Buffer de risco ao solo</li>
            <li><strong style="color: #0066cc;">Adjacent Area</strong> - Área adjacente (5km)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Selecione o arquivo KML de entrada",
        type=['kml'],
        key='kml_input'
    )
    
    if uploaded_file:
        # Create two columns for parameters
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
        from src.generate_safety_margins import calculate_grb_size
        grb_preview = calculate_grb_size(height)
        st.info(f"📊 Ground Risk Buffer calculado: {grb_preview:.2f} m")
        
        # Generate button
        if st.button("🚀 Gerar Margens de Segurança", type="primary"):
            with st.spinner("Processando KML..."):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp_input:
                    tmp_input.write(uploaded_file.getvalue())
                    tmp_input_path = tmp_input.name
                
                # Generate output path
                output_dir = tempfile.mkdtemp()
                output_path = os.path.join(output_dir, 'safety_margins.kml')
                
                try:
                    # Generate safety margins
                    result_path = generate_safety_margins(
                        input_kml_path=tmp_input_path,
                        output_kml_path=output_path,
                        fg_size=fg_size,
                        height=height,
                        cv_size=cv_size,
                        corner_style=corner_style
                    )
                    
                    # Store in session state
                    st.session_state['safety_margins_kml'] = result_path
                    
                    # Success message
                    st.success("✅ Margens de segurança geradas com sucesso!")
                    
                    # Download button
                    with open(result_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download KML com Margens de Segurança",
                            data=f,
                            file_name='safety_margins.kml',
                            mime='application/vnd.google-earth.kml+xml'
                        )
                    
                    # Show preview
                    with st.expander("👁️ Visualizar Camadas Geradas"):
                        gdf = gpd.read_file(result_path)
                        st.dataframe(gdf[['Name']].value_counts())
                    
                except Exception as e:
                    st.error(f"❌ Erro ao processar KML: {str(e)}")
                finally:
                    # Cleanup
                    if os.path.exists(tmp_input_path):
                        os.unlink(tmp_input_path)


def step2_population_analysis():
    """Step 2: Population Analysis."""
    st.markdown("### 📊 Etapa 2: Análise de Densidade Populacional")
    
    st.markdown("""
    <div class="info-card">
        <h3>ℹ️ Sobre esta etapa</h3>
        <p>Faça upload do KML gerado na Etapa 1 (com as 4 camadas de segurança). 
        O sistema irá analisar a densidade populacional usando dados do IBGE Censo 2022.</p>
        <p><strong>Grade Estatística IBGE:</strong></p>
        <ul>
            <li>Resolução: 1km × 1km (rural) e 200m × 200m (urbano)</li>
            <li>Projeção: Albers Equal Area (SIRGAS2000)</li>
            <li>Dados: Censo 2022</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if safety margins KML exists in session
    has_session_kml = 'safety_margins_kml' in st.session_state
    
    if has_session_kml:
        st.info("✅ KML da Etapa 1 detectado. Você pode prosseguir diretamente ou fazer upload de um novo arquivo.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Selecione o arquivo KML com margens de segurança",
        type=['kml'],
        key='kml_analysis'
    )
    
    # Determine which file to use
    kml_to_analyze = None
    if uploaded_file:
        kml_to_analyze = uploaded_file
    elif has_session_kml:
        kml_to_analyze = st.session_state['safety_margins_kml']
    
    if kml_to_analyze:
        # Analyze button
        if st.button("🔍 Iniciar Análise Populacional", type="primary"):
            with st.spinner("Analisando densidade populacional... Isso pode levar alguns minutos."):
                # Save uploaded file if needed
                if isinstance(kml_to_analyze, str):
                    # Already a file path
                    input_path = kml_to_analyze
                else:
                    # Uploaded file, save temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp:
                        tmp.write(kml_to_analyze.getvalue())
                        input_path = tmp.name
                
                # Create output directory
                output_dir = tempfile.mkdtemp()
                
                try:
                    # Run analysis
                    results = analyze_population(input_path, output_dir)
                    
                    if results:
                        st.success("✅ Análise concluída com sucesso!")
                        
                        # Display results
                        st.markdown("### 📈 Resultados da Análise")
                        
                        # Create metrics
                        cols = st.columns(len(results))
                        for idx, (layer_name, stats) in enumerate(results.items()):
                            with cols[idx]:
                                st.metric(
                                    label=layer_name,
                                    value=f"{int(stats['total_pessoas']):,}",
                                    delta=f"{stats['densidade_media']:.1f} hab/km²"
                                )
                        
                        # Display maps
                        st.markdown("### 🗺️ Mapas de Densidade Populacional")
                        
                        maps = [
                            'map_flight_geography.png',
                            'map_ground_risk_buffer.png',
                            'map_adjacent_area.png'
                        ]
                        
                        for map_file in maps:
                            map_path = os.path.join(output_dir, map_file)
                            if os.path.exists(map_path):
                                st.image(map_path, use_container_width=True)
                        
                        # Download results
                        st.markdown("### 📥 Download dos Resultados")
                        
                        for map_file in maps:
                            map_path = os.path.join(output_dir, map_file)
                            if os.path.exists(map_path):
                                with open(map_path, 'rb') as f:
                                    st.download_button(
                                        label=f"Download {map_file}",
                                        data=f,
                                        file_name=map_file,
                                        mime='image/png'
                                    )
                    else:
                        st.warning("⚠️ Nenhum resultado foi gerado. Verifique o arquivo KML.")
                
                except Exception as e:
                    st.error(f"❌ Erro durante a análise: {str(e)}")
                    import traceback
                    with st.expander("Ver detalhes do erro"):
                        st.code(traceback.format_exc())


def main():
    """Main application."""
    # Header
    create_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Navegação")
        page = st.radio(
            "Selecione a etapa:",
            options=[
                "📍 Etapa 1: Margens de Segurança",
                "📊 Etapa 2: Análise Populacional",
                "ℹ️ Sobre"
            ],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### 📞 Contato")
        st.markdown("""
        **AL Drones**  
        Líder em Certificação de Drones
        
        🌐 [aldrones.com.br](https://aldrones.com.br)  
        📧 contato@aldrones.com.br  
        📱 Instagram: [@aldrones_aviation](https://instagram.com/aldrones_aviation)
        """)
    
    # Main content
    if page == "📍 Etapa 1: Margens de Segurança":
        step1_safety_margins()
    elif page == "📊 Etapa 2: Análise Populacional":
        step2_population_analysis()
    else:  # Sobre
        st.markdown("### ℹ️ Sobre o Sistema")
        
        st.markdown("""
        <div class="info-card">
            <h3>🚁 AL Drones Population Analysis Tool</h3>
            <p>Sistema de análise de densidade populacional para operações de drones, 
            desenvolvido pela AL Drones para auxiliar em estudos de risco para autorizações BVLOS.</p>
            
            <h4>Funcionalidades:</h4>
            <ul>
                <li><strong>Geração Automática de Margens de Segurança:</strong> 
                Cria 4 camadas de segurança baseadas em parâmetros de voo</li>
                <li><strong>Análise Populacional:</strong> 
                Utiliza dados oficiais do IBGE Censo 2022</li>
                <li><strong>Visualização Geoespacial:</strong> 
                Mapas de densidade populacional com camadas sobrepostas</li>
                <li><strong>Estatísticas Detalhadas:</strong> 
                População total, área e densidade média por camada</li>
            </ul>
            
            <h4>Tecnologias:</h4>
            <p>Python, GeoPandas, Streamlit, IBGE API, OpenStreetMap</p>
            
            <h4>Sobre a AL Drones:</h4>
            <p>A AL Drones é líder em certificação de drones no Brasil, especializada em 
            autorizações ANAC para voos BVLOS e drones de grande porte. Nossa equipe de 
            engenheiros aeronáuticos traz a experiência da aviação tripulada para o 
            desenvolvimento e certificação de aeronaves não tripuladas.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Team info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-card">
                <h4>👨‍✈️ André Arruda</h4>
                <p><strong>Co-Fundador</strong></p>
                <p>Eng. Aeronáutico<br>
                Especialista em Ensaios em Voo<br>
                Experiência: EMBRAER, AIRBUS, LATAM</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-card">
                <h4>👨‍💼 Lucas Florêncio</h4>
                <p><strong>Co-Fundador</strong></p>
                <p>Eng. Aeronáutico & MBA<br>
                Especialista em Certificação<br>
                Experiência: Airship do Brasil, Octans Aircraft</p>
            </div>
            """, unsafe_allow_html=True)
    
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
