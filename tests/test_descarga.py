def test_descarga_estacion():
    from datasinca import Sinca

    s = Sinca()
    try:
        res = s.descarga(
            estacion=273,
            parametro='MP2.5',
            inicio='01012024',
            fin='31012024'
        )
    finally:
        s.close()

    assert res is not None
    assert not res.data.empty
    assert res.data.index.equals(res.validacion.index)


def test_mensaje_tabla():
    from datasinca.downloader import descargar_mensaje_estacion
    transport = FakeTransport("tests/data/msj_pudahuel.txt")

    resultado = descargar_mensaje_estacion(transport, 123, include_tablas=True)

    assert resultado is not None
    assert isinstance(resultado, str)
    assert "Atenuación" in resultado


class FakeTransport:
    def __init__(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            self.text = f.read()

    def get(self, url):
        return self