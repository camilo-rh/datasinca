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

def descargar_serie(inicio, fin, cod_reg, cod_est, cod_param, altura=0, transport=None):
    url = build_url(inicio,fin,cod_param,altura,cod_est,cod_reg)
    transport = transport or Transport()
    return transport.get(url)