import requests

BASE_URL = "https://sinca.mma.gob.cl"
URL_ESTACION = BASE_URL + "/index.php/estacion/index/id/"
URL_DESCARGA = BASE_URL + "/cgi-bin/APUB-MMA/apub.tsindico2.cgi?outtype=txt&macro=./"

def build_url(inicio,fin,codparam,altura,codest,codreg):
        codaltura = str(altura).rjust(3, '0')
        url = URL_DESCARGA
        if codparam in ['PM25' , 'PM10' ,'0003' , '0NOX' , '0001' , '0008' ,'0004','0002']:
            url += codreg +'/'+ codest +'/Cal/'+ codparam +'//'+ codparam +'.horario.horario'
        elif codparam in ['TEMP','WSPD', 'RHUM']:
            url += codreg +'/'+ codest +'/Met/'+ codparam +'//horario_'+codaltura
        elif codparam in ['WDIR']:
            url += codreg +'/'+ codest +'/Met/'+ codparam +'//horario_'+codaltura+'_spec'
        else:
            raise Exception(f'Parámetro no reconocido: {codparam}')
        url += '.ic&from='+ inicio +'&to='+ fin +'&path=/usr/airviro/data/CONAMA/&lang=esp&rsrc=&macropath='
        return url

class Transport:
    def __init__(self, timeout=10, session=None):
        self.timeout = timeout
        self.session = session or self._build_session()

    def _build_session(self):
        s = requests.Session()
        s.headers.update({"User-Agent": "datasinca/0.1"}) # User-Agent propio para identificar datasinca frente al servidor
        return s
    
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

def descargar_serie(inicio, fin, cod_reg, cod_est, cod_param, altura=0, transport=None):
    url = build_url(inicio,fin,cod_param,altura,cod_est,cod_reg)
    transport = transport or Transport()
    return transport.get(url)


# def datasinca(inicio,fin,parametros,R=1,est=-1,altura=0, aviso_codigo=True, aviso_estacion=True, aviso_descarga=True):
#     if type(R)==str: R = reg.index(R)
#     parametros, paramname = elige_param(parametros)
#     column_names = ['comuna','estacion','parametro']

#     if aviso_codigo:
#         cprint('Ojo, algunas regiones tienen diferente tamaño de las listas:\n     comuna,EstacionC,EstacionN,idest:','white','on_red')
#         for i,x in enumerate(comuna):
#             print(i, (reg[i]+':').ljust(7,' '),len(comuna[i]),len(EstacionC[i]),len(EstacionN[i]),len(idest[i]))
    
#     inicio = input_fecha(inicio)
#     fin = input_fecha(fin)
#     if aviso_descarga: cprint(f'Descarga de datos SINCA desde {inicio.strftime('%d/%m/%Y')} hasta {fin.strftime('%d/%m/%Y')}', attrs=['bold'])
#     inicio = inicio.strftime('%y%m%d')
#     fin = fin.strftime('%y%m%d')
#     if est==None or est==-1:  est = range(0,len(EstacionN[R]))
#     if isinstance(est,int): est=[est]
   
#     urlest ='https://sinca.mma.gob.cl/index.php/estacion/index/id/'  # url info de estaciones
    
#     df_param = []
#     df_validez = []
#     unidades = {}
#     transport = Transport()
#     for i,ind in enumerate(parametros):
#         for j in est:
#             if aviso_descarga:
#                 print(f'{paramname[i]} - estación:{EstacionN[R][j]} - comuna:{comuna[R][j]}')
#             if parametros.index(ind)==0:
#                 mensaje= re.search('"mensajeStn".*</div', transport.get(urlest + idest[R][j]).text )
#                 if mensaje and aviso_estacion:
#                     mensaje = re.sub('&(?P<vocal>[aeiou])acute;', r'\g<vocal>', mensaje.group()[13:-5])
#                     mensaje = re.sub('<p>|</p>',lambda x: '',mensaje)
#                     cprint('Mensaje de la estación ' + EstacionN[R][j], 'red', attrs=['bold'])
#                     cprint(mensaje,'red',attrs=['bold'])
#             # inicio,fin,c_param,altura,c_est,c_region
#             url = build_url(inicio, fin, Csust[ind], altura, EstacionC[R][j], reg[R])
#             req = None
#             try:
#                 req = transport.get(url)
#                 df, index = procesar_req(req)
#                 if aviso_descarga:
#                     print('descarga lista')
#             except requests.exceptions.ConnectionError:
#                 cprint(f'No se pudo conectar a SINCA para {paramname[i]} en {EstacionN[R][j]}','white','on_blue')
#             except Exception as ex:
#                 if req is not None and req.text.startswith(
#                     "psgraph: Could not load macro: Can't open macro file"
#                 ):
#                     cprint(f'DATOS CAÍDOS O NO HAY DATOS DE {paramname[i]} en {EstacionN[R][j]}.', 'white', 'on_red', attrs=['bold'], end=' ')
#                     print('URL: ' + urlest + idest[R][j])
#                     continue
#                 else:
#                     raise
#             df.set_index(index,inplace=True)
#             df.dropna(inplace=True)
#             df.drop(df.columns[:2],axis=1,inplace=True)
#             plot_vars = get_plot_vars(req.text)
#             unidad = re.search(r'\([^)]*', plot_vars[0])[0][1:]
#             columna = (comuna[R][j], EstacionN[R][j], paramname[i])
#             unidades[columna] = unidad
#             serie_param, serie_validez = remcol(df, columna, plot_vars)
#             df_param.append(serie_param)
#             df_validez.append(serie_validez)
    
#     if df_param:
#         df_param = pd.concat(df_param,axis=1)
#         df_param.columns.names = column_names
#         df_validez = pd.concat(df_validez,axis=1)
#         df_validez.columns.names = column_names
#     else:
#         df_param = pd.DataFrame([],columns=column_names)
#         df_validez = pd.DataFrame([],columns=column_names)
#     df_param.attrs['fuente'] = 'SINCA'
#     df_param.attrs['unidades'] = unidades
#     return DataSINCA(df_param, df_validez)