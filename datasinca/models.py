import pandas as pd
import re
from .inputs import input_est, input_param, input_fecha
import warnings

class DataSinca:
    def __init__(self, data, validacion, metadata):
        self.data = data # dataframe con datos de la serie, indexado por datetime
        self.validacion = validacion # dataframe con el estado de validación de cada dato, indexado por datetime
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
        return self.conteo_validacion_por_serie().sum().to_frame(name="conteo")

    def conteo_validacion_por_serie(self):
        series_sin_validacion = self.validacion.isna().all()
        if series_sin_validacion.all():
            raise ValueError("Este DataSinca no contiene variables con validación")
        elif series_sin_validacion.any():
             warnings.warn("El conteo de validación solo se aplica a los datos con información de validación."
                           " Actualmente, los parámetros meteorológicos del SINCA no presentan estados de validación.",
                           UserWarning, stacklevel=2)
             
        conteo = self.validacion.apply(lambda x: x.value_counts()).astype('Int64').T
        conteo.loc[series_sin_validacion, :] = pd.NA
        return conteo

    def resumen(self):
        """
        Metodo de inspección rápida. Muestra número de estaciones, parámetros, periodo cubierto, y conteo de datos por nivel de validación.
        """
        num_estaciones = self.data.columns.get_level_values('estacion').nunique()
        num_parametros = self.data.columns.get_level_values('parametro').nunique()
        periodo = (self.data.index.min(), self.data.index.max())
        conteo_validacion = self.conteo_validacion()
        print()
        print(f"Numero de estaciones: {num_estaciones}")
        print(f"Numero de parámetros: {num_parametros}")
        print(f"Periodo: {periodo[0].date()} a {periodo[1].date()}")
        print("Conteo por estado de validación:")
        for index, row in conteo_validacion.iterrows():
            print(f'\t{str(index).ljust(13)}: {row["conteo"]}')

    def contaminantes(self):
        mask = self._metadata.parametros['tipo_param'] == 'cal'
        alias_cal = self._metadata.parametros.loc[mask, 'alias_param'].tolist()
        conts = [param for param in self.parametros() if param in alias_cal]
        return self.sel(parametro=conts)
    
    def meteorologicos(self):
        mask = self._metadata.parametros['tipo_param'] == 'met'
        alias_meteo = self._metadata.parametros.loc[mask, 'alias_param'].tolist()
        meteo = [param for param in self.parametros() if param in alias_meteo]
        return self.sel(parametro=meteo)
    
    def sep_contam_meteo(self):
        alias_cal = self._metadata.parametros.loc[self._metadata.parametros['tipo_param'] == 'cal', 'alias_param'].tolist()
        conts = [param for param in self.parametros() if param in alias_cal]
        meteo = [param for param in self.parametros() if param not in alias_cal]
        return self.sel(parametro=conts), self.sel(parametro=meteo)
    
    def filtrar_validacion(self, nivel, fill_value=None): #'validado', 'preliminar', 'novalidado'
        if not self.validacion.notna().any().any():
            raise ValueError("Este DataSinca no contiene variables con validación")
        elif self.validacion.isna().all().any():
             warnings.warn("Solo se filtrarán los datos con información de validación."
                           "Actualmente, los parámetros meteorológicos del SINCA no presentan estados de validación.")

        if isinstance(nivel, str):
            nivel = [nivel]
        mask = self.validacion.isin(nivel)
        return DataSinca(self.data.where(mask, other=fill_value),
                         self.validacion.where(mask, other=fill_value),
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
        return DataSinca(self.data.loc[:, idx[comuna, estacion, parametro, unidad, altura]],
                         self.validacion.loc[:, idx[comuna, estacion, parametro, unidad, altura]],
                         self._metadata)

    def buscar_estacion(self, selector):
        cols = self.data.columns

        if isinstance(selector, list):
            pattern = "|".join(map(re.escape, selector))
        else:
            pattern = re.escape(selector)

        mask = cols.get_level_values('estacion').str.contains(pattern, case=False, na=False, regex=True)

        return DataSinca(self.data.loc[:, mask],
                        self.validacion.loc[:, mask],
                        self._metadata)

    def swap_levels(self, nivel1, nivel2):
        return DataSinca(self.data.swaplevel(nivel1, nivel2, axis=1).sort_index(axis=1),
                         self.validacion.swaplevel(nivel1, nivel2, axis=1).sort_index(axis=1),
                         self._metadata)

    def drop_empty_columns(self):
        data = self.data.dropna(axis=1, how='all').copy()
        estado = self.validacion.loc[:, data.columns].copy()
        return DataSinca(data,
                         estado,
                         self._metadata)

    def flatten_levels(self, keep='all', sep='|'):
        cols = self.data.columns
        if keep == 'all':
            keep = list(cols.names)
        elif isinstance(keep, str):
            keep = [keep]
        else:
            keep = list(keep)

        missing = set(keep) - set(cols.names)
        if missing:
            raise ValueError(f"Niveles no válidos: {missing}. Disponibles: {cols.names}")
        drop = [l for l in cols.names if l not in keep]
        new_cols = cols.droplevel(drop) if drop else cols

        if isinstance(new_cols, pd.MultiIndex):
            flat = new_cols.map(lambda x: sep.join(map(str, x)))
        else:
            flat = new_cols.astype(str)

        df = self.data.copy()
        df.columns = flat

        dfv = self.validacion.copy()
        dfv.columns = flat
        return DataSinca(df, dfv, self._metadata)

    def flatten_nonconstant_levels(self, sep='|'):
        columns = self.data.columns
        keep = [name for i, name in enumerate(columns.names)
                if columns.get_level_values(i).nunique() > 1]
        return self.flatten_levels(keep=keep, sep=sep)

    def entre(self, inicio=None, fin=None):
        inicio = input_fecha(inicio, permitir_futuro=True)
        fin = input_fecha(fin, permitir_futuro=True)  
        return DataSinca(self.data.loc[inicio:fin],
                         self.validacion.loc[inicio:fin],
                         self._metadata)
    
    def tipo(self):
        if self.contiene_meteo() and self.contiene_contam():
            return "mixto"
        elif self.contiene_meteo():
            return "meteo"
        elif self.contiene_contam():
            return "contam"
        elif self.data.empty:
            warnings.warn("El DataSinca está vacío. No se puede determinar si contiene datos meteorológicos o contaminantes.", UserWarning)
            return None

    def contiene_meteo(self):
        alias_meteo = self._alias_meteo()
        contiene_meteo = any(param in alias_meteo for param in self.parametros())
        return contiene_meteo
    
    def contiene_contam(self):
        alias_contam = self._alias_contam()
        contiene_contam = any(param in alias_contam for param in self.parametros())
        return contiene_contam

    def _alias_contam(self):
        mask = self._metadata.parametros['tipo_param'] == 'cal'
        alias_cal = self._metadata.parametros.loc[mask, 'alias_param'].tolist()
        return alias_cal

    def _alias_meteo(self):
        mask = self._metadata.parametros['tipo_param'] == 'met'
        alias_meteo = self._metadata.parametros.loc[mask, 'alias_param'].tolist()
        return alias_meteo
    
    def __repr__(self):
        return f"DataSinca(data.shape={self.data.shape})"




def _normalize_altura(altura):
    if altura is None:
        return slice(None)

    if isinstance(altura, list):
        return [_normalize_altura(a) for a in altura]

    if isinstance(altura, (int, float)):
        return f"{int(altura)}m"

    if isinstance(altura, str):
        a = altura.strip().lower()

        if a in ["s/i", "si", "none"]:
            return "S/I"

        if a.endswith("m"):
            num = a.replace("m", "").strip()
            if num.isdigit():
                return f"{int(num)}m"

    return altura