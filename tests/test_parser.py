def test_procesar_request_texto_real():
    from datasinca.parser import procesar_request, remcol

    columna = ("Santiago", "Parque O'Higgins", "Ozono.-")

    with open("tests/data/sinca_sample.txt", encoding="latin-1") as f:
        raw_text = f.read()

    df_raw, plot_vars, unidad = procesar_request(raw_text)
    serie_datos, serie_validacion = remcol(df_raw, columna, plot_vars)

    assert serie_datos is not None
    assert serie_validacion is not None

    assert not serie_datos.empty
    assert not serie_validacion.empty

    assert serie_datos.index.equals(serie_validacion.index)

    assert isinstance(unidad, str)
    assert "ppb" in unidad.lower()


def test_procesar_request_valores_correctos():
    from datasinca.parser import procesar_request, remcol

    columna = ("", "", "")

    with open("tests/data/sinca_sample.txt", encoding="latin-1") as f:
        raw_text = f.read()

    df_raw, plot_vars, _ = procesar_request(raw_text)
    serie_datos, _ = remcol(df_raw, columna, plot_vars) 

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

    df_raw, plot_vars, unidad = procesar_request(raw_text)

    assert df_raw == 'psgraph'
    assert plot_vars is None
    assert unidad is None