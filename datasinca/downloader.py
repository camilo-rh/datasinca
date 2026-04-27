import requests
import re
import html
import pandas as pd
from io import StringIO

BASE_URL = "https://sinca.mma.gob.cl"
URL_ESTACION = BASE_URL + "/index.php/estacion/index/id/"
URL_DESCARGA = BASE_URL + "/cgi-bin/APUB-MMA/apub.tsindico2.cgi?outtype=txt&macro=./"
AGREGACION_DEFECTO = {'horario': 'horario',
                     'diario': 'diario',
                     'discreto': 'diario'}

PARAMS_CAL = {'PM25', 'PM10', '0003', '0NOX', '0001', '0008', '0004', '0002', 'CTOT', 'TRSG',
                'THCM', 'PM2D', '00Cu', 'PM1D', 'ARSE', '00Pb', '0CH4', 'CORG', '00Ni', 'NMHC'}
PARAMS_MET = {'TEMP', 'WSPD', 'RHUM', 'PRES', 'SOL', 'RAIN', 'GLOB'}
PARAMS_WDIR = {'WDIR'}

def build_url(inicio,fin,codparam,altura,codest,codreg,muestreo,agregacion):
        codaltura = str(altura if altura != "S/I" else 0).rjust(3, '0')
        agregacion = AGREGACION_DEFECTO.get(muestreo, 'horario') if agregacion is None else agregacion
        url = f"{URL_DESCARGA}{codreg}/{codest}/"

        if codparam in PARAMS_CAL:
            url += f'Cal/{codparam}//{codparam}.{muestreo}.{agregacion}'
        elif codparam in PARAMS_MET:
            url += f'Met/{codparam}//{muestreo}_{codaltura}'
        elif codparam in PARAMS_WDIR:
            url += f'Met/{codparam}//{muestreo}_{codaltura}_spec'
        else:
            raise ValueError(f'Parámetro no reconocido: {codparam}')
        
        url += f'.ic&from={inicio}&to={fin}&path=/usr/airviro/data/CONAMA/&lang=esp&rsrc=&macropath='
        return url

class Transport:
    def __init__(self, timeout=10, session=None):
        self.timeout = timeout
        self._external_session = session is not None
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

    def close(self):
        if not self._external_session and self.session:
            self.session.close()

def descargar_serie(inicio, fin, cod_reg, cod_est, cod_param, altura, muestreo, agregacion, transport=None):
    url = build_url(inicio,fin,cod_param,altura,cod_est,cod_reg,muestreo,agregacion)
    transport = transport or Transport()
    return transport.get(url)


def descargar_mensaje_estacion(transport, id_est, include_tablas=False):
    text = transport.get(URL_ESTACION + str(id_est)).text

    match = re.search(r'"mensajeStn".*?</div', text, flags=re.DOTALL)
    if not match:
        return None
    mensaje = match.group()[13:-5]

    if not include_tablas and re.search(r'<table\b', mensaje, flags=re.IGNORECASE):
        return None
    if include_tablas:
        match = re.search(r'<table\b.*?</table>', mensaje, flags=re.DOTALL)
        if not match:
            return None
        tabla = match.group()
        df = pd.read_html(StringIO(tabla))[0]
        tabla = df.to_string(index=False)
        tabla = "\n".join(f"\t{line}" for line in tabla.splitlines())
        prev_mensaje = (limpiar_mensaje(mensaje[:match.start()]) + "\n")
        post_mensaje = ("\n" + limpiar_mensaje(mensaje[match.end():])).rstrip()
        mensaje = prev_mensaje + tabla + post_mensaje
    else:
        mensaje = limpiar_mensaje(mensaje)
    return mensaje

def limpiar_mensaje(mensaje):
    mensaje = re.sub(r'<[^>]+>', '', mensaje)
    mensaje = html.unescape(mensaje)
    mensaje = re.sub(r'\s+', ' ', mensaje).strip()
    return mensaje