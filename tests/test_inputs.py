def test_default_values():
    from datasinca import Sinca
    from datetime import date
    s = Sinca()

    assert s.region is None
    assert s.estacion is None
    assert s.parametro is None
    assert s.inicio == date.today().strftime('%d/%m/%Y')
    assert s.fin == date.today().strftime('%d/%m/%Y')
    assert s.altura is None
    assert s.muestreo == 'horario'
    assert s.agregacion is None
    s.close()

def test_basic_inputs():
    from datasinca import Sinca
    from datetime import date
    s = Sinca()
    s.inicio = '01012024'
    s.fin = '31012024'
    s.altura = 3
    s.muestreo = 'diario'
    assert s.inicio == date(2024, 1, 1).strftime('%d/%m/%Y')
    assert s.fin == date(2024, 1, 31).strftime('%d/%m/%Y')
    assert s.altura == [3]
    assert s.muestreo == 'diario'
    s.close()

def test_region_mapping():
    from datasinca import Sinca
    s = Sinca()
    s.region = 5
    assert s.region == ['Valparaíso']
    s.region = 'XI'
    assert s.region == ['Aysén']
    s.region = 'tarapaca'
    assert s.region == ['Tarapacá']
    s.region = ['metropolitana', 'antofagasta']
    assert set(s.region) == {'Metropolitana', 'Antofagasta'}
    s.close()

def test_estacion_dependencia_region():
    from datasinca import Sinca
    s = Sinca()
    s.estacion = 296
    assert 'Cochrane' in s.estacion.values
    assert s.region == ['Aysén']
    assert s.parametro is not None
    
    params_cochrane = s.parametro
    s.region = 'M'
    assert s.region == ['Metropolitana']
    assert 'Parque O\'Higgins' in s.estacion.values
    assert 'Cochrane' not in s.estacion.values
    assert s.parametro != params_cochrane
    s.close()

def test_parametro_mapping():
    from datasinca import Sinca
    s = Sinca()
    s.parametro = 'temperatura'
    assert s._cod_params == ['TEMP']
    s.parametro = 'precipitacion'
    assert s._cod_params == ['RAIN']

