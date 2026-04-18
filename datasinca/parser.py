import pandas as pd
import re

def procesar_request(req):
    reqt = req.text[req.text.find('#DATA') + 6:req.text.find('EOF')].replace(' ','')
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
        serie_validez = df_['variable'].rename(columname)
        return serie_param, serie_validez
        
    # Caso meteorológico (una sola columna)
    elif len(plot_vars)==1:
        serie_param = (df_[2].astype(str).str.replace(',', '.', regex=False)
                    .pipe(pd.to_numeric, errors='coerce').rename(columname))
        serie_validez = pd.Series(data='sin_info', index=serie_param.index, name=columname)
        return serie_param, serie_validez
    else:
        raise ValueError("Número inesperado de variables en el header. Se esperaban 1 o 3.")