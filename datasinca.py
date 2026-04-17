#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 00:25:28 2020

@author: Camilo Ramírez Herrera
"""


import requests
import pandas
from termcolor import cprint
import datetime
import re
import unicodedata
from datasinca._info import Csust, Nsust, reg, comuna, EstacionN, EstacionC, idest, REGIONES, REGIONES_NOMBRE

def build_url(inicio,fin,codparam,altura,codest,codreg):
        codaltura = str(altura).rjust(3, '0')
        url = 'https://sinca.mma.gob.cl/cgi-bin/APUB-MMA/apub.tsindico2.cgi?outtype=txt&macro=./'
        if codparam in ['PM25' , 'PM10' ,'0003' , '0NOX' , '0001' , '0008' ,'0004','0002']:
            url += codreg +'/'+ codest +'/Cal/'+ codparam +'//'+ codparam +'.horario.horario'
        elif codparam in ['TEMP','WSPD', 'RHUM']:
            url += codreg +'/'+ codest +'/Met/'+ codparam +'//horario_'+codaltura
        elif codparam in ['WDIR']:
            url += codreg +'/'+ codest +'/Met/'+ codparam +'//horario_'+codaltura+'_spec'
        else:
            raise Exception('Parámetro no reconocido')
        url += '.ic&from='+ inicio +'&to='+ fin +'&path=/usr/airviro/data/CONAMA/&lang=esp&rsrc=&macropath='
        return url

class Transport:
    def __init__(self, timeout=10):
        self.timeout = timeout
    def get(self, url):
        try:
            return self._request(url)
        except (requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout):
            # https a http
            if url.startswith("https://"):
                fallback_url = url.replace("https://", "http://", 1)
                return self._request(fallback_url)
            raise
    def _request(self, url):
        r = requests.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r

class DataSINCA:
    def __init__(self, data, validez):
        self.data = data
        self.validez = validez

    def filtrar_validez(self, nivel):
        return self.data[self.validez == nivel]

    def solo_validos(self):
        return self.filtrar_validez('validado')
    
class Sinca:
    def __init__(self, region=None, estacion=None, parametro=None,
                 inicio=None, fin=None, altura=0):
        self._region = None
        self._estaciones = None
        self._parametros_idx = None
        self._parametros_nom = None
        
        self.region = region
        self.estacion = estacion
        self.parametro = parametro
        self.inicio = inicio
        self.fin = fin
        self.altura = altura

    def listar_regiones(self):
        return reg
    
    def listar_estaciones(self, region=None):
        if region is None:
            region = self.region
        if region is None:
            raise ValueError("Debe especificar una región o establecerla al crear el cliente.")
        return EstacionN[reg.index(region)]
    
    def config(self):
        return {
            'inicio': self.inicio,
            'fin': self.fin,
            'parametro': self.parametro,
            'region': self.region,
            'estacion': self.estacion,
            'altura': self.altura,
            }
    def _build_params(self):
        return {
            'inicio': self._inicio,
            'fin': self._fin,
            'parametros': self._parametros_idx,
            'R': self._region,
            'est': self._estaciones,
            'altura': self.altura
            }
    
    def set(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __setattr__(self, name, value):
        cls = type(self)
        if hasattr(cls, name) and name not in self.__dict__:
            attr = getattr(cls, name)

            if isinstance(attr, property) and attr.fset is not None:
                attr.fset(self, value)
                return
            raise AttributeError(f"No puedes sobrescribir '{name}'")
        super().__setattr__(name, value)
    
    def descarga(self, **kwargs):
        inputs = {**self._build_params(), **kwargs}
        print("Descargando datos con configuración:", inputs)
        return datasinca(**inputs)

    def _map_region(self, region):
        if region is None:
            return None
        
        r = region.strip()
        
        if r in REGIONES:
            return REGIONES[r]
        
        if r in REGIONES.values():
            return r
        
        for k, v in REGIONES_NOMBRE.items():
            if r.lower() == k.lower():
                return v
        raise ValueError(f"Región no válida: {region}")
    
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
        return self._region

    @region.setter
    def region(self, value):
        self._region = self._map_region(value)

    @property
    def estacion(self):
        if self._estaciones is None:
            return 'todas'
        return self._estaciones

    @estacion.setter
    def estacion(self, value):
        if value is None or value == -1:
            self._estaciones = None  # significado: "todas"
            return

        if isinstance(value, int):
            self._estaciones = [value]
            return

        if isinstance(value, (list, tuple)):
            self._estaciones = list(value)
            return

        raise ValueError("Formato de estación no válido")
    
    @property
    def parametro(self):
        return self._parametros_nom

    @parametro.setter
    def parametro(self, value):
        idx, nombres = elige_param(value)
        self._parametros_idx = idx
        self._parametros_nom = nombres
        
    def __repr__(self):
        cfg = self.config()
        return (
            "SINCAClient(\n"
            f"  region={cfg['region']},\n"
            f"  estacion={cfg['estacion']},\n"
            f"  parametro={cfg['parametro']},\n"
            f"  inicio={cfg['inicio']}, fin={cfg['fin']}\n"
            ")"
        )

def procesar_req(req):
    reqt = req.text[req.text.find('#DATA') + 6:req.text.find('EOF')].replace(' ','')
    reqsplit = [x.split(',') for x in reqt.split('\n')]
    df = pandas.DataFrame(reqsplit)
    index = pandas.to_datetime(
        df.iloc[:,0] + df.iloc[:,1],
        errors='coerce',
        format='%y%m%d%H%M'
    )
    return df, index

def datasinca(inicio,fin,parametros,R=1,est=-1,altura=0, aviso_codigo=True, aviso_estacion=True, aviso_descarga=True):
    if type(R)==str: R = reg.index(R)
    parametros, paramname = elige_param(parametros)
    column_names = ['comuna','estacion','parametro']

    if aviso_codigo:
        cprint('Ojo, algunas regiones tienen diferente tamaño de las listas:\n     comuna,EstacionC,EstacionN,idest:','white','on_red')
        for i,x in enumerate(comuna):
            print(i, (reg[i]+':').ljust(7,' '),len(comuna[i]),len(EstacionC[i]),len(EstacionN[i]),len(idest[i]))
    
    inicio = input_fecha(inicio)
    fin = input_fecha(fin)
    if aviso_descarga: cprint(f'Descarga de datos SINCA desde {inicio.strftime('%d/%m/%Y')} hasta {fin.strftime('%d/%m/%Y')}', attrs=['bold'])
    inicio = inicio.strftime('%y%m%d')
    fin = fin.strftime('%y%m%d')
    if est==None or est==-1:  est = range(0,len(EstacionN[R]))
    if isinstance(est,int): est=[est]
   
    urlest ='https://sinca.mma.gob.cl/index.php/estacion/index/id/'  # url info de estaciones
    
    df_param = []
    df_validez = []
    unidades = {}
    transport = Transport()
    for i,ind in enumerate(parametros):
        for j in est:
            if aviso_descarga:
                print(f'{paramname[i]} - estación:{EstacionN[R][j]} - comuna:{comuna[R][j]}')
            if parametros.index(ind)==0:
                mensaje= re.search('"mensajeStn".*</div', transport.get(urlest + idest[R][j]).text )
                if mensaje and aviso_estacion:
                    mensaje = re.sub('&(?P<vocal>[aeiou])acute;', r'\g<vocal>', mensaje.group()[13:-5])
                    mensaje = re.sub('<p>|</p>',lambda x: '',mensaje)
                    cprint('Mensaje de la estación ' + EstacionN[R][j], 'red', attrs=['bold'])
                    cprint(mensaje,'red',attrs=['bold'])
            # inicio,fin,c_param,altura,c_est,c_region
            url = build_url(inicio, fin, Csust[ind], altura, EstacionC[R][j], reg[R])
            req = None
            try:
                req = transport.get(url)
                df, index = procesar_req(req)
                if aviso_descarga:
                    print('descarga lista')
            except requests.exceptions.ConnectionError:
                cprint(f'No se pudo conectar a SINCA para {paramname[i]} en {EstacionN[R][j]}','white','on_blue')
            except Exception as ex:
                if req is not None and req.text.startswith(
                    "psgraph: Could not load macro: Can't open macro file"
                ):
                    cprint(f'DATOS CAÍDOS O NO HAY DATOS DE {paramname[i]} en {EstacionN[R][j]}.', 'white', 'on_red', attrs=['bold'], end=' ')
                    print('URL: ' + urlest + idest[R][j])
                    continue
                else:
                    raise
            df.set_index(index,inplace=True)
            df.dropna(inplace=True)
            df.drop(df.columns[:2],axis=1,inplace=True)
            plot_vars = get_plot_vars(req.text)
            unidad = re.search(r'\([^)]*', plot_vars[0])[0][1:]
            columna = (comuna[R][j], EstacionN[R][j], paramname[i])
            unidades[columna] = unidad
            serie_param, serie_validez = remcol(df, columna, plot_vars)
            df_param.append(serie_param)
            df_validez.append(serie_validez)
    
    if df_param:
        df_param = pandas.concat(df_param,axis=1)
        df_param.columns.names = column_names
        df_validez = pandas.concat(df_validez,axis=1)
        df_validez.columns.names = column_names
    else:
        df_param = pandas.DataFrame([],columns=column_names)
        df_validez = pandas.DataFrame([],columns=column_names)
    df_param.attrs['fuente'] = 'SINCA'
    df_param.attrs['unidades'] = unidades
    return DataSINCA(df_param, df_validez)

# def get_n_variables_from_header(text):
#     match = re.search(r'Plot var\.\s*:\s*(.*?)#IGNORE', text, re.IGNORECASE | re.DOTALL)
#     if not match:
#         raise ValueError("No se encontró sección 'Plot var.'")
#     bloque = match.group(1)
#     # contar líneas tipo "# 1.", "# 2.", etc.
#     nvars = len(re.findall(r'#\s*\d+\.', bloque))
#     return nvars

def get_plot_vars(text):
    match = re.search(r'Plot var\.\s*:\s*(.*?)#IGNORE', text, re.IGNORECASE | re.DOTALL)
    bloque = match.group(1)
    return re.findall(r'#\s*\d+\.\s*(.*)', bloque)

def remcol(df,columname, plot_vars):
    df_ = df.replace('', pandas.NA)
    # Caso de contaminantes (tres columnas: validado, preliminar, novalidado)
    if len(plot_vars)==3:
        df_ = df_.rename(columns={2:'validado',3:'preliminar',4:'novalidado'})
        df_ = pandas.melt(df_, value_vars=['validado','preliminar','novalidado'], value_name="Valname", ignore_index=False)
        mask = df_.index.duplicated(keep=False) & df_['Valname'].isna()
        df_ = df_.loc[~mask] # borra filas con (indices duplicados y que 'Valname' es NA)
        dup = df_.index.duplicated(keep=False)
        if dup.any():
            print("Hay múltiples valores por hora. Revisa las filas con índices duplicados.")
        serie_param = (df_['Valname'].str.replace(',', '.', regex=False)
                    .pipe(pandas.to_numeric, errors='coerce').rename(columname))
        serie_validez = df_['variable'].rename(columname)
        return serie_param, serie_validez
        
    # Caso meteorológico (una sola columna)
    elif len(plot_vars)==1:
        serie_param = (df_[2].astype(str).str.replace(',', '.', regex=False)
                    .pipe(pandas.to_numeric, errors='coerce').rename(columname))
        serie_validez = pandas.Series(data='sin_info', index=serie_param.index, name=columname)
        return serie_param, serie_validez
    else:
        raise ValueError("Número inesperado de variables en el header. Se esperaban 1 o 3.")

def elige_param(parametros):
    def normalizar_string(s):
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn') # Normalizar tildes
        return (s.lower().replace(" ", "").replace("_", "")
                .replace("-", "").replace(",", ".")
                .replace("{", "").replace("}", ""))
    d1 = {sust: sust for sust in Nsust}
    d1.update(dict.fromkeys(['pm2.5','pm25','mp25','mp2.5'],'PM25'))
    d1.update(dict.fromkeys(['mp10','pm10'],'PM10'))
    d1.update(dict.fromkeys(['no2','dioxidonitrogeno','diodenx','diox.nitrogeno'], 'NO2'))
    d1.update(dict.fromkeys(['nox','oxidosdenitrogeno','oxidosnitrogeno'], 'NOx'))
    d1.update(dict.fromkeys(['so2','dioxidodeazufre','dioxidoazufre'], 'SO2'))
    d1.update(dict.fromkeys(['o3','ozono'], 'O3'))
    d1.update(dict.fromkeys(['co','monoxidocarbono','monoxidodecarbono'], 'CO'))
    d1.update(dict.fromkeys(['no','monoxidonitrogeno','monoxidodenitrogeno'], 'NO'))
    d1.update(dict.fromkeys(['wdir','dirviento','dv'], 'Dir Viento'))
    d1.update(dict.fromkeys(['wspd','velviento'], 'Vel Viento'))
    d1.update(dict.fromkeys(['rh','hr','humedadrelativa','hum','hume'], 'Humedad Relativa'))
    d1.update(dict.fromkeys(['temp','t','temperatura'],'Temperatura'))

    if parametros is None or parametros == -1:
        return list(range(len(Csust))), Nsust.copy()

    def normalizar(x):
        if isinstance(x, str):
            x = normalizar_string(x)
            if x not in d1:
                raise ValueError(f"Parámetro desconocido: {x}")
            nombre = d1[x]
            return Nsust.index(nombre), nombre
        elif isinstance(x, int):
            return x, Nsust[x]
        else:
            raise TypeError(f"Tipo no soportado: {type(x)}")

    if isinstance(parametros, (str, int)):
        idx, nombre = normalizar(parametros)
        return [idx], [nombre]

    if isinstance(parametros, list):
        idxs = []
        nombres = []
        for x in parametros:
            idx, nombre = normalizar(x)
            idxs.append(idx)
            nombres.append(nombre)
        return idxs, nombres

    raise TypeError("parametros debe ser str, int, list, None o -1")

def input_fecha(fecha):
    today = datetime.date.today()

    # --- datetime/date ---
    if isinstance(fecha, datetime.datetime):
        fecha = fecha.date()
    elif isinstance(fecha, datetime.date):
        pass

    # --- int (días relativos) ---
    elif isinstance(fecha, int):
        if fecha <= 0:
            fecha = today + datetime.timedelta(days=fecha)
        elif fecha > 0:
            raise Exception('No puedes ingresar un entero positivo (fecha futura)')

    # --- string ---
    elif isinstance(fecha, str):
        fecha = fecha.strip()
        if '/' in fecha:
            parts = fecha.split('/')
            if len(parts) != 3:
                raise ValueError("Formato de fecha inválido")

            d, m, y = parts
            if len(y) == 2:
                fmt = '%d/%m/%y'
            elif len(y) == 4:
                fmt = '%d/%m/%Y'
            else:
                raise ValueError("Formato de año inválido")
            fecha = datetime.datetime.strptime(fecha, fmt).date()

        elif fecha.isdigit():
            if len(fecha) == 6:
                fecha = datetime.datetime.strptime(fecha, '%d%m%y').date()
            elif len(fecha) == 8:
                fecha = datetime.datetime.strptime(fecha, '%d%m%Y').date()
            else:
                raise ValueError("Formato de fecha inválido. Debe ser dd/mm/yy, dd/mm/yyyy, ddmmyy o ddmmyyyy")
        else:
            raise ValueError("Formato de fecha inválido. Debe ser dd/mm/yy, dd/mm/yyyy, ddmmyy o ddmmyyyy")
    else:
        raise TypeError("Tipo de fecha no soportado")

    if fecha > today:
        raise ValueError('No se permiten fechas futuras')

    return fecha