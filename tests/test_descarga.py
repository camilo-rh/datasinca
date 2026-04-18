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
    assert res.data.index.equals(res.validez.index)