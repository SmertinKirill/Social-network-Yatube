from django.test import TestCase, Client
from django.urls import reverse


class CoreViewTest(TestCase):
    def test_error(self):
        self.guest_client = Client()
        response = self.guest_client.get('/random-text/')
        self.assertTemplateUsed(response, 'core/404.html') 
