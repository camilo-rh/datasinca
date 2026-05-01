import pandas as pd
import re
from .inputs import input_est, input_param, input_fecha

class DataSINCA:
    def __init__(self, data, estado_validacion, metadata):
        self.data = data # dataframe con datos de la serie, indexado por datetime
        self.estado_validacion = estado_validacion # dataframe con el estado de validación de cada dato, indexado por datetime
        self._metadata = metadata
    
    def estaciones(self):
        return self.data.columns.get_level_values('estacion').unique().tolist()
    
    def parametros(self):
        return self.data.columns.get_level_values('parametro').unique().tolist()
    
    def series(self):
        return self.data.columns.to_numpy()
    
    def periodo(self):
        return (self.data.index.min(), self.data.index.max())
    
    def conteo_validacion(self):
        return self.estado_validacion.apply(lambda x: x.value_counts(dropna=False)).sum(axis=1).astype('Int64')

    def conteo_validacion_por_serie(self):
        return self.estado_validacion.apply(lambda x: x.value_counts(dropna=False)).astype('Int64').T

    def resumen(self):
        """
        Metodo de inspección rápida. Muestra número de estaciones, parámetros, periodo cubierto, y conteo de datos por nivel de validación.
        """
        num_estaciones = self.data.columns.get_level_values('estacion').nunique()
        num_parametros = self.data.columns.get_level_values('parametro').nunique()
        periodo = (self.data.index.min(), self.data.index.max())
        conteo_validacion = self.conteo_validacion()
        
        print(f"Numero de estaciones: {num_estaciones}")
        print(f"Numero de parámetros: {num_parametros}")
        print(f"Periodo: {periodo[0].date()} a {periodo[1].date()}")
        print("Conteo por estado de validación:")
        print(conteo_validacion)

    
    def filtrar_validacion(self, nivel, fill_value=None): #'validado', 'preliminar', 'novalidado'
        if isinstance(nivel, str):
            nivel = [nivel]
        mask = self.estado_validacion.isin(nivel)
        return DataSINCA(self.data.where(mask, other=fill_value),
                         self.estado_validacion.where(mask, other=fill_value),
                         self._metadata)

    def sel(self, comuna=None, estacion=None, parametro=None, unidad=None, altura=None):
        idx = pd.IndexSlice
        
        if estacion is not None:
            estacion, _ = input_est(estacion, self._metadata.estaciones, 'nombre_est')
        else:
            estacion = slice(None)
        
        if parametro is not None:
            parametro = input_param(parametro, self._metadata.parametros, 'alias_param')
        else:
            parametro = slice(None)

        altura = _normalize_altura(altura)
        comuna = comuna if comuna is not None else slice(None)
        unidad = unidad if unidad is not None else slice(None)
        return DataSINCA(self.data.loc[:, idx[comuna, estacion, parametro, unidad, altura]],
                         self.estado_validacion.loc[:, idx[comuna, estacion, parametro, unidad, altura]],
                         self._metadata)

    def buscar_estacion(self, selector):
        cols = self.data.columns

        if isinstance(selector, list):
            pattern = "|".join(map(re.escape, selector))
        else:
            pattern = re.escape(selector)

        mask = cols.get_level_values('estacion').str.contains(pattern, case=False, na=False, regex=True)

        return DataSINCA(self.data.loc[:, mask],
                        self.estado_validacion.loc[:, mask],
                        self._metadata)

    def swap_levels(self, nivel1, nivel2):
        return DataSINCA(self.data.swaplevel(nivel1, nivel2, axis=1).sort_index(axis=1),
                         self.estado_validacion.swaplevel(nivel1, nivel2, axis=1).sort_index(axis=1),
                         self._metadata)

    def flatten_columns(self, sep=' | '):
        df = self.data.copy()
        df.columns = [sep.join(map(str, col)) for col in df.columns]
        dfv = self.estado_validacion.copy()
        dfv.columns = df.columns
        return DataSINCA(df, dfv, self._metadata)

    def entre(self, inicio=None, fin=None):
        inicio = input_fecha(inicio, permitir_futuro=True)
        fin = input_fecha(fin, permitir_futuro=True)  
        return DataSINCA(self.data.loc[inicio:fin],
                         self.estado_validacion.loc[inicio:fin],
                         self._metadata)
    
    def __repr__(self):
        return f"DataSINCA(data.shape={self.data.shape})"




def _normalize_altura(altura):
    if altura is None:
        return slice(None)

    if isinstance(altura, list):
        return [_normalize_altura(a) for a in altura]

    if isinstance(altura, (int, float)):
        return f"{int(altura)} m"

    if isinstance(altura, str):
        a = altura.strip().lower()

        if a in ["s/i", "si", "none"]:
            return "S/I"

        if a.endswith("m"):
            num = a.replace("m", "").strip()
            if num.isdigit():
                return f"{int(num)} m"

    return altura