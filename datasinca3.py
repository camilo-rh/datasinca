#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 00:25:28 2020

@author: Camilo Ramírez Herrera
"""


from requests import get
import pandas
from termcolor import cprint
import datetime
import re
from datasinca._info import Csust, Nsust, reg, comuna, EstacionN, EstacionC, idest

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

def datasinca(inicio,fin,parametros,*opcional,R=1,est=-1,registros='max',altura=0, aviso_codigo=True, aviso_estacion=True, aviso_descarga=True):
    if type(R)==str: R = reg.index(R)
    parametros, paramname = elige_param(parametros)

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
   
# a: Reg[R]
# b: Estacion[R][x]
# c: Csust[x]
    urlest ='https://sinca.mma.gob.cl/index.php/estacion/index/id/'  # url info de estaciones
    
    frames = []
    for i,ind in enumerate(parametros):
        for j in est:
            if aviso_descarga:
                print([paramname[i],EstacionN[R][j]],':Descargando...', end='\t')
            if parametros.index(ind)==0:
                mensaje= re.search('"mensajeStn".*</div', get(urlest + idest[R][j]).text )
                print(urlest + idest[R][j])
                if mensaje and aviso_estacion:
                    mensaje = re.sub('&(?P<vocal>[aeiou])acute;', r'\g<vocal>', mensaje.group()[13:-5])
                    mensaje = re.sub('<p>|</p>',lambda x: '',mensaje)
                    cprint('Mensaje de la estación ' + EstacionN[R][j], 'red', attrs=['bold'])
                    cprint(mensaje,'red',attrs=['bold'])
            # inicio,fin,c_param,altura,c_est,c_region
            url = build_url(inicio, fin, Csust[ind], altura, EstacionC[R][j], reg[R])
            try:
                req = get(url)
                reqt = req.text[req.text.find('#DATA') + 6:req.text.find('EOF')].replace(' ','')
                reqsplit = [x.split(',') for x in reqt.split('\n')]
                df = pandas.DataFrame(reqsplit)
                index= pandas.to_datetime(df.iloc[:,0] + df.iloc[:,1], errors='coerce', format='%y%m%d%H%M')
                if aviso_descarga:
                    print('descarga lista')
            except Exception as ex:
                if str(ex).startswith('HTTPConnectionPool'):
                    cprint('No hay respuesta, revisar conexión a internet','white','on_blue')
                    try:                                
                        req = get(url[Csust[ind]](reg[R],EstacionC[R][j],Csust[ind]))
                        reqt = req.text[req.text.find('#DATA') + 6:req.text.find('EOF')].replace(' ','')
                        reqsplit = [x.split(',') for x in reqt.split('\n')]
                        df = pandas.DataFrame(reqsplit)
                        index= pandas.to_datetime(df.iloc[:,0] + df.iloc[:,1], errors='coerce', format='%y%m%d%H%M')
                    except Exception as ex:
                        if str(ex).startswith('HTTPConnectionPool'):
                            cprint('No hay respuesta, revisar conexión a internet','white','on_blue')
                    
                elif req.text.startswith("psgraph: Could not load macro: Can't open macro file"):
                    cprint('DATOS CAÍDOS O NO HAY DATOS DE ' + paramname[i] + ' en '+EstacionN[R][j], 'white', 'on_red', attrs=['bold'])
                    continue
                else:
                    raise
            try:
                df.set_index(index,inplace=True)
                df.dropna(inplace=True)
                df.drop(df.columns[:2],axis=1,inplace=True)
                unidad=re.search('Plot var',req.text,re.IGNORECASE)
                unidad = re.search(r'\([^)]*', req.text[unidad.end():])[0][1:]
                if opcional:
                    columnas = (comuna[R][j], EstacionN[R][j], paramname[i], unidad, eval(opcional[0])[R][j])
                    column_names = ['comuna','estacion','parametro', 'unidad',opcional[0]]
                else:
                    columnas = (comuna[R][j], EstacionN[R][j], paramname[i], unidad)
                    column_names = ['comuna','estacion','parametro', 'unidad']
                remwh=remcol(df,columnas,reg=registros)
                frames.append(pandas.to_numeric(remwh))
            except Exception as ex:
                if ex.args[0][:22]=='Unable to parse string':
                    frames.append(pandas.to_numeric(remwh.str.replace(',','.')))
                else:
                    raise
    
    if frames:
        frame = pandas.concat(frames,axis=1)
        frame.columns.names = column_names
    else:
        frame = pandas.DataFrame([],columns=column_names)
    return frame



def remcol(df,columname,reg='max'):
    registros={'val': -1, 'prelim': 0, 'noval': 1, 'max': len(df.columns)-2 }
    # dflen=df.copy()
    dfalreg=df.copy()
    x=registros[reg]
    if x+1 >= len(df.columns):
        x = len(df.columns)-2
    # for i in range(x,-1,-1):
    #     dflen[dflen.columns[i]].loc[dflen[dflen.columns[i]]=='']= dflen[dflen.columns[i+1]].loc[dflen[dflen.columns[i]]=='']
    # remcolen=dflen.iloc[:,0].rename(columname)
    
    for i in range(x,-1,-1):
        dfalreg[dfalreg.columns[i]] = dfalreg[dfalreg.columns[i]].where(dfalreg.iloc[:,i]!='',dfalreg[dfalreg.columns[i+1]])
    remcolwh=dfalreg.iloc[:,0].rename(columname)
    return remcolwh #,remcolen]

def elige_param(parametros):
    def normalizar_string(s):
        return (s.lower().replace(" ", "").replace("_", "")
                .replace("-", "").replace(",", ".")
                .replace("{", "").replace("}", "")
                )
    d1 = {sust: sust for sust in Nsust}
    d1.update(dict.fromkeys(['pm2.5','pm25','mp25','mp2.5'],'PM25'))
    d1.update(dict.fromkeys(['mp10','pm10'],'PM10'))
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
    if type(fecha)==str:
        if not bool(fecha):
            fecha = datetime.date.today()
        elif len(fecha)<4:
            try:
                fecha = int(fecha)
            except:
                pass
        elif '/' in fecha:
            fecha = datetime.datetime.strptime(fecha,'%d/%m/%y').date()
        else:
            fecha = datetime.datetime.strptime(fecha,'%d%m%y').date()
    if type(fecha)==int:
        if fecha<=0 and fecha>-10000:
            a = datetime.date.today()+datetime.timedelta(days=fecha)
            fecha = datetime.date(a.year,a.month,a.day)
        elif fecha>0:
            raise Exception('No puedes ingresar un entero positivo pues expresaría una fecha futura')
        else:
            raise Exception('Ingresaste un número x=<-10000, para referirte a una fecha hace más de 10 mil días, eso es mucho tiempo ¿o no?')
    if datetime.date.today() < fecha:
        raise ValueError('Fecha inapropiada: No es posible descargar datos de fechas futuras')
    if not ('timestamp' in str(type(fecha)) or 'date' in str(type(fecha))):
        raise TypeError('Esta fecha debe ser un string en formato ddmmyy o una variable de tipo timestamp/date o un int entre -999 y 0')
    return fecha