from django.core.cache import cache
from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase


class SMSSendCodeViewTestCase(APITestCase):
    phone_number = "+1234567890"

    def setUp(self) -> None:
        cache.clear()

    def test_success(self):
        response = self.client.post(
            reverse_lazy("verification-service:SMSSendCode"),
            {"phone_number": self.phone_number},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("uuid", response.data)

    def test_resent(self):
        response = self.client.post(
            reverse_lazy("verification-service:SMSSendCode"),
            {"phone_number": self.phone_number},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("uuid", response.data)

        # resent
        response = self.client.post(
            reverse_lazy("verification-service:SMSSendCode"),
            {"phone_number": self.phone_number},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
