def test_default_values():
    from datasinca import Sinca
    from datetime import date
    s = Sinca()

    assert set(s._id_regiones) == set(['II', 'V', 'IV', 'IX', 'VIII', 'VII', 'III', 'VI', 'XIV', 'X', 'M', 'I', 'XI', 'XV','XII'])
    assert len(s._id_estaciones) > 100
    assert len(s._cod_params) > 0 and s._cod_params is not None
    assert s.inicio == date.today().strftime('%d/%m/%Y')
    assert s.fin == date.today().strftime('%d/%m/%Y')
    assert len(s._altura) > 4 and 'S/I' in s._altura
    assert s._registro == 'horario'
    s.close()

def test_basic_inputs():
    from datasinca import Sinca
    from datetime import date
    s = Sinca()
    s.inicio = '20240101'
    s.fin = '20240131'
    s.altura = 3
    s.registro = 'diario'
    assert s.inicio == date(2024, 1, 1).strftime('%d/%m/%Y')
    assert s.fin == date(2024, 1, 31).strftime('%d/%m/%Y')
    assert s._altura == [3]
    assert s._registro == 'diario'
    s.close()

def test_region_mapping():
    from datasinca import Sinca
    s = Sinca()
    s.region = 5
    assert s._id_regiones[0] == 'V'
    s.region = 'XI'
    assert s._id_regiones[0] == 'XI'
    s.region = 'tarapaca'
    assert s._id_regiones[0] == 'I'
    s.region = ['metropolitana', 'antofagasta']
    assert set(s._id_regiones) == {'M', 'II'}
    s.close()

def test_estacion_dependencia_region():
    from datasinca import Sinca
    s = Sinca()
    s.estacion = 296
    assert 296 == s.estacion.index[0]
    assert 'XI' == s.region.index[0]
    
    params_cochrane = s._cod_params
    s.region = 'M'
    assert 'M' == s._id_regiones[0]
    assert 273 in s._id_estaciones
    assert 296 not in s._id_estaciones
    assert s._cod_params != params_cochrane
    s.close()

def test_parametro_mapping():
    from datasinca import Sinca
    s = Sinca()
    s.parametro = 'temperatura'
    assert s._cod_params == ['TEMP']
    s.parametro = 'precipitacion'
    assert s._cod_params == ['RAIN']
    s.close()