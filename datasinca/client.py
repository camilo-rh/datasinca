#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 00:25:28 2020

@author: Camilo Ramírez Herrera
"""


import requests
import pandas as pd
from termcolor import cprint
import datetime
import re
from .downloader import Transport, descargar_serie, URL_ESTACION
from .parser import procesar_request, get_plot_vars, remcol
from .models import DataSINCA
from .inputs import input_param, input_fecha, input_region, input_est
from .metadata import load_metadata

class Sinca:
    def __init__(self, region=None, estacion=None, parametro=None, inicio=None,
                 fin=None, altura=0, transport=None, data_path=None, force=False):

        regiones, estaciones, parametros, series = load_metadata(data_path)

        self._regiones = regiones
        self._estaciones = estaciones
        self._parametros = parametros
        self._series = series
        
        self._set_reg_est_par(None, None, None)
        if region is not None or estacion is not None or parametro is not None:
            id_regiones, id_estaciones, cod_params = self._resolve_reg_est_param(region, estacion, parametro)
            self._set_reg_est_par(id_regiones, id_estaciones, cod_params)

        self.inicio = inicio
        self.fin = fin
        self.altura = altura
        self._external_transport = transport is not None
        self.transport = transport or Transport()
        self.force = force

        self._mensajes_cache = {}

    def descarga(self, **kwargs):
        kwargs = self._normalizar_inputs(kwargs)
        inputs = {**self._build_params(), **kwargs}

        inicio, fin, id_regiones, id_estaciones, cod_params, altura, transport, force = self._parse_inputs(inputs)
        n_est = len(id_estaciones)
        n_param = len(cod_params)
        if n_est * n_param > 50 and not force:
            raise ValueError(
                f"Descarga grande: {n_est} estaciones x {n_param} parámetros.\n"
                "\tUsa descarga(force=True) para esta llamada\n"
                "\to inicializa Sinca(force=True) para permitirlo siempre"
            )

        cprint(f'Descarga de datos SINCA desde {inicio.strftime('%d/%m/%Y')} hasta {fin.strftime('%d/%m/%Y')}', attrs=['bold'])
        inicio = inicio.strftime('%y%m%d')
        fin = fin.strftime('%y%m%d')

        column_names = ['comuna','estacion','parametro']
        df_datos = []
        df_validez = []
        unidades = {}
        for id_est in id_estaciones:
            row = self._estaciones.loc[id_est]
            nombre_est = row['nombre_est']
            cod_est = row['cod_est']
            nombre_comuna = row['comuna']
            id_reg = row['id_reg']
            cod_reg = self._regiones.loc[id_reg,'cod_reg']

            print(f'{nombre_est} - {nombre_comuna} - ', end='')
            print(f'URL: {URL_ESTACION}{id_est}')
            mensaje = self._get_mensaje_estacion(id_est)
            if mensaje:
                cprint('Mensaje de la estación ' + nombre_est, 'red', attrs=['bold'])
                cprint(mensaje,'red',attrs=['bold'])

            for cod_param in cod_params:
                nombre_param = self._parametros.loc[cod_param,'nombre_param']
                try:
                    print(f'\t{nombre_param}', end=' ... ', flush=True)
                    req = descargar_serie(
                        inicio=inicio,
                        fin=fin,
                        cod_reg=cod_reg,
                        cod_param=cod_param,
                        cod_est=cod_est,
                        altura=altura,
                        transport=transport
                    )
                except requests.exceptions.ConnectionError:
                    cprint(f'No se pudo conectar a SINCA para {nombre_param} en {nombre_est}', 'white', 'on_blue')
                    continue
                # validación de contenido
                if req.text.startswith("psgraph: Could not load macro: Can't open macro file"):
                    cprint(f'DATOS CAÍDOS O NO HAY DATOS DE {nombre_param} en {nombre_est}', 'red', attrs=['bold'])
                    continue
                print('descarga lista')
                df_raw = procesar_request(req)
                plot_vars = get_plot_vars(req.text) # buscar descripción de columnas originales en metadata del encabezado
                match = re.search(r'\([^)]*', plot_vars[0]) # extraer unidad (ej: "ug/m3")
                unidad = match[0][1:] if match else None
                columna = (nombre_comuna, nombre_est, nombre_param) # clave de la serie (MultiIndex)
                unidades[columna] = unidad

                serie_datos, serie_validez = remcol(df_raw, columna, plot_vars) # colapsar columnas a (serie de datos + serie de validez)

                df_datos.append(serie_datos) # acumular series
                df_validez.append(serie_validez)

        # concatenar series datos y validez en dataframes
        if df_datos:
            df_datos = pd.concat(df_datos, axis=1)
            df_validez = pd.concat(df_validez, axis=1)
        else:
            df_datos = pd.DataFrame()
            df_validez = pd.DataFrame()

        # nombres de niveles de columnas (MultiIndex)
        df_datos.columns.names = column_names
        df_validez.columns.names = column_names

        return DataSINCA(df_datos, df_validez, unidades)
    
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
            'transport': self.transport,
            'force': self.force
            }
    
    def _normalizar_inputs(self, kwargs):
        inputs = kwargs.copy()
        for key in ['region', 'estacion', 'parametro']:
            if key not in inputs:
                inputs[key] = None

        region, estacion, parametro = inputs['region'], inputs['estacion'], inputs['parametro']
        id_regiones, id_estaciones, cod_params = self._resolve_reg_est_param(region, estacion, parametro)
        inputs['id_regiones'] = id_regiones
        inputs['id_estaciones'] = id_estaciones
        inputs['cod_params'] = cod_params
        del inputs['region'], inputs['estacion'], inputs['parametro']

        for key, value in inputs.items():
            if key in ['inicio', 'fin']:
                inputs[key] = input_fecha(value)
            elif key == 'altura':
                inputs['altura'] = value
            elif key == 'transport':
                inputs['transport'] = value
            elif key == 'force':
                inputs['force'] = value
            elif key in ['id_regiones', 'id_estaciones', 'cod_params']:
                pass
            else:
                raise ValueError(f"Variable de entrada desconocida: {key}")                
        return inputs
    
    def _parse_inputs(self, inputs):
        inicio = inputs['inicio']
        fin = inputs['fin']
        id_regiones = inputs['id_regiones']
        id_estaciones = inputs['id_estaciones']
        cod_params = inputs['cod_params']
        altura = inputs['altura']
        transport = inputs['transport']
        force = inputs['force']
        return inicio, fin, id_regiones, id_estaciones, cod_params, altura, transport, force
    
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
        if value is None:
            value = datetime.date.today()
        self._inicio = input_fecha(value)

    @property
    def fin(self):
        return self._fin.strftime('%d/%m/%Y')

    @fin.setter
    def fin(self, value):
        if value is None:
            value = datetime.date.today()
        self._fin = input_fecha(value)

    @property
    def region(self):
        return self._nombre_regiones

    @region.setter
    def region(self, value):
        id_regiones, id_estaciones, cod_params = self._resolve_reg_est_param(region=value)
        self._set_reg_est_par(id_regiones, id_estaciones, cod_params)

    @property
    def estacion(self):
        return self._nombre_estaciones

    @estacion.setter
    def estacion(self, value):
        id_regiones, id_estaciones, cod_params = self._resolve_reg_est_param(estacion=value)
        self._set_reg_est_par(id_regiones, id_estaciones, cod_params)
    
    @property
    def parametro(self):
        return self._nombre_params

    @parametro.setter
    def parametro(self, value):
        id_regiones, id_estaciones, cod_params = self._resolve_reg_est_param(parametro=value)
        self._set_reg_est_par(id_regiones, id_estaciones, cod_params)

    def __setattr__(self, name, value):
        cls = type(self)
        if hasattr(cls, name) and name not in self.__dict__:
            attr = getattr(cls, name)

            if isinstance(attr, property) and attr.fset is not None:
                attr.fset(self, value)
                return
            raise AttributeError(f"No puedes sobrescribir '{name}'")
        super().__setattr__(name, value)

    def _resolve_reg_est_param(self, region=None, estacion=None, parametro=None):
        if region is not None:
            id_regiones = input_region(region, self._regiones)
            mask = self._estaciones['id_reg'].isin(id_regiones)
            id_estaciones = self._estaciones[mask].index.tolist()

        if estacion is not None:
            id_estaciones, id_reg_est = input_est(estacion, self._estaciones)

            # en cualquier caso, tomar solo las regiones de las estaciones configuradas
            id_regiones = id_reg_est
        
        if parametro:
            cod_params = input_param(parametro, self._parametros)
        # si se está configurando region o estacion, y no parametro, entonces
        # tomar todos los de las estaciones configuradas
        elif (region or estacion) and parametro is None:
                cod_params = self._series.loc[(id_estaciones, slice(None)), :].index.get_level_values(1).tolist()
                cod_params = list(set(cod_params))
        else:
            cod_params = getattr(self, "_cod_params", None)

        if estacion is None and region is None:
            id_estaciones = getattr(self, "_id_estaciones", None)
            id_regiones = getattr(self, "_id_regiones", None)

        return id_regiones, id_estaciones, cod_params
    
    def _set_reg_est_par(self, id_regiones, id_estaciones, cod_params):
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

    def __repr__(self):
        return (
            "Sinca(\n"
            f"  region={self._id_regiones},\n"
            f"  estacion={self._id_estaciones},\n"
            f"  parametro={self._cod_params},\n"
            f"  inicio={self._inicio}, fin={self._fin}\n"
            ")"
        )

    def __str__(self):
        return (
            "Sinca(\n"
            f"  region={self._nombre_regiones},\n"
            f"  estacion={self._nombre_estaciones},\n"
            f"  parametro={self._nombre_params},\n"
            f"  inicio={self.inicio}, fin={self.fin}\n"
            ")"
        )