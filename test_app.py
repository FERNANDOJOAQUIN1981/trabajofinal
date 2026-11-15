import unittest
from app import app, init_db

class NasaTrainerTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def test_1_login_page_loads(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Iniciar Sesi', res.data)

    def test_2_login_admin_success(self):
        res = self.client.post('/', data={'username': 'admin', 'password': '123'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Simulador de Base Lunar', res.data)

    def test_3_role_protection_for_astronaut(self):
        self.client.post('/register', data={'username': 'cadete_prueba', 'password': '123', 'rol': 'astronauta'})
        self.client.post('/', data={'username': 'cadete_prueba', 'password': '123'})
        res = self.client.get('/admin/escenarios', follow_redirects=True)
        self.assertIn(b'Acceso denegado', res.data)

    def test_4_crud_guardar_mision(self):
        self.client.post('/', data={'username': 'admin', 'password': '123'})
        res = self.client.post('/guardar_mision', data={
            'nombre_cadete': 'Cadete Apollo',
            'energia': 65,
            'oxigeno': 80,
            'escudo': 55,
            'estado': 'Misión Cumplida'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Cadete Apollo', res.data)

if __name__ == '__main__':
    unittest.main()