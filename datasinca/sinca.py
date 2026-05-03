"""
Cliente de datasinca.

Maneja la descarga y procesamiento de datos desde SINCA.
"""

import requests
import pandas as pd
import logging
import shutil
from .metadata import load_metadata
from .inputs import input_param, input_fecha, input_region, input_est, input_altura, input_muestreo, input_agregacion
from .validators import _xval_estacion, _xval_parametro, _xval_altura
from .downloader import Transport, descargar_serie, URL_ESTACION, descargar_mensaje_estacion
from .parser import procesar_request, remcol
from .models import DataSINCA

class Sinca:
    def __init__(self, inicio=None, fin=None, region=None, estacion=None, parametro=None, altura=None,
                 muestreo='horario', agregacion=None, transport=None, data_path=None, log=False):
        
        self.logger = logging.getLogger("datasinca")
        self._configure_logging(log)

        self._metadata = load_metadata(data_path)

        self._set_variables(None, None, None, None, self._metadata.series.copy())
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
        lista_series_datos = []
        lista_series_validacion = []

        estaciones_impresas = set()

        for id_reg, series_reg in series_sel.groupby('id_reg', sort=True):
            nombre_region = self._metadata.regiones.loc[id_reg, 'nombre_region']
            width = shutil.get_terminal_size().columns
            print()
            print(f" Region {nombre_region} ({id_reg}) ".center(width, '-'))
            for (id_est, cod_param), row_serie in series_reg.sort_index().iterrows():
                row_est = self._metadata.estaciones.loc[id_est]
                row_param = self._metadata.parametros.loc[cod_param]
                nombre_est = row_est['nombre_est']
                cod_est = row_est['cod_est']
                nombre_comuna = row_est['comuna']
                id_reg = row_est['id_reg']
                cod_reg = self._metadata.regiones.loc[id_reg,'cod_reg']

                nombre_param = row_param['nombre_param']
                alias_param = row_param['alias_param']
                tipo_param = row_param['tipo_param']
                altura_actual = row_serie['altura']
                altura_str = f"{altura_actual}m" if isinstance(altura_actual, int) else altura_actual

                if id_est not in estaciones_impresas:
                    print(f"\n{nombre_est} ({id_est}) - URL: {URL_ESTACION}{id_est}")
                    estaciones_impresas.add(id_est)
                    mensaje = descargar_mensaje_estacion(self.transport, id_est, include_tablas=True)
                    if mensaje:
                        self._mensajes_cache[id_est] = mensaje
                        print(end='\t', flush=True)
                        self.logger.warning(f"{nombre_est} ({id_est}): {mensaje}"); print()

                print(f"\t{alias_param} - altura: {altura_str}",end=' - ', flush=True)

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
                        tipo_param=tipo_param,
                        transport=transport
                    )
                except requests.exceptions.ConnectionError:
                    self.logger.error(f"Error conexión SINCA: {alias_param} en {nombre_est} ({id_est})")
                    continue
                print('Descargado. ... ', end='', flush=True)
                df_raw, plot_vars, unidad = procesar_request(req.text)
                
                if df_raw is None:
                    print(end='\n\t')
                    self.logger.warning(f"Sin datos: {alias_param} en {nombre_est} ({id_est})")
                    continue

                columna = (nombre_comuna, nombre_est, alias_param, unidad, altura_str) # clave de la serie (MultiIndex)
                serie_datos, serie_validacion = remcol(df_raw, columna, plot_vars) # colapsar columnas a (serie de datos + serie de validacion)
                print('Procesado')
                lista_series_datos.append(serie_datos) # acumular series
                lista_series_validacion.append(serie_validacion)

        # concatenar series datos y validacion en dataframes
        if lista_series_datos:
            df_datos = pd.concat(lista_series_datos, axis=1)
            df_validacion = pd.concat(lista_series_validacion, axis=1)
            # nombres de niveles de columnas (MultiIndex)
            df_datos.columns.names = column_names
            df_validacion.columns.names = column_names
        else:
            df_datos = pd.DataFrame()
            df_validacion = pd.DataFrame()

        return DataSINCA(df_datos, df_validacion, self._metadata)
    
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

        _, _, _, _, series_sel = self._resolve_series(region, estacion, parametro, altura)
        norm['series_sel'] = series_sel
        del norm['region'], norm['estacion'], norm['parametro'], norm['altura']

        for key, value in norm.items():
            if key in ['inicio', 'fin']:
                norm[key] = input_fecha(value)
            elif key == 'muestreo':
                norm['muestreo'] = input_muestreo(value)
            elif key == 'agregacion':
                norm['agregacion'] = input_agregacion(value)
            elif key == 'transport':
                pass
            elif key in ['id_regiones', 'id_estaciones', 'cod_params', 'altura', 'series_sel']:
                pass
            else:
                raise ValueError(f"Variable de entrada desconocida: {key}")
            
            if norm[key] is None: # estos se reemplazarán por defaults en el constructor, no deben quedar como None
                del norm[key]
        return norm
    
    def _parse_inputs(self, inputs):
        inicio = inputs['inicio']
        fin = inputs['fin']
        series_sel = inputs['series_sel']
        muestreo = inputs['muestreo']
        agregacion = inputs['agregacion']
        transport = inputs['transport']
        return inicio, fin, series_sel, muestreo, agregacion, transport
    


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
        return self._estaciones_ux

    @estacion.setter
    def estacion(self, value):
        id_regiones, id_estaciones, cod_params, alturas, series_sel = self._resolve_series(estacion=value)
        self._set_variables(id_regiones, id_estaciones, cod_params, alturas, series_sel)

    @property
    def parametro(self):
        return self._alias_params

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
        
        series_sel = self._metadata.series.copy()
        nivel = [] # por jerarquía de inputs: region > estacion > parametro > altura

        nivel.append(region)
        if all(v is None for v in nivel):
            id_regiones = getattr(self, '_id_regiones', None)
            if id_regiones is not None:
                mask = series_sel['id_reg'].isin(id_regiones)
                series_sel = series_sel.loc[mask, :]
        elif region is not None:
            id_regiones = input_region(region, self._metadata.regiones)
            mask = series_sel['id_reg'].isin(id_regiones)
            series_sel = series_sel.loc[mask, :]

        nivel.append(estacion)
        if all(v is None for v in nivel):
            id_estaciones = getattr(self, '_id_estaciones', None)
            if id_estaciones is not None:
                series_sel = series_sel.loc[(id_estaciones, slice(None)), :]
        elif estacion is not None:
            id_estaciones, id_regiones = input_est(estacion, self._metadata.estaciones)
            _xval_estacion(id_estaciones, series_sel, self._metadata.estaciones)
            series_sel = series_sel.loc[(id_estaciones, slice(None)), :]

        nivel.append(parametro)
        if all(v is None for v in nivel):
            cod_params = getattr(self, '_cod_params', None)
            if cod_params is not None:
                series_sel = series_sel.loc[(slice(None), cod_params), :]
        elif parametro is not None:
            cod_params = input_param(parametro, self._metadata.parametros)
            _xval_parametro(cod_params, series_sel, self._metadata.estaciones, self._metadata.parametros)
            series_sel = series_sel.loc[(slice(None), cod_params), :]

        nivel.append(altura)
        if all(v is None for v in nivel):
            alturas = getattr(self, '_altura', None)
            if alturas is not None:
                mask = series_sel['altura'].isin(alturas)
                series_sel = series_sel.loc[mask, :]
        elif altura is not None:
            alturas = input_altura(altura)
            _xval_altura(alturas, series_sel, self._metadata.estaciones, self._metadata.parametros)
            mask = series_sel['altura'].isin(alturas)
            series_sel = series_sel.loc[mask, :]


        id_estaciones = series_sel.index.get_level_values(0).unique().tolist()
        cod_params = series_sel.index.get_level_values(1).unique().tolist()
        alturas = series_sel['altura'].unique().tolist()

        id_regiones = self._metadata.estaciones.loc[id_estaciones, 'id_reg'].unique().tolist()
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
            self._regiones_sel = self._metadata.regiones.loc[id_regiones]
            self._id_regiones = self._regiones_sel.index.tolist()
            self._nombre_regiones = self._regiones_sel['nombre_region'].tolist()

        if id_estaciones is None:
            self._estaciones_sel = None
            self._id_estaciones = None
            self._nombre_estaciones = None
            self._estaciones_ux = None
        else:
            self._estaciones_sel = self._metadata.estaciones.loc[id_estaciones]
            self._id_estaciones = self._estaciones_sel.index.tolist()
            self._nombre_estaciones = self._estaciones_sel['nombre_est'].tolist()
            self._estaciones_ux = self._metadata.estaciones.loc[self._id_estaciones]['nombre_est'].to_frame()

        if cod_params is None:
            self._parametros_sel = None
            self._cod_params = None
            self._alias_params = None
        else:
            self._parametros_sel = self._metadata.parametros.loc[cod_params]
            self._cod_params = self._parametros_sel.index.tolist()
            self._alias_params = self._parametros_sel['alias_param'].tolist()

        if alturas is None:
            self._altura = None
        else:
            self._altura = alturas

    def _configure_logging(self, log):
        if log:
            from .log_config import setup_logging
            setup_logging()
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)

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
            f"  parametro={self._alias_params},\n"
            f"  altura={self._altura},\n"
            f"  muestreo={self._muestreo},\n"
            f"  agregacion={self._agregacion},\n"
            f"  inicio={self.inicio}, fin={self.fin}"
            ")"
        )