def test_procesar_request_texto_real():
    from datasinca.parser import procesar_request

    columna = ("Santiago", "Parque O'Higgins", "Ozono.-")

    with open("tests/data/sinca_sample.txt", encoding="latin-1") as f:
        raw_text = f.read()

    serie_datos, serie_validez, unidad = procesar_request(raw_text, columna)

    assert serie_datos is not None
    assert serie_validez is not None

    assert not serie_datos.empty
    assert not serie_validez.empty

    assert serie_datos.index.equals(serie_validez.index)

    assert isinstance(unidad, str)
    assert "ppb" in unidad.lower()


def test_procesar_request_valores_correctos():
    from datasinca.parser import procesar_request

    columna = ("", "", "")

    with open("tests/data/sinca_sample.txt", encoding="latin-1") as f:
        raw_text = f.read()

    serie_datos, _, _ = procesar_request(raw_text, columna)

    valores = serie_datos.tolist()
    assert len(serie_datos) == 691

    assert serie_datos.isna().sum() < len(serie_datos)

    # tipo consistente
    assert all(isinstance(x, (int, float)) for x in serie_datos.dropna())

    valores = serie_datos.tolist()
    
    assert valores[300] == 31
    assert valores[0] == 6
    assert valores[-1] == 20


def test_procesar_request_sin_datos():
    from datasinca.parser import procesar_request

    raw_text = "psgraph: Could not load macro: Can't open macro file"

    columna = ("", "ESTACION DE PRUEBA", "PARAMETRO DE PRUEBA")

    serie_datos, serie_validez, unidad = procesar_request(raw_text, columna)

    assert serie_datos is None
    assert serie_validez is None
    assert unidad is None