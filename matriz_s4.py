import streamlit as st
import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import re
import urllib.parse
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform

# Configuración de la página
st.set_page_config(page_title="Financial Portfolio Analyzer", layout="wide")

# ---- Función de Limpieza de Tickers ----
def clean_ticker(ticker_str):
    """
    Limpia cualquier carácter extraño, espacios invisibles (\xa0, \u200b),
    comillas o caracteres no válidos que impidan a Yahoo Finance encontrar el ticker.
    """
    if not isinstance(ticker_str, str):
        ticker_str = str(ticker_str) if pd.notna(ticker_str) else ""
    cleaned = re.sub(r'[^a-zA-Z0-9\.\-]', '', ticker_str)
    return cleaned.upper()

# ---- Título e Introducción ----
st.title("Financial Portfolio & Correlation Analyzer")
st.subheader("Analiza precios históricos, matriz de correlación por retornos diarios y explora el clustering jerárquico por ramas.")
st.text(" ")

# Inicializar sesión de tickers vacía si no existe
if "ticker_pool" not in st.session_state:
    st.session_state.ticker_pool = []

# ---- Configuración de Entradas (Sidebar) ----
st.sidebar.header("1. Carga y Gestión de Tickers")

# Carga obligatoria/opcional de archivo Excel
uploaded_file = st.sidebar.file_uploader("Subir archivo Excel (.xlsx, .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df_excel = pd.read_excel(uploaded_file, header=None)
        
        # Se toma la primera columna (índice 0)
        raw_excel_tickers = df_excel.iloc[:, 0].dropna().astype(str).tolist()
        
        # Limpieza y eliminación de duplicados
        excel_tickers = list(dict.fromkeys([clean_ticker(t) for t in raw_excel_tickers if clean_ticker(t)]))
        
        # Si la primera celda es un encabezado común, se descarta
        if excel_tickers and excel_tickers[0] in ["TICKER", "TICKERS", "SIMBOLO", "SYMBOL", "ASSET"]:
            excel_tickers = excel_tickers[1:]
            
        if excel_tickers:
            st.session_state.ticker_pool = excel_tickers
            st.sidebar.success(f"Archivo cargado: {len(excel_tickers)} tickers importados.")
        else:
            st.sidebar.warning("No se encontraron tickers válidos en la primera columna del archivo.")
    except Exception as e:
        st.sidebar.error(f"Error al procesar el archivo Excel: {e}")

# Opción manual para agregar nuevos tickers
new_ticker_input = st.sidebar.text_input("Añadir ticker(s) manualmente (por coma):")
if st.sidebar.button("➕ Agregar al Pool"):
    if new_ticker_input:
        raw_list = new_ticker_input.split(",")
        new_list = [clean_ticker(t) for t in raw_list if clean_ticker(t)]
        
        added_count = 0
        for t in new_list:
            if t not in st.session_state.ticker_pool:
                st.session_state.ticker_pool.append(t)
                added_count += 1
        if added_count > 0:
            st.sidebar.success(f"Se agregaron {added_count} ticker(s) a la lista.")
        else:
            st.sidebar.info("El/Los ticker(s) ya existían en la lista.")

# Multiselect para elegir qué tickers comparar del pool cargado
st.sidebar.header("2. Selección para Análisis")
if st.session_state.ticker_pool:
    selected_tickers = st.sidebar.multiselect(
        "Selecciona los tickers a comparar:",
        options=st.session_state.ticker_pool,
        default=st.session_state.ticker_pool
    )
else:
    selected_tickers = []
    st.sidebar.info("Sube un archivo Excel o escribe tickers manualmente para comenzar.")

# Selección de Fechas
st.sidebar.header("3. Rango de Fechas")
col_date1, col_date2 = st.sidebar.columns(2)
start_date = col_date1.date_input("Fecha Inicio:", datetime.date(2023, 1, 1))
end_date = col_date2.date_input("Fecha Fin:", datetime.date.today())

# Función para extraer información del Sector y Nombre de la Empresa con link en la Empresa
@st.cache_data(show_spinner=False)
def get_tickers_info(ticker_tuple):
    info_list = []
    for t in ticker_tuple:
        try:
            tk = yf.Ticker(t)
            name = tk.info.get('longName', tk.info.get('shortName', t))
            sector = tk.info.get('sector', tk.info.get('quoteType', 'N/A'))
        except Exception:
            name = t
            sector = 'N/A'
            
        # Limpiar el nombre para la URL
        clean_name = str(name).strip()
        query = f"de que es la compañia {clean_name} ticker {t} y quienes son sus principales clientes"
        encoded_query = urllib.parse.quote_plus(query)
        
        # Guardamos la URL llevando el nombre al final (#company_name) para que regex lo extraiga como texto visible
        encoded_display_name = urllib.parse.quote(clean_name)
        google_ai_url = f"https://www.google.com/search?q={encoded_query}&udm=50#{encoded_display_name}"
        
        info_list.append({
            'Ticker': t,
            'Empresa': google_ai_url,
            'Sector': sector
        })
    return pd.DataFrame(info_list)

# Función para renderizar la tabla nativa de Streamlit con la Empresa como hipervínculo azul
def render_interactive_info_table(df_info):
    st.dataframe(
        df_info,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker"),
            "Empresa": st.column_config.LinkColumn(
                "Empresa",
                help="Haz clic sobre la empresa para abrir Google IA y ver qué hace y sus clientes",
                display_text=r"#(.+)$"  # Extrae y muestra únicamente el nombre de la empresa
            ),
            "Sector": st.column_config.TextColumn("Sector")
        },
        use_container_width=True,
        hide_index=True
    )

# Función para descargar datos desde Yahoo Finance
@st.cache_data
def load_financial_data(ticker_list, start, end):
    if not ticker_list:
        return None, None, None
    try:
        clean_list = [clean_ticker(t) for t in ticker_list if clean_ticker(t)]
        sorted_tickers = sorted(list(set(clean_list)))
        
        if not sorted_tickers:
            return None, None, None

        df_download = yf.download(sorted_tickers, start=start, end=end)
        
        if isinstance(df_download.columns, pd.MultiIndex) and 'Close' in df_download.columns.levels[0]:
            data = df_download['Close']
        else:
            data = df_download['Close'] if 'Close' in df_download else df_download

        if isinstance(data, pd.Series):
            data = data.to_frame()

        data = data[[t for t in clean_list if t in data.columns]]
        data = data.dropna(how='all', axis=1)

        returns = data.pct_change().dropna()
        corr_matrix = returns.corr()
        
        return data, returns, corr_matrix
    except Exception as e:
        st.error(f"Error al descargar datos de Yahoo Finance: {e}")
        return None, None, None

# ---- Cargar Datos de los seleccionados ----
if selected_tickers:
    data, returns, corr_matrix = load_financial_data(selected_tickers, start_date, end_date)
else:
    data, returns, corr_matrix = None, None, None

# ==== Aplicación Principal ====
def main():
    activities = [
        "Análisis de Datos & Precios", 
        "Visualización General", 
        "🌳 Explorador por Ramas / Clusters", 
        "Descarga de Archivos"
    ]
    option = st.sidebar.selectbox("Elige una operación:", activities)

    # ----------------- 1. Análisis de Datos -----------------
    if option == "Análisis de Datos & Precios":
        st.subheader("📈 Precios Históricos y Retornos Diarios")
        
        st.write("#### Precios de Cierre Históricos")
        st.dataframe(data)
        
        st.write("#### Retornos Diarios Porcentuales")
        st.dataframe(returns)

        if st.checkbox("Mostrar Resumen Estadístico de los Retornos"):
            st.write(returns.describe())

    # ----------------- 2. Visualización General -----------------
    elif option == "Visualización General":
        st.subheader("📊 Diagramas Generales de Correlación")

        if st.checkbox("Mostrar Precios Normalizados (Base 100)", value=True):
            fig, ax = plt.subplots(figsize=(8, 3.5))
            normalized = (data / data.iloc[0]) * 100
            for col in normalized.columns:
                ax.plot(normalized.index, normalized[col], label=col)
            ax.set_title("Rendimiento Relativo de Activos (Base 100)", fontsize=11)
            ax.set_ylabel("Valor Relativo", fontsize=9)
            ax.tick_params(labelsize=8)
            ax.legend(loc="upper left", bbox_to_anchor=(1, 1), fontsize=8)
            
            col_chart, _ = st.columns([3, 1])
            with col_chart:
                st.pyplot(fig)
            plt.close(fig)

        if st.checkbox("Mostrar Mapa de Calor Completo", value=True):
            st.write("#### Matriz de Correlación Completa (basada en Retornos Diarios)")
            
            num_tickers = len(corr_matrix.columns)
            show_annot = num_tickers <= 20
            fig_size_val = max(6, min(14, num_tickers * 0.4))
            
            fig, ax = plt.subplots(figsize=(fig_size_val, fig_size_val * 0.75))
            sns.heatmap(
                corr_matrix, 
                annot=show_annot, 
                fmt=".2f", 
                cmap="coolwarm", 
                vmin=-1, vmax=1, 
                linewidths=0.5, 
                annot_kws={"size": max(6, 10 - num_tickers // 5)},
                ax=ax
            )
            ax.set_title("Matriz de Correlación de Retornos Diarios", fontsize=11, pad=10)
            ax.tick_params(labelsize=max(6, 10 - num_tickers // 5))
            
            col_m1, col_m2 = st.columns([3, 2])
            with col_m1:
                st.pyplot(fig)
                plt.close(fig)
            with col_m2:
                st.write("##### 📋 Información de Empresas y Sectores")
                df_info_all = get_tickers_info(tuple(corr_matrix.columns))
                render_interactive_info_table(df_info_all)

    # ----------------- 3. Explorador por Ramas / Clusters -----------------
    elif option == "🌳 Explorador por Ramas / Clusters":
        st.subheader("🌳 Exploración Detallada por Ramas / Clusters Jerárquicos")
        st.caption("Aísla subgrupos de activos correlacionados según sus retornos diarios y consulta sus sectores.")

        clean_corr = corr_matrix.copy().dropna(how="all", axis=0).dropna(how="all", axis=1).fillna(0)
        num_assets = clean_corr.shape[0]

        if num_assets >= 3:
            dist_matrix = np.clip(1 - clean_corr.values, 0, 2)
            dist_matrix = (dist_matrix + dist_matrix.T) / 2
            condensed_dist = squareform(dist_matrix, checks=False)
            linkage_matrix = sch.linkage(condensed_dist, method='ward')

            col_control1, col_control2 = st.columns(2)
            with col_control1:
                n_clusters = st.slider(
                    "Número de Ramas / Grupos a dividir:", 
                    min_value=2, 
                    max_value=min(15, num_assets - 1), 
                    value=min(4, num_assets - 1)
                )

            cluster_labels = sch.fcluster(linkage_matrix, t=n_clusters, criterion='maxclust')
            cluster_df = pd.DataFrame({"Ticker": clean_corr.columns, "Cluster": cluster_labels})

            with col_control2:
                selected_cluster = st.selectbox(
                    "Selecciona la Rama / Cluster a visualizar:", 
                    options=[f"Rama {i} ({sum(cluster_labels == i)} tickers)" for i in range(1, n_clusters + 1)]
                )

            cluster_idx = int(selected_cluster.split()[1])
            tickers_in_cluster = cluster_df[cluster_df["Cluster"] == cluster_idx]["Ticker"].tolist()

            if len(tickers_in_cluster) >= 2:
                sub_corr = clean_corr.loc[tickers_in_cluster, tickers_in_cluster]

                col_sub1, col_sub2 = st.columns([3, 2])
                
                with col_sub1:
                    fig_sub, ax_sub = plt.subplots(figsize=(6, 4.5))
                    sns.heatmap(
                        sub_corr, 
                        annot=True, 
                        fmt=".2f", 
                        cmap="coolwarm", 
                        vmin=-1, vmax=1, 
                        linewidths=0.8, 
                        annot_kws={"size": 9},
                        ax=ax_sub
                    )
                    ax_sub.set_title(f"Matriz de Correlación de Retornos - Rama {cluster_idx}", fontsize=11, pad=10)
                    ax_sub.tick_params(labelsize=9)
                    st.pyplot(fig_sub)
                    plt.close(fig_sub)
                
                with col_sub2:
                    st.write(f"##### 📋 Tickers y Sectores de la **Rama {cluster_idx}**")
                    df_sector_cluster = get_tickers_info(tuple(tickers_in_cluster))
                    render_interactive_info_table(df_sector_cluster)

            else:
                st.warning("Esta rama contiene solo 1 ticker. Selecciona una rama con 2 o más activos para ver la matriz de correlación.")

            st.divider()
            st.write("#### 🌲 Árbol Jerárquico Completo (Dendrograma de Retornos)")
            fig_dend, ax_dend = plt.subplots(figsize=(10, 4))
            sch.dendrogram(
                linkage_matrix, 
                labels=clean_corr.columns.tolist(), 
                ax=ax_dend, 
                leaf_rotation=90, 
                leaf_font_size=8
            )
            ax_dend.set_title("Dendrograma de Clustering del Portafolio", fontsize=11)
            ax_dend.set_ylabel("Distancia de Disimilitud")
            st.pyplot(fig_dend)
            plt.close(fig_dend)

        else:
            st.info("Necesitas seleccionar al menos 3 tickers activos para realizar el agrupamiento por ramas.")

    # ----------------- 4. Descarga de Archivos -----------------
    elif option == "Descarga de Archivos":
        st.subheader("💾 Descargar Resultados en CSV")
        
        col1, col2, col3 = st.columns(3)

        with col1:
            csv_data = data.to_csv().encode('utf-8')
            st.download_button(
                label="Descargar Precios Históricos",
                data=csv_data,
                file_name="precios_historicos_yahoo.csv",
                mime="text/csv",
            )

        with col2:
            csv_returns = returns.to_csv().encode('utf-8')
            st.download_button(
                label="Descargar Retornos Diarios",
                data=csv_returns,
                file_name="retornos_diarios_yahoo.csv",
                mime="text/csv",
            )

        with col3:
            csv_corr = corr_matrix.to_csv().encode('utf-8')
            st.download_button(
                label="Descargar Matriz Correlación",
                data=csv_corr,
                file_name="matriz_correlacion.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    if data is not None and not data.empty:
        main()
    else:
        st.info("👈 Por favor, sube un archivo Excel en la barra lateral para comenzar el análisis.")