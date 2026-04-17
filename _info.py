# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 01:01:28 2024

@author: Camilo
"""
import pandas as pd

class Info:
    def __init__(self):
        self.parametros = Nsust
        self.regiones = reg
        # self.comunas = {r:set(comuna[i]) for i,r in enumerate(reg)}
        self.estaciones = estaciones
        self.df = dfinfo
    def __str__(self):
        return salida
    def __repr__(self):
        return salida

Csust = ['PM25' , 'PM10' ,'0003' , '0NOX' , '0001' , '0008' ,'0004' ,'0002','WDIR','WSPD' , 'RHUM','TEMP']
Nsust = ['PM25' , 'PM10' ,'NO2' , 'NOx' , 'SO2' , 'O3' ,'CO' , 'NO', 'Dir Viento', 'Vel Viento', 'Humedad Relativa', 'Temperatura']
# reg = ['RV', 'RM','RVIII', 'RIX', 'RX' , 'RXI']
reg = ['RXV', 'RI', 'RII', 'RIII', 'RIV', 'RV', 'RM', 'RVI', 'RVII',
   'RVIII', 'RIX', 'RXIV', 'RX', 'RXI', 'RXII']
REGIONES = {
    'XV': 'RXV',
    'I': 'RI',
    'II': 'RII',
    'III': 'RIII',
    'IV': 'RIV',
    'V': 'RV',
    'RM': 'RM',
    'VI': 'RVI',
    'VII': 'RVII',
    'VIII': 'RVIII',
    'IX': 'RIX',
    'XIV': 'RXIV',
    'X': 'RX',
    'XI': 'RXI',
    'XII': 'RXII'
}

REGIONES_NOMBRE = {
    'Arica y Parinacota': 'RXV',
    'Tarapacá': 'RI',
    'Antofagasta': 'RII',
    'Atacama': 'RIII',
    'Coquimbo': 'RIV',
    'Valparaíso': 'RV',
    'Metropolitana': 'RM',
    "O'Higgins": 'RVI',
    'Maule': 'RVII',
    'Biobío': 'RVIII',
    'La Araucanía': 'RIX',
    'Los Ríos': 'RXIV',
    'Los Lagos': 'RX',
    'Aysén': 'RXI',
    'Magallanes': 'RXII'
}
comuna = [  # TODAS (frec horaria). Comunas correspondientes a las estaciones en EstacionN y EstacionC
    ['Arica'],  #'RXV'
    ['Alto Hospicio'], # 'RI'
    ['Antofagasta', 'Antofagasta', 'Calama', 'Calama', 'Calama', #'RII'
    'Calama', 'Calama', 'Calama', 'Calama', 'Calama', 'Calama',
    'Calama', 'Calama', 'María Elena', 'Mejillones', 'Mejillones',
    'Mejillones', 'Mejillones', 'Sierra Gorda', 'Taltal', 'Taltal',
    'Tocopilla', 'Tocopilla', 'Tocopilla', 'Tocopilla', 'Tocopilla',
    'Antofagasta', 'Antofagasta', 'Tocopilla'],
    ['Copiapó', 'Copiapó', 'Copiapó', 'Copiapó', 'Copiapó', # 'RIII'
    'Diego de Almagro', 'Diego de Almagro', 'Freirina', 'Freirina',
    'Freirina', 'Huasco', 'Huasco', 'Huasco', 'Huasco', 'Huasco',
    'Huasco', 'Huasco', 'Huasco', 'Huasco', 'Huasco', 'Huasco',
    'Tierra Amarilla', 'Tierra Amarilla'],
    ['Andacollo', 'Andacollo', 'Andacollo', 'Andacollo', 'Andacollo', # 'RIV'
    'Coquimbo', 'Coquimbo', 'Salamanca'], 
    ['Calera', 'Calera', 'Calera', 'Catemu', 'Catemu', 'Catemu', # 'RV'
    'Catemu', 'Concón', 'Concón', 'Concón', 'Concón', 'Concón',
    'Concón', 'La Cruz', 'Los Andes', 'Panquehue', 'Puchuncaví',
    'Puchuncaví', 'Puchuncaví', 'Puchuncaví', 'Puchuncaví',
    'Puchuncaví', 'Quillota', 'Quillota', 'Quillota', 'Quillota',
    'Quilpué', 'Quintero', 'Quintero', 'Quintero', 'Quintero',
    'Quintero', 'Valparaíso', 'Viña del Mar', 'Puchuncaví', 'Quilpué',
    'Quintero'], 
    ['Cerrillos', 'Cerrillos', 'Cerrillos','Cerro Navia', 'El Bosque', # 'RM'
    'Independencia', 'La Florida', 'Las Condes', 'Pudahuel',
    'Puente Alto', 'Quilicura', 'Quilicura', 'Santiago', 'Talagante'],
    ['Codegua', 'Machalí', 'Machalí', 'Machalí', 'Machalí', 'Mostazal', # 'RVI'
    'Mostazal', 'Rancagua', 'Rancagua', 'Rengo', 'Requinoa',
    'Requinoa', 'San Fernando', 'Codegua'],
    ['Cauquenes', 'Curicó', 'Linares', 'Talca', 'Talca', 'Talca',  # 'RVII'
    'Teno', 'Teno'], 
    ['Cabrero', 'Chiguayante', 'Chiguayante', 'Chillán', 'Chillán',  # 'RVIII'
    'Concepción', 'Coronel', 'Coronel', 'Coronel', 'Coronel',
    'Coronel', 'Coronel', 'Coronel', 'Coronel', 'Curanilahue',
    'Hualpén', 'Hualpén', 'Hualpén', 'Hualqui', 'Laja', 'Los Angeles',
    'Los Angeles', 'Los Angeles', 'Nacimiento', 'Nacimiento',
    'Nacimiento', 'Quillón', 'Quillón', 'Ránquil',
    'San Pedro de la Paz', 'Talcahuano', 'Talcahuano', 'Talcahuano',
    'Talcahuano', 'Talcahuano', 'Tomé', 'Coronel'], 
    ['Padre las Casas', 'Padre las Casas', 'Temuco', 'Temuco', 'Temuco'], # 'RIX'
    ['Lago Ranco', 'La Unión', 'Máfil', 'Máfil', 'Máfil','Valdivia', 'Valdivia'], # 'RXIV'
    ['Osorno', 'Osorno', 'Puerto Montt', 'Puerto Montt', 'Puerto Montt', # 'RX'
    'Puerto Montt', 'Puerto Varas'], 
    ['Aysén', 'Coyhaique', 'Coyhaique'], # 'RXI'
    ['Punta Arenas']  # 'RXII'
    ]

EstacionN = [ # todas
    ['Arica'],
    ['Alto Hospicio'], 
    ['Antofagasta', 'Sur', 'Chiu Chiu', 'Club Deportivo 23 de Marzo',
    'Colegio Pedro Vergara Keller', 'Estación Centro',
    'Hospital el Cobre', 'Nueva ChiuChiu', 'Oasis',
    'Servicio Médico Legal', 'Aukahuasi', 'San José', 'Villa Caspana',
    'Hospital', 'Jardín Infantil Integra', 'Juan Jose Latorre',
    'Compañía de Bomberos', 'Ferrocarriles', 'Sierra Gorda ', 'Paposo',
    'Punto de Máximo Impacto', 'Bomberos', 'Gobernación', 'Super Site',
    'Tres Marias', 'Escuela E-10', 'Playa Blanca', 'Rendic', 'Centro'],
    ['Copiapo Sivica', 'Copiapó', 'Los Volcanes', 'Paipote',
    'San Fernando', 'CAP', 'Doña Ines', 'SM6 ', 'SM7 ', 'SM8 ',
    'Huasco Sivica', '21 de Mayo', 'EME F', 'EME M', 'EME ME',
    'Huasco II', 'SM1 ', 'SM2', 'SM3 ', 'SM4 ', 'SM5 ',
    'Tierra Amarilla', 'Pabellón'], 
    ['Andacollo', 'Chepiquilla', 'El Sauce', 'Hospital',
    'Urmeneta - Plaza Centenario', 'Coquimbo', 'La Serena',
    'Cuncumen '], 
    ['La Cruz, Colbún', 'La Calera', 'Rural 1', 'Catemu',
    'Chagres Meteorologia', 'Romeral', 'Santa Margarita', 'Concón MMA',
    'Colmo', 'Concón', 'Junta de Vecinos', 'Las Gaviotas',
    'Concón sur', 'La Cruz, Melón', 'Los Andes', 'Lo Campo',
    'Puchuncaví', 'Campiche', 'La Greda', 'Los Maitenes', 'Ventanas',
    'Terminal Concentrados', 'Cuerpo de Bomberos ', 'La Palma',
    'San Pedro', 'Manzanar', 'Quilpue', 'Centro Quintero', 'Loncura',
    'Quintero', 'Sur', 'Valle Alegre', 'Valparaiso', 'Viña del Mar',
    'Meteorológica Principal', 'ARMAT', 'Central Quintero'],
    ['Cerrillos', 'Cerrillos I', 'Cerrillos II', 'Cerro Navia', 'El Bosque',
    'Independencia', 'La Florida', 'Las Condes', 'Pudahuel',
    'Puente Alto', 'Quilicura', 'Quilicura I', "Parque O'Higgins",
    'Talagante'],
    ['Codegua', 'Cauquenes', 'Cipreses', 'Coya Población', 'Sewell',
    'Casas de Peuco', 'San Francisco de Mostazal', 'Rancagua I',
    'Rancagua II', 'Rengo', 'MVC', 'Totihue', 'San Fernando',
    'Subestación Candelaria'], 
    ['Cauquenes Sivica', 'Curicó', 'Linares', 'La Florida',
    'U.C. Maule', 'Universidad de Talca', 'Teno, CEMENTOS BIO BIO',
    'Teno, ENLASA'], 
    ['Colicheu', 'Punteras', 'Meteorológica, Chiguayante',
    'INIA, Chillán', 'Puren', 'Kingston College', 'Cerro Merquín',
    'Calabozo', 'Coronel Norte', 'Coronel Sur', 'Escuadron, ENEL',
    'Lagunillas, ENEL', 'Lota rural', 'Lota urbana',
    'Balneario Curanilahue', 'Bocatoma', 'ENAP Price', 'JUNJI',
    'Hualqui', 'Laja', '21 de mayo', 'Los Ángeles Oriente',
    'CESFAM, Los Ángeles', 'Club de Empleados', 'Entre Ríos',
    'Lautaro', 'Cayumanqui', 'Quillón', 'Nueva  Aldea', 'MASISA Mapal',
    'Consultorio - San Vicente', 'San Vicente, Bomberos', 'Indura',
    'Inpesca', 'Nueva Libertad', 'Liceo Polivalente',
    'Escuadron, ENESA'], 
    ['Padre Las Casas II', 'Padre Las Casas', 'Las Encinas Temuco',
    'Ñielol', 'Museo Ferroviario'], 
    ['CESFAM Lago Ranco', 'La Union', 'Consultorio Máfil', 'Fundo La Ribera',
     'Vivero Los Castaños', 'Valdivia',
    'Valdivia 2'],
    ['Osorno', 'Entre Lagos', 'Alerce', 'Mirasol', 'Trapén Norte',
    'Trapén Sur', 'Puerto Varas'], 
    ['Vialidad', 'Coyhaique', 'Coyhaique II'], 
    ['Punta Arenas'], 
    ]

EstacionC = [  # TODAS
    ['F01'],  # 'RXV'
    ['117'],  # 'RI'
    ['237', '213', '228', '233', '235', '236', '217', '253', '234',  #'RII'
    '227', '219', '220', '218', '210', '209', '252', '221', '207',
    '204', '216', '215', '230', '201', '251', '231', '222', '226',
    '225', '205'],
    ['332', '311', '315', '314', '313', '320', '321', '306', '307',  # 'RIII'
    '308', '333', '330', '310', '309', '324', '329', '301', '302',
    '303', '304', '305', '312', '316'],
    ['420', '411', '412', '414', '415', '426', '425', '424'], # 'RIV'
    ['534', '517', '518', '522', '537', '523', '524', '560', '511',  # 'RV'
    '509', '535', '512', '510', '519', '532', '521', '505', '501',
    '503', '504', '548', '502', '513', '515', '514', '533', '549',
    '539', '547', '540', '506', '507', '550', '529', '508', '525',
    '546'],
    ['D31', 'D16', 'D35','D18', 'D17', 'D11', 'D12', 'D13', 'D15', 'D27',  # 'RM'
    'D30', 'D29', 'D14', 'D28'], 
    ['601', '606', '605', '604', '608', '603', '602', '609', '615', # 'RVI'
    '611', '613', '614', '612', '610'], 
    ['714', '709', '713', '703', '710', '711', '704', '705'],   # 'RVII'
    ['876', '854', '833', '810', '873', '827', '831', '809', '878',  # 'RVIII'
    '816', '880', '879', '859', '860', '832', '805', '838', '804',
    '841', '826', '875', '874', '836', '818', '852', '870', '871',
    '850', '846', '819', '802', '801', '807', '806', '837', '830',
    '881'], 
    ['902', '903', '901', '905', '904'],  # 'RIX' 
    ['E06', 'E04', 'E01', 'E05', 'E02','E03', 'E08'],  # 'RXIV' 
    ['A01', 'A04', 'A08', 'A07', 'A02', 'A03', 'A09'],  # 'RX'
    ['B05', 'B03', 'B04'],  # 'RXI'
    ['C05']  # 'RXII'
    ]
idest = [    # esta lista sirve solo para buscar algun aviso en la pagina (tiene misma forma que EstacionC,EstacionN y comuna)
    ['232'], 
    ['157'], 
    ['259', '70', '33', '46', '234', '207', '222', '275', '124', '282',
    '134', '12', '108', '69', '3', '68', '2', '1', '279', '4', '66',
    '255', '71', '72', '178', '270', '172', '169', '274', '128', '39',
    '130', '51'],
    ['176', '223', '248', '196', '139', '45', '38', '114', '44', '258',
    '187', '265', '219', '201', '205', '175', '163', '179', '243',
    '192', '252', '214', '121', '224', '40'],
    ['171', '156', '150', '268', '148', '194', '95', '32', '9', '15',
    '144', '257', '8', '137', '16', '17'],
    ['13', '7', '145', '165', '131', '253', '132', '202', '177', '185',
    '89', '193', '140', '14', '266', '210', '200', '182', '278', '136',
    '188', '109', '73', '141', '142', '41', '6', '155', '5', '204',
    '208', '129', '183', '251', '203', '174', '247'], 
    ['206', '116', '290','228', '260', '272', '262', '239', '190', '233',  # RM
    '271', '149', '273', '197'], 
    ['113', '59', '173', '246', '225', '65', '58', '112', '250', '220', # 'RVI'
    '212', '152', '47', '244'], 
    ['287', '269', '53', '181', '276', '230', '217', '31', '30'], # 'RVII'
    ['226', '235', '83', '215', '216', '261', '227', '118', '280', # 'RVIII'
    '221', '286', '283', '285', '135', '170', '189', '277', '105',
    '43', '242', '119', '236', '211', '67', '245', '76', '213', '231',
    '254', '184', '27', '241', '127', '91', '104', '209', '240', '195'],
    ['263', '18', '186', '237', '110'],              # 'RIX'    
    ['115', '180', '126', '49', '94', '267', '218'], # 'RXIV'   
    ['229', '111', '198', '54', '74', '93', '281'], 
    ['166', '238', '264'], 
    ['191'], 
    ]

l=[]
for i,r in enumerate(reg):
    l.append(pd.DataFrame([[r]*len(comuna[i]),comuna[i],EstacionN[i],EstacionC[i]],index=['region','comuna','estacion','codigo']).T)
dfinfo = pd.concat(l, ignore_index=True)

estaciones = {r:{j:EstacionN[i][j] for j,_ in enumerate(EstacionN[i])} for i,r in enumerate(reg)}
salida = ''
for r,estit in estaciones.items():
    salida += f'{r}:\n'
    for j,est in estit.items():
        salida += f'\t  {j}:'.ljust(6) + f'{est}\n'