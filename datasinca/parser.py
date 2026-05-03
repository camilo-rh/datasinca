import pandas as pd
import re

def parse_response(req_text):
    reqt = req_text[req_text.find('#DATA') + 6:req_text.find('EOF')].replace(' ','')
    reqsplit = [x.split(',') for x in reqt.split('\n')]
    df = pd.DataFrame(reqsplit)
    index = pd.to_datetime( # índice con columnas 'fecha' y 'hora'
        df.iloc[:,0] + df.iloc[:,1],
        errors='coerce',
        format='%y%m%d%H%M'
    )
    df.set_index(index,inplace=True)
    df.dropna(inplace=True)
    df.drop(df.columns[:2],axis=1,inplace=True)
    return df

def get_plot_vars(text):
    match = re.search(r'Plot var\.\s*:\s*(.*?)#IGNORE', text, re.IGNORECASE | re.DOTALL)
    bloque = match.group(1)
    return re.findall(r'#\s*\d+\.\s*(.*)', bloque)

def remcol(df,columname, plot_vars):
    df_ = df.replace('', pd.NA)
    # Caso de contaminantes (tres columnas: validado, preliminar, novalidado)
    if len(plot_vars)==3:
        df_ = df_.rename(columns={2:'validado',3:'preliminar',4:'novalidado'})
        df_ = pd.melt(df_, value_vars=['validado','preliminar','novalidado'], value_name="Valname", ignore_index=False)
        mask = df_.index.duplicated(keep=False) & df_['Valname'].isna()
        df_ = df_.loc[~mask] # borra filas con (indices duplicados y que 'Valname' es NA)
        dup = df_.index.duplicated(keep=False)
        if dup.any():
            print("Hay múltiples valores por hora. Revisa las filas con índices duplicados.")
        serie_param = (df_['Valname'].str.replace(',', '.', regex=False)
                    .pipe(pd.to_numeric, errors='coerce').rename(columname))
        estado_validacion = df_['variable'].rename(columname)
        estado_validacion[serie_param.isna()] = pd.NA
        
    # Caso meteorológico (una sola columna)
    elif len(plot_vars)==1:
        serie_param = (df_[2].astype(str).str.replace(',', '.', regex=False)
                    .pipe(pd.to_numeric, errors='coerce').rename(columname))
        estado_validacion = pd.Series(pd.NA, index=serie_param.index, name=columname)
    else:
        raise ValueError("Número inesperado de variables en el header. Se esperaban 1 o 3.")
    
    dtype_validacion = pd.CategoricalDtype(
        categories=['validado', 'preliminar', 'novalidado'],
        ordered=True
        )
    estado_validacion = estado_validacion.astype(dtype_validacion)
    return serie_param, estado_validacion


def procesar_request(req_text):
    # validación de contenido
    if req_text.startswith("psgraph: Could not load macro: Can't open macro file"):
        return None, None, None
    df_raw = parse_response(req_text)
    plot_vars = get_plot_vars(req_text) # buscar descripción de columnas originales en metadata del encabezado
    match = re.search(r'\([^)]*', plot_vars[0]) # extraer unidad (ej: "ug/m3")
    unidad = match[0][1:] if match else None
    return df_raw, plot_vars, unidad