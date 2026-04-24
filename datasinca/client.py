"""
Cliente de datasinca.

Maneja la descarga y procesamiento de datos desde SINCA.
"""

import requests
import pandas as pd
import re
import logging
from .metadata import load_metadata
from .inputs import input_param, input_fecha, input_region, input_est, input_altura, input_muestreo, input_agregacion
from .data.validators import _xval_estacion, _xval_parametro, _xval_altura
from .downloader import Transport, descargar_serie, URL_ESTACION
from .parser import procesar_request, remcol
from .models import DataSINCA

class Sinca:
    def __init__(self, region=None, estacion=None, parametro=None, inicio=None,
                 fin=None, altura=None, muestreo='horario', agregacion=None, transport=None, data_path=None):
        
        self.logger = logging.getLogger("datasinca")
        regiones, estaciones, parametros, series = load_metadata(data_path)

        self._regiones = regiones
        self._estaciones = estaciones
        self._parametros = parametros
        self._series = (series
                        # .merge(estaciones, on='id_est', how='left')
                        # .merge(parametros, on='cod_param', how='left')
                        )

        self._set_variables(None, None, None, None, series.copy())

        if any([region, estacion, parametro, altura]):
            id_regiones, id_estaciones, cod_params, alturas, series_sel = self._resolve_series(region, estacion, parametro, altura)
            self._set_variables(id_regiones, id_estaciones, cod_params, alturas, series_sel)


        self.inicio = inicio
        self.fin = fin
        self.muestreo = muestreo
        self.agregacion = agregacion
        self._external_transport = transport is not None
        self.transport = transport or Transport()

        self._mensajes_cache = {}

    def descarga(self, **kwargs):
        kwargs = self._normalizar_inputs(kwargs)
        inputs = {**self._build_params(), **kwargs}

        inicio, fin, series_sel, muestreo, agregacion, transport = self._parse_inputs(inputs)
        filtros = {k:v for k,v in inputs.items() if not k in ['series_sel', 'transport']}
        self.logger.info(f"Inicio descarga SINCA | {filtros}")

        inicio = inicio.strftime('%y%m%d')
        fin = fin.strftime('%y%m%d')

        column_names = ['comuna','estacion','parametro', 'unidad', 'altura']
        df_datos = []
        df_validez = []

        estaciones_impresas = set()

        for (id_est, cod_param), row_serie in series_sel.sort_index().iterrows():
            row_est = self._estaciones.loc[id_est]
            nombre_est = row_est['nombre_est']
            cod_est = row_est['cod_est']
            nombre_comuna = row_est['comuna']
            id_reg = row_est['id_reg']
            cod_reg = self._regiones.loc[id_reg,'cod_reg']

            nombre_param = self._parametros.loc[cod_param,'nombre_param']
            alias_param = self._parametros.loc[cod_param,'alias_param']
            altura_actual = row_serie['altura']
            altura_str = f"{altura_actual} m" if isinstance(altura_actual, int) else altura_actual

            if id_est not in estaciones_impresas:
                print(f"\n{row_est['nombre_est']} - {row_est['comuna']} - URL: {URL_ESTACION}{id_est}")
                estaciones_impresas.add(id_est)
                mensaje = self._get_mensaje_estacion(id_est)
                if mensaje:
                    print(end='\t', flush=True)
                    self.logger.warning(f"{nombre_est} ({id_est}): {mensaje}")

            print(f"\t{nombre_param} (altura: {altura_str})",end=' - ', flush=True)

            try:
                req = descargar_serie(
                    inicio=inicio,
                    fin=fin,
                    cod_reg=cod_reg,
                    cod_param=cod_param,
                    cod_est=cod_est,
                    altura=altura_actual,
                    muestreo=muestreo,
                    agregacion=agregacion,
                    transport=transport
                )
            except requests.exceptions.ConnectionError:
                self.logger.error(f"Error conexión SINCA: {nombre_param} ({cod_param}) en {nombre_est} ({id_est})")
                continue
            print('Descargado. ... ', end='', flush=True)
            df_raw, plot_vars, unidad = procesar_request(req.text)
            
            if df_raw is None:
                print(end='\n\t')
                self.logger.warning(f"Sin datos: {nombre_param} ({cod_param}) en {nombre_est} ({id_est})")
                continue

            columna = (nombre_comuna, nombre_est, alias_param, unidad, altura_str) # clave de la serie (MultiIndex)
            serie_datos, serie_validez = remcol(df_raw, columna, plot_vars) # colapsar columnas a (serie de datos + serie de validez)
            print('Procesado')
            df_datos.append(serie_datos) # acumular series
            df_validez.append(serie_validez)

        # concatenar series datos y validez en dataframes
        if df_datos:
            df_datos = pd.concat(df_datos, axis=1)
            df_validez = pd.concat(df_validez, axis=1)
            # nombres de niveles de columnas (MultiIndex)
            df_datos.columns.names = column_names
            df_validez.columns.names = column_names
        else:
            df_datos = pd.DataFrame()
            df_validez = pd.DataFrame()

        return DataSINCA(df_datos, df_validez)
    
    def set(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def close(self):
        if not self._external_transport and self.transport:
            self.transport.close()

    def _build_params(self):
        return {
            'inicio': self._inicio,
            'fin': self._fin,
            'id_regiones': self._id_regiones,
            'id_estaciones': self._id_estaciones,
            'cod_params': self._cod_params,
            'altura': self.altura,
            'series_sel': self._series_sel,
            'muestreo': self.muestreo,
            'agregacion': self.agregacion,
            'transport': self.transport,
            }
    
    def _normalizar_inputs(self, inputs):
        norm = inputs.copy()
        region = norm.setdefault('region')
        estacion = norm.setdefault('estacion')
        parametro = norm.setdefault('parametro')
        altura = norm.setdefault('altura')

        id_regiones, id_estaciones, cod_params, alturas, series_sel = self._resolve_series(region, estacion, parametro, altura)
        norm['id_regiones'] = id_regiones
        norm['id_estaciones'] = id_estaciones
        norm['cod_params'] = cod_params
        norm['altura'] = alturas
        norm['series_sel'] = series_sel
        del norm['region'], norm['estacion'], norm['parametro'], #norm['altura']

        for key, value in norm.items():
            if key in ['inicio', 'fin']:
                norm[key] = input_fecha(value)
            elif key == 'muestreo':
                norm['muestreo'] = input_muestreo(value)
            elif key == 'agregacion':
                norm['agregacion'] = input_agregacion(value)
            elif key == 'transport':
                pass
            elif key in ['id_regiones', 'id_estaciones', 'cod_params', 'alturas', 'series_sel']:
                pass
            else:
                raise ValueError(f"Variable de entrada desconocida: {key}")
            
            if value is None: # estos se reemplazarán por defaults en el constructor, no deben quedar como None
                del norm[key]
        return norm
    
    def _parse_inputs(self, inputs):
        inicio = inputs['inicio']
        fin = inputs['fin']
        # id_regiones = inputs['id_regiones']
        # id_estaciones = inputs['id_estaciones']
        # cod_params = inputs['cod_params']
        # alturas = inputs['alturas']
        series_sel = inputs['series_sel']
        muestreo = inputs['muestreo']
        agregacion = inputs['agregacion']
        transport = inputs['transport']
        return inicio, fin, series_sel, muestreo, agregacion, transport
    
    def _get_mensaje_estacion(self, id_estacion):
        text = self.transport.get(URL_ESTACION + str(id_estacion)).text

        match = re.search(r'"mensajeStn".*</div', text)
        if not match:
            return None
        mensaje = match.group()[13:-5]
        mensaje = re.sub(r'&(?P<vocal>[aeiou])acute;', r'\g<vocal>', mensaje)
        mensaje = re.sub(r'<p>|</p>', '', mensaje)
        self._mensajes_cache[id_estacion] = mensaje
        return mensaje
    
    @property
    def inicio(self):
        return self._inicio.strftime('%d/%m/%Y')

    @inicio.setter
    def inicio(self, value):
        self._inicio = input_fecha(value)

    @property
    def fin(self):
        return self._fin.strftime('%d/%m/%Y')

    @fin.setter
    def fin(self, value):
        self._fin = input_fecha(value)

    @property
    def region(self):
        return self._nombre_regiones

    @region.setter
    def region(self, value):
        id_regiones, id_estaciones, cod_params, alturas, series_sel = self._resolve_series(region=value)
        self._set_variables(id_regiones, id_estaciones, cod_params, alturas, series_sel)

    @property
    def estacion(self):
        return self._nombre_estaciones

    @estacion.setter
    def estacion(self, value):
        id_regiones, id_estaciones, cod_params, alturas, series_sel = self._resolve_series(estacion=value)
        self._set_variables(id_regiones, id_estaciones, cod_params, alturas, series_sel)

    @property
    def parametro(self):
        return self._nombre_params

    @parametro.setter
    def parametro(self, value):
        id_regiones, id_estaciones, cod_params, alturas, series_sel = self._resolve_series(parametro=value)
        self._set_variables(id_regiones, id_estaciones, cod_params, alturas, series_sel)

    @property
    def altura(self):
        return self._altura

    @altura.setter
    def altura(self, value):
        id_regiones, id_estaciones, cod_params, alturas, series_sel = self._resolve_series(altura=value)
        self._set_variables(id_regiones, id_estaciones, cod_params, alturas, series_sel)

    @property
    def muestreo(self):
        return self._muestreo

    @muestreo.setter
    def muestreo(self, value):
        self._muestreo = input_muestreo(value)

    @property
    def agregacion(self):
        return self._agregacion

    @agregacion.setter
    def agregacion(self, value):
        self._agregacion = input_agregacion(value)

    def __setattr__(self, name, value):
        cls = type(self)
        if hasattr(cls, name) and name not in self.__dict__:
            attr = getattr(cls, name)

            if isinstance(attr, property) and attr.fset is not None:
                attr.fset(self, value)
                return
            raise AttributeError(f"No puedes sobrescribir '{name}'")
        super().__setattr__(name, value)

    def _resolve_series(self, region=None, estacion=None, parametro=None, altura=None):
        
        series_sel = self._series.copy()
        nivel = [] # por jerarquía de inputs: region > estacion > parametro > altura

        nivel.append(region)
        if all(v is None for v in nivel):
            id_regiones = getattr(self, '_id_regiones', None)
            if id_regiones is not None:
                mask = series_sel['id_reg'].isin(id_regiones)
                series_sel = series_sel.loc[mask, :]
        elif region is not None:
            id_regiones = input_region(region, self._regiones)
            mask = series_sel['id_reg'].isin(id_regiones)
            series_sel = series_sel.loc[mask, :]

        nivel.append(estacion)
        if all(v is None for v in nivel):
            id_estaciones = getattr(self, '_id_estaciones', None)
            if id_estaciones is not None:
                series_sel = series_sel.loc[(id_estaciones, slice(None)), :]
        elif estacion is not None:
            id_estaciones, id_regiones = input_est(estacion, self._estaciones)
            _xval_estacion(id_estaciones, series_sel, self._estaciones)
            series_sel = series_sel.loc[(id_estaciones, slice(None)), :]

        nivel.append(parametro)
        if all(v is None for v in nivel):
            cod_params = getattr(self, '_cod_params', None)
            if cod_params is not None:
                series_sel = series_sel.loc[(slice(None), cod_params), :]
        elif parametro is not None:
            cod_params = input_param(parametro, self._parametros)
            _xval_parametro(cod_params, series_sel, self._estaciones, self._parametros)
            series_sel = series_sel.loc[(slice(None), cod_params), :]

        nivel.append(altura)
        if all(v is None for v in nivel):
            alturas = getattr(self, '_altura', None)
            if alturas is not None:
                mask = series_sel['altura'].isin(alturas)
                series_sel = series_sel.loc[mask, :]
        elif altura is not None:
            alturas = input_altura(altura)
            _xval_altura(alturas, series_sel, self._estaciones, self._parametros)
            mask = series_sel['altura'].isin(alturas)
            series_sel = series_sel.loc[mask, :]


        id_estaciones = series_sel.index.get_level_values(0).unique().tolist()
        cod_params = series_sel.index.get_level_values(1).unique().tolist()
        alturas = series_sel['altura'].unique().tolist()

        id_regiones = self._estaciones.loc[id_estaciones, 'id_reg'].unique().tolist()
        return id_regiones, id_estaciones, cod_params, alturas, series_sel


    def _set_variables(self, id_regiones, id_estaciones, cod_params, alturas, series_sel):
        if series_sel is None:
            self._series_sel = None
        else:
            self._series_sel = series_sel

        if id_regiones is None:
            self._regiones_sel = None
            self._id_regiones = None
            self._nombre_regiones = None
        else:
            self._regiones_sel = self._regiones.loc[id_regiones]
            self._id_regiones = self._regiones_sel.index.tolist()
            self._nombre_regiones = self._regiones_sel['nombre_region'].tolist()

        if id_estaciones is None:
            self._estaciones_sel = None
            self._id_estaciones = None
            self._nombre_estaciones = None
        else:
            self._estaciones_sel = self._estaciones.loc[id_estaciones]
            self._id_estaciones = self._estaciones_sel.index.tolist()
            self._nombre_estaciones = self._estaciones_sel['nombre_est'].tolist()

        if cod_params is None:
            self._parametros_sel = None
            self._cod_params = None
            self._nombre_params = None
        else:
            self._parametros_sel = self._parametros.loc[cod_params]
            self._cod_params = self._parametros_sel.index.tolist()
            self._nombre_params = self._parametros_sel['nombre_param'].tolist()

        if alturas is None:
            self._altura = None
        else:
            self._altura = alturas


    def __repr__(self):
        return (
            "Sinca(\n"
            f"  region={self._id_regiones},\n"
            f"  estacion={self._id_estaciones},\n"
            f"  parametro={self._cod_params},\n"
            f"  altura={self._altura},\n"
            f"  muestreo={self._muestreo},\n"
            f"  agregacion={self._agregacion},\n"
            f"  inicio={self.inicio}, fin={self.fin}"
            ")"
        )

    def __str__(self):
        return (
            "Sinca(\n"
            f"  region={self._nombre_regiones},\n"
            f"  estacion={self._nombre_estaciones},\n"
            f"  parametro={self._nombre_params},\n"
            f"  altura={self._altura},\n"
            f"  muestreo={self._muestreo},\n"
            f"  agregacion={self._agregacion},\n"
            f"  inicio={self.inicio}, fin={self.fin}"
            ")"
        )